"""
Interlock Tech-Transfer Agent — structured LangGraph workflow.

Routes user intent into one of:
  • ASK   – look up an existing part and answer questions about it
  • MODIFY – clarify what to change, then execute modifications
  • NEW   – gather requirements, then build a manufacturing tree bottom-up
  • GENERAL – answer general questions without tool calls
"""

from __future__ import annotations

import os
from dataclasses import asdict
from typing import Literal
from uuid import UUID, uuid4

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from models.main import (
    CurrencyAmount,
    LaborNode,
    NodeStatus,
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
#  Tool Definitions (simplified wrappers for the LLM)
# ═══════════════════════════════════════════════════════════════════════

# ── Read / Query Tools ────────────────────────────────────────────────


@tool
def search_parts(query: str, limit: int = 20) -> str:
    """Search for parts by listing them. Returns IDs and names.
    Use this to find existing parts in the database.
    Args:
        query: Not used for filtering yet, but describes what you're looking for.
        limit: Max number of parts to return.
    """
    try:
        parts = list_parts(limit=limit)
        if not parts:
            return "No parts found in the database."
        lines = [f"• {p.name} (ID: {p.id}, Status: {p.status})" for p in parts]
        return "Found parts:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error searching parts: {e}"


@tool
def get_part_details(part_id: str) -> str:
    """Get full details of a specific part by its UUID string.
    Args:
        part_id: UUID string of the part to look up.
    """
    try:
        part = get_part(UUID(part_id))
        if not part:
            return f"Part {part_id} not found."
        # Also get its creator operation
        creator = get_created_by(UUID(part_id))
        creator_info = ""
        if creator:
            creator_info = (
                f"\nCreated by operation: {creator.name} "
                f"(Type: {creator.op_type}, ID: {creator.id})"
            )
        return (
            f"Part: {part.name}\n"
            f"ID: {part.id}\n"
            f"Description: {part.description}\n"
            f"Status: {part.status}"
            f"{creator_info}"
        )
    except Exception as e:
        return f"Error: {e}"


@tool
def get_part_tree(part_id: str) -> str:
    """Get the full manufacturing tree for a part, showing all ancestors
    and how it was built.
    Args:
        part_id: UUID string of the part.
    """
    try:
        tree = get_tree_json(UUID(part_id))
        return f"Manufacturing tree:\n{tree}"
    except Exception as e:
        return f"Error: {e}"


@tool
def get_part_ancestors(part_id: str) -> str:
    """Get all upstream ancestor parts that feed into this part.
    Args:
        part_id: UUID string of the part.
    """
    try:
        ancestors = get_ancestors(UUID(part_id))
        if not ancestors:
            return "No ancestors found (this may be a raw material)."
        lines = [f"• {a.name} (ID: {a.id})" for a in ancestors]
        return "Ancestor parts:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_part_costs(part_id: str) -> str:
    """Get all leaf currency nodes (raw costs) upstream of a part.
    Args:
        part_id: UUID string of the part.
    """
    try:
        currencies = get_leaf_currencies(UUID(part_id))
        if not currencies:
            return "No cost information found."
        lines = [f"• {c.name}: {c.iso_code} (ID: {c.id})" for c in currencies]
        return "Cost breakdown:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_part_timeline(part_id: str) -> str:
    """Get the full manufacturing timeline for a part.
    Args:
        part_id: UUID string of the part.
    """
    try:
        timeline = get_full_timeline(UUID(part_id))
        if not timeline:
            return "No timeline data."
        lines = [f"• {n.name} (ID: {n.id})" for n in timeline]
        return "Timeline:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@tool
def list_all_labor() -> str:
    """List all labor types available in the system."""
    try:
        labor_list = list_labor()
        if not labor_list:
            return "No labor types defined."
        lines = [
            f"• {lb.name} – ${lb.hourly_rate}/hr (ID: {lb.id})" for lb in labor_list
        ]
        return "Labor types:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@tool
def list_all_tools() -> str:
    """List all tools/machines available in the system."""
    try:
        tool_list = list_tools()
        if not tool_list:
            return "No tools defined."
        lines = [
            f"• {t.name} – ${t.cost_rate}/{t.rate_unit} "
            f"(ID: {t.id}, linked part: {t.linked_part_id})"
            for t in tool_list
        ]
        return "Tools:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ── Write / Mutation Tools ────────────────────────────────────────────


@tool
def purchase_raw_material(
    name: str,
    cost: float,
    currency: str = "USD",
    description: str | None = None,
    unit_of_measure: str = "each",
) -> str:
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
    try:
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
        return (
            f"✅ Purchased '{result.name}'\n"
            f"   Part ID: {result.id}\n"
            f"   Cost: {cost} {currency}\n"
            f"   Unit: {unit_of_measure}"
        )
    except Exception as e:
        return f"❌ Error purchasing {name}: {e}"


@tool
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
) -> str:
    """Assemble/manufacture a new part from existing input parts, with
    labor and tool usage.

    IMPORTANT: All input parts must already exist. Use search_parts or
    purchase_raw_material first. At least one labor or tool is REQUIRED.

    Args:
        name: Name of the new assembled part
        input_part_ids: List of UUID strings for input parts (REQUIRED, >=1)
        quantities: Quantities for each input part (default 1.0 each)
        description: Optional description of the assembly
        instructions: Step-by-step work instructions for this operation
        yield_rate: Fraction of good output, 0.95 = 5% scrap (default 1.0)
        setup_time_minutes: Fixed setup time before production (default 0)
        estimated_duration_minutes: Run time per unit produced (default 0)
        labor_ids: List of UUID strings for labor types used (REQUIRED
            unless tool_ids provided)
        labor_quantities: Quantities for each labor input (hours)
        labor_units: Units for each labor quantity (default "hours")
        tool_ids: List of UUID strings for tools used (REQUIRED unless
            labor_ids provided)
        tool_quantities: Quantities for each tool input (hours)
        tool_units: Units for each tool quantity (default "hours")
    """
    try:
        if not input_part_ids:
            return "❌ Error: At least one input part is required."

        if not (labor_ids or tool_ids):
            return (
                "❌ Error: At least one labor or tool is required. "
                "Parts don't assemble themselves."
            )

        if quantities and len(quantities) != len(input_part_ids):
            return "❌ Error: quantities length must match input_part_ids."

        # Build part inputs
        part_inputs = []
        for i, pid in enumerate(input_part_ids):
            qty = quantities[i] if quantities else 1.0
            part_inputs.append(
                QuantityInput(resource_id=UUID(pid), quantity=qty, unit="each")
            )

        # Build labor inputs
        labor_inputs: list[QuantityInput] = []
        if labor_ids:
            for i, lid in enumerate(labor_ids):
                qty = labor_quantities[i] if labor_quantities else 1.0
                unit = labor_units[i] if labor_units else "hours"
                labor_inputs.append(
                    QuantityInput(resource_id=UUID(lid), quantity=qty, unit=unit)
                )

        # Build tool inputs
        tool_inputs: list[QuantityInput] = []
        if tool_ids:
            for i, tid in enumerate(tool_ids):
                qty = tool_quantities[i] if tool_quantities else 1.0
                unit = tool_units[i] if tool_units else "hours"
                tool_inputs.append(
                    QuantityInput(resource_id=UUID(tid), quantity=qty, unit=unit)
                )

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
        return (
            f"✅ Assembled '{result.name}'\n"
            f"   Part ID: {result.id}\n"
            f"   Inputs: {len(part_inputs)} parts, "
            f"{len(labor_inputs)} labor, "
            f"{len(tool_inputs)} tools\n"
            f"   Yield: {yield_rate * 100:.0f}%"
        )
    except Exception as e:
        return f"❌ Error assembling {name}: {e}"


@tool
def create_labor_type(
    name: str,
    hourly_rate: float,
    description: str | None = None,
    skill_level: str | None = None,
) -> str:
    """Create a new type of labor (e.g. "Welding", "CNC Operation").
    Args:
        name: Name of the labor type
        hourly_rate: Cost per hour
        description: Optional description
        skill_level: Required skill or certification
            (e.g. "AWS D1.1 Certified", "Level 3 Machinist")
    """
    try:
        labor_id = uuid4()
        labor = LaborNode(
            id=labor_id,
            name=name,
            hourly_rate=hourly_rate,
            description=description or f"{name} labor",
            skill_level=skill_level,
        )
        result = create_labor(labor)
        skill_info = f"\n   Skill: {result.skill_level}" if result.skill_level else ""
        return (
            f"✅ Created labor '{result.name}'\n"
            f"   ID: {result.id}\n"
            f"   Rate: ${result.hourly_rate}/hr"
            f"{skill_info}"
        )
    except Exception as e:
        return f"❌ Error creating labor: {e}"


@tool
def create_machine_tool(
    name: str,
    linked_part_id: str,
    cost_rate: float,
    rate_unit: str = "hour",
    setup_time_minutes: float = 0.0,
    description: str | None = None,
) -> str:
    """Create a tool/machine entry. The machine itself must already exist
    as a purchased part (use purchase_raw_material first for the machine).
    Args:
        name: Name of the tool/machine
        linked_part_id: UUID string of the part representing this machine
        cost_rate: Cost rate for using this machine
        rate_unit: Unit for the rate (default "hour")
        setup_time_minutes: Fixed setup time in minutes (default 0)
        description: Optional description
    """
    try:
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
        return (
            f"✅ Created tool '{result.name}'\n"
            f"   ID: {result.id}\n"
            f"   Rate: ${result.cost_rate}/{result.rate_unit}\n"
            f"   Setup: {result.setup_time_minutes} min"
        )
    except Exception as e:
        return f"❌ Error creating tool: {e}"


@tool
def modify_part(
    part_id: str,
    new_name: str | None = None,
    new_description: str | None = None,
    new_status: str | None = None,
) -> str:
    """Modify an existing part's name, description, or status.
    Args:
        part_id: UUID string of the part to modify
        new_name: New name (or None to keep current)
        new_description: New description (or None to keep current)
        new_status: New status: PENDING, APPROVED, or REJECTED (or None)
    """
    try:
        part = get_part(UUID(part_id))
        if not part:
            return f"❌ Part {part_id} not found."

        if new_name is not None:
            part.name = new_name
        if new_description is not None:
            part.description = new_description
        if new_status is not None:
            part.status = NodeStatus(new_status)

        result = update_part(part)
        return (
            f"✅ Updated part '{result.name}'\n"
            f"   ID: {result.id}\n"
            f"   Status: {result.status}"
        )
    except Exception as e:
        return f"❌ Error modifying part: {e}"


@tool
def remove_part(part_id: str) -> str:
    """Delete a part from the database.
    Args:
        part_id: UUID string of the part to delete.
    """
    try:
        success = delete_part(UUID(part_id))
        if success:
            return f"✅ Deleted part {part_id}"
        return f"❌ Could not delete part {part_id}"
    except Exception as e:
        return f"❌ Error: {e}"


@tool
def validate_part_tree(part_id: str) -> str:
    """Validate the manufacturing tree starting from a root part.
    Checks structural integrity.
    Args:
        part_id: UUID string of the root part.
    """
    try:
        result = validate_tree(UUID(part_id))
        d = asdict(result)
        return f"Validation result:\n{d}"
    except Exception as e:
        return f"Error validating: {e}"


# ═══════════════════════════════════════════════════════════════════════
#  Tool Groups — organized by workflow phase
# ═══════════════════════════════════════════════════════════════════════

QUERY_TOOLS = [
    search_parts,
    get_part_details,
    get_part_tree,
    get_part_ancestors,
    get_part_costs,
    get_part_timeline,
    list_all_labor,
    list_all_tools,
]

MODIFY_TOOLS = [
    search_parts,
    get_part_details,
    modify_part,
    remove_part,
    validate_part_tree,
]

CREATE_TOOLS = [
    search_parts,
    get_part_details,
    purchase_raw_material,
    assemble_part,
    create_labor_type,
    create_machine_tool,
    list_all_labor,
    list_all_tools,
    validate_part_tree,
]

ALL_TOOLS = list(
    {t.name: t for t in QUERY_TOOLS + MODIFY_TOOLS + CREATE_TOOLS}.values()
)

# ═══════════════════════════════════════════════════════════════════════
#  LangGraph State & Workflow
# ═══════════════════════════════════════════════════════════════════════


class AgentState(MessagesState):
    """Extended state with intent tracking."""

    intent: str  # NEW_PART | ASK_EXISTING | MODIFY_EXISTING | GENERAL


# ── System Prompts ────────────────────────────────────────────────────

ROUTER_SYSTEM_PROMPT = """\
You are an intent classifier for a manufacturing tech-transfer system.

Given a user message, classify the intent as EXACTLY one of:
- NEW_PART: The user wants to create, build, or define a new part or product.
- ASK_EXISTING: The user wants to ask about, look up, or inspect an existing \
part, its costs, its tree, or its timeline.
- MODIFY_EXISTING: The user wants to change, update, rename, delete, or \
modify an existing part.
- GENERAL: The user is asking a general question not related to a specific \
action on a part.

Respond with ONLY the classification label, nothing else. \
For example: NEW_PART
"""

ASK_SYSTEM_PROMPT = """\
You are an expert manufacturing analyst. The user wants information about \
existing parts in the manufacturing database.

Your workflow:
1. First, use search_parts to find relevant parts in the database.
2. Use get_part_details to get specifics about a part.
3. Use get_part_tree, get_part_ancestors, get_part_costs, or \
get_part_timeline to answer deeper questions.
4. Synthesize the information and provide a clear, helpful answer.

Always use the tools to look up real data. Never make up part IDs or details.
"""

MODIFY_SYSTEM_PROMPT = """\
You are an expert manufacturing engineer helping modify parts in the database.

Your workflow:
1. First, clarify what the user wants to modify. If the request is ambiguous, \
ask for clarification before making changes.
2. Use search_parts to find the part(s) in question.
3. Use get_part_details to confirm the current state.
4. Use modify_part to make changes, or remove_part to delete.
5. Use validate_part_tree to confirm the tree is still valid after changes.
6. Summarize what was changed.

IMPORTANT: Always confirm the part ID and intended changes before modifying. \
Do not guess part IDs.
"""

CREATE_SYSTEM_PROMPT = """\
You are an expert manufacturing engineer building part trees in the database.

DEFINITIONS — understand these EXACTLY:
- PART: A physical thing (raw material, sub-assembly, or finished product). \
Created by purchase_raw_material or assemble_part.
- LABOR: A type of human work with an hourly rate (e.g. "Welding" at \
$45/hr, "Assembly" at $25/hr). Created by create_labor_type. \
Labor is NOT a part. Do NOT purchase labor as a raw material.
- TOOL/MACHINE: Equipment used in manufacturing (e.g. a CNC Mill, a \
Welding Station). Every machine MUST first be purchased as a Part, then \
registered as a Tool with create_machine_tool. Tools are NOT labor.

TREE STRUCTURE:
- Leaf nodes = purchased raw materials (purchase_raw_material, each with cost)
- Intermediate nodes = assembled parts (assemble_part, combining inputs)
- Root node = the finished product
- Build BOTTOM-UP: materials → sub-assemblies → final product

YOUR STEP-BY-STEP WORKFLOW:

Step 1 — PURCHASE RAW MATERIALS:
  Use purchase_raw_material for each physical material or component.
  Example materials: steel sheet, wood plank, bolt, screw, paint, wire.
  Each call returns a Part ID. SAVE every ID.

Step 2 — PURCHASE MACHINES (if needed):
  a) Use purchase_raw_material to buy the machine as a part.
  b) Use create_machine_tool with the Part ID from step (a).
  This returns a Tool ID. SAVE it.
  Example: Purchase "CNC Mill" for $50000, then create_machine_tool.

Step 3 — CREATE LABOR TYPES (if needed):
  Use create_labor_type for each type of human work.
  Example: create_labor_type("Welding", 45.0) → Labor ID. SAVE it.

Step 4 — ASSEMBLE SUB-ASSEMBLIES:
  Use assemble_part to combine purchased parts.
  Pass input_part_ids (the Part IDs from Step 1).
  Pass labor_ids and tool_ids to attribute labor and machine usage.
  This returns a new Part ID. SAVE it.

Step 5 — ASSEMBLE HIGHER-LEVEL PARTS:
  Use assemble_part again, using sub-assembly Part IDs from Step 4 as inputs.
  Keep building upward until you reach the final product.

Step 6 — VALIDATE:
  Use validate_part_tree on the final product Part ID.

EXAMPLE — Building a "Wooden Table":
  1. purchase_raw_material("Oak Plank", 15.0) → Part A
  2. purchase_raw_material("Steel Leg", 8.0) → Part B (buy 4)
  3. purchase_raw_material("Wood Screws Box", 3.0) → Part C
  4. purchase_raw_material("Wood Finish", 12.0) → Part D
  5. purchase_raw_material("Table Saw", 500.0) → Part E
  6. create_machine_tool("Table Saw", linked_part_id=E, cost_rate=5.0) → Tool T1
  7. create_labor_type("Carpentry", 35.0) → Labor L1
  8. create_labor_type("Finishing", 25.0) → Labor L2
  9. assemble_part("Table Top", [A, C], tool_ids=[T1], labor_ids=[L1])
     → Part F
  10. assemble_part("Table Frame", [B, C], labor_ids=[L1])
      → Part G
  11. assemble_part("Unfinished Table", [F, G], labor_ids=[L1])
      → Part H
  12. assemble_part("Wooden Table", [H, D], labor_ids=[L2])
      → Part I (FINAL)
  13. validate_part_tree(I)

STRICT RULES:
- ALWAYS use IDs returned by tools. NEVER invent or guess UUIDs.
- NEVER purchase labor as a raw material. Use create_labor_type instead.
- EVERY machine must be: purchased as part THEN registered as tool.
- Every assemble_part call needs at least one input_part_id.
- Include realistic labor and tool usage on every assembly step.
- If you don't know specific costs, use reasonable estimates.
- Ask the user for clarification if the product is ambiguous.
"""

GENERAL_SYSTEM_PROMPT = """\
You are an expert in manufacturing tech transfer. Answer the user's question \
helpfully and concisely. If their question could be better answered by \
looking up data in the manufacturing database, suggest they ask about a \
specific part.
"""


# ═══════════════════════════════════════════════════════════════════════
#  Graph Construction
# ═══════════════════════════════════════════════════════════════════════


def _get_llm():
    """Create the LLM instance."""
    from langchain_google_genai import (
        ChatGoogleGenerativeAI,  # ty:ignore[unresolved-import]
    )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable not set. "
            "Please set it in your .env file."
        )

    return ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=0,
        api_key=api_key,
    )


def get_tech_transfer_agent():
    """
    Build and return the structured LangGraph agent as a Runnable.

    Returns a Runnable that accepts ``{"question": "..."}`` and returns
    a plain string answer.
    """
    from langchain_core.runnables import RunnableLambda

    llm = _get_llm()

    # ── Node functions ────────────────────────────────────────────────

    def route_intent(state: AgentState) -> dict:
        """Classify the user's intent."""
        messages = state["messages"]
        user_msg = messages[-1].content if messages else ""

        router_messages = [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ]
        response = llm.invoke(router_messages)

        # Handle case where content is a list (Gemini sometimes returns lists)
        content = response.content
        if isinstance(content, list):
            content = str(content)
        raw = content.strip().upper()

        # Parse intent from response
        intent = "GENERAL"
        for candidate in ["NEW_PART", "ASK_EXISTING", "MODIFY_EXISTING"]:
            if candidate in raw:
                intent = candidate
                break

        return {"intent": intent}

    def ask_node(state: AgentState) -> dict:
        """Handle ASK_EXISTING: query the database and answer."""
        query_llm = llm.bind_tools(QUERY_TOOLS)
        messages = [SystemMessage(content=ASK_SYSTEM_PROMPT)] + state["messages"]
        response = query_llm.invoke(messages)
        return {"messages": [response]}

    def modify_node(state: AgentState) -> dict:
        """Handle MODIFY_EXISTING: clarify and execute modifications."""
        modify_llm = llm.bind_tools(MODIFY_TOOLS)
        messages = [SystemMessage(content=MODIFY_SYSTEM_PROMPT)] + state["messages"]
        response = modify_llm.invoke(messages)
        return {"messages": [response]}

    def create_node(state: AgentState) -> dict:
        """Handle NEW_PART: build manufacturing tree bottom-up."""
        create_llm = llm.bind_tools(CREATE_TOOLS)
        messages = [SystemMessage(content=CREATE_SYSTEM_PROMPT)] + state["messages"]
        response = create_llm.invoke(messages)
        return {"messages": [response]}

    def general_node(state: AgentState) -> dict:
        """Handle GENERAL questions without tools."""
        messages = [SystemMessage(content=GENERAL_SYSTEM_PROMPT)] + state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    # ── Tool execution nodes ──────────────────────────────────────────

    ask_tool_node = ToolNode(tools=QUERY_TOOLS)
    modify_tool_node = ToolNode(tools=MODIFY_TOOLS)
    create_tool_node = ToolNode(tools=CREATE_TOOLS)

    # ── Routing functions ─────────────────────────────────────────────

    def route_by_intent(
        state: AgentState,
    ) -> Literal["ask_node", "modify_node", "create_node", "general_node"]:
        """Route to the appropriate handler based on classified intent."""
        intent = state.get("intent", "GENERAL")
        if intent == "ASK_EXISTING":
            return "ask_node"
        elif intent == "MODIFY_EXISTING":
            return "modify_node"
        elif intent == "NEW_PART":
            return "create_node"
        else:
            return "general_node"

    def _should_continue_tools(tool_node_name: str, agent_node_name: str):
        """Factory for tool-continuation routing.

        If the last message has tool_calls, route to the tool node;
        otherwise, we're done.
        """

        def _router(
            state: AgentState,
        ) -> str:
            last = state["messages"][-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                return tool_node_name
            return END

        return _router

    # ── Build the graph ───────────────────────────────────────────────

    graph = StateGraph(AgentState)  # type: ignore[invalid-argument-type]

    # Add nodes
    graph.add_node("router", route_intent)
    graph.add_node("ask_node", ask_node)
    graph.add_node("modify_node", modify_node)
    graph.add_node("create_node", create_node)
    graph.add_node("general_node", general_node)
    graph.add_node("ask_tools", ask_tool_node)
    graph.add_node("modify_tools", modify_tool_node)
    graph.add_node("create_tools", create_tool_node)

    # Entry point
    graph.add_edge(START, "router")

    # Router → intent-specific handler
    graph.add_conditional_edges("router", route_by_intent)

    # Each handler → check for tool calls → tool execution → loop back
    graph.add_conditional_edges(
        "ask_node",
        _should_continue_tools("ask_tools", "ask_node"),
    )
    graph.add_edge("ask_tools", "ask_node")

    graph.add_conditional_edges(
        "modify_node",
        _should_continue_tools("modify_tools", "modify_node"),
    )
    graph.add_edge("modify_tools", "modify_node")

    graph.add_conditional_edges(
        "create_node",
        _should_continue_tools("create_tools", "create_node"),
    )
    graph.add_edge("create_tools", "create_node")

    # General node goes straight to END (no tools)
    graph.add_edge("general_node", END)

    # Compile
    compiled = graph.compile()

    # ── Wrap as a simple Runnable ─────────────────────────────────────

    def input_adapter(inputs: dict) -> dict:
        return {
            "messages": [HumanMessage(content=inputs["question"])],
            "intent": "",
        }

    def safe_invoke(inputs: dict) -> dict:
        try:
            return compiled.invoke(inputs, config={"recursion_limit": 60})
        except Exception as e:
            error_msg = f"The agent encountered an error: {e}"
            return {
                "messages": inputs["messages"] + [AIMessage(content=error_msg)],
                "intent": inputs.get("intent", ""),
            }

    def output_adapter(outputs: dict) -> str:
        content = outputs["messages"][-1].content

        # Handle Gemini's list-of-dicts format: [{'type': 'text', 'text': '...'}]
        if isinstance(content, list):
            # Extract text from all text blocks
            texts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    texts.append(item.get("text", ""))
            if texts:
                return "\n".join(texts)
            return str(content)  # Fallback to string representation

        return content

    return (
        RunnableLambda(input_adapter)
        | RunnableLambda(safe_invoke)
        | RunnableLambda(output_adapter)
    )
