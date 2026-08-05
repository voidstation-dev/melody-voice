import json
from typing import Any
from urllib.parse import urlparse

AUDIO_KEY_PRIORITY = {
    "speech_url": 0,
    "speechUrl": 0,
    "audio_url": 1,
    "audioUrl": 1,
    "play_url": 2,
    "playUrl": 2,
    "download_url": 3,
    "downloadUrl": 3,
    "url": 4,
    "uri": 5,
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
    candidates: list[tuple[int, int, str]] = []
    order = 0

    def walk(node: Any, parent_key: str | None = None) -> None:
        nonlocal order
        node = _maybe_decode_json(node)
        if isinstance(node, dict):
            for key, value in node.items():
                decoded = _maybe_decode_json(value)
                if (
                    key in AUDIO_KEY_PRIORITY
                    and isinstance(decoded, str)
                    and _is_http_url(decoded)
                ):
                    candidates.append((AUDIO_KEY_PRIORITY[key], order, decoded))
                    order += 1
                walk(decoded, key)
        elif isinstance(node, list):
            for item in node:
                walk(item, parent_key)

    walk(payload)
    results: list[str] = []
    seen: set[str] = set()
    for _, _, url in sorted(candidates):
        if url not in seen:
            seen.add(url)
            results.append(url)
    return results
