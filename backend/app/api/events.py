import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from app.database import get_db
from app.models.lot import Lot
from app.models.event import Event
from app.schemas.event import EventCreate, EventResponse, EventList
from app.schemas.event_data import validate_event_data

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse)
async def create_event(body: EventCreate, db: AsyncSession = Depends(get_db)):
    lot = (await db.execute(select(Lot).where(Lot.lot_id == body.lot_id))).scalars().first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    if lot.is_locked:
        raise HTTPException(status_code=409, detail="Lot is locked, cannot add events")
    try:
        validated_data = validate_event_data(body.event_type, body.data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    event = Event(
        event_type=body.event_type,
        lot_id=body.lot_id,
        container_code=body.container_code,
        location_code=body.location_code,
        actor=body.actor,
        event_time=body.event_time,
        data=validated_data,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.event_id == event_id))
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("", response_model=EventList)
async def list_events(skip: int = 0, limit: int = 100, lot_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    base = select(Event)
    if lot_id is not None:
        base = base.where(Event.lot_id == lot_id)
    if lot_id is not None:
        total = (await db.execute(select(func.count()).select_from(Event).where(Event.lot_id == lot_id))).scalar() or 0
    else:
        total = (await db.execute(select(func.count()).select_from(Event))).scalar() or 0
    result = await db.execute(base.order_by(Event.event_time).offset(skip).limit(limit))
    items = list(result.scalars().all())
    return EventList(items=items, total=total)
