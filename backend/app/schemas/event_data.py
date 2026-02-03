# 事件 data 字段的 Pydantic v2 校验（缺失/类型错误 → 422）
from typing import Any, Optional
from pydantic import BaseModel, Field
from enum import IntEnum


# ----- RECEIVE_CHERRY -----
class ReceiveCherryData(BaseModel):
    cherry_weight_kg: float = Field(..., gt=0)
    float_rate_pct: float = Field(..., ge=0, le=100)
    defect_rate_pct: float = Field(..., ge=0, le=100)
    ripeness_grade: int = Field(..., ge=0, le=3)
    fruit_temp_c: Optional[float] = None
    brix: Optional[float] = None
    ambient_temp_c: Optional[float] = None
    ambient_rh: Optional[float] = None


# ----- FERMENT -----
class TimeValuePoint(BaseModel):
    t: str  # ISO datetime or timestamp label
    value: float


class FermentData(BaseModel):
    mode: str = Field(..., min_length=1)
    start_time: str = Field(..., min_length=1)
    end_time: str = Field(..., min_length=1)
    temp_series: list[TimeValuePoint] = Field(default_factory=list)
    ph_series: list[TimeValuePoint] = Field(default_factory=list)
    brix_series: Optional[list[TimeValuePoint]] = None
    odor_flags: Optional[list[str]] = None


# ----- DRYING_CHECK -----
class DryingCheckData(BaseModel):
    moisture_pct: float = Field(..., ge=0, le=100)
    turns_per_day: float = Field(..., ge=0)
    covered_overnight: bool
    mold_flag: bool
    ambient_temp_c: Optional[float] = None
    ambient_rh: Optional[float] = None
    fruit_temp_c: Optional[float] = None


# ----- WAREHOUSE_IN -----
class WarehouseInData(BaseModel):
    in_weight_kg: float = Field(..., gt=0)
    packaging_type: str = Field(..., min_length=1)
    bin_code: str = Field(..., min_length=1)


# ----- WAREHOUSE_OUT -----
class WarehouseOutData(BaseModel):
    out_weight_kg: float = Field(..., gt=0)
    buyer_name: str = Field(..., min_length=1)
    shipment_ref: str = Field(..., min_length=1)
    sample_retained_kg: Optional[float] = Field(None, ge=0)


# ----- SENSOR_READING -----
class SensorReadingData(BaseModel):
    device_id: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    value: float = Field(...)
    unit: str = Field(..., min_length=1)
    quality_flag: Optional[str] = None
    raw: Optional[dict[str, Any]] = None


# 事件类型 → 校验模型
EVENT_DATA_SCHEMAS = {
    "RECEIVE_CHERRY": ReceiveCherryData,
    "FERMENT": FermentData,
    "DRYING_CHECK": DryingCheckData,
    "WAREHOUSE_IN": WarehouseInData,
    "WAREHOUSE_OUT": WarehouseOutData,
    "SENSOR_READING": SensorReadingData,
}

# 导出供 API 文档用
RECEIVE_CHERRY_SCHEMA = ReceiveCherryData
FERMENT_SCHEMA = FermentData
DRYING_CHECK_SCHEMA = DryingCheckData
WAREHOUSE_IN_SCHEMA = WarehouseInData
WAREHOUSE_OUT_SCHEMA = WarehouseOutData
SENSOR_READING_SCHEMA = SensorReadingData


def get_event_data_validator(event_type: str):
    return EVENT_DATA_SCHEMAS.get(event_type)


def validate_event_data(event_type: str, data: dict) -> dict:
    """校验 data 并返回校验后的 dict（用于写入 DB）。校验失败抛出 Pydantic ValidationError → 422。"""
    model_class = get_event_data_validator(event_type)
    if model_class is None:
        raise ValueError(f"Unknown event_type: {event_type}")
    instance = model_class.model_validate(data)
    return instance.model_dump(mode="json")
