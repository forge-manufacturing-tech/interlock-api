from uuid import UUID, uuid4

from auth.dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from models.main import (
    CurrencyAmount,
    LaborNode,
    OperationNode,
    OpType,
    PartNode,
    QuantityInput,
    ToolNode,
)
from orm.main import (
    create_labor,
    create_tool,
    delete_part,
    get_ancestors,
    get_bom,
    get_full_timeline,
    get_leaf_currencies,
    get_operation,
    get_part,
    list_labor,
    list_tools,
    manufacture_part,
    purchase_part,
    update_operation,
    update_operation_inputs,
    update_part,
    validate_tree,
)
from pydantic import BaseModel

router = APIRouter(tags=["Manufacturing"])


# ── Request Models ────────────────────────────────────────────────────


class PurchaseRequest(BaseModel):
    name: str
    cost: float
    currency: str = "USD"
    description: str | None = None
    unit_of_measure: str = "each"
    project_label: str | None = None
    is_public: bool = False


class AssembleRequest(BaseModel):
    name: str
    input_part_ids: list[UUID]
    quantities: list[float] | None = None
    description: str | None = None
    instructions: str | None = None
    yield_rate: float = 1.0
    setup_time_minutes: float = 0.0
    estimated_duration_minutes: float = 0.0
    labor_ids: list[UUID] | None = None
    labor_quantities: list[float] | None = None
    labor_units: list[str] | None = None
    tool_ids: list[UUID] | None = None
    tool_quantities: list[float] | None = None
    tool_units: list[str] | None = None
    project_label: str | None = None
    is_public: bool = False


class CreateLaborRequest(BaseModel):
    name: str
    hourly_rate: float
    description: str | None = None
    skill_level: str | None = None


class CreateToolRequest(BaseModel):
    name: str
    linked_part_id: UUID
    cost_rate: float
    rate_unit: str = "hour"
    setup_time_minutes: float = 0.0
    description: str | None = None


class ModifyPartRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    project_label: str | None = None
    is_public: bool | None = None


class UpdateOperationRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    instructions: str | None = None
    yield_rate: float | None = None
    setup_time_minutes: float | None = None
    estimated_duration_minutes: float | None = None
    project_label: str | None = None
    is_public: bool | None = None


class UpdateOperationInputsRequest(BaseModel):
    input_parts: list[QuantityInput] | None = None
    input_labor: list[QuantityInput] | None = None
    input_tools: list[QuantityInput] | None = None
    input_currencies: list[QuantityInput] | None = None


# ── Endpoints ─────────────────────────────────────────────────────────


@router.post("/parts/purchase", response_model=PartNode)
async def purchase_material_endpoint(
    req: PurchaseRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Purchase a new raw material or component.
    Creates a purchased part with an associated Purchase operation and cost.
    """
    part_id = uuid4()
    part = PartNode(
        id=part_id,
        name=req.name,
        description=req.description or f"Purchased {req.name}",
        unit_of_measure=req.unit_of_measure,
        owner_id=current_user["id"],
        project_label=req.project_label,
        is_public=req.is_public,
    )
    op_id = uuid4()
    op = OperationNode(
        id=op_id,
        name=f"Purchase {req.name}",
        description=f"Purchase transaction for {req.name}",
        op_type=OpType.PURCHASE,
        owner_id=current_user["id"],
        project_label=req.project_label,
        is_public=req.is_public,
    )
    cost_obj = CurrencyAmount(amount=req.cost, currency_code=req.currency)
    try:
        return purchase_part(part, op, [cost_obj])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/parts/assemble", response_model=PartNode)
async def assemble_part_endpoint(
    req: AssembleRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Assemble/manufacture a new part from existing input parts, with labor and tool usage.
    """
    if not req.input_part_ids:
        raise HTTPException(status_code=400, detail="At least one input part is required.")

    if not (req.labor_ids or req.tool_ids):
        raise HTTPException(status_code=400, detail="At least one labor or tool is required.")

    if req.quantities and len(req.quantities) != len(req.input_part_ids):
        raise HTTPException(status_code=400, detail="Quantities length must match input_part_ids.")

    # Build part inputs
    part_inputs = []
    for i, pid in enumerate(req.input_part_ids):
        qty = req.quantities[i] if req.quantities else 1.0
        part_inputs.append(QuantityInput(resource_id=pid, quantity=qty, unit="each"))

    # Build labor inputs
    labor_inputs: list[QuantityInput] = []
    if req.labor_ids:
        for i, lid in enumerate(req.labor_ids):
            qty = req.labor_quantities[i] if req.labor_quantities else 1.0
            unit = req.labor_units[i] if req.labor_units else "hours"
            labor_inputs.append(QuantityInput(resource_id=lid, quantity=qty, unit=unit))

    # Build tool inputs
    tool_inputs: list[QuantityInput] = []
    if req.tool_ids:
        for i, tid in enumerate(req.tool_ids):
            qty = req.tool_quantities[i] if req.tool_quantities else 1.0
            unit = req.tool_units[i] if req.tool_units else "hours"
            tool_inputs.append(QuantityInput(resource_id=tid, quantity=qty, unit=unit))

    part_id = uuid4()
    part = PartNode(
        id=part_id,
        name=req.name,
        description=req.description or f"Assembled {req.name}",
        owner_id=current_user["id"],
        project_label=req.project_label,
        is_public=req.is_public,
    )
    op_id = uuid4()
    op = OperationNode(
        id=op_id,
        name=f"Assemble {req.name}",
        description=f"Assembly/manufacturing operation for {req.name}",
        op_type=OpType.STANDARD,
        instructions=req.instructions,
        yield_rate=req.yield_rate,
        setup_time_minutes=req.setup_time_minutes,
        estimated_duration_minutes=req.estimated_duration_minutes,
        owner_id=current_user["id"],
        project_label=req.project_label,
        is_public=req.is_public,
    )

    try:
        return manufacture_part(part, op, part_inputs, labor_inputs, tool_inputs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/parts/{part_id}", response_model=PartNode)
async def modify_part_endpoint(
    part_id: UUID,
    req: ModifyPartRequest,
    current_user: dict = Depends(get_current_user),
):
    """Modify an existing part's name or description."""
    part = get_part(part_id, user_id=current_user["id"])
    if not part:
        raise HTTPException(status_code=404, detail="Part not found or access denied")
    if str(part.owner_id) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Only the owner can modify this part")

    if req.name is not None:
        part.name = req.name
    if req.description is not None:
        part.description = req.description
    if req.project_label is not None:
        part.project_label = req.project_label
    if req.is_public is not None:
        part.is_public = req.is_public

    try:
        return update_part(part)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/parts/{part_id}")
async def remove_part_endpoint(
    part_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Delete a part from the database."""
    part = get_part(part_id, user_id=current_user["id"])
    if not part:
        raise HTTPException(status_code=404, detail="Part not found or access denied")
    if str(part.owner_id) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Only the owner can delete this part")

    try:
        success = delete_part(part_id)
        if not success:
            raise HTTPException(status_code=404, detail="Part not found or could not be deleted")
        return {"status": "success", "message": f"Deleted part {part_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/parts/{part_id}/validate")
async def validate_part_endpoint(
    part_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Validate the manufacturing tree starting from a root part."""
    part = get_part(part_id, user_id=current_user["id"])
    if not part:
        raise HTTPException(status_code=404, detail="Part not found or access denied")
    try:
        result = validate_tree(part_id, user_id=current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/parts/{part_id}/ancestors", response_model=list[PartNode])
async def get_part_ancestors_endpoint(
    part_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get all upstream ancestor parts that feed into this part."""
    part = get_part(part_id, user_id=current_user["id"])
    if not part:
        raise HTTPException(status_code=404, detail="Part not found or access denied")
    try:
        return get_ancestors(part_id, user_id=current_user["id"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/parts/{part_id}/costs")
async def get_part_costs_endpoint(
    part_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get all leaf currency nodes (raw costs) upstream of a part."""
    part = get_part(part_id, user_id=current_user["id"])
    if not part:
        raise HTTPException(status_code=404, detail="Part not found or access denied")
    try:
        return get_leaf_currencies(part_id, user_id=current_user["id"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/parts/{part_id}/timeline")
async def get_part_timeline_endpoint(
    part_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get the full manufacturing timeline for a part."""
    part = get_part(part_id, user_id=current_user["id"])
    if not part:
        raise HTTPException(status_code=404, detail="Part not found or access denied")
    try:
        # get_full_timeline returns BaseNode list, which is polymorphic
        # FastAPI might struggle with strict List[BaseNode] if not handled,
        # allowing implicit dict return is safer here given polymorphic nature.
        return get_full_timeline(part_id, user_id=current_user["id"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/parts/{part_id}/bom")
async def get_part_bom_endpoint(
    part_id: UUID,
    quantity: float = 1.0,
    current_user: dict = Depends(get_current_user),
):
    """Get the flattened Bill of Materials for a part and quantity."""
    part = get_part(part_id, user_id=current_user["id"])
    if not part:
        raise HTTPException(status_code=404, detail="Part not found or access denied")
    try:
        return get_bom(part_id, quantity, user_id=current_user["id"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ── Operation Endpoints ────────────────────────────────────────────────


@router.patch("/operations/{op_id}", response_model=OperationNode)
async def patch_operation_endpoint(
    op_id: UUID,
    req: UpdateOperationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update operation details."""
    op = get_operation(op_id, user_id=current_user["id"])
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found or access denied")
    if str(op.owner_id) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Only the owner can modify this operation")

    if req.name is not None:
        op.name = req.name
    if req.description is not None:
        op.description = req.description
    if req.instructions is not None:
        op.instructions = req.instructions
    if req.yield_rate is not None:
        op.yield_rate = req.yield_rate
    if req.setup_time_minutes is not None:
        op.setup_time_minutes = req.setup_time_minutes
    if req.estimated_duration_minutes is not None:
        op.estimated_duration_minutes = req.estimated_duration_minutes
    if req.project_label is not None:
        op.project_label = req.project_label
    if req.is_public is not None:
        op.is_public = req.is_public

    try:
        return update_operation(op)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/operations/{op_id}/inputs")
async def update_operation_inputs_endpoint(
    op_id: UUID,
    req: UpdateOperationInputsRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update operation inputs (parts, labor, tools, currencies)."""
    op = get_operation(op_id, user_id=current_user["id"])
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found or access denied")
    if str(op.owner_id) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Only the owner can modify operation inputs")

    try:
        update_operation_inputs(
            op_id=op_id,
            input_parts=req.input_parts,
            input_labor=req.input_labor,
            input_tools=req.input_tools,
            input_currencies=req.input_currencies,
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ── Labor Endpoints ───────────────────────────────────────────────────


@router.get("/labor", response_model=list[LaborNode])
async def list_labor_endpoint(
    current_user: dict = Depends(get_current_user),
):
    """List all labor types available in the system."""
    return list_labor(user_id=current_user["id"])


@router.post("/labor", response_model=LaborNode)
async def create_labor_endpoint(
    req: CreateLaborRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new type of labor."""
    labor_id = uuid4()
    labor = LaborNode(
        id=labor_id,
        name=req.name,
        hourly_rate=req.hourly_rate,
        description=req.description or f"{req.name} labor",
        skill_level=req.skill_level,
        owner_id=current_user["id"],
        is_public=False,
    )
    try:
        return create_labor(labor)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ── Tool Endpoints ────────────────────────────────────────────────────


@router.get("/tools", response_model=list[ToolNode])
async def list_tools_endpoint(
    current_user: dict = Depends(get_current_user),
):
    """List all tools/machines available in the system."""
    return list_tools(user_id=current_user["id"])


@router.post("/tools", response_model=ToolNode)
async def create_tool_endpoint(
    req: CreateToolRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new tool/machine entry."""
    tool_id = uuid4()
    tool = ToolNode(
        id=tool_id,
        name=req.name,
        linked_part_id=req.linked_part_id,
        cost_rate=req.cost_rate,
        rate_unit=req.rate_unit,
        setup_time_minutes=req.setup_time_minutes,
        description=req.description or f"{req.name} machine/tool",
        owner_id=current_user["id"],
        is_public=False,
    )
    try:
        return create_tool(tool)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
