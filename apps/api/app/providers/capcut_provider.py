import json
from pathlib import Path
from typing import Any
from app.providers.base import ProviderResult, ProviderVoice

class CapCutProvider:
    def __init__(self, *, catalog_path: Path, device_path: Path | None = None):
        self.catalog_path = catalog_path
        self.device_path = device_path

    def list_voices(self, language: str | None = None) -> list[ProviderVoice]:
        if not self.catalog_path.exists():
            return []
        
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        voices: list[ProviderVoice] = []
        for item in data:
            lang_code = item.get("lang", "")
            if language and lang_code.lower() != language.lower():
                continue
            voices.append(
                ProviderVoice(
                    language_short=item.get("lan", ""),
                    language_code=lang_code,
                    voice_type=item.get("voice_type", ""),
                    display_name=item.get("display_name", ""),
                    resource_id=item.get("resource_id", ""),
                    captured_at=item.get("captured_at"),
                )
            )
        return voices

    def synthesize(
        self,
        *,
        text: str,
        voice_type: str,
        resource_id: str | None,
        rate: float,
    ) -> ProviderResult:
        from capcut_tts_api import CapCutClient
        from app.services.provider_response_parser import extract_audio_urls

        client = CapCutClient(device=self.device_path) if self.device_path else CapCutClient()
        response: dict[str, Any] = client.generate_speech(
            texts=text,
            voice=voice_type,
            resource_id=resource_id,
            rate=f"{rate:.2f}",
            wait=True,
            poll_interval=1.0,
            timeout=90.0,
        )

        return ProviderResult(
            raw_response=response,
            audio_urls=extract_audio_urls(response),
        )
