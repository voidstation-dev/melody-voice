from dataclasses import dataclass
from typing import Any, Protocol

@dataclass(frozen=True)
class ProviderVoice:
    language_short: str
    language_code: str
    voice_type: str
    display_name: str
    resource_id: str
    captured_at: str | None = None

@dataclass(frozen=True)
class ProviderResult:
    raw_response: dict[str, Any]
    audio_urls: list[str]

class TTSProvider(Protocol):
    def list_voices(self, language: str | None = None) -> list[ProviderVoice]: ...
    def synthesize(
        self,
        *,
        text: str,
        voice_type: str,
        resource_id: str | None,
        rate: float,
    ) -> ProviderResult: ...
