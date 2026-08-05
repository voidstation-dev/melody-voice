import asyncio
import logging
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings
from app.database import AsyncSessionLocal
from app.exceptions import TTSJobError
from app.models.tts_job import TTSJobModel
from app.providers.capcut_provider import CapCutProvider
from app.services.audio_cleanup import cleanup_job_artifacts
from app.services.audio_storage import download_audio, validate_audio_file
from app.services.chunk_executor import (
    ChunkLimitExceeded,
    ChunkResult,
    JobSnapshot,
    ensure_chunk_limit,
    execute_chunks_bounded,
)
from app.services.progress_reporter import ProgressReporter
from app.services.raw_response_storage import save_failed_provider_response
from app.services.retry_policy import (
    calculate_retry_delay,
    map_download_error,
    map_provider_error,
)
from app.services.tts_service import claim_job
from app.utils.audio_utils import get_audio_duration
from app.utils.text_utils import split_text_into_chunks

logger = logging.getLogger(__name__)


async def process_chunk(
    *,
    index: int,
    text: str,
    provider: Any,
    job: JobSnapshot,
) -> ChunkResult:
    try:
        result = await provider.synthesize(
            text=text,
            voice_type=job.voice_type,
            resource_id=job.resource_id,
            rate=job.rate,
            style=job.style,
        )
    except Exception as exc:
        raise map_provider_error(exc) from exc

    if not result.audio_urls and not result.local_paths:
        raise TTSJobError(
            code="AUDIO_URL_NOT_FOUND",
            message=f"No playable audio URL or local path extracted for chunk {index}",
            retryable=False,
        )

    destination = settings.audio_storage_dir / f"{job.id}_part{index}.mp3"
    try:
        if result.local_paths and len(result.local_paths) > 0:
            import shutil

            shutil.move(str(result.local_paths[0]), str(destination))
            mime_type = "audio/mpeg"
            size = destination.stat().st_size
        else:
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

    ffmpeg_binary = settings.ffmpeg_binary_path
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
    provider_registry: dict[str, Any] | None = None,
    worker_id: int = 0,
) -> None:
    started_monotonic = time.monotonic()
    async with AsyncSessionLocal() as session:
        if not await claim_job(session, job_id):
            return
        job = await session.get(TTSJobModel, job_id)
        if not job:
            return

        active_provider = None
        if provider_registry:
            active_provider = provider_registry.get(job.provider_id)
        if not active_provider:
            active_provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
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
                style=job.style,
                rate=(1.0 if settings.tts_apply_rate_with_ffmpeg else job.rate),
            )
            raw_responses = [None] * len(chunks)
            progress_reporter = ProgressReporter(
                commit_interval_seconds=(settings.tts_progress_commit_interval_seconds),
                commit_step_percent=settings.tts_progress_commit_step_percent,
            )

            async def run_chunk(*, index: int, text: str) -> ChunkResult:
                return await process_chunk(
                    index=index,
                    text=text,
                    provider=active_provider,
                    job=snapshot,
                )

            async def check_cancelled() -> bool:
                await session.refresh(job, ["cancel_requested"])
                return job.cancel_requested

            completed = 0
            async for result in execute_chunks_bounded(
                chunks,
                concurrency=settings.tts_chunk_concurrency,
                process_chunk=run_chunk,
                is_cancelled=check_cancelled,
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

            downloaded_files.sort(key=lambda path: int(path.stem.rsplit("part", 1)[1]))
            await combine_audio_parts(
                parts=downloaded_files,
                destination=final_destination,
                rate=(job.rate if settings.tts_apply_rate_with_ffmpeg else 1.0),
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
            
            if job.export_path:
                try:
                    import shutil
                    export_dir = Path(job.export_path)
                    export_dir.mkdir(parents=True, exist_ok=True)
                    
                    if job.source_file_name:
                        base_name = Path(job.source_file_name).stem
                    else:
                        first_line = job.text.split("\n")[0][:30].strip()
                        import re
                        safe_name = re.sub(r'[^a-zA-Z0-9\-_ ]', '', first_line).strip()
                        base_name = safe_name or f"melody-{job.id}"
                        
                    format_ext = job.export_format or "mp3"
                    export_file = export_dir / f"{base_name}.{format_ext}"
                    
                    if format_ext == "mp3":
                        shutil.copy2(final_destination, export_file)
                    else:
                        ffmpeg_binary = settings.ffmpeg_binary_path
                        command = [
                            ffmpeg_binary,
                            "-y",
                            "-i",
                            str(final_destination),
                            "-c:a",
                            "aac",
                            "-b:a",
                            "256k",
                            str(export_file),
                        ]
                        process = await asyncio.create_subprocess_exec(
                            *command,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        _, stderr = await process.communicate()
                        if process.returncode != 0:
                            logger.error(f"Auto-export to {format_ext} failed: {stderr}")
                except Exception as e:
                    logger.error(f"Auto-export failed for {job.id}: {e}")

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
                    "duration_ms": int((time.monotonic() - started_monotonic) * 1000),
                },
            )

        except Exception as exc:  # noqa: BLE001
            import asyncio

            if (
                isinstance(exc, asyncio.CancelledError)
                or getattr(exc, "args", [None])[0] == "Job was cancelled by user"
            ):
                # Handle cancellation
                for part in downloaded_files:
                    part.unlink(missing_ok=True)
                job.status = "cancelled"
                job.progress = 0
                job.error_code = "CANCELLED"
                job.error_message = "Job was cancelled by the user"
                await session.commit()
                logger.info("Job cancelled: %s", job.id)
                return

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

            if error.retryable and job.attempt_count <= settings.tts_max_auto_retries:
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
                    batch_position=job.batch_position or 0,
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
                exc_info=True,
                extra={
                    "job_id": job.id,
                    "batch_id": job.batch_id,
                    "worker_id": worker_id,
                    "attempt": job.attempt_count,
                    "voice_type": job.voice_type,
                    "text_length": len(job.text),
                    "status": "failed",
                    "duration_ms": int((time.monotonic() - started_monotonic) * 1000),
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
