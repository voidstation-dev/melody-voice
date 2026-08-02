import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class TTSJobModel(Base):
    __tablename__ = "tts_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kind: Mapped[str] = mapped_column(String(20), default="generation", index=True)
    
    # Batch & Queue fields
    batch_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    batch_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    voice_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    voice_display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language_code: Mapped[str] = mapped_column(String(20), nullable=False)
    rate: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(20), index=True, default="queued")
    progress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_task_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    audio_file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_response_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
