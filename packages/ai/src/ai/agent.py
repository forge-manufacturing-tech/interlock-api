"""
Interlock Tech-Transfer Agent — single tool-calling ReAct agent (PydanticAI).
"""

from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any
from uuid import UUID, uuid4

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
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

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
#  PydanticAI Agent
# ═══════════════════════════════════════════════════════════════════════


def _build_model() -> OpenAIChatModel:
    """Create the OpenAI-compatible model pointed at OpenRouter."""
    provider = OpenAIProvider(
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    )
    return OpenAIChatModel("google/gemini-2.0-flash-001", provider=provider)


# Single shared agent instance (created lazily to allow env vars to be set first)
_agent: Agent[Any, str] | None = None


def _get_agent() -> Agent[Any, str]:
    global _agent
    if _agent is None:
        _agent = Agent(
            _build_model(),
            system_prompt=SYSTEM_PROMPT,
        )
        _register_tools(_agent)
    return _agent


def _register_tools(agent: Agent[Any, str]) -> None:
    """Attach all tools to the agent using @agent.tool_plain decorators."""

    @agent.tool_plain
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

        printed_lines: list[str] = []

        from typing import Literal

        def capture_print(kind: Literal["stdout"], text: str) -> None:
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

            result_parts: list[str] = []
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
#  History Conversion
# ═══════════════════════════════════════════════════════════════════════


def _history_to_model_messages(history: list[dict[str, Any]]) -> list[ModelMessage]:
    """Convert [{role, content}] dicts into PydanticAI ModelMessage objects."""
    messages: list[ModelMessage] = []
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        # Normalise content — may be a string or a list of blocks
        if isinstance(content, list):
            # Flatten multimodal content to a single text string for history
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            content = "\n".join(text_parts)

        if role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        elif role == "assistant":
            messages.append(ModelResponse(parts=[TextPart(content=content)]))
    return messages


# ═══════════════════════════════════════════════════════════════════════
#  Tool-call extraction from result messages
# ═══════════════════════════════════════════════════════════════════════


def _extract_tool_calls(messages: list[ModelMessage]) -> list[dict[str, Any]]:
    """Walk PydanticAI result messages and pull out tool-call pairs."""
    from pydantic_ai.messages import ToolCallPart, ToolReturnPart

    tool_calls: list[dict[str, Any]] = []
    # Keep a map of tool_call_id -> index in tool_calls for matching returns
    id_to_idx: dict[str, int] = {}

    for msg in messages:
        for part in msg.parts:
            if isinstance(part, ToolCallPart):
                args_str = part.args_as_json_str() if hasattr(part, "args_as_json_str") else str(part.args)
                idx = len(tool_calls)
                tool_calls.append(
                    {
                        "tool": part.tool_name,
                        "input": args_str,
                        "output": None,
                    }
                )
                if part.tool_call_id:
                    id_to_idx[part.tool_call_id] = idx
            elif isinstance(part, ToolReturnPart):
                idx = id_to_idx.get(part.tool_call_id)
                if idx is not None:
                    output_str = str(part.content)
                    if len(output_str) > 500:
                        output_str = output_str[:500] + "... [truncated]"
                    tool_calls[idx]["output"] = output_str

    return tool_calls


# ═══════════════════════════════════════════════════════════════════════
#  Public API — matches what main.py expects
# ═══════════════════════════════════════════════════════════════════════


def get_tech_transfer_agent():
    """
    Return a callable object that mimics the old LangChain Runnable interface.

    Accepts ``{"question": "...", "history": [...]}`` via ``.invoke()``
    and returns ``{"response": str, "tool_calls": list}``.
    """

    class _AgentRunnable:
        """Thin wrapper to expose ``.invoke()`` so main.py doesn't need to change."""

        def invoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
            import asyncio

            question = inputs["question"]
            history = inputs.get("history", [])

            # Build the message content for the current turn
            if isinstance(question, list):
                # Multimodal content blocks — flatten to string for now
                text_parts = []
                for block in question:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                user_text = "\n".join(text_parts)
            else:
                user_text = str(question)

            model_history = _history_to_model_messages(history)

            agent = _get_agent()

            async def _run() -> dict[str, Any]:
                result = await agent.run(user_text, message_history=model_history)
                tool_calls = _extract_tool_calls(result.new_messages())
                return {"response": result.output, "tool_calls": tool_calls}

            return asyncio.run(_run())

    return _AgentRunnable()


async def stream_tech_transfer_agent(question: Any, history: list[dict[str, Any]]):
    """
    Stream the tech-transfer agent events.
    Yields dicts with 'type', 'content'/'tool'/'input'/'output'.

    The event schema matches what main.py's event_generator() expects:
        {"type": "content",    "content": str}
        {"type": "tool_start", "tool": str, "input": str}
        {"type": "tool_end",   "tool": str, "output": str}
    """
    from pydantic_ai.messages import ToolCallPart, ToolReturnPart

    if isinstance(question, list):
        text_parts = []
        for block in question:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        user_text = "\n".join(text_parts)
    else:
        user_text = str(question)

    model_history = _history_to_model_messages(history)
    agent = _get_agent()

    async with agent.run_stream(user_text, message_history=model_history) as result:
        # Stream text deltas
        async for text_delta in result.stream_text(delta=True):
            if text_delta:
                yield {"type": "content", "content": text_delta}

    # After the stream completes, emit tool events from the recorded messages
    for msg in result.new_messages():
        for part in msg.parts:
            if isinstance(part, ToolCallPart):
                args_str = part.args_as_json_str() if hasattr(part, "args_as_json_str") else str(part.args)
                if part.tool_name == "python_interpreter":
                    try:
                        import json as _json

                        args = _json.loads(args_str)
                        input_display = args.get("code", args_str)
                    except Exception:
                        input_display = args_str
                else:
                    input_display = args_str
                yield {"type": "tool_start", "tool": part.tool_name, "input": input_display}
            elif isinstance(part, ToolReturnPart):
                output_str = str(part.content)
                if len(output_str) > 1000:
                    output_str = output_str[:1000] + "... [truncated]"
                yield {"type": "tool_end", "tool": part.tool_name, "output": output_str}
