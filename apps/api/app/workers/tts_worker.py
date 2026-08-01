import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.tts_job import TTSJobModel
from app.providers.capcut_provider import CapCutProvider
from app.services.audio_storage import download_audio

async def execute_tts_job_step(job_id: str, session: AsyncSession) -> None:
    job = await session.get(TTSJobModel, job_id)
    if not job or job.status != "queued":
        return

    job.status = "processing"
    job.started_at = datetime.now(timezone.utc)
    await session.commit()

    provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
    
    try:
        result = await asyncio.to_thread(
            provider.synthesize,
            text=job.text,
            voice_type=job.voice_type,
            resource_id=job.resource_id,
            rate=job.rate,
        )

        if settings.save_raw_provider_responses:
            settings.raw_response_dir.mkdir(parents=True, exist_ok=True)
            raw_file = settings.raw_response_dir / f"{job_id}.json"
            raw_file.write_text(json.dumps(result.raw_response, indent=2))
            job.raw_response_path = str(raw_file)

        if not result.audio_urls:
            raise ValueError("AUDIO_URL_NOT_FOUND: No playable audio URL extracted from provider")

        dest = settings.audio_storage_dir / f"{job_id}.mp3"
        mime, size = await download_audio(url=result.audio_urls[0], destination=dest)

        job.status = "completed"
        job.audio_path = str(dest)
        job.audio_mime_type = mime
        job.audio_file_size = size
        job.completed_at = datetime.now(timezone.utc)

    except Exception as exc:
        job.status = "failed"
        job.error_code = "PROVIDER_UNAVAILABLE" if "Provider" in str(exc) else "INTERNAL_ERROR"
        job.error_message = str(exc)
    
    await session.commit()
