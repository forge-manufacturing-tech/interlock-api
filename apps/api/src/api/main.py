from uuid import UUID

from ai.agent import get_tech_transfer_agent
from auth.dependencies import get_current_user
from auth.routes import router as auth_router
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from models.main import PartNode
from orm.main import get_part, get_tree_json, list_parts, list_root_parts
from parsers.bom import parse_messy_bom
from scalar_fastapi import get_scalar_api_reference

app = FastAPI(title="Interlock API", description="Manufacturing Graph Intelligence")

app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"system": "Interlock OS", "status": "online"}


@app.get("/api-docs", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Interlock API",
    )


@app.post("/ingest/bom")
async def ingest_bom(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    content = await file.read()
    data = parse_messy_bom(content, file.filename or "unknown")
    return {"filename": file.filename, "rows": len(data), "preview": data[:3]}


@app.post("/agent/chat")
async def chat_agent(
    message: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Chat with the tech transfer agent.
    The agent can inspect and modify the manufacturing graph.
    """
    agent = get_tech_transfer_agent()
    try:
        response = agent.invoke({"question": message})
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/parts")
async def read_parts(
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
) -> list[PartNode]:
    """List parts in the manufacturing graph."""
    return list_parts(limit=limit, offset=offset)


@app.get("/parts/{part_id}")
async def read_part(
    part_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> PartNode:
    """Get a specific part by ID."""
    part = get_part(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part


@app.get("/trees")
async def read_trees(
    current_user: dict = Depends(get_current_user),
) -> list[PartNode]:
    """Get all root parts (ends of trees)."""
    return list_root_parts()


@app.get("/trees/{part_id}")
async def read_tree_structure(
    part_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get a recursive tree structure starting from part_id."""
    return get_tree_json(part_id)
