import json
from typing import Any
from urllib.parse import urlparse

PREFERRED_AUDIO_KEYS = {
    "audio_url", "audioUrl", "download_url", "downloadUrl",
    "play_url", "playUrl", "url", "uri", "speech_url",
}

def _maybe_decode_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped or stripped[0] not in "[{":
        return value
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return value

def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

def extract_audio_urls(payload: Any) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()

    def walk(node: Any, parent_key: str | None = None) -> None:
        node = _maybe_decode_json(node)
        if isinstance(node, dict):
            for key, value in node.items():
                decoded = _maybe_decode_json(value)
                if key in PREFERRED_AUDIO_KEYS and isinstance(decoded, str) and _is_http_url(decoded):
                    if decoded not in seen:
                        seen.add(decoded)
                        results.append(decoded)
                walk(decoded, key)
        elif isinstance(node, list):
            for item in node:
                walk(item, parent_key)
        elif isinstance(node, str) and parent_key in PREFERRED_AUDIO_KEYS and _is_http_url(node):
            if node not in seen:
                seen.add(node)
                results.append(node)

    walk(payload)
    return results
