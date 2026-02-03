import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Numeric, text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Lot(Base):
    __tablename__ = "lots"

    lot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lot_type: Mapped[str] = mapped_column(String(64), nullable=False)  # washed / natural / honey
    sub_process: Mapped[str | None] = mapped_column(String(128), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active")
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    lot_plots: Mapped[list["LotPlot"]] = relationship("LotPlot", back_populates="lot", cascade="all, delete-orphan")
    events: Mapped[list["Event"]] = relationship("Event", back_populates="lot", order_by="Event.event_time")


class LotPlot(Base):
    __tablename__ = "lot_plots"

    lot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lots.lot_id", ondelete="CASCADE"), primary_key=True)
    plot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plots.plot_id", ondelete="CASCADE"), primary_key=True)
    share_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    lot: Mapped["Lot"] = relationship("Lot", back_populates="lot_plots")
    plot: Mapped["Plot"] = relationship("Plot", back_populates="lot_plots")
