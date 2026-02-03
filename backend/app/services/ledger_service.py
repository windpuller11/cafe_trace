# 对账聚合与红灯规则引擎
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.schemas.ledger import LedgerResponse, RedLight

# 红灯规则码
LEDGER_IMBALANCE = "LEDGER_IMBALANCE"
MOLD_FLAG = "MOLD_FLAG"
IMBALANCE_THRESHOLD_KG = 1.0


async def compute_ledger(session: AsyncSession, lot_id: uuid.UUID) -> LedgerResponse:
    """从 events 聚合计算对账摘要并运行红灯规则。"""
    stmt = (
        select(Event)
        .where(Event.lot_id == lot_id)
        .order_by(Event.event_time)
    )
    result = await session.execute(stmt)
    events = list(result.scalars().all())

    total_receive_cherry_kg = 0.0
    total_warehouse_in_kg = 0.0
    total_warehouse_out_kg = 0.0
    total_sample_retained_kg = 0.0
    red_lights: list[RedLight] = []

    for ev in events:
        d = ev.data or {}
        if ev.event_type == "RECEIVE_CHERRY":
            total_receive_cherry_kg += float(d.get("cherry_weight_kg", 0))
        elif ev.event_type == "WAREHOUSE_IN":
            total_warehouse_in_kg += float(d.get("in_weight_kg", 0))
        elif ev.event_type == "WAREHOUSE_OUT":
            total_warehouse_out_kg += float(d.get("out_weight_kg", 0))
            total_sample_retained_kg += float(d.get("sample_retained_kg", 0) or 0)
        elif ev.event_type == "DRYING_CHECK":
            if d.get("mold_flag") is True:
                red_lights.append(RedLight(code=MOLD_FLAG, message="干燥检测存在霉变标记"))

    # 生豆平衡：入库 - 出库 - 留样
    balance_kg = total_warehouse_in_kg - total_warehouse_out_kg - total_sample_retained_kg
    if abs(balance_kg) > IMBALANCE_THRESHOLD_KG:
        red_lights.append(
            RedLight(
                code=LEDGER_IMBALANCE,
                message=f"对账不平衡: balance_kg={balance_kg:.2f}，阈值 ±{IMBALANCE_THRESHOLD_KG}",
            )
        )

    status = "red" if red_lights else "green"
    return LedgerResponse(
        lot_id=str(lot_id),
        status=status,
        balance_kg=round(balance_kg, 2),
        total_receive_cherry_kg=round(total_receive_cherry_kg, 2),
        total_warehouse_in_kg=round(total_warehouse_in_kg, 2),
        total_warehouse_out_kg=round(total_warehouse_out_kg, 2),
        total_sample_retained_kg=round(total_sample_retained_kg, 2),
        red_lights=red_lights,
    )


class LedgerService:
    compute_ledger = staticmethod(compute_ledger)


ledger_service = LedgerService()
