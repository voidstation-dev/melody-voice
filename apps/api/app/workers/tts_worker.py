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

from app.utils.text_utils import split_text_into_chunks

async def execute_tts_job_step(job_id: str) -> None:
    # Use an independent session for the background task
    async with AsyncSessionLocal() as session:
        job = await session.get(TTSJobModel, job_id)
        if not job or job.status != "queued" or job.cancel_requested:
            return

        job.status = "processing"
        job.progress = 0
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

        provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
        
        try:
            chunks = split_text_into_chunks(job.text)
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
                
                # Update progress per chunk
                job.progress = int(((i + 1) / total_chunks) * 90)
                await session.commit()

            if settings.save_raw_provider_responses:
                settings.raw_response_dir.mkdir(parents=True, exist_ok=True)
                raw_file = settings.raw_response_dir / f"{job_id}.json"
                raw_file.write_text(json.dumps(raw_responses, indent=2))
                job.raw_response_path = str(raw_file)

            final_dest = settings.audio_storage_dir / f"{job_id}.mp3"

            needs_ffmpeg = len(downloaded_files) > 1 or job.rate != 1.0

            if not needs_ffmpeg:
                downloaded_files[0].rename(final_dest)
            else:
                list_file = settings.audio_storage_dir / f"{job_id}_list.txt"
                with list_file.open("w", encoding="utf-8") as f:
                    for pf in downloaded_files:
                        f.write(f"file '{pf.absolute()}'\n")
                
                ffmpeg_cmd = os.environ.get("FFMPEG_BINARY_PATH", "ffmpeg")
                cmd = [
                    ffmpeg_cmd, "-y", "-f", "concat", "-safe", "0",
                    "-i", str(list_file.absolute())
                ]
                
                if job.rate != 1.0:
                    cmd.extend(["-filter:a", f"atempo={job.rate}", "-q:a", "2"])
                else:
                    cmd.extend(["-c", "copy"])
                
                cmd.append(str(final_dest.absolute()))
                
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                out, err = await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(f"FFmpeg processing failed: {err.decode('utf-8', errors='ignore')}")
                    
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
            
            if job.attempt_count < 5:
                job.attempt_count += 1
                job.status = "queued"
                job.progress = 0
                job.started_at = None
                job.error_code = None
                job.error_message = None
                await session.commit()
                
                # Small delay to avoid immediate rate limit hit
                await asyncio.sleep(2)
                
                # Local import to avoid circular dependency
                from app.workers.queue_manager import queue_manager
                await queue_manager.enqueue(job.id)
                return
                
            job.status = "failed"
            job.error_code = "PROVIDER_UNAVAILABLE" if "Provider" in str(exc) else "INTERNAL_ERROR"
            job.error_message = str(exc)
        
        await session.commit()
