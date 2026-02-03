# 文件上传与 sha256，存储到 uploads/
import hashlib
import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.file import File, EventFile
from app.schemas.file import FileUploadMeta

settings = get_settings()
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _storage_url(relative_path: str) -> str:
    return f"/uploads/{relative_path}"


async def save_upload(file: UploadFile, meta: dict | None = None) -> FileUploadMeta:
    """保存上传文件到 uploads/，计算 sha256，写入 files 表，返回元数据。"""
    content = await file.read()
    digest = _sha256(content)
    ext = Path(file.filename or "bin").suffix or ".bin"
    name = f"{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / name
    path.write_bytes(content)
    relative = name
    storage_url = _storage_url(relative)

    async with AsyncSessionLocal() as session:
        f = File(
            storage_url=storage_url,
            sha256=digest,
            meta=meta,
        )
        session.add(f)
        await session.commit()
        await session.refresh(f)
        return FileUploadMeta(file_id=f.file_id, storage_url=storage_url, sha256=digest, meta=meta)


async def bind_file_to_event(event_id: uuid.UUID, file_id: uuid.UUID) -> None:
    """将 file 绑定到 event（event_files 表）。"""
    async with AsyncSessionLocal() as session:
        ef = EventFile(event_id=event_id, file_id=file_id)
        session.add(ef)
        await session.commit()
