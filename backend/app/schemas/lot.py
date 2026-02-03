import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class LotPlotBind(BaseModel):
    plot_id: uuid.UUID
    share_pct: float | None = None


class LotCreate(BaseModel):
    lot_type: str = Field(..., min_length=1, max_length=64)  # washed / natural / honey
    sub_process: str | None = Field(None, max_length=128)
    received_at: datetime
    status: str = Field(default="active", max_length=64)
    notes: str | None = Field(None, max_length=1024)
    plot_ids: list[LotPlotBind] = Field(default_factory=list)


class LotResponse(BaseModel):
    lot_id: uuid.UUID
    lot_type: str
    sub_process: str | None
    received_at: datetime
    status: str
    notes: str | None
    is_locked: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LotList(BaseModel):
    items: list[LotResponse]
    total: int
