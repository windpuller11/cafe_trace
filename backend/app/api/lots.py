import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.lot import Lot, LotPlot
from app.models.plot import Plot
from app.schemas.lot import LotCreate, LotResponse, LotList
from app.schemas.event import EventList
from app.schemas.ledger import LedgerResponse

router = APIRouter(prefix="/lots", tags=["lots"])


@router.post("", response_model=LotResponse)
async def create_lot(body: LotCreate, db: AsyncSession = Depends(get_db)):
    lot = Lot(
        lot_type=body.lot_type,
        sub_process=body.sub_process,
        received_at=body.received_at,
        status=body.status,
        notes=body.notes,
    )
    db.add(lot)
    await db.flush()
    for bind in body.plot_ids:
        plot_exists = (await db.execute(select(Plot).where(Plot.plot_id == bind.plot_id))).scalars().first()
        if not plot_exists:
            raise HTTPException(status_code=404, detail=f"Plot {bind.plot_id} not found")
        db.add(LotPlot(lot_id=lot.lot_id, plot_id=bind.plot_id, share_pct=bind.share_pct))
    await db.refresh(lot)
    return lot


@router.get("", response_model=LotList)
async def list_lots(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    total = (await db.execute(select(func.count()).select_from(Lot))).scalar() or 0
    result = await db.execute(select(Lot).offset(skip).limit(limit))
    items = list(result.scalars().all())
    return LotList(items=items, total=total)


@router.get("/{lot_id}", response_model=LotResponse)
async def get_lot(lot_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lot).where(Lot.lot_id == lot_id))
    lot = result.scalars().first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    return lot


@router.get("/{lot_id}/events", response_model=EventList)
async def list_lot_events(lot_id: uuid.UUID, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    from app.models.event import Event
    lot_exists = (await db.execute(select(Lot).where(Lot.lot_id == lot_id))).scalars().first()
    if not lot_exists:
        raise HTTPException(status_code=404, detail="Lot not found")
    total = (await db.execute(select(func.count()).select_from(Event).where(Event.lot_id == lot_id))).scalar() or 0
    result = await db.execute(
        select(Event).where(Event.lot_id == lot_id).order_by(Event.event_time).offset(skip).limit(limit)
    )
    items = list(result.scalars().all())
    return EventList(items=items, total=total)


@router.get("/{lot_id}/ledger", response_model=LedgerResponse)
async def get_lot_ledger(lot_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from app.services.ledger_service import ledger_service
    lot_exists = (await db.execute(select(Lot).where(Lot.lot_id == lot_id))).scalars().first()
    if not lot_exists:
        raise HTTPException(status_code=404, detail="Lot not found")
    return await ledger_service.compute_ledger(db, lot_id)
