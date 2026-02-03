"""initial

Revision ID: 001
Revises:
Create Date: 2025-02-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plots",
        sa.Column("plot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plot_name", sa.String(255), nullable=False),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("admin_division", sa.String(255), nullable=False),
        sa.Column("geo_polygon", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("area_m2", sa.Numeric(12, 2), nullable=True),
        sa.Column("tenure_type", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("plot_id"),
    )
    op.create_table(
        "lots",
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lot_type", sa.String(64), nullable=False),
        sa.Column("sub_process", sa.String(128), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default=sa.text("'active'")),
        sa.Column("notes", sa.String(1024), nullable=True),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("lot_id"),
    )
    op.create_table(
        "lot_plots",
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("share_pct", sa.Numeric(5, 2), nullable=True),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.lot_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plot_id"], ["plots.plot_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("lot_id", "plot_id"),
    )
    op.create_table(
        "events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("container_code", sa.String(64), nullable=True),
        sa.Column("location_code", sa.String(64), nullable=True),
        sa.Column("actor", sa.String(255), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.lot_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_table(
        "files",
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_url", sa.String(512), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("file_id"),
    )
    op.create_table(
        "event_files",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.event_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.file_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id", "file_id"),
    )
    op.create_table(
        "devices",
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_type", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("serial_no", sa.String(128), nullable=False),
        sa.Column("location_code", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("calibration_due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("device_id"),
    )
    op.create_table(
        "device_channels",
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric", sa.String(64), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
        sa.Column("sampling_interval_sec", sa.Numeric(10, 0), nullable=True),
        sa.ForeignKeyConstraint(["device_id"], ["devices.device_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("channel_id"),
    )


def downgrade() -> None:
    op.drop_table("device_channels")
    op.drop_table("devices")
    op.drop_table("event_files")
    op.drop_table("files")
    op.drop_table("events")
    op.drop_table("lot_plots")
    op.drop_table("lots")
    op.drop_table("plots")
