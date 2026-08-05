"""add provider fields to tts_jobs

Revision ID: a3f1c9d2e7b4
Revises: 1ccaccfcb3f0
Create Date: 2026-08-05

Adds provider_id (NOT NULL DEFAULT 'capcut'), backbone_id, style,
voice_profile_id, and request_metadata to tts_jobs so jobs can be routed to
the correct TTS provider (CapCut legacy or VieNeu). Existing rows
automatically receive provider_id='capcut' via the column server default, so
old jobs keep their provider and retry behavior.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a3f1c9d2e7b4"
down_revision: str | Sequence[str] | None = "1ccaccfcb3f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tts_jobs",
        sa.Column(
            "provider_id",
            sa.String(length=30),
            nullable=False,
            server_default="capcut",
        ),
    )
    op.add_column(
        "tts_jobs",
        sa.Column("backbone_id", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "tts_jobs",
        sa.Column("style", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "tts_jobs",
        sa.Column("voice_profile_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "tts_jobs",
        sa.Column("request_metadata", sa.Text(), nullable=True),
    )
    op.create_index(
        op.f("ix_tts_jobs_provider_id"),
        "tts_jobs",
        ["provider_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # SQLite cannot drop columns / indexes without batch mode.
    op.drop_index(op.f("ix_tts_jobs_provider_id"), table_name="tts_jobs")
    with op.batch_alter_table("tts_jobs") as batch_op:
        batch_op.drop_column("request_metadata")
        batch_op.drop_column("voice_profile_id")
        batch_op.drop_column("style")
        batch_op.drop_column("backbone_id")
        batch_op.drop_column("provider_id")