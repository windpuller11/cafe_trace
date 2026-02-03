import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from app.database import get_db
from app.services.file_service import save_upload, bind_file_to_event
from app.schemas.file import FileUploadMeta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.file import File

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileUploadMeta)
async def upload_file(file: UploadFile):
    meta = await save_upload(file)
    return meta


@router.post("/bind")
async def bind_to_event(event_id: uuid.UUID, file_id: uuid.UUID):
    await bind_file_to_event(event_id, file_id)
    return {"ok": True, "event_id": str(event_id), "file_id": str(file_id)}


@router.get("/{file_id}", response_model=FileUploadMeta)
async def get_file_meta(file_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(File).where(File.file_id == file_id))
    f = result.scalars().first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    return FileUploadMeta(file_id=f.file_id, storage_url=f.storage_url, sha256=f.sha256, meta=f.meta)
