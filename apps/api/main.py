from fastapi import FastAPI, UploadFile, File
from scalar_fastapi import get_scalar_api_reference

# Import from your internal packages!
from core.agent import get_tech_transfer_agent
from parsers.bom import parse_messy_bom

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
    data = parse_messy_bom(content, file.filename)
    return {"filename": file.filename, "rows": len(data), "preview": data[:3]}

@app.post("/agent/ask")
async def ask_agent(question: str):
    agent = get_tech_transfer_agent()
    # Note: In production, use async invoke
    response = agent.invoke({"question": question})
    return {"answer": response}