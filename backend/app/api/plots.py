import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.plot import Plot
from app.schemas.plot import PlotCreate, PlotResponse, PlotList

router = APIRouter(prefix="/plots", tags=["plots"])


@router.post("", response_model=PlotResponse)
async def create_plot(body: PlotCreate, db: AsyncSession = Depends(get_db)):
    plot = Plot(
        plot_name=body.plot_name,
        entity_name=body.entity_name,
        admin_division=body.admin_division,
        geo_polygon=body.geo_polygon,
        area_m2=body.area_m2,
        tenure_type=body.tenure_type,
    )
    db.add(plot)
    await db.flush()
    await db.refresh(plot)
    return plot


@router.get("", response_model=PlotList)
async def list_plots(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    total = (await db.execute(select(func.count()).select_from(Plot))).scalar() or 0
    result = await db.execute(select(Plot).offset(skip).limit(limit))
    items = list(result.scalars().all())
    return PlotList(items=items, total=total)


@router.get("/{plot_id}", response_model=PlotResponse)
async def get_plot(plot_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plot).where(Plot.plot_id == plot_id))
    plot = result.scalars().first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    return plot
