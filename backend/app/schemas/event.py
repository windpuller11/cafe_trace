import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=64)
    lot_id: uuid.UUID
    container_code: str | None = Field(None, max_length=64)
    location_code: str | None = Field(None, max_length=64)
    actor: str | None = Field(None, max_length=255)
    event_time: datetime
    data: dict = Field(..., min_length=1)


class EventResponse(BaseModel):
    event_id: uuid.UUID
    event_type: str
    lot_id: uuid.UUID
    container_code: str | None
    location_code: str | None
    actor: str | None
    event_time: datetime
    data: dict
    is_locked: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EventList(BaseModel):
    items: list[EventResponse]
    total: int
