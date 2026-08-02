import hashlib
from datetime import datetime, timezone
from typing import Sequence
from fastapi import HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tts_job import TTSJobModel
from app.config import settings
from app.models.tts_job import utc_now

def compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


async def claim_job(session: AsyncSession, job_id: str) -> bool:
    result = await session.execute(
        update(TTSJobModel)
        .where(
            TTSJobModel.id == job_id,
            TTSJobModel.status == "queued",
            TTSJobModel.cancel_requested.is_(False),
            TTSJobModel.attempt_count
            < settings.tts_max_auto_retries + 1,
        )
        .values(
            status="processing",
            progress=0,
            started_at=utc_now(),
            attempt_count=TTSJobModel.attempt_count + 1,
        )
    )
    await session.commit()
    return result.rowcount == 1


async def assert_batch_capacity(
    session: AsyncSession,
    *,
    batch_id: str,
    new_text_length: int,
    max_files: int,
    max_total_chars: int,
) -> None:
    result = await session.execute(
        select(
            func.count(TTSJobModel.id),
            func.coalesce(func.sum(func.length(TTSJobModel.text)), 0),
        ).where(TTSJobModel.batch_id == batch_id)
    )
    file_count, total_chars = result.one()

    if file_count + 1 > max_files:
        raise HTTPException(
            status_code=422,
            detail="BATCH_FILE_LIMIT_EXCEEDED",
        )
    if int(total_chars) + new_text_length > max_total_chars:
        raise HTTPException(
            status_code=422,
            detail="BATCH_TEXT_LIMIT_EXCEEDED",
        )

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
