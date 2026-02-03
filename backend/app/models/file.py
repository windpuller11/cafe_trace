import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class File(Base):
    __tablename__ = "files"

    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storage_url: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    event_files: Mapped[list["EventFile"]] = relationship("EventFile", back_populates="file", cascade="all, delete-orphan")


class EventFile(Base):
    __tablename__ = "event_files"

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.event_id", ondelete="CASCADE"), primary_key=True)
    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("files.file_id", ondelete="CASCADE"), primary_key=True)

    event: Mapped["Event"] = relationship("Event", back_populates="event_files")
    file: Mapped["File"] = relationship("File", back_populates="event_files")
