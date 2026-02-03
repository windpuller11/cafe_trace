import uuid
from datetime import datetime
from pydantic import BaseModel


class FileResponse(BaseModel):
    file_id: uuid.UUID
    storage_url: str
    sha256: str
    meta: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FileUploadMeta(BaseModel):
    file_id: uuid.UUID
    storage_url: str
    sha256: str
    meta: dict | None = None
