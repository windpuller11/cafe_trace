from pydantic import BaseModel
from typing import Literal


class RedLight(BaseModel):
    code: str  # LEDGER_IMBALANCE | MOLD_FLAG | ...
    message: str


class LedgerResponse(BaseModel):
    lot_id: str
    status: Literal["green", "red"]
    balance_kg: float
    # 汇总（从事件聚合）
    total_receive_cherry_kg: float
    total_warehouse_in_kg: float
    total_warehouse_out_kg: float
    total_sample_retained_kg: float
    red_lights: list[RedLight]
