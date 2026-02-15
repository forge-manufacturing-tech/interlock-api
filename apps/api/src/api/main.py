import base64
import csv
import io
import os
from typing import Optional
from uuid import UUID

import fitz
from ai.agent import get_tech_transfer_agent
from auth.dependencies import get_current_user, require_ai_access
from auth.routes import router as auth_router
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from models.main import PartNode
from openai import OpenAI
from orm.main import get_part, get_tree_json, list_parts, list_root_parts
from parsers.bom import parse_messy_bom
from scalar_fastapi import get_scalar_api_reference

app = FastAPI(title="Interlock API", description="Manufacturing Graph Intelligence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.middleware("http")
async def strip_api_prefix(request, call_next):
    if request.url.path.startswith("/api/"):
        request.scope["path"] = request.url.path[4:]
    return await call_next(request)

_WORKSPACE = os.environ.get("REPL_HOME", "/home/runner/workspace")
STATIC_DIR = os.path.join(_WORKSPACE, "frontend", "dist")


@app.get("/")
def read_root():
    if os.path.isdir(STATIC_DIR):
        from starlette.responses import FileResponse
        index = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
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


def _extract_pdf_text(content: bytes) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def _describe_image_with_ai(content: bytes, filename: str) -> str:
    client = OpenAI(
        api_key=os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY"),
        base_url=os.getenv("AI_INTEGRATIONS_OPENAI_BASE_URL"),
    )
    b64 = base64.b64encode(content).decode("utf-8")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/png")

    # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
    # do not change this unless explicitly requested by the user
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in detail. If it contains a manufacturing drawing, BOM, schematic, or technical document, extract all relevant data including part names, dimensions, materials, quantities, and specifications. Be thorough and structured."},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }
        ],
        max_completion_tokens=4096,
    )
    return response.choices[0].message.content or ""


@app.post("/agent/chat")
async def chat_agent(
    message: str = Form(""),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(require_ai_access),
):
    """
    Chat with the tech transfer agent.
    Supports optional file attachments (PDF, images).
    """
    parts = []

    if file:
        file_content = await file.read()
        filename = file.filename or "unknown"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext == "pdf":
            pdf_text = _extract_pdf_text(file_content)
            parts.append(f"[Extracted from uploaded PDF '{filename}']\n{pdf_text}")
        elif ext in ("png", "jpg", "jpeg", "gif", "webp"):
            description = _describe_image_with_ai(file_content, filename)
            parts.append(f"[AI analysis of uploaded image '{filename}']\n{description}")
        else:
            try:
                text_content = file_content.decode("utf-8")
                parts.append(f"[Content of uploaded file '{filename}']\n{text_content}")
            except UnicodeDecodeError:
                parts.append(f"[Uploaded binary file '{filename}' — {len(file_content)} bytes, could not decode as text]")

    if message:
        parts.append(message)

    combined = "\n\n".join(parts)
    if not combined.strip():
        raise HTTPException(status_code=400, detail="No message or file provided")

    agent = get_tech_transfer_agent()
    try:
        response = agent.invoke({"question": combined})
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def _flatten_tree_to_bom(node: dict, parent_name: str = "", rows: list | None = None) -> list[dict]:
    if rows is None:
        rows = []

    row = {
        "part_name": node.get("name", ""),
        "part_id": node.get("id", ""),
        "type": node.get("type", ""),
        "parent": parent_name,
        "description": node.get("description", ""),
        "unit_cost": node.get("unit_cost") or node.get("cost") or "",
        "quantity": node.get("quantity", ""),
        "unit": node.get("unit", ""),
        "status": node.get("status", ""),
    }
    rows.append(row)

    for child in node.get("children", []):
        _flatten_tree_to_bom(child, node.get("name", ""), rows)

    linked = node.get("linked_part")
    if linked:
        _flatten_tree_to_bom(linked, node.get("name", ""), rows)

    return rows


def _tree_to_work_instructions(node: dict, depth: int = 0) -> str:
    lines = []
    indent = "  " * depth
    node_name = node.get("name", "Unknown")
    node_type = node.get("type", "")

    if depth == 0:
        lines.append(f"# Work Instructions: {node_name}")
        lines.append(f"")
        lines.append(f"**Part ID:** {node.get('id', 'N/A')}")
        lines.append(f"**Status:** {node.get('status', 'N/A')}")
        if node.get("description"):
            lines.append(f"**Description:** {node['description']}")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")
    else:
        prefix = f"{indent}-"
        label = f"**{node_name}**"
        meta_parts = []
        if node_type:
            meta_parts.append(f"Type: {node_type}")
        if node.get("quantity"):
            qty_str = f"{node['quantity']}"
            if node.get("unit"):
                qty_str += f" {node['unit']}"
            meta_parts.append(f"Qty: {qty_str}")
        if node.get("unit_cost") or node.get("cost"):
            cost = node.get("unit_cost") or node.get("cost")
            meta_parts.append(f"Cost: ${cost}")
        if node.get("description"):
            meta_parts.append(node["description"])

        meta = f" ({', '.join(meta_parts)})" if meta_parts else ""
        lines.append(f"{prefix} {label}{meta}")

    children = node.get("children", [])

    operations = [c for c in children if c.get("type", "").lower() == "operation"]
    other_children = [c for c in children if c.get("type", "").lower() != "operation"]

    if operations and depth == 0:
        lines.append(f"## Assembly Steps")
        lines.append(f"")
        for i, op in enumerate(operations, 1):
            op_type = op.get("op_type", op.get("type", ""))
            lines.append(f"### Step {i}: {op.get('name', 'Operation')} ({op_type})")
            if op.get("description"):
                lines.append(f"")
                lines.append(f"{op['description']}")
            op_children = op.get("children", [])
            if op_children:
                lines.append(f"")
                lines.append(f"**Required Materials:**")
                for child in op_children:
                    _add_material_line(child, lines, 0)
            lines.append(f"")
    elif operations:
        for op in operations:
            lines.append(f"{indent}  - **Operation:** {op.get('name', '')} ({op.get('op_type', '')})")
            for child in op.get("children", []):
                _tree_to_work_instructions_recurse(child, depth + 2, lines)

    if other_children:
        if depth == 0:
            lines.append(f"## Bill of Materials")
            lines.append(f"")
        for child in other_children:
            sub = _tree_to_work_instructions(child, depth + 1)
            lines.append(sub)

    linked = node.get("linked_part")
    if linked:
        sub = _tree_to_work_instructions(linked, depth + 1)
        lines.append(sub)

    return "\n".join(lines)


def _add_material_line(node: dict, lines: list, depth: int):
    indent = "  " * depth
    qty = node.get("quantity", "")
    unit = node.get("unit", "")
    qty_str = f" - {qty} {unit}".strip() if qty else ""
    lines.append(f"{indent}  - {node.get('name', 'Unknown')}{qty_str}")
    for child in node.get("children", []):
        _add_material_line(child, lines, depth + 1)


def _tree_to_work_instructions_recurse(node: dict, depth: int, lines: list):
    indent = "  " * depth
    lines.append(f"{indent}- {node.get('name', '')} ({node.get('type', '')})")
    for child in node.get("children", []):
        _tree_to_work_instructions_recurse(child, depth + 1, lines)


@app.get("/trees/{part_id}/export/bom")
async def export_tree_as_bom(
    part_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Export a manufacturing tree as a CSV Bill of Materials."""
    tree = get_tree_json(part_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Tree not found")

    rows = _flatten_tree_to_bom(tree)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["part_name", "part_id", "type", "parent", "description", "unit_cost", "quantity", "unit", "status"])
    writer.writeheader()
    writer.writerows(rows)

    content = output.getvalue().encode("utf-8")
    root_name = tree.get("name", "tree").replace(" ", "_")

    return StreamingResponse(
        io.BytesIO(content),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{root_name}_bom.csv"'},
    )


@app.get("/trees/{part_id}/export/work-instructions")
async def export_tree_as_work_instructions(
    part_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Export a manufacturing tree as markdown work instructions."""
    tree = get_tree_json(part_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Tree not found")

    markdown = _tree_to_work_instructions(tree)

    content = markdown.encode("utf-8")
    root_name = tree.get("name", "tree").replace(" ", "_")

    return StreamingResponse(
        io.BytesIO(content),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{root_name}_work_instructions.md"'},
    )


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


if os.path.isdir(STATIC_DIR):
    from starlette.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        return {"detail": "Not found"}

    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="static-assets")
