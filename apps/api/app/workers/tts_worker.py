import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.tts_job import TTSJobModel
from app.providers.capcut_provider import CapCutProvider
from app.services.audio_storage import download_audio

import re

def split_text_into_chunks(text: str, max_chunk_len: int = 1500) -> list[str]:
    sentences = re.split(r'(?<=[.!?\n])\s+', text.strip())
    chunks = []
    current_chunk = ""
    for s in sentences:
        if not s.strip():
            continue
        if len(current_chunk) + len(s) + 1 <= max_chunk_len:
            current_chunk = current_chunk + " " + s if current_chunk else s
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(s) > max_chunk_len:
                words = s.split()
                sub_chunk = ""
                for w in words:
                    if len(sub_chunk) + len(w) + 1 <= max_chunk_len:
                        sub_chunk = sub_chunk + " " + w if sub_chunk else w
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = w
                current_chunk = sub_chunk
            else:
                current_chunk = s
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

async def execute_tts_job_step(job_id: str, session: AsyncSession) -> None:
    job = await session.get(TTSJobModel, job_id)
    if not job or job.status != "queued":
        return

    job.status = "processing"
    job.progress = 0
    job.started_at = datetime.now(timezone.utc)
    await session.commit()

    provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
    
    try:
        chunks = split_text_into_chunks(job.text, max_chunk_len=1500)
        if not chunks:
            chunks = [""]

        total_chunks = len(chunks)
        downloaded_files = []
        raw_responses = []
        
        for i, chunk in enumerate(chunks):
            result = await asyncio.to_thread(
                provider.synthesize,
                text=chunk,
                voice_type=job.voice_type,
                resource_id=job.resource_id,
                rate=job.rate,
            )
            raw_responses.append(result.raw_response)

            if not result.audio_urls:
                raise ValueError(f"AUDIO_URL_NOT_FOUND: No playable audio URL extracted from provider for chunk {i}")

            part_dest = settings.audio_storage_dir / f"{job_id}_part{i}.mp3"
            mime, size = await download_audio(url=result.audio_urls[0], destination=part_dest)
            downloaded_files.append(part_dest)
            
            job.progress = int(((i + 1) / total_chunks) * 90)
            await session.commit()

        if settings.save_raw_provider_responses:
            settings.raw_response_dir.mkdir(parents=True, exist_ok=True)
            raw_file = settings.raw_response_dir / f"{job_id}.json"
            raw_file.write_text(json.dumps(raw_responses, indent=2))
            job.raw_response_path = str(raw_file)

        final_dest = settings.audio_storage_dir / f"{job_id}.mp3"

        if len(downloaded_files) == 1:
            downloaded_files[0].rename(final_dest)
        else:
            list_file = settings.audio_storage_dir / f"{job_id}_list.txt"
            with list_file.open("w", encoding="utf-8") as f:
                for pf in downloaded_files:
                    f.write(f"file '{pf.absolute()}'\n")
            
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(list_file.absolute()), "-c", "copy",
                str(final_dest.absolute())
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            out, err = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"FFmpeg concat failed: {err.decode('utf-8', errors='ignore')}")
                
            list_file.unlink(missing_ok=True)
            for pf in downloaded_files:
                pf.unlink(missing_ok=True)

        final_size = final_dest.stat().st_size
        job.status = "completed"
        job.audio_path = str(final_dest)
        job.audio_mime_type = "audio/mpeg"
        job.audio_file_size = final_size
        job.progress = 100
        job.completed_at = datetime.now(timezone.utc)

    except Exception as exc:
        import traceback
        traceback.print_exc()
        job.status = "failed"
        job.error_code = "PROVIDER_UNAVAILABLE" if "Provider" in str(exc) else "INTERNAL_ERROR"
        job.error_message = str(exc)
    
    await session.commit()
