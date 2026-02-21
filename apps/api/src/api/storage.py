from __future__ import annotations

import os
from io import BytesIO
from uuid import UUID, uuid4

from auth.dependencies import get_current_user, require_ai_access
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from models.main import FileAttachment
from orm.main import (
    add_file_attachment,
    delete_file_attachment,
    get_file_attachment,
    get_operation,
    get_part,
    list_file_attachments,
)
from storage import get_storage_provider

router = APIRouter(tags=["Storage"])


@router.post("/parts/{part_id}/files", response_model=FileAttachment)
async def upload_part_file(
    part_id: UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_ai_access),
):
    """Upload a file associated with a part."""
    part = get_part(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    storage = get_storage_provider()
    file_id = uuid4()
    extension = os.path.splitext(file.filename)[1] if file.filename else ""
    storage_path = f"parts/{part_id}/{file_id}{extension}"

    content = await file.read()
    size = len(content)

    try:
        storage.upload_file(storage_path, BytesIO(content), content_type=file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {str(e)}") from e

    return add_file_attachment(
        name=file.filename or "unnamed",
        storage_path=storage_path,
        content_type=file.content_type,
        size=size,
        part_id=part_id,
        owner_id=current_user["id"],
    )


@router.get("/parts/{part_id}/files", response_model=list[FileAttachment])
async def list_part_files(
    part_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """List all files associated with a part."""
    return list_file_attachments(part_id=part_id)


@router.post("/operations/{op_id}/files", response_model=FileAttachment)
async def upload_operation_file(
    op_id: UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_ai_access),
):
    """Upload a file associated with an operation."""
    op = get_operation(op_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")

    storage = get_storage_provider()
    file_id = uuid4()
    extension = os.path.splitext(file.filename)[1] if file.filename else ""
    storage_path = f"operations/{op_id}/{file_id}{extension}"

    content = await file.read()
    size = len(content)

    try:
        storage.upload_file(storage_path, BytesIO(content), content_type=file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {str(e)}") from e

    return add_file_attachment(
        name=file.filename or "unnamed",
        storage_path=storage_path,
        content_type=file.content_type,
        size=size,
        operation_id=op_id,
        owner_id=current_user["id"],
    )


@router.get("/operations/{op_id}/files", response_model=list[FileAttachment])
async def list_operation_files(
    op_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """List all files associated with an operation."""
    return list_file_attachments(operation_id=op_id)


@router.get("/files/{file_id}/download")
async def get_file_download_url(
    file_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get a signed URL to download a file."""
    attachment = get_file_attachment(file_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        storage = get_storage_provider()
        signed_url = storage.get_signed_url(attachment.storage_path)
        return {"url": signed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {str(e)}") from e


@router.delete("/files/{file_id}")
async def delete_file_endpoint(
    file_id: UUID,
    current_user: dict = Depends(require_ai_access),
):
    """Delete a file from storage and database."""
    attachment = get_file_attachment(file_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="File not found")

    # Only owner or admin can delete
    if str(attachment.owner_id) != str(current_user["id"]) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")

    try:
        storage = get_storage_provider()
        storage.delete_file(attachment.storage_path)
    except Exception as e:
        # We might want to continue deleting from DB if storage delete fails (e.g. file already gone)
        # But for now let's be strict.
        print(f"Warning: Failed to delete from storage: {e}")

    success = delete_file_attachment(file_id)
    return {"status": "success" if success else "failed"}
