"""Create the baseline TTS jobs schema.

Revision ID: 37c7b24d235a
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "37c7b24d235a"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tts_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("batch_id", sa.String(length=36), nullable=True),
        sa.Column("batch_position", sa.Integer(), nullable=True),
        sa.Column("source_file_name", sa.String(length=255), nullable=True),
        sa.Column("source_file_size", sa.Integer(), nullable=True),
        sa.Column(
            "cancel_requested",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("voice_type", sa.String(length=100), nullable=False),
        sa.Column("voice_display_name", sa.String(length=150), nullable=False),
        sa.Column("resource_id", sa.String(length=100), nullable=True),
        sa.Column("language_code", sa.String(length=20), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=True),
        sa.Column("provider_task_id", sa.String(length=100), nullable=True),
        sa.Column("provider_token", sa.String(length=255), nullable=True),
        sa.Column("audio_path", sa.String(length=255), nullable=True),
        sa.Column("audio_mime_type", sa.String(length=50), nullable=True),
        sa.Column("audio_file_size", sa.Integer(), nullable=True),
        sa.Column("raw_response_path", sa.String(length=255), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "batch_id",
        "created_at",
        "kind",
        "status",
        "text_hash",
        "voice_type",
    ):
        op.create_index(
            op.f(f"ix_tts_jobs_{column}"),
            "tts_jobs",
            [column],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("tts_jobs")
