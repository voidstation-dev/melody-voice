import asyncio
import logging
import os
import tempfile
from pathlib import Path

from vieneu_core.engine import ModelManager
from vieneu_core.fixtures import FIXTURE_VOICES

from app.providers.base import ProviderResult, ProviderVoice

logger = logging.getLogger(__name__)

class VieneuProvider:
    def __init__(self):
        self.manager = ModelManager()
        self._inference_semaphore = asyncio.Semaphore(1)

    async def list_voices(self, language: str | None = None) -> list[ProviderVoice]:
        return [
            ProviderVoice(
                language_short="vi",
                language_code="vi-VN",
                voice_type=v.voice_id,
                display_name=v.display_name,
                resource_id=None,
            )
            for v in FIXTURE_VOICES
        ]

    async def synthesize(
        self,
        *,
        text: str,
        voice_type: str,
        resource_id: str | None,
        rate: float,
    ) -> ProviderResult:
        logger.info("VieneuProvider synthesizing %s", voice_type)
        engine = await self.manager.get_engine()
        
        # inference is cpu bound, run in thread behind semaphore
        async with self._inference_semaphore:
            wav = await asyncio.to_thread(
                engine.infer,
                text=text,
                voice=voice_type,
                style="tu_nhien",
                apply_watermark=False,
            )
        
        fd, wav_path_str = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        wav_path = Path(wav_path_str)
        
        try:
            await asyncio.to_thread(engine.save, wav, wav_path)
            
            mp3_path = wav_path.with_suffix(".mp3")
            ffmpeg_binary = os.environ.get("FFMPEG_BINARY_PATH", "ffmpeg")
            
            command = [
                ffmpeg_binary,
                "-y",
                "-i", str(wav_path),
                "-q:a", "2",
                str(mp3_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg conversion failed: {stderr.decode('utf-8', errors='ignore')}")
                
            return ProviderResult(
                raw_response={"engine": "vieneu-v3-turbo", "voice": voice_type},
                audio_urls=[],
                local_paths=[str(mp3_path)],
            )
        finally:
            wav_path.unlink(missing_ok=True)
