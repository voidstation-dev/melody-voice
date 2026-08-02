import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.tts_job import TTSJobModel
from app.providers.capcut_provider import CapCutProvider
from app.services.audio_storage import download_audio
from app.services.chunk_executor import (
    ChunkLimitExceeded,
    ChunkResult,
    JobSnapshot,
    ensure_chunk_limit,
    execute_chunks_bounded,
)
from app.services.progress_reporter import ProgressReporter
from app.utils.text_utils import split_text_into_chunks


async def process_chunk(
    *,
    index: int,
    text: str,
    provider: CapCutProvider,
    job: JobSnapshot,
) -> ChunkResult:
    result = await asyncio.to_thread(
        provider.synthesize,
        text=text,
        voice_type=job.voice_type,
        resource_id=job.resource_id,
        rate=job.rate,
    )

    if not result.audio_urls:
        raise ValueError(
            "AUDIO_URL_NOT_FOUND: "
            f"No playable audio URL extracted for chunk {index}"
        )

    destination = settings.audio_storage_dir / f"{job.id}_part{index}.mp3"
    mime_type, size = await download_audio(
        url=result.audio_urls[0],
        destination=destination,
        max_bytes=settings.tts_audio_max_bytes,
    )
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
    if len(parts) == 1 and rate == 1.0:
        parts[0].replace(destination)
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
    command.append(str(destination.absolute()))

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(
                "FFmpeg processing failed: "
                + stderr.decode("utf-8", errors="ignore")
            )
    finally:
        list_file.unlink(missing_ok=True)


async def execute_tts_job_step(
    job_id: str,
    *,
    provider: CapCutProvider | None = None,
    worker_id: int = 0,
) -> None:
    del worker_id  # Structured worker context is added in Phase 7.
    async with AsyncSessionLocal() as session:
        job = await session.get(TTSJobModel, job_id)
        if not job or job.status != "queued" or job.cancel_requested:
            return

        job.status = "processing"
        job.progress = 0
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

        active_provider = provider or CapCutProvider(
            catalog_path=settings.capcut_catalog_path
        )
        downloaded_files: list[Path] = []

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
                rate=job.rate,
            )
            raw_responses: list[dict | None] = [None] * len(chunks)
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
            if settings.save_raw_provider_responses:
                settings.raw_response_dir.mkdir(parents=True, exist_ok=True)
                raw_path = settings.raw_response_dir / f"{job.id}.json"
                raw_path.write_text(
                    json.dumps(raw_responses, indent=2),
                    encoding="utf-8",
                )
                job.raw_response_path = str(raw_path)

            final_destination = settings.audio_storage_dir / f"{job.id}.mp3"
            await combine_audio_parts(
                parts=downloaded_files,
                destination=final_destination,
                rate=snapshot.rate,
            )
            for part in downloaded_files:
                part.unlink(missing_ok=True)

            job.status = "completed"
            job.audio_path = str(final_destination)
            job.audio_mime_type = "audio/mpeg"
            job.audio_file_size = final_destination.stat().st_size
            job.progress = 100
            job.completed_at = datetime.now(timezone.utc)

        except ChunkLimitExceeded as exc:
            job.status = "failed"
            job.error_code = "TOO_MANY_CHUNKS"
            job.error_message = str(exc)
        except Exception as exc:
            if job.attempt_count < 5:
                job.attempt_count += 1
                job.status = "queued"
                job.progress = 0
                job.started_at = None
                job.error_code = None
                job.error_message = None
                await session.commit()

                await asyncio.sleep(2)
                from app.workers.queue_manager import queue_manager

                await queue_manager.enqueue(job.id)
                return

            job.status = "failed"
            job.error_code = (
                "PROVIDER_UNAVAILABLE"
                if "Provider" in str(exc)
                else "INTERNAL_ERROR"
            )
            job.error_message = str(exc)

        await session.commit()
