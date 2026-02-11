# Import from your internal packages!
from uuid import UUID

from ai.agent import get_tech_transfer_agent
from fastapi import FastAPI, File, HTTPException, UploadFile
from interlock_graph.main import get_part, list_parts
from models.main import PartNode
from parsers.bom import parse_messy_bom
from scalar_fastapi import get_scalar_api_reference

app = FastAPI()


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
async def ingest_bom(file: UploadFile = File(...)):
    content = await file.read()
    data = parse_messy_bom(content, file.filename or "unknown")
    return {"filename": file.filename, "rows": len(data), "preview": data[:3]}


@app.post("/agent/chat")
async def chat_agent(message: str):
    """
    Chat with the tech transfer agent.
    The agent can inspect and modify the manufacturing graph.
    """
    agent = get_tech_transfer_agent()
    # Note: In production, use async invoke and maintain history
    response = agent.invoke({"question": message})
    return {"response": response}


@app.get("/parts")
async def read_parts(limit: int = 100, offset: int = 0) -> list[PartNode]:
    """List parts in the manufacturing graph."""
    return list_parts(limit=limit, offset=offset)


@app.get("/parts/{part_id}")
async def read_part(part_id: UUID) -> PartNode:
    """Get a specific part by ID."""
    part = get_part(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part
