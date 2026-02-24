"""
Interlock Tech-Transfer Agent — single tool-calling ReAct agent.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import UUID, uuid4

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from models.main import (
    CurrencyAmount,
    LaborNode,
    OperationNode,
    OpType,
    PartNode,
    QuantityInput,
)
from models.main import (
    ToolNode as MfgToolNode,
)
from orm.main import (
    create_labor,
    create_tool,
    delete_part,
    get_ancestors,
    get_created_by,
    get_full_timeline,
    get_leaf_currencies,
    get_part,
    get_tree_json,
    list_labor,
    list_parts,
    list_tools,
    manufacture_part,
    purchase_part,
    update_part,
    validate_tree,
)

# ═══════════════════════════════════════════════════════════════════════
#  Tool Definitions
# ═══════════════════════════════════════════════════════════════════════

# ── Read / Query Functions ────────────────────────────────────────────


def search_parts(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search for parts by listing them. Returns a list of dicts with ID and name.
    Args:
        query: Not used for filtering yet, but describes what you're looking for.
        limit: Max number of parts to return.
    """
    parts = list_parts(limit=limit)
    return [{"id": str(p.id), "name": p.name} for p in parts]


def get_part_details(part_id: str) -> dict[str, Any]:
    """Get full details of a specific part by its UUID string.
    Args:
        part_id: UUID string of the part to look up.
    """
    part = get_part(UUID(part_id))
    if not part:
        return {"error": f"Part {part_id} not found."}
    creator = get_created_by(UUID(part_id))
    creator_info = {}
    if creator:
        creator_info = {"created_by_op_id": str(creator.id), "op_name": creator.name, "op_type": str(creator.op_type)}
    return {
        "id": str(part.id),
        "name": part.name,
        "description": part.description,
        "unit_of_measure": part.unit_of_measure,
        **creator_info,
    }


def get_part_tree(part_id: str) -> dict[str, Any]:
    """Get the full manufacturing tree for a part.
    Args:
        part_id: UUID string of the part.
    """
    return get_tree_json(UUID(part_id))


def get_part_ancestors(part_id: str) -> list[dict[str, Any]]:
    """Get all upstream ancestor parts that feed into this part.
    Args:
        part_id: UUID string of the part.
    """
    ancestors = get_ancestors(UUID(part_id))
    return [{"id": str(a.id), "name": a.name} for a in ancestors]


def get_part_costs(part_id: str) -> list[dict[str, Any]]:
    """Get all leaf currency nodes (raw costs) upstream of a part.
    Args:
        part_id: UUID string of the part.
    """
    currencies = get_leaf_currencies(UUID(part_id))
    return [{"id": str(c.id), "name": c.name, "iso_code": c.iso_code} for c in currencies]


def get_part_timeline(part_id: str) -> list[dict[str, Any]]:
    """Get the full manufacturing timeline for a part.
    Args:
        part_id: UUID string of the part.
    """
    timeline = get_full_timeline(UUID(part_id))
    return [{"id": str(n.id), "name": n.name, "type": type(n).__name__} for n in timeline]


def list_all_labor() -> list[dict[str, Any]]:
    """List all labor types available in the system."""
    labor_list = list_labor()
    return [{"id": str(lb.id), "name": lb.name, "hourly_rate": lb.hourly_rate} for lb in labor_list]


def list_all_tools() -> list[dict[str, Any]]:
    """List all tools/machines available in the system."""
    tool_list = list_tools()
    return [{"id": str(t.id), "name": t.name, "cost_rate": t.cost_rate, "rate_unit": t.rate_unit, "linked_part_id": str(t.linked_part_id)} for t in tool_list]


# ── Write / Mutation Functions ────────────────────────────────────────


def purchase_raw_material(
    name: str,
    cost: float,
    currency: str = "USD",
    description: str | None = None,
    unit_of_measure: str = "each",
) -> dict[str, Any]:
    """Purchase a new raw material or component. Creates a purchased part
    with an associated Purchase operation and cost.
    Args:
        name: Name of the material/component (e.g. "Steel Sheet", "Bolt M6")
        cost: Cost per unit in the given currency
        currency: Currency code (default "USD")
        description: Optional description
        unit_of_measure: What is one unit? e.g. "each", "kg", "meter",
            "liter", "sheet" (default "each")
    """
    part_id = uuid4()
    part = PartNode(
        id=part_id,
        name=name,
        description=description or f"Purchased {name}",
        unit_of_measure=unit_of_measure,
    )
    op_id = uuid4()
    op = OperationNode(
        id=op_id,
        name=f"Purchase {name}",
        description=f"Purchase transaction for {name}",
        op_type=OpType.PURCHASE,
    )
    cost_obj = CurrencyAmount(amount=cost, currency_code=currency)
    result = purchase_part(part, op, [cost_obj])
    return {
        "id": str(result.id),
        "name": result.name,
        "cost": cost,
        "currency": currency,
        "unit_of_measure": unit_of_measure,
        "status": "success",
    }


def assemble_part(
    name: str,
    input_part_ids: list[str],
    quantities: list[float] | None = None,
    description: str | None = None,
    instructions: str | None = None,
    yield_rate: float = 1.0,
    setup_time_minutes: float = 0.0,
    estimated_duration_minutes: float = 0.0,
    labor_ids: list[str] | None = None,
    labor_quantities: list[float] | None = None,
    labor_units: list[str] | None = None,
    tool_ids: list[str] | None = None,
    tool_quantities: list[float] | None = None,
    tool_units: list[str] | None = None,
) -> dict[str, Any]:
    """Assemble/manufacture a new part from existing input parts, with
    labor and tool usage.

    IMPORTANT: All input parts must already exist. At least one labor or tool is REQUIRED.

    Args:
        name: Name of the new assembled part
        input_part_ids: List of UUID strings for input parts (REQUIRED, >=1)
        quantities: Quantities for each input part (default 1.0 each)
        description: Optional description of the assembly
        instructions: Step-by-step work instructions for this operation
        yield_rate: Fraction of good output, 0.95 = 5% scrap (default 1.0)
        setup_time_minutes: Fixed setup time before production (default 0)
        estimated_duration_minutes: Run time per unit produced (default 0)
        labor_ids: List of UUID strings for labor types used
        labor_quantities: Quantities for each labor input (hours)
        labor_units: Units for each labor quantity (default "hours")
        tool_ids: List of UUID strings for tools used
        tool_quantities: Quantities for each tool input (hours)
        tool_units: Units for each tool quantity (default "hours")
    """
    if not input_part_ids:
        raise ValueError("At least one input part is required.")

    if not (labor_ids or tool_ids):
        raise ValueError("At least one labor or tool is required. Parts don't assemble themselves.")

    if quantities and len(quantities) != len(input_part_ids):
        raise ValueError("quantities length must match input_part_ids.")

    part_inputs = []
    for i, pid in enumerate(input_part_ids):
        qty = quantities[i] if quantities else 1.0
        part_inputs.append(QuantityInput(resource_id=UUID(pid), quantity=qty, unit="each"))

    labor_inputs: list[QuantityInput] = []
    if labor_ids:
        for i, lid in enumerate(labor_ids):
            qty = labor_quantities[i] if labor_quantities else 1.0
            unit = labor_units[i] if labor_units else "hours"
            labor_inputs.append(QuantityInput(resource_id=UUID(lid), quantity=qty, unit=unit))

    tool_inputs: list[QuantityInput] = []
    if tool_ids:
        for i, tid in enumerate(tool_ids):
            qty = tool_quantities[i] if tool_quantities else 1.0
            unit = tool_units[i] if tool_units else "hours"
            tool_inputs.append(QuantityInput(resource_id=UUID(tid), quantity=qty, unit=unit))

    part_id = uuid4()
    part = PartNode(
        id=part_id,
        name=name,
        description=description or f"Assembled {name}",
    )
    op_id = uuid4()
    op = OperationNode(
        id=op_id,
        name=f"Assemble {name}",
        description=f"Assembly/manufacturing operation for {name}",
        op_type=OpType.STANDARD,
        instructions=instructions,
        yield_rate=yield_rate,
        setup_time_minutes=setup_time_minutes,
        estimated_duration_minutes=estimated_duration_minutes,
    )

    result = manufacture_part(part, op, part_inputs, labor_inputs, tool_inputs)
    return {
        "id": str(result.id),
        "name": result.name,
        "input_count": len(part_inputs),
        "labor_count": len(labor_inputs),
        "tool_count": len(tool_inputs),
        "yield_rate": yield_rate,
        "status": "success",
    }


def create_labor_type(
    name: str,
    hourly_rate: float,
    description: str | None = None,
    skill_level: str | None = None,
) -> dict[str, Any]:
    """Create a new type of labor (e.g. "Welding", "CNC Operation").
    Args:
        name: Name of the labor type
        hourly_rate: Cost per hour
        description: Optional description
        skill_level: Required skill or certification
    """
    labor_id = uuid4()
    labor = LaborNode(
        id=labor_id,
        name=name,
        hourly_rate=hourly_rate,
        description=description or f"{name} labor",
        skill_level=skill_level,
    )
    result = create_labor(labor)
    return {
        "id": str(result.id),
        "name": result.name,
        "hourly_rate": result.hourly_rate,
        "skill_level": result.skill_level,
        "status": "success",
    }


def create_machine_tool(
    name: str,
    linked_part_id: str,
    cost_rate: float,
    rate_unit: str = "hour",
    setup_time_minutes: float = 0.0,
    description: str | None = None,
) -> dict[str, Any]:
    """Create a tool/machine entry. The machine itself must already exist
    as a purchased part.
    Args:
        name: Name of the tool/machine
        linked_part_id: UUID string of the part representing this machine
        cost_rate: Cost rate for using this machine
        rate_unit: Unit for the rate (default "hour")
        setup_time_minutes: Fixed setup time in minutes (default 0)
        description: Optional description
    """
    tool_id = uuid4()
    t = MfgToolNode(
        id=tool_id,
        name=name,
        linked_part_id=UUID(linked_part_id),
        cost_rate=cost_rate,
        rate_unit=rate_unit,
        setup_time_minutes=setup_time_minutes,
        description=description or f"{name} machine/tool",
    )
    result = create_tool(t)
    return {
        "id": str(result.id),
        "name": result.name,
        "cost_rate": result.cost_rate,
        "rate_unit": result.rate_unit,
        "status": "success",
    }


def modify_part(
    part_id: str,
    new_name: str | None = None,
    new_description: str | None = None,
) -> dict[str, Any]:
    """Modify an existing part's name or description.
    Args:
        part_id: UUID string of the part to modify
        new_name: New name (or None to keep current)
        new_description: New description (or None to keep current)
    """
    part = get_part(UUID(part_id))
    if not part:
        return {"error": f"Part {part_id} not found."}

    if new_name is not None:
        part.name = new_name
    if new_description is not None:
        part.description = new_description

    result = update_part(part)
    return {"id": str(result.id), "name": result.name, "status": "success"}


def remove_part(part_id: str) -> dict[str, Any]:
    """Delete a part from the database.
    Args:
        part_id: UUID string of the part to delete.
    """
    success = delete_part(UUID(part_id))
    return {"id": part_id, "success": success}


def validate_part_tree(part_id: str) -> dict[str, Any]:
    """Validate the manufacturing tree starting from a root part.
    Args:
        part_id: UUID string of the root part.
    """
    result = validate_tree(UUID(part_id))
    return asdict(result)


# ── Python Interpreter Tool ───────────────────────────────────────────


@tool
def python_interpreter(code: str) -> str:
    """Execute Python code in a secure sandbox.
    Use this to perform complex manufacturing tasks by calling available functions.

    The environment has access to:
    - search_parts(query: str, limit: int = 20) -> list[dict]
    - get_part_details(part_id: str) -> dict
    - get_part_tree(part_id: str) -> dict
    - get_part_ancestors(part_id: str) -> list[dict]
    - get_part_costs(part_id: str) -> list[dict]
    - get_part_timeline(part_id: str) -> list[dict]
    - list_all_labor() -> list[dict]
    - list_all_tools() -> list[dict]
    - purchase_raw_material(name, cost, currency="USD", description=None, unit_of_measure="each") -> dict
    - assemble_part(name, input_part_ids, quantities=None, ...) -> dict
    - create_labor_type(name, hourly_rate, description=None, skill_level=None) -> dict
    - create_machine_tool(name, linked_part_id, cost_rate, rate_unit="hour", ...) -> dict
    - modify_part(part_id, new_name=None, new_description=None) -> dict
    - remove_part(part_id: str) -> dict
    - validate_part_tree(part_id: str) -> dict

    Example:
    ```python
    steel = purchase_raw_material("Steel Plate", 50.0)
    steel_id = steel['id']
    print(f"Created steel: {steel_id}")
    ```
    Note: Use `print()` to see intermediate results. The interpreter also returns the value of the last expression.
    CRITICAL: Do NOT prefix function calls with `default_api.` or any other module name. Call them directly.
    """
    import pydantic_monty

    # Map functions for Monty
    funcs = {
        "search_parts": search_parts,
        "get_part_details": get_part_details,
        "get_part_tree": get_part_tree,
        "get_part_ancestors": get_part_ancestors,
        "get_part_costs": get_part_costs,
        "get_part_timeline": get_part_timeline,
        "list_all_labor": list_all_labor,
        "list_all_tools": list_all_tools,
        "purchase_raw_material": purchase_raw_material,
        "assemble_part": assemble_part,
        "create_labor_type": create_labor_type,
        "create_machine_tool": create_machine_tool,
        "modify_part": modify_part,
        "remove_part": remove_part,
        "validate_part_tree": validate_part_tree,
    }

    printed_lines = []

    from typing import Literal

    def capture_print(kind: Literal["stdout"], text: str):
        printed_lines.append(text)

    try:
        m = pydantic_monty.Monty(
            code,
            external_functions=list(funcs.keys()),
        )
        output = m.run(
            external_functions=funcs,
            print_callback=capture_print,
        )

        # Combine printed output and the return value
        result_parts = []
        if printed_lines:
            result_parts.append("\n".join(printed_lines))
        if output is not None:
            result_parts.append(f"Return Value: {output}")

        if not result_parts:
            return "Code executed successfully (no output)."

        return "\n".join(result_parts)
    except Exception as e:
        return f"Error executing code: {e}"


# ═══════════════════════════════════════════════════════════════════════
#  All Tools
# ═══════════════════════════════════════════════════════════════════════

ALL_TOOLS = [
    python_interpreter,
]

# ═══════════════════════════════════════════════════════════════════════
#  System Prompt
# ═══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
You are a manufacturing assistant with access to a parts database.
You are a vision-capable agent and can see images and PDF pages uploaded by the user. Use these visuals to identify parts, understand assemblies, and extract technical details.

You have ONE tool: `python_interpreter`. You MUST use it to interact with the manufacturing system.
Instead of calling multiple tools sequentially, you should write a single Python script that performs all necessary steps efficiently.

Available functions within the `python_interpreter` (all return dicts or lists of dicts):
- search_parts(query: str, limit: int = 20) -> list[dict]
- get_part_details(part_id: str) -> dict
- get_part_tree(part_id: str) -> dict
- get_part_ancestors(part_id: str) -> list[dict]
- get_part_costs(part_id: str) -> list[dict]
- get_part_timeline(part_id: str) -> list[dict]
- list_all_labor() -> list[dict]
- list_all_tools() -> list[dict]
- purchase_raw_material(name, cost, currency="USD", description=None, unit_of_measure="each") -> dict
- assemble_part(name, input_part_ids, quantities=None, description=None, instructions=None, yield_rate=1.0, setup_time_minutes=0.0, estimated_duration_minutes=0.0, labor_ids=None, labor_quantities=None, labor_units=None, tool_ids=None, tool_quantities=None, tool_units=None) -> dict
- create_labor_type(name, hourly_rate, description=None, skill_level=None) -> dict
- create_machine_tool(name, linked_part_id, cost_rate, rate_unit="hour", setup_time_minutes=0.0, description=None) -> dict
- modify_part(part_id, new_name=None, new_description=None) -> dict
- remove_part(part_id: str) -> dict
- validate_part_tree(part_id: str) -> dict

Rules for creating new parts:
1. Search/list what's already in the database first.
2. Purchase raw materials and machines (as parts), then register machines as tools.
3. Create labor types as needed.
4. Assemble parts together - every assembly needs at least one labor OR tool.
5. Validate the final tree.

Efficient Workflow Example:
If asked to create a part from scratch, your Python script should perform all steps at once and use `print()` to report progress:
1. Check for existing components using `search_parts()`.
2. Purchase missing ones using `purchase_raw_material()`.
3. Define necessary labor/tools using `create_labor_type()` and `create_machine_tool()`.
4. Assemble the final part using `assemble_part()`.
5. Validate the final tree using `validate_part_tree()`.

CRITICAL: Call all functions directly (e.g., `search_parts(...)`). Do NOT prefix them with modules (e.g., NOT `default_api.search_parts(...)`).

Always use IDs returned by the functions. Provide clear, direct answers with part IDs and summaries.
"""

# ═══════════════════════════════════════════════════════════════════════
#  LLM Helpers
# ═══════════════════════════════════════════════════════════════════════


def _get_strong_llm():

    from langchain_openrouter import ChatOpenRouter

    return ChatOpenRouter(
        model="google/gemini-2.0-flash-001",
        temperature=0.3,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Agent Entry Point
# ═══════════════════════════════════════════════════════════════════════


def _get_agent():
    """Internal helper to create the agent instance."""
    from langchain.agents import create_agent
    from langchain_core.messages import SystemMessage

    llm = _get_strong_llm()
    return create_agent(
        model=llm,
        tools=ALL_TOOLS,
        system_prompt=SystemMessage(content=SYSTEM_PROMPT),
    )


def _prepare_messages(question: Any, history: list[dict[str, Any]]):
    """Convert question and history into a list of LangChain messages."""

    messages = []
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    # Add current question
    messages.append(HumanMessage(content=question))
    return messages


def get_tech_transfer_agent():
    """
    Build and return the tech-transfer agent as a Runnable.

    Accepts ``{"question": "...", "history": [...]}`` and returns a plain string answer.
    The history is a list of dicts with "role" and "content" keys.
    """
    from langchain_core.runnables import RunnableLambda

    agent = _get_agent()

    def input_adapter(inputs: dict) -> dict:
        messages = _prepare_messages(inputs["question"], inputs.get("history", []))
        return {"messages": messages}

    def safe_invoke(inputs: dict, max_retries: int = 3) -> dict:
        """Invoke the agent with retry logic for resilience."""
        last_error = None
        last_result = None
        debug_info = []

        # Track conversation to allow agent to continue after tool calls
        current_messages = list(inputs.get("messages", []))

        for attempt in range(max_retries + 1):
            try:
                debug_info.append(f"Attempt {attempt + 1}/{max_retries + 1}: Invoking agent...")
                agent_input = {"messages": current_messages}
                result = agent.invoke(agent_input)
                last_result = result

                # LangGraph create_agent returns {"messages": [...], ...}
                messages = result.get("messages", [])
                debug_info.append(f"  - Result keys: {list(result.keys())}, messages: {len(messages)}")

                if not messages:
                    debug_info.append("  - No messages in result")
                    if attempt < max_retries:
                        current_messages.append(HumanMessage(content="Please provide a response."))
                        continue
                    break

                last_msg = messages[-1]
                msg_type = type(last_msg).__name__
                debug_info.append(f"  - Last message type: {msg_type}")

                # Check for tool calls - agent wants to use tools
                has_tool_calls = hasattr(last_msg, "tool_calls") and last_msg.tool_calls
                if has_tool_calls:
                    tool_names = [tc.get("name", "unknown") for tc in last_msg.tool_calls]
                    debug_info.append(f"  - Agent making tool calls: {tool_names}")

                    # Specifically log the python_interpreter code for programmatic tool calling
                    for tc in last_msg.tool_calls:
                        if tc.get("name") == "python_interpreter":
                            code = tc.get("args", {}).get("code", "")
                            debug_info.append(f"  - python_interpreter code: {code[:100]}...")

                    # Let the agent continue - LangGraph should auto-execute tools
                    # Update messages and loop to let it continue
                    current_messages = list(messages)
                    continue

                # Check for content in the last message
                content = ""
                if hasattr(last_msg, "content") and last_msg.content:
                    if isinstance(last_msg.content, str):
                        content = last_msg.content
                    elif isinstance(last_msg.content, list):
                        # Handle list of content blocks
                        for block in last_msg.content:
                            if isinstance(block, dict):
                                text = block.get("text", "")
                                if text:
                                    content += text
                            elif hasattr(block, "text"):
                                content += block.text

                if content:
                    content_preview = str(content)[:150]
                    debug_info.append(f"  - Last message content: {content_preview}")

                    if "wasn't able to generate" not in str(content).lower():
                        debug_info.append("  - Valid response received")
                        return result
                    else:
                        debug_info.append("  - Content indicates failure")
                else:
                    debug_info.append("  - Last message has no content")

                # No valid response yet
                debug_info.append(f"  - Response invalid, attempt {attempt} of {max_retries}")
                if attempt < max_retries:
                    # Add a reminder message and retry
                    current_messages = list(messages)
                    current_messages.append(HumanMessage(content="Please provide a complete response to the user's question."))
                    continue

            except Exception as e:
                last_error = e
                debug_info.append(f"  - Exception: {type(e).__name__}: {e}")
                if attempt < max_retries:
                    debug_info.append("  - Retrying after exception...")
                    continue

        # All retries exhausted - try to extract any useful info
        error_details = "\n".join(debug_info)

        # If we have any messages with tool results, summarize those
        if last_result and last_result.get("messages"):
            # Check for tool results in the message history
            tool_results = []
            for msg in last_result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_results.append(tc.get("name", "unknown"))
            if tool_results:
                summary = f"I attempted to use tools ({', '.join(tool_results)}) but didn't get a final response. Try rephrasing your question."
                return {
                    "messages": current_messages + [AIMessage(content=summary)],
                }

        if last_error is None and last_result is not None:
            result_keys = list(last_result.keys()) if last_result else []
            error_msg = f"Agent failed to generate a valid response after {max_retries + 1} attempts.\n\nDebug info:\n{error_details}\n\nLast result keys: {result_keys}"
        elif last_error is None:
            error_msg = f"Agent failed with no response after {max_retries + 1} attempts.\n\nDebug info:\n{error_details}"
        else:
            error_msg = f"Agent encountered an error after {max_retries + 1} attempts: {last_error}\n\nDebug info:\n{error_details}"

        return {
            "messages": current_messages + [AIMessage(content=error_msg)],
        }

    def output_adapter(outputs: dict) -> tuple[str, list[dict]]:
        # Extract tool calls from messages
        tool_calls: list[dict] = []
        messages = outputs.get("messages", [])

        for msg in messages:
            # Check for tool calls in the message
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append(
                        {
                            "tool": tc.get("name", tc.get("tool", "unknown")),
                            "input": str(tc.get("args", tc.get("input", {}))),
                            "output": None,
                        }
                    )
            # Also check for tool results in additional kwargs
            if hasattr(msg, "additional_kwargs"):
                additional = msg.additional_kwargs or {}
                # Look for tool results
                tool_results = additional.get("tool_calls", [])
                for tr in tool_results:
                    if "output" in tr:
                        # Match to previous tool call
                        tool_name = tr.get("name", "")
                        for tc in tool_calls:
                            if tc.get("tool") == tool_name:
                                tc["output"] = str(tr.get("output", ""))[:500]

        # Try to extract content from the last message
        content = ""
        if messages:
            last_msg = messages[-1]

            # Handle various content formats
            if hasattr(last_msg, "content"):
                raw_content = last_msg.content

                if isinstance(raw_content, str):
                    content = raw_content.strip()
                elif isinstance(raw_content, list):
                    # Handle list of content blocks (e.g., [TextContent(...), ...])
                    texts = []
                    for item in raw_content:
                        if isinstance(item, dict):
                            texts.append(item.get("text", ""))
                        elif hasattr(item, "text"):
                            texts.append(item.text)
                        elif isinstance(item, str):
                            texts.append(item)
                    content = "\n".join(texts).strip()
                elif raw_content:
                    content = str(raw_content).strip()

            # Also check if there's a valid text attribute
            if not content and hasattr(last_msg, "text"):
                content = str(last_msg.text).strip()

        # If still no content, try to construct from tool calls summary
        if not content and tool_calls:
            tool_summary = []
            for tc in tool_calls:
                tool_name = tc.get("tool", "unknown")
                tool_summary.append(f"[Used tool: {tool_name}]")
            content = "I executed the following tools:\n" + "\n".join(tool_summary)
            if not content.strip():
                content = "I wasn't able to generate a response. Could you try rephrasing your question?"
        elif not content:
            content = "I wasn't able to generate a response. Could you try rephrasing your question?"

        return content, tool_calls

    def final_adapter(outputs: tuple[str, list[dict]]) -> dict:
        """Convert tuple to dict for FastAPI response."""
        content, tool_calls = outputs
        return {"response": content, "tool_calls": tool_calls}

    return RunnableLambda(input_adapter) | RunnableLambda(safe_invoke) | RunnableLambda(output_adapter) | RunnableLambda(final_adapter)


async def stream_tech_transfer_agent(question: Any, history: list[dict[str, Any]]):
    """
    Build and stream the tech-transfer agent events.
    Yields dicts with 'type', 'content'/'tool'/'input'/'output'.
    """
    agent = _get_agent()
    messages = _prepare_messages(question, history)

    async for event in agent.astream_events({"messages": messages}, version="v2"):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield {"type": "content", "content": content}

        elif kind == "on_tool_start":
            tool_name = event["name"]
            tool_input = event["data"].get("input", {})

            # Highlight python_interpreter code execution in streaming events
            if tool_name == "python_interpreter" and isinstance(tool_input, dict) and "code" in tool_input:
                yield {
                    "type": "tool_start",
                    "tool": tool_name,
                    "input": tool_input["code"],
                }
            else:
                yield {
                    "type": "tool_start",
                    "tool": tool_name,
                    "input": str(tool_input),
                }

        elif kind == "on_tool_end":
            output = event["data"].get("output")
            # Truncate output if too long
            output_str = str(output)
            if len(output_str) > 1000:
                output_str = output_str[:1000] + "... [truncated]"

            yield {
                "type": "tool_end",
                "tool": event["name"],
                "output": output_str,
            }
