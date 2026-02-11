import os
from dataclasses import asdict
from uuid import UUID

from interlock_graph.main import (
    add_equipment,
    add_input,
    clear_created_by,
    create_operation,
    create_part,
    delete_operation,
    delete_part,
    get_ancestors,
    get_consumers,
    get_created_by,
    get_equipment,
    get_full_timeline,
    get_inputs,
    get_leaf_currencies,
    get_node_by_id,
    get_operation,
    get_output_part,
    get_part,
    list_operations,
    list_parts,
    remove_equipment,
    remove_input,
    set_created_by,
    update_operation,
    update_part,
    validate_tree,
)
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from models.main import BaseNode, NodeStatus, OperationNode, OpType, PartNode

# ── Tool Definitions ──────────────────────────────────────────────────────────


@tool
def param_create_part(part: PartNode) -> PartNode:
    """Create a new part node in the manufacturing graph."""
    return create_part(part)


@tool
def param_get_part(part_id: UUID) -> PartNode | None:
    """Get a part node by its ID."""
    return get_part(part_id)


@tool
def param_list_parts(
    status: NodeStatus | None = None,
    is_currency: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[PartNode]:
    """List parts with optional filtering."""
    return list_parts(
        status=status, is_currency=is_currency, limit=limit, offset=offset
    )


@tool
def param_update_part(part: PartNode) -> PartNode:
    """Update an existing part node."""
    return update_part(part)


@tool
def param_delete_part(part_id: UUID) -> bool:
    """Delete a part node by ID."""
    return delete_part(part_id)


@tool
def param_create_operation(op: OperationNode) -> OperationNode:
    """Create a new operation node."""
    return create_operation(op)


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
def param_update_operation(op: OperationNode) -> OperationNode:
    """Update an existing operation node."""
    return update_operation(op)


@tool
def param_delete_operation(op_id: UUID) -> bool:
    """Delete an operation node by ID."""
    return delete_operation(op_id)


@tool
def param_get_node_by_id(node_id: UUID) -> BaseNode | None:
    """Get any node (Part or Operation) by ID."""
    return get_node_by_id(node_id)


@tool
def param_set_created_by(part_id: UUID, op_id: UUID) -> None:
    """Set the operation that creates a specific part."""
    set_created_by(part_id, op_id)


@tool
def param_clear_created_by(part_id: UUID) -> None:
    """Clear the 'created_by' relationship for a part."""
    clear_created_by(part_id)


@tool
def param_get_created_by(part_id: UUID) -> OperationNode | None:
    """Get the operation that creates a specific part."""
    return get_created_by(part_id)


@tool
def param_get_output_part(op_id: UUID) -> PartNode | None:
    """Get the part created by a specific operation."""
    return get_output_part(op_id)


@tool
def param_add_input(op_id: UUID, part_id: UUID) -> None:
    """Add a part as an input to an operation."""
    add_input(op_id, part_id)


@tool
def param_remove_input(op_id: UUID, part_id: UUID) -> bool:
    """Remove a part input from an operation."""
    return remove_input(op_id, part_id)


@tool
def param_get_inputs(op_id: UUID) -> list[PartNode]:
    """Get all input parts for an operation."""
    return get_inputs(op_id)


@tool
def param_get_consumers(part_id: UUID) -> list[OperationNode]:
    """Get all operations that consume a specific part."""
    return get_consumers(part_id)


@tool
def param_add_equipment(op_id: UUID, part_id: UUID) -> None:
    """Add a part as equipment/tooling for an operation."""
    add_equipment(op_id, part_id)


@tool
def param_remove_equipment(op_id: UUID, part_id: UUID) -> bool:
    """Remove equipment/tooling from an operation."""
    return remove_equipment(op_id, part_id)


@tool
def param_get_equipment(op_id: UUID) -> list[PartNode]:
    """Get all equipment/tooling used by an operation."""
    return get_equipment(op_id)


@tool
def param_get_full_timeline(part_id: UUID) -> list[BaseNode]:
    """Get the full manufacturing timeline for a part."""
    return get_full_timeline(part_id)


@tool
def param_get_ancestors(part_id: UUID) -> list[PartNode]:
    """Get all upstream ancestor parts."""
    return get_ancestors(part_id)


@tool
def param_get_leaf_currencies(part_id: UUID) -> list[PartNode]:
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
        model="gemini-3-flash-preview", google_api_key=os.environ["GEMINI_API_KEY"]
    )

    tools = [
        param_create_part,
        param_get_part,
        param_list_parts,
        param_update_part,
        param_delete_part,
        param_create_operation,
        param_get_operation,
        param_list_operations,
        param_update_operation,
        param_delete_operation,
        param_get_node_by_id,
        param_set_created_by,
        param_clear_created_by,
        param_get_created_by,
        param_get_output_part,
        param_add_input,
        param_remove_input,
        param_get_inputs,
        param_get_consumers,
        param_add_equipment,
        param_remove_equipment,
        param_get_equipment,
        param_get_full_timeline,
        param_get_ancestors,
        param_get_leaf_currencies,
        param_validate_tree,
    ]

    system_prompt = (
        "You are an expert in manufacturing tech transfer. "
        "You have access to a graph database of parts and operations. "
        "Use the provided tools to inspect, modify, "
        "and validate the manufacturing graph. "
        "Answer the user's questions based on the graph data. "
        "If you perform an action, explain what you did."
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
