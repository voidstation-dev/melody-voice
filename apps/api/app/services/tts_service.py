import hashlib
from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tts_job import TTSJobModel

def compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

async def create_tts_job(
    session: AsyncSession,
    *,
    text: str,
    voice_type: str,
    voice_display_name: str,
    language_code: str,
    resource_id: str | None = None,
    rate: float = 1.0,
    kind: str = "generation",
    batch_id: str | None = None,
    batch_position: int | None = None,
    source_file_name: str | None = None,
    source_file_size: int | None = None,
) -> TTSJobModel:
    cleaned_text = text.strip()
    job = TTSJobModel(
        kind=kind,
        text=cleaned_text,
        text_hash=compute_text_hash(cleaned_text),
        voice_type=voice_type,
        voice_display_name=voice_display_name,
        resource_id=resource_id,
        language_code=language_code,
        rate=rate,
        status="queued",
        batch_id=batch_id,
        batch_position=batch_position,
        source_file_name=source_file_name,
        source_file_size=source_file_size,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job

async def get_job_by_id(session: AsyncSession, job_id: str) -> TTSJobModel | None:
    return await session.get(TTSJobModel, job_id)

async def list_jobs(
    session: AsyncSession,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[TTSJobModel], int]:
    stmt = select(TTSJobModel).order_by(TTSJobModel.created_at.desc())
    if status:
        stmt = stmt.where(TTSJobModel.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    jobs = (await session.execute(stmt)).scalars().all()

    return jobs, total
