import os
from dataclasses import asdict
from uuid import UUID

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from models.main import (
    BaseNode,
    CurrencyAmount,
    CurrencyNode,
    CurrencyQuantity,
    LaborNode,
    LaborQuantity,
    NodeStatus,
    OperationNode,
    OpType,
    PartNode,
    PartQuantity,
    QuantityInput,
    ToolNode,
    ToolQuantity,
)
from orm.main import (
    create_currency,
    create_labor,
    create_tool,
    delete_operation,
    delete_part,
    get_ancestors,
    get_created_by,
    get_currency,
    get_full_timeline,
    get_input_currencies,
    get_input_labor,
    get_input_parts,
    get_input_tools,
    get_labor,
    get_leaf_currencies,
    get_node_by_id,
    get_operation,
    get_output_part,
    get_part,
    get_tool,
    list_currencies,
    list_labor,
    list_operations,
    list_parts,
    list_tools,
    manufacture_part,
    purchase_part,
    update_operation,
    update_part,
    validate_tree,
)

# ── Tool Definitions ──────────────────────────────────────────────────────────

# -- Atomic / Transactional --


@tool
def param_purchase_part(
    part: PartNode,
    operation: OperationNode,
    cost: list[CurrencyAmount],
) -> PartNode | str:
    """
    Atomically create a raw material or purchased part.
    1. Validates operation type.
    2. Creates the PartNode.
    3. Creates the Purchase OperationNode.
    4. Creates a NEW CurrencyNode for this transaction (based on cost).
    5. Links Part -> Operation and Operation -> Currency.
    """
    try:
        return purchase_part(part, operation, cost)
    except ValueError as e:
        return f"Error: {e}"


@tool
def param_manufacture_part(
    part: PartNode,
    operation: OperationNode,
    input_parts: list[QuantityInput],
    input_labor: list[QuantityInput] | None = None,
    input_tools: list[QuantityInput] | None = None,
) -> PartNode | str:
    """
    Atomically create a manufactured part from upstream inputs.
    1. Validates that all input parts, labor, and tools exist.
    2. Validates that input parts are valid (have a creator).
    3. Creates the PartNode.
    4. Creates the Standard OperationNode.
    5. Links Part -> Operation and Operation -> Inputs.
    """
    try:
        return manufacture_part(
            part,
            operation,
            input_parts,
            input_labor or [],
            input_tools or [],
        )
    except ValueError as e:
        return f"Error: {e}"


# -- Part --


@tool
def param_get_part(part_id: UUID) -> PartNode | None:
    """Get a part node by its ID."""
    return get_part(part_id)


@tool
def param_list_parts(
    status: NodeStatus | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[PartNode]:
    """List parts with optional filtering."""
    return list_parts(status=status, limit=limit, offset=offset)


@tool
def param_update_part(part: PartNode) -> PartNode | str:
    """Update an existing part node."""
    try:
        return update_part(part)
    except ValueError as e:
        return f"Error: {e}"


@tool
def param_delete_part(part_id: UUID) -> bool:
    """Delete a part node by ID."""
    return delete_part(part_id)


# -- Currency --


@tool
def param_create_currency(curr: CurrencyNode) -> CurrencyNode | str:
    """Create a new currency node."""
    try:
        return create_currency(curr)
    except ValueError as e:
        return f"Error: {e}"


@tool
def param_get_currency(curr_id: UUID) -> CurrencyNode | None:
    """Get a currency node by ID."""
    return get_currency(curr_id)


@tool
def param_list_currencies() -> list[CurrencyNode]:
    """List all currencies."""
    return list_currencies()


# -- Labor --


@tool
def param_create_labor(labor: LaborNode) -> LaborNode | str:
    """Create a new labor node."""
    try:
        return create_labor(labor)
    except ValueError as e:
        return f"Error: {e}"


@tool
def param_get_labor(labor_id: UUID) -> LaborNode | None:
    """Get a labor node by ID."""
    return get_labor(labor_id)


@tool
def param_list_labor() -> list[LaborNode]:
    """List all labor nodes."""
    return list_labor()


# -- Tool --


@tool
def param_create_tool(tool: ToolNode) -> ToolNode | str:
    """Create a new tool node.

    The tool.linked_part_id MUST be the UUID of an existing PartNode.
    If that part does not exist, you must create it first.
    """
    try:
        return create_tool(tool)
    except ValueError as e:
        return f"Error: {e}"


@tool
def param_get_tool(tool_id: UUID) -> ToolNode | None:
    """Get a tool node by ID."""
    return get_tool(tool_id)


@tool
def param_list_tools() -> list[ToolNode]:
    """List all tool nodes."""
    return list_tools()


# -- Operation --


@tool
def param_get_operation(op_id: UUID) -> OperationNode | None:
    """Get an operation node by ID."""
    return get_operation(op_id)


@tool
def param_list_operations(
    op_type: OpType | None = None, limit: int = 100, offset: int = 0
) -> list[OperationNode]:
    """List operations with optional filtering."""
    return list_operations(op_type=op_type, limit=limit, offset=offset)


@tool
def param_update_operation(op: OperationNode) -> OperationNode | str:
    """Update an existing operation node."""
    try:
        return update_operation(op)
    except ValueError as e:
        return f"Error: {e}"


@tool
def param_delete_operation(op_id: UUID) -> bool:
    """Delete an operation node by ID."""
    return delete_operation(op_id)


# -- Generic --


@tool
def param_get_node_by_id(node_id: UUID) -> BaseNode | None:
    """Get any node (Part, Operation, Currency, Labor, Tool) by ID."""
    return get_node_by_id(node_id)


# -- Relationships --


@tool
def param_get_created_by(part_id: UUID) -> OperationNode | None:
    """Get the operation that creates a specific part."""
    return get_created_by(part_id)


@tool
def param_get_output_part(op_id: UUID) -> PartNode | None:
    """Get the part created by a specific operation."""
    return get_output_part(op_id)


# -- Inputs --


@tool
def param_get_input_parts(op_id: UUID) -> list[PartQuantity]:
    """Get input parts for an operation."""
    return get_input_parts(op_id)


@tool
def param_get_input_labor(op_id: UUID) -> list[LaborQuantity]:
    """Get input labor for an operation."""
    return get_input_labor(op_id)


@tool
def param_get_input_tools(op_id: UUID) -> list[ToolQuantity]:
    """Get input tools for an operation."""
    return get_input_tools(op_id)


@tool
def param_get_input_currencies(op_id: UUID) -> list[CurrencyQuantity]:
    """Get input currencies for an operation."""
    return get_input_currencies(op_id)


# -- Traversal --


@tool
def param_get_full_timeline(part_id: UUID) -> list[BaseNode]:
    """Get the full manufacturing timeline for a part."""
    return get_full_timeline(part_id)


@tool
def param_get_ancestors(part_id: UUID) -> list[PartNode]:
    """Get all upstream ancestor parts."""
    return get_ancestors(part_id)


@tool
def param_get_leaf_currencies(part_id: UUID) -> list[CurrencyNode]:
    """Get all leaf currency nodes (raw costs) upstream."""
    return get_leaf_currencies(part_id)


@tool
def param_validate_tree(root_id: UUID) -> dict:
    """Validate the manufacturing tree structure starting from a root."""
    return asdict(validate_tree(root_id))


# ── Agent Factory ─────────────────────────────────────────────────────────────


def get_tech_transfer_agent():
    """
    Returns a configured LangChain AgentExecutor compatible with StrOutputParser
    expectations.
    """
    from langchain.agents import create_agent
    from langchain_core.messages import HumanMessage
    from langchain_core.runnables import RunnableLambda

    if "GEMINI_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=os.environ["GEMINI_API_KEY"],
    )

    tools = [
        # Atomic
        param_purchase_part,
        param_manufacture_part,
        # Part
        param_get_part,
        param_list_parts,
        param_update_part,
        param_delete_part,
        # Currency
        param_create_currency,
        param_get_currency,
        param_list_currencies,
        # Labor
        param_create_labor,
        param_get_labor,
        param_list_labor,
        # Tool
        param_create_tool,
        param_get_tool,
        param_list_tools,
        # Operation
        param_get_operation,
        param_list_operations,
        param_update_operation,
        param_delete_operation,
        # Generic
        param_get_node_by_id,
        # Relationships
        param_get_created_by,
        param_get_output_part,
        # Inputs
        param_get_input_parts,
        param_get_input_labor,
        param_get_input_tools,
        param_get_input_currencies,
        # Traversal
        param_get_full_timeline,
        param_get_ancestors,
        param_get_leaf_currencies,
        param_validate_tree,
    ]

    system_prompt = (
        "You are an expert in manufacturing tech transfer. "
        "You use a graph database to model manufacturing processes. "
        "RULES FOR GRAPH CONSTRUCTION: "
        "1. STRICT COSTING: only PURCHASE operations can use Currency inputs. "
        "   Do NOT assign Currency directly to a STANDARD operation. "
        "   Labor and Tool costs are automatically calculated "
        "by the system based on usage. "
        "2. BOTTOM-UP BUILD: Start with raw materials (PURCHASE ops). "
        "   Then build sub-assemblies and final products (STANDARD ops). "
        "3. TREE STRUCTURE: Prefer deep, vertical trees over flat ones. "
        "   Try to limit STANDARD operations to 2 input parts max. "
        "   It is better to have multiple sequential sub-assemblies "
        "than one huge assembly step. "
        "4. INPUTS REQUIRED: Every STANDARD operation MUST have inputs: "
        "   - Input Parts (from previous steps) "
        "   - Labor (type and hours) "
        "   - Tools (type and hours) "
        "Never create an orphan part. Always define its operation immediately."
    )

    graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )

    def input_adapter(inputs: dict) -> dict:
        return {"messages": [HumanMessage(content=inputs["question"])]}

    def output_adapter(outputs: dict) -> str:
        # outputs["messages"] is a list of messages.
        # The last one should be the AI response.
        return outputs["messages"][-1].content

    return RunnableLambda(input_adapter) | graph | RunnableLambda(output_adapter)
