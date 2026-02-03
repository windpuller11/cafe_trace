import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Numeric, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_type: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    serial_no: Mapped[str] = mapped_column(String(128), nullable=False)
    location_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    calibration_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    channels: Mapped[list["DeviceChannel"]] = relationship("DeviceChannel", back_populates="device", cascade="all, delete-orphan")


class DeviceChannel(Base):
    __tablename__ = "device_channels"

    channel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    sampling_interval_sec: Mapped[int | None] = mapped_column(Numeric(10, 0), nullable=True)

    device: Mapped["Device"] = relationship("Device", back_populates="channels")
