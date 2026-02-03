import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Plot(Base):
    __tablename__ = "plots"

    plot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plot_name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_division: Mapped[str] = mapped_column(String(255), nullable=False)
    geo_polygon: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    area_m2: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    tenure_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    lot_plots: Mapped[list["LotPlot"]] = relationship("LotPlot", back_populates="plot")
