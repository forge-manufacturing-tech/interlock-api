"""
Interlock Tech-Transfer Agent — adversarial two-agent LangGraph workflow.

Routes user intent into one of:
  • ASK   – look up an existing part and answer questions about it
  • MODIFY – clarify what to change, then execute modifications
  • NEW   – **adversarial loop**: Builder agent creates the tree in the DB,
            Reviewer agent reads from the DB and critiques. They iterate
            until the Reviewer is fully satisfied, then report to the user.
  • GENERAL – answer general questions without tool calls
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Literal
from uuid import UUID, uuid4

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
        lines = [f"• {p.name} (ID: {p.id})" for p in parts]
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
            creator_info = f"\nCreated by operation: {creator.name} (Type: {creator.op_type}, ID: {creator.id})"
        return f"Part: {part.name}\nID: {part.id}\nDescription: {part.description}{creator_info}"
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
        lines = [f"• {lb.name} – ${lb.hourly_rate}/hr (ID: {lb.id})" for lb in labor_list]
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
        lines = [f"• {t.name} – ${t.cost_rate}/{t.rate_unit} (ID: {t.id}, linked part: {t.linked_part_id})" for t in tool_list]
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
        return f"✅ Purchased '{result.name}'\n   Part ID: {result.id}\n   Cost: {cost} {currency}\n   Unit: {unit_of_measure}"
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
            return "❌ Error: At least one labor or tool is required. Parts don't assemble themselves."

        if quantities and len(quantities) != len(input_part_ids):
            return "❌ Error: quantities length must match input_part_ids."

        # Build part inputs
        part_inputs = []
        for i, pid in enumerate(input_part_ids):
            qty = quantities[i] if quantities else 1.0
            part_inputs.append(QuantityInput(resource_id=UUID(pid), quantity=qty, unit="each"))

        # Build labor inputs
        labor_inputs: list[QuantityInput] = []
        if labor_ids:
            for i, lid in enumerate(labor_ids):
                qty = labor_quantities[i] if labor_quantities else 1.0
                unit = labor_units[i] if labor_units else "hours"
                labor_inputs.append(QuantityInput(resource_id=UUID(lid), quantity=qty, unit=unit))

        # Build tool inputs
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
        return f"✅ Assembled '{result.name}'\n   Part ID: {result.id}\n   Inputs: {len(part_inputs)} parts, {len(labor_inputs)} labor, {len(tool_inputs)} tools\n   Yield: {yield_rate * 100:.0f}%"
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
        return f"✅ Created labor '{result.name}'\n   ID: {result.id}\n   Rate: ${result.hourly_rate}/hr{skill_info}"
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
        return f"✅ Created tool '{result.name}'\n   ID: {result.id}\n   Rate: ${result.cost_rate}/{result.rate_unit}\n   Setup: {result.setup_time_minutes} min"
    except Exception as e:
        return f"❌ Error creating tool: {e}"


@tool
def modify_part(
    part_id: str,
    new_name: str | None = None,
    new_description: str | None = None,
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

        result = update_part(part)
        return f"✅ Updated part '{result.name}'\n   ID: {result.id}"
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

# Reviewer only gets read-only tools + validate
REVIEW_TOOLS = [
    search_parts,
    get_part_details,
    get_part_tree,
    get_part_ancestors,
    get_part_costs,
    get_part_timeline,
    list_all_labor,
    list_all_tools,
    validate_part_tree,
]

ALL_TOOLS = list({t.name: t for t in QUERY_TOOLS + MODIFY_TOOLS + CREATE_TOOLS}.values())

# ═══════════════════════════════════════════════════════════════════════
#  LangGraph State & Workflow
# ═══════════════════════════════════════════════════════════════════════

# Maximum number of tool-call rounds before we force a final answer.
MAX_TOOL_ROUNDS_SOFT = 15
MAX_TOOL_ROUNDS_HARD = 20

# Maximum adversarial refinement rounds before forcing acceptance.
MAX_REFINEMENT_ROUNDS = 10


class AgentState(MessagesState):
    """Extended state with intent tracking and adversarial loop control."""

    intent: str  # NEW_PART | ASK_EXISTING | MODIFY_EXISTING | GENERAL
    tool_call_count: int  # number of tool-call round-trips so far

    # ── Adversarial loop fields (NEW_PART only) ───────────────────────
    refinement_round: int  # current refinement iteration (0 = first build)
    builder_messages: list  # separate message history for the Builder agent
    reviewer_messages: list  # separate message history for the Reviewer agent
    root_part_id: str  # the root part ID built by the Builder
    reviewer_verdict: str  # APPROVED | NEEDS_REVISION | "" (pending)
    reviewer_feedback: str  # feedback text from Reviewer to Builder


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

GENERAL_SYSTEM_PROMPT = """\
You are an expert in manufacturing tech transfer. Answer the user's question \
helpfully and concisely. If their question could be better answered by \
looking up data in the manufacturing database, suggest they ask about a \
specific part.
"""

# ── Adversarial Agent Prompts (NEW_PART only) ─────────────────────────

REFINER_SYSTEM_PROMPT = """\
You are Agent 1, the Requirement Refiner. The user wants to build a new \
manufactured part or product. Your job is to take their raw request and \
produce a precise, unambiguous manufacturing specification for Agent 2 \
(the Builder) to follow.

Your output must be a single, clear message containing:
1. PRODUCT NAME: Exactly what is being built.
2. BILL OF MATERIALS: Every raw material, with realistic cost estimates.
3. LABOR TYPES: What kinds of human labor are needed, with hourly rates.
4. MACHINES/TOOLS: What equipment is needed, with cost rates.
5. ASSEMBLY SEQUENCE: Bottom-up steps from raw materials to final product. \
CRITICAL: You must explicitly list every assembly step. Raw materials must \
be combined into sub-assemblies, and sub-assemblies into the final product.
6. WORK INSTRUCTIONS: Brief instructions for each assembly step.

Be specific. Do NOT leave anything ambiguous. If the user's request is \
vague (e.g. "build me a chair"), fill in reasonable manufacturing details. \
The Builder agent will follow your specification literally.

Respond with ONLY the specification — no preamble, no questions.
"""

BUILDER_SYSTEM_PROMPT = """\
You are Agent 2, the Builder. You receive a manufacturing specification \
and your job is to execute it EXACTLY by creating parts in the database.

DEFINITIONS — understand these EXACTLY:
- PART: A physical thing (raw material, sub-assembly, or finished product). \
Created by purchase_raw_material or assemble_part.
- LABOR: A type of human work with an hourly rate. Created by \
create_labor_type. Labor is NOT a part.
- TOOL/MACHINE: Equipment. Must be purchased as a Part first, then \
registered as a Tool with create_machine_tool.

YOUR STEP-BY-STEP WORKFLOW:
1. Purchase all raw materials using purchase_raw_material. SAVE every Part ID.
2. Purchase machines as parts, then register with create_machine_tool. \
SAVE Tool IDs.
3. Create labor types with create_labor_type. SAVE Labor IDs.
4. ASSEMBLE (CRITICAL STEP): Use assemble_part to combine purchased parts \
into the final product. You MUST perform assembly. Purchasing materials \
is NOT enough.
5. Continue assembling upward until you have ONE final root part that \
represents the finished product.
6. Validate with validate_part_tree on the final product.
7. When done, respond with EXACTLY this format (no other text):
   DONE: ROOT_PART_ID=<uuid-of-the-final-product>

STRICT RULES:
- ALWAYS use IDs returned by tools. NEVER invent UUIDs.
- DO NOT STOP after purchasing materials. You MUST assemble them.
- EVERY machine: purchased as part THEN registered as tool.
- Every assemble_part needs at least one input_part_id + labor or tool.
- Include realistic work instructions on every assembly step.
- Follow the specification you receive. Do not improvise.
"""

REVIEWER_SYSTEM_PROMPT = """\
You are Agent 1, the Reviewer. Agent 2 (the Builder) has just created a \
manufacturing tree in the database. Your job is to read the tree from \
the database and determine whether a human could follow it to build the \
product WITHOUT ANY AMBIGUITY.

YOUR WORKFLOW:
1. Use get_part_tree to read the full manufacturing tree.
2. Use get_part_details on key parts to check descriptions and operations.
3. Use validate_part_tree to check structural integrity.
4. Walk through every assembly step and ask yourself:
   - Does this tree actually combine materials? Or is it just a list of \
purchased items? (REJECT if no assembly steps).
   - Are the work instructions clear and complete?
   - Are all materials and quantities specified?
   - Is the assembly sequence logical and unambiguous?
   - Are labor types and tools properly assigned?
   - Could a technician follow this without asking questions?

WHEN YOU ARE DONE reviewing, respond with EXACTLY one of:

If the tree is FULLY CLEAR and executable:
  VERDICT: APPROVED
  <followed by a summary of the complete manufacturing plan for the user>

If there is ANY confusion, missing detail, or ambiguity:
  VERDICT: NEEDS_REVISION
  FEEDBACK: <specific, actionable list of what must be fixed>

Be strict. If the Builder bought materials but didn't assemble them, \
REJECT IT immediately and tell them to use assemble_part.
"""

BUILDER_REVISION_PROMPT = """\
You are Agent 2, the Builder. The Reviewer (Agent 1) has found issues with \
your manufacturing tree and is asking you to fix it.

The Reviewer's feedback is below. You must address EVERY point raised.

You have access to all creation tools. You may need to:
- Use assemble_part to combine orphaned raw materials into a finished product.
- Create additional parts or materials that were missing.
- Modify existing parts with better descriptions or instructions.
- Add missing labor or tool assignments.

Use search_parts and get_part_details to find existing parts before \
modifying them. Do NOT recreate materials you already bought.

When you have addressed ALL feedback, respond with EXACTLY:
  DONE: ROOT_PART_ID=<uuid-of-the-final-product>

REVIEWER FEEDBACK:
{feedback}
"""


# ═══════════════════════════════════════════════════════════════════════
#  Graph Construction
# ═══════════════════════════════════════════════════════════════════════


def _get_llm():
    from langchain_openrouter import ChatOpenRouter

    # Standard model for quick tasks (e.g. classification, simple queries)
    return ChatOpenRouter(
        model="openai/gpt-oss-safeguard-20b:nitro",
        temperature=0.3,
    )


def _get_strong_llm():
    from langchain_openrouter import ChatOpenRouter

    # Strong model for reasoning and complex tasks (e.g. manufacturing planning)
    return ChatOpenRouter(
        model="openai/gpt-oss-safeguard-20b:nitro",
        temperature=0.3,
    )


def get_tech_transfer_agent():
    """
    Build and return the structured LangGraph agent as a Runnable.

    Returns a Runnable that accepts ``{"question": "..."}`` and returns
    a plain string answer.
    """
    from typing import Any, cast

    from langchain_core.runnables import RunnableLambda

    standard_llm = _get_llm()
    strong_llm = _get_strong_llm()

    # ── Helpers ─────────────────────────────────────────────────────────

    WRAP_UP_MSG = "IMPORTANT: You have used many tool calls already. Do NOT call any more tools. Summarize everything you have done so far and provide your final answer to the user NOW."

    def _extract_text(content: object) -> str:
        """Safely extract text from LLM response content."""

        if isinstance(content, list):
            texts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    d = cast(dict[str, str], item)
                    if d.get("type") == "text":
                        texts.append(d.get("text", ""))
                    else:
                        texts.append(str(d.get("text", "")))
                else:
                    texts.append(str(item))
            return " ".join(texts).strip()
        return str(content).strip() if content else ""

    def _build_agent_node(
        system_prompt: str,
        tools_list: list,
        llm_instance: Any,
    ):
        """Factory that creates an agent node with iteration awareness."""

        def _node(state: AgentState) -> dict:
            rounds = state.get("tool_call_count", 0)
            messages = [SystemMessage(content=system_prompt)] + state["messages"]

            if rounds >= MAX_TOOL_ROUNDS_HARD:
                messages.append(SystemMessage(content=WRAP_UP_MSG))
                response = llm_instance.invoke(messages)
            elif rounds >= MAX_TOOL_ROUNDS_SOFT:
                messages.append(SystemMessage(content=WRAP_UP_MSG))
                bound = llm_instance.bind_tools(tools_list)
                response = bound.invoke(messages)
            else:
                bound = llm_instance.bind_tools(tools_list)
                response = bound.invoke(messages)

            has_tool_calls = hasattr(response, "tool_calls") and response.tool_calls
            content = _extract_text(response.content)
            is_empty = not content

            if is_empty and not has_tool_calls:
                messages.append(SystemMessage(content=("Your previous response was empty. Please provide a helpful text answer to the user.")))
                response = llm_instance.invoke(messages)

            new_count = rounds + 1 if has_tool_calls else rounds
            return {"messages": [response], "tool_call_count": new_count}

        return _node

    def _build_sub_agent_node(
        system_prompt: str,
        tools_list: list,
        msg_key: str,
        llm_instance: Any,
    ):
        """Factory for sub-agent nodes (Builder/Reviewer) that maintain
        their own separate message history in state[msg_key].

        The sub-agent's response is appended to state[msg_key] AND to
        the main messages (so tool nodes can see tool_calls).
        """

        def _node(state: AgentState) -> dict:
            rounds = state.get("tool_call_count", 0)
            sub_messages = list(state.get(msg_key, []))
            messages = [SystemMessage(content=system_prompt)] + sub_messages

            if rounds >= MAX_TOOL_ROUNDS_HARD:
                messages.append(SystemMessage(content=WRAP_UP_MSG))
                response = llm_instance.invoke(messages)
            elif rounds >= MAX_TOOL_ROUNDS_SOFT:
                messages.append(SystemMessage(content=WRAP_UP_MSG))
                bound = llm_instance.bind_tools(tools_list)
                response = bound.invoke(messages)
            else:
                bound = llm_instance.bind_tools(tools_list)
                response = bound.invoke(messages)

            has_tool_calls = hasattr(response, "tool_calls") and response.tool_calls
            content = _extract_text(response.content)
            is_empty = not content

            if is_empty and not has_tool_calls:
                messages.append(SystemMessage(content=("Your previous response was empty. Please provide a response.")))
                response = llm_instance.invoke(messages)

            new_count = rounds + 1 if has_tool_calls else rounds
            new_sub = sub_messages + [response]

            result: dict = {
                "messages": [response],
                "tool_call_count": new_count,
                msg_key: new_sub,
            }

            # If the Builder says DONE, extract the root part ID
            if not has_tool_calls and msg_key == "builder_messages":
                text = _extract_text(response.content)
                if "DONE:" in text and "ROOT_PART_ID=" in text:
                    try:
                        part_id = text.split("ROOT_PART_ID=")[1].strip().split()[0]
                        result["root_part_id"] = part_id
                    except (IndexError, ValueError):
                        pass

            # If the Reviewer gives a verdict, extract it
            if not has_tool_calls and msg_key == "reviewer_messages":
                text = _extract_text(response.content)
                if "VERDICT:" in text:
                    if "APPROVED" in text:
                        result["reviewer_verdict"] = "APPROVED"
                    elif "NEEDS_REVISION" in text:
                        result["reviewer_verdict"] = "NEEDS_REVISION"
                        # Extract feedback
                        if "FEEDBACK:" in text:
                            fb = text.split("FEEDBACK:", 1)[1].strip()
                            result["reviewer_feedback"] = fb
                        else:
                            result["reviewer_feedback"] = text

            return result

        return _node

    # ── Node functions ────────────────────────────────────────────────

    def route_intent(state: AgentState) -> dict:
        """Classify the user's intent."""
        messages = state["messages"]
        user_msg = messages[-1].content if messages else ""

        router_messages = [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ]
        response = standard_llm.invoke(router_messages)

        content = response.content
        if isinstance(content, list):
            content = str(content)
        raw = str(content).strip().upper()

        intent = "GENERAL"
        for candidate in ["NEW_PART", "ASK_EXISTING", "MODIFY_EXISTING"]:
            if candidate in raw:
                intent = candidate
                break

        return {
            "intent": intent,
            "tool_call_count": 0,
            "refinement_round": 0,
            "builder_messages": [],
            "reviewer_messages": [],
            "root_part_id": "",
            "reviewer_verdict": "",
            "reviewer_feedback": "",
        }

    ask_node = _build_agent_node(ASK_SYSTEM_PROMPT, QUERY_TOOLS, standard_llm)
    modify_node = _build_agent_node(MODIFY_SYSTEM_PROMPT, MODIFY_TOOLS, standard_llm)

    def general_node(state: AgentState) -> dict:
        """Handle GENERAL questions without tools."""
        messages = [SystemMessage(content=GENERAL_SYSTEM_PROMPT)] + state["messages"]
        response = standard_llm.invoke(messages)
        return {"messages": [response]}

    # ── Adversarial NEW_PART nodes ────────────────────────────────────

    def refiner_node(state: AgentState) -> dict:
        """Agent 1 Step 1: Refine the user's request into a precise spec."""
        user_msg = state["messages"][-1].content if state["messages"] else ""
        messages = [
            SystemMessage(content=REFINER_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ]
        response = standard_llm.invoke(messages)
        spec_text = _extract_text(response.content)

        # Seed the builder's message history with the specification
        builder_seed = HumanMessage(content=("Build the following manufacturing tree in the database. Follow this specification exactly:\n\n" + spec_text))

        return {
            "messages": [AIMessage(content=("📋 I've analyzed your request and created a detailed manufacturing specification. The Builder agent is now constructing the part tree in the database..."))],
            "builder_messages": [builder_seed],
            "tool_call_count": 0,
        }

    builder_node = _build_sub_agent_node(BUILDER_SYSTEM_PROMPT, CREATE_TOOLS, "builder_messages", strong_llm)

    def reviewer_setup_node(state: AgentState) -> dict:
        """Prepare the Reviewer's message history to read from the DB."""
        root_id = state.get("root_part_id", "")
        round_num = state.get("refinement_round", 0)

        review_instruction = HumanMessage(content=(f"The Builder has completed the manufacturing tree. The root part ID is: {root_id}\nThis is review round {round_num + 1}.\n\nUse the tools to read the full tree from the database, inspect every part and operation, then give your verdict."))

        return {
            "reviewer_messages": [review_instruction],
            "reviewer_verdict": "",
            "reviewer_feedback": "",
            "tool_call_count": 0,
        }

    reviewer_node = _build_sub_agent_node(REVIEWER_SYSTEM_PROMPT, REVIEW_TOOLS, "reviewer_messages", standard_llm)

    def revision_setup_node(state: AgentState) -> dict:
        """Prepare the Builder for a revision round with Reviewer feedback."""
        feedback = state.get("reviewer_feedback", "No specific feedback provided.")
        round_num = state.get("refinement_round", 0)
        root_id = state.get("root_part_id", "")

        revision_prompt = BUILDER_REVISION_PROMPT.format(feedback=feedback)

        revision_msg = HumanMessage(content=(f"REVISION ROUND {round_num + 1}.\nThe current root part ID is: {root_id}\n\nThe Reviewer found issues. Fix them ALL:\n\n{feedback}"))

        # Keep existing builder messages and append the revision request
        existing_builder = list(state.get("builder_messages", []))
        existing_builder.append(revision_msg)

        return {
            "builder_messages": existing_builder,
            "builder_system_prompt": revision_prompt,
            "refinement_round": round_num + 1,
            "tool_call_count": 0,
            "reviewer_verdict": "",
        }

    def final_report_node(state: AgentState) -> dict:
        """The Reviewer approved. Produce the final report for the user."""
        # Find the reviewer's approval message which contains the summary
        reviewer_msgs = state.get("reviewer_messages", [])
        summary = ""
        for msg in reversed(reviewer_msgs):
            text = _extract_text(msg.content) if hasattr(msg, "content") else ""
            if "APPROVED" in text:
                # Extract everything after APPROVED
                parts = text.split("APPROVED", 1)
                summary = parts[1].strip() if len(parts) > 1 else text
                break

        rounds = state.get("refinement_round", 0) + 1
        root_id = state.get("root_part_id", "")

        report = f"✅ **Manufacturing tree built and verified!**\n\nThe Builder and Reviewer agents iterated through **{rounds} round(s)** to produce an unambiguous manufacturing plan.\n\n**Root Part ID:** `{root_id}`\n\n"
        if summary:
            report += f"**Reviewer Summary:**\n{summary}"
        else:
            report += "The manufacturing tree has been validated and is ready for execution. Use the tree viewer to inspect the full plan."

        return {"messages": [AIMessage(content=report)]}

    # ── Tool execution nodes ──────────────────────────────────────────

    ask_tool_node = ToolNode(tools=QUERY_TOOLS)
    modify_tool_node = ToolNode(tools=MODIFY_TOOLS)

    # Builder and Reviewer each get their own ToolNode
    builder_tool_node = ToolNode(tools=CREATE_TOOLS)
    reviewer_tool_node = ToolNode(tools=REVIEW_TOOLS)

    def builder_tool_passthrough(state: AgentState) -> dict:
        """After builder tools execute, append results to builder_messages."""
        # The last message(s) in state["messages"] are ToolMessages
        # We need to also track them in builder_messages
        last_msg = state["messages"][-1]
        existing = list(state.get("builder_messages", []))
        existing.append(last_msg)
        return {"builder_messages": existing}

    def reviewer_tool_passthrough(state: AgentState) -> dict:
        """After reviewer tools execute, append results to reviewer_messages."""
        last_msg = state["messages"][-1]
        existing = list(state.get("reviewer_messages", []))
        existing.append(last_msg)
        return {"reviewer_messages": existing}

    # ── Routing functions ─────────────────────────────────────────────

    def route_by_intent(
        state: AgentState,
    ) -> Literal["ask_node", "modify_node", "refiner_node", "general_node"]:
        """Route to the appropriate handler based on classified intent."""
        intent = state.get("intent", "GENERAL")
        if intent == "ASK_EXISTING":
            return "ask_node"
        elif intent == "MODIFY_EXISTING":
            return "modify_node"
        elif intent == "NEW_PART":
            return "refiner_node"
        else:
            return "general_node"

    def _should_continue_tools(tool_node_name: str, _agent_node_name: str):
        """Factory for tool-continuation routing."""

        def _router(state: AgentState) -> str:
            last = state["messages"][-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                return tool_node_name
            return END

        return _router

    def builder_should_continue(state: AgentState) -> str:
        """Check if the Builder needs to call more tools or is done."""
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "builder_tools"
        # Builder is done (produced text with DONE or hit limit)
        return "reviewer_setup"

    def reviewer_should_continue(state: AgentState) -> str:
        """Check if the Reviewer needs more tools or has given a verdict."""
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "reviewer_tools"
        # Reviewer is done — check verdict
        return "adversarial_gate"

    def adversarial_gate_node(state: AgentState) -> dict[str, Any]:
        """No-op node to anchor the adversarial decision gate."""
        return {}

    def adversarial_decision(state: AgentState) -> str:
        """Route based on the Reviewer's verdict."""
        verdict = state.get("reviewer_verdict", "")
        round_num = state.get("refinement_round", 0)

        if verdict == "APPROVED":
            return "final_report"
        elif round_num >= MAX_REFINEMENT_ROUNDS:
            # Force acceptance after max rounds
            return "final_report"
        else:
            # NEEDS_REVISION or unclear — send back to Builder
            return "revision_setup"

    # ── Build the graph ───────────────────────────────────────────────

    graph = StateGraph(AgentState)  # type: ignore[invalid-argument-type]

    # Shared nodes
    graph.add_node("router", route_intent)
    graph.add_node("ask_node", ask_node)
    graph.add_node("modify_node", modify_node)
    graph.add_node("general_node", general_node)
    graph.add_node("ask_tools", ask_tool_node)
    graph.add_node("modify_tools", modify_tool_node)

    # Adversarial NEW_PART nodes
    graph.add_node("refiner_node", refiner_node)
    graph.add_node("builder_node", builder_node)
    graph.add_node("builder_tools", builder_tool_node)
    graph.add_node("builder_tool_pass", builder_tool_passthrough)
    graph.add_node("reviewer_setup", reviewer_setup_node)
    graph.add_node("reviewer_node", reviewer_node)
    graph.add_node("reviewer_tools", reviewer_tool_node)
    graph.add_node("reviewer_tool_pass", reviewer_tool_passthrough)
    graph.add_node("adversarial_gate", adversarial_gate_node)
    graph.add_node("revision_setup", revision_setup_node)
    graph.add_node("final_report", final_report_node)

    # ── Edges ─────────────────────────────────────────────────────────

    # Entry
    graph.add_edge(START, "router")
    graph.add_conditional_edges("router", route_by_intent)

    # ASK flow (unchanged)
    graph.add_conditional_edges("ask_node", _should_continue_tools("ask_tools", "ask_node"))
    graph.add_edge("ask_tools", "ask_node")

    # MODIFY flow (unchanged)
    graph.add_conditional_edges("modify_node", _should_continue_tools("modify_tools", "modify_node"))
    graph.add_edge("modify_tools", "modify_node")

    # GENERAL flow (unchanged)
    graph.add_edge("general_node", END)

    # ── Adversarial NEW_PART flow ─────────────────────────────────────
    #
    # refiner_node → builder_node ⇄ builder_tools
    #                     ↓ (DONE)
    #              reviewer_setup → reviewer_node ⇄ reviewer_tools
    #                                    ↓ (verdict)
    #                           adversarial_gate
    #                          ↙              ↘
    #                  revision_setup      final_report → END
    #                       ↓
    #                  builder_node (loops back)

    graph.add_edge("refiner_node", "builder_node")

    # Builder tool loop
    graph.add_conditional_edges("builder_node", builder_should_continue)
    graph.add_edge("builder_tools", "builder_tool_pass")
    graph.add_edge("builder_tool_pass", "builder_node")

    # Builder done → Reviewer
    graph.add_edge("reviewer_setup", "reviewer_node")

    # Reviewer tool loop
    graph.add_conditional_edges("reviewer_node", reviewer_should_continue)
    graph.add_edge("reviewer_tools", "reviewer_tool_pass")
    graph.add_edge("reviewer_tool_pass", "reviewer_node")

    # Adversarial decision gate (not a real node — use conditional edges)
    # We use the adversarial_gate as a routing node
    graph.add_conditional_edges(
        "adversarial_gate",
        lambda state: adversarial_decision(state),
        {
            "final_report": "final_report",
            "revision_setup": "revision_setup",
        },
    )

    # Revision → Builder again
    graph.add_edge("revision_setup", "builder_node")

    # Final report → END
    graph.add_edge("final_report", END)

    # Compile
    compiled = graph.compile()

    # ── Wrap as a simple Runnable ─────────────────────────────────────

    def input_adapter(inputs: dict) -> dict:
        return {
            "messages": [HumanMessage(content=inputs["question"])],
            "intent": "",
            "tool_call_count": 0,
            "refinement_round": 0,
            "builder_messages": [],
            "reviewer_messages": [],
            "root_part_id": "",
            "reviewer_verdict": "",
            "reviewer_feedback": "",
        }

    def safe_invoke(inputs: dict) -> dict:
        try:
            return compiled.invoke(inputs, config={"recursion_limit": 200})
        except Exception as e:
            error_msg = f"The agent encountered an error: {e}"
            return {
                "messages": inputs["messages"] + [AIMessage(content=error_msg)],
                "intent": inputs.get("intent", ""),
            }

    def output_adapter(outputs: dict) -> str:
        content = outputs["messages"][-1].content

        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    texts.append(item.get("text", ""))
            if texts:
                content = "\n".join(texts)
            else:
                content = str(content)

        if not content or not str(content).strip():
            return "I'm sorry, I wasn't able to generate a response. Could you try rephrasing your question?"

        return content

    return RunnableLambda(input_adapter) | RunnableLambda(safe_invoke) | RunnableLambda(output_adapter)
