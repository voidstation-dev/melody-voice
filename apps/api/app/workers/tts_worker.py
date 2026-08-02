import asyncio
import logging
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.database import AsyncSessionLocal
from app.exceptions import TTSJobError
from app.models.tts_job import TTSJobModel
from app.providers.capcut_provider import CapCutProvider
from app.services.audio_storage import download_audio
from app.services.audio_storage import validate_audio_file
from app.services.audio_cleanup import cleanup_job_artifacts
from app.utils.audio_utils import get_audio_duration
from app.services.chunk_executor import (
    ChunkLimitExceeded,
    ChunkResult,
    JobSnapshot,
    ensure_chunk_limit,
    execute_chunks_bounded,
)
from app.services.progress_reporter import ProgressReporter
from app.services.retry_policy import (
    calculate_retry_delay,
    map_download_error,
    map_provider_error,
)
from app.utils.text_utils import split_text_into_chunks
from app.services.tts_service import claim_job
from app.services.raw_response_storage import save_failed_provider_response


logger = logging.getLogger(__name__)


async def process_chunk(
    *,
    index: int,
    text: str,
    provider: CapCutProvider,
    job: JobSnapshot,
) -> ChunkResult:
    try:
        result = await asyncio.to_thread(
            provider.synthesize,
            text=text,
            voice_type=job.voice_type,
            resource_id=job.resource_id,
            rate=job.rate,
        )
    except Exception as exc:
        raise map_provider_error(exc) from exc

    if not result.audio_urls:
        raise TTSJobError(
            code="AUDIO_URL_NOT_FOUND",
            message=f"No playable audio URL extracted for chunk {index}",
            retryable=False,
        )

    destination = settings.audio_storage_dir / f"{job.id}_part{index}.mp3"
    try:
        mime_type, size = await download_audio(
            url=result.audio_urls[0],
            destination=destination,
            max_bytes=settings.tts_audio_max_bytes,
        )
    except Exception as exc:
        raise map_download_error(exc) from exc
    return ChunkResult(
        index=index,
        path=destination,
        raw_response=result.raw_response,
        mime_type=mime_type,
        size=size,
    )


async def combine_audio_parts(
    *,
    parts: list[Path],
    destination: Path,
    rate: float,
) -> None:
    temporary = Path(f"{destination}.tmp")
    if len(parts) == 1 and rate == 1.0:
        try:
            parts[0].replace(temporary)
            validate_audio_file(temporary, mime_type="audio/mpeg")
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        return

    list_file = destination.with_name(f"{destination.stem}_list.txt")
    with list_file.open("w", encoding="utf-8") as output:
        for part in parts:
            output.write(f"file '{part.absolute()}'\n")

    ffmpeg_binary = os.environ.get("FFMPEG_BINARY_PATH", "ffmpeg")
    command = [
        ffmpeg_binary,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file.absolute()),
    ]
    if rate != 1.0:
        command.extend(["-filter:a", f"atempo={rate}", "-q:a", "2"])
    else:
        command.extend(["-c", "copy"])
    command.extend(["-f", "mp3", str(temporary.absolute())])

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise TTSJobError(
                code="FFMPEG_FAILED",
                message=(
                    "FFmpeg processing failed: "
                    + stderr.decode("utf-8", errors="ignore")
                ),
                retryable=False,
            )
        validate_audio_file(temporary, mime_type="audio/mpeg")
        temporary.replace(destination)
    finally:
        list_file.unlink(missing_ok=True)
        temporary.unlink(missing_ok=True)


async def execute_tts_job_step(
    job_id: str,
    *,
    provider: CapCutProvider | None = None,
    worker_id: int = 0,
) -> None:
    started_monotonic = time.monotonic()
    async with AsyncSessionLocal() as session:
        if not await claim_job(session, job_id):
            return
        job = await session.get(TTSJobModel, job_id)
        if not job:
            return

        active_provider = provider or CapCutProvider(
            catalog_path=settings.capcut_catalog_path
        )
        downloaded_files: list[Path] = []
        final_destination = settings.audio_storage_dir / f"{job.id}.mp3"
        raw_responses: list[dict | None] = []

        logger.info(
            "TTS job started",
            extra={
                "job_id": job.id,
                "batch_id": job.batch_id,
                "worker_id": worker_id,
                "attempt": job.attempt_count,
                "voice_type": job.voice_type,
                "text_length": len(job.text),
                "status": "processing",
            },
        )

        try:
            chunks = split_text_into_chunks(job.text) or [""]
            ensure_chunk_limit(
                chunks,
                max_chunks=settings.tts_max_chunks_per_job,
            )

            snapshot = JobSnapshot(
                id=job.id,
                voice_type=job.voice_type,
                resource_id=job.resource_id,
                rate=(
                    1.0
                    if settings.tts_apply_rate_with_ffmpeg
                    else job.rate
                ),
            )
            raw_responses = [None] * len(chunks)
            progress_reporter = ProgressReporter(
                commit_interval_seconds=(
                    settings.tts_progress_commit_interval_seconds
                ),
                commit_step_percent=settings.tts_progress_commit_step_percent,
            )

            async def run_chunk(*, index: int, text: str) -> ChunkResult:
                return await process_chunk(
                    index=index,
                    text=text,
                    provider=active_provider,
                    job=snapshot,
                )

            completed = 0
            async for result in execute_chunks_bounded(
                chunks,
                concurrency=settings.tts_chunk_concurrency,
                process_chunk=run_chunk,
            ):
                downloaded_files.append(result.path)
                raw_responses[result.index] = result.raw_response
                completed += 1
                if progress_reporter.should_commit(
                    completed=completed,
                    total=len(chunks),
                ):
                    job.progress = int((completed / len(chunks)) * 90)
                    await session.commit()

            downloaded_files.sort(
                key=lambda path: int(path.stem.rsplit("part", 1)[1])
            )
            await combine_audio_parts(
                parts=downloaded_files,
                destination=final_destination,
                rate=(
                    job.rate
                    if settings.tts_apply_rate_with_ffmpeg
                    else 1.0
                ),
            )
            for part in downloaded_files:
                part.unlink(missing_ok=True)

            final_size = validate_audio_file(
                final_destination,
                mime_type="audio/mpeg",
            )
            
            audio_duration = await get_audio_duration(final_destination)

            job.status = "completed"
            job.audio_path = str(final_destination)
            job.audio_mime_type = "audio/mpeg"
            job.audio_file_size = final_size
            job.audio_duration = audio_duration
            job.progress = 100
            job.completed_at = datetime.now(timezone.utc)
            logger.info(
                "TTS job completed",
                extra={
                    "job_id": job.id,
                    "batch_id": job.batch_id,
                    "worker_id": worker_id,
                    "attempt": job.attempt_count,
                    "chunk_count": len(chunks),
                    "voice_type": job.voice_type,
                    "text_length": len(job.text),
                    "status": "completed",
                    "duration_ms": int(
                        (time.monotonic() - started_monotonic) * 1000
                    ),
                },
            )

        except Exception as exc:
            if isinstance(exc, ChunkLimitExceeded):
                error = TTSJobError(
                    code="TOO_MANY_CHUNKS",
                    message=str(exc),
                    retryable=False,
                )
            elif isinstance(exc, TTSJobError):
                error = exc
            else:
                error = TTSJobError(
                    code="INTERNAL_ERROR",
                    message=str(exc),
                    retryable=False,
                )

            if (
                error.retryable
                and job.attempt_count <= settings.tts_max_auto_retries
            ):
                job.status = "queued"
                job.progress = 0
                job.started_at = None
                job.error_code = None
                job.error_message = None
                await session.commit()
                from app.workers.queue_manager import queue_manager

                delay = calculate_retry_delay(
                    attempt=job.attempt_count - 1,
                    base_delay_seconds=settings.tts_retry_base_delay_seconds,
                    retry_after_seconds=error.retry_after_seconds,
                    jitter=random.uniform(0, 1),
                )
                await queue_manager.enqueue_after(
                    job.id,
                    delay_seconds=delay,
                )
                logger.warning(
                    "TTS job scheduled for retry",
                    extra={
                        "job_id": job.id,
                        "batch_id": job.batch_id,
                        "worker_id": worker_id,
                        "attempt": job.attempt_count,
                        "voice_type": job.voice_type,
                        "text_length": len(job.text),
                        "status": "queued",
                        "duration_ms": int(
                            (time.monotonic() - started_monotonic) * 1000
                        ),
                        "error_code": error.code,
                    },
                )
                return

            job.status = "failed"
            job.error_code = error.code
            job.error_message = error.message
            if settings.save_raw_provider_responses and any(raw_responses):
                raw_path = save_failed_provider_response(
                    job_id=job.id,
                    payload=raw_responses,
                    directory=settings.raw_response_dir,
                )
                job.raw_response_path = str(raw_path)
            logger.error(
                "TTS job failed",
                extra={
                    "job_id": job.id,
                    "batch_id": job.batch_id,
                    "worker_id": worker_id,
                    "attempt": job.attempt_count,
                    "voice_type": job.voice_type,
                    "text_length": len(job.text),
                    "status": "failed",
                    "duration_ms": int(
                        (time.monotonic() - started_monotonic) * 1000
                    ),
                    "error_code": error.code,
                },
            )

        finally:
            cleanup_job_artifacts(
                job.id,
                audio_dir=settings.audio_storage_dir,
            )
            if job.status != "completed":
                final_destination.unlink(missing_ok=True)

        await session.commit()
