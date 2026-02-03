import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class PlotCreate(BaseModel):
    plot_name: str = Field(..., min_length=1, max_length=255)
    entity_name: str = Field(..., min_length=1, max_length=255)
    admin_division: str = Field(..., min_length=1, max_length=255)
    geo_polygon: dict | None = None
    area_m2: float | None = None
    tenure_type: str | None = Field(None, max_length=64)


class PlotResponse(BaseModel):
    plot_id: uuid.UUID
    plot_name: str
    entity_name: str
    admin_division: str
    geo_polygon: dict | None
    area_m2: float | None
    tenure_type: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlotList(BaseModel):
    items: list[PlotResponse]
    total: int
