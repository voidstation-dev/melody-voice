import json
import time
from pathlib import Path
from typing import Any

SENSITIVE_KEY_PARTS = (
    "token",
    "url",
    "uri",
    "sign",
    "device",
    "text",
    "ssml",
)


def redact_provider_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            key_lower = key.lower()
            if any(part in key_lower for part in SENSITIVE_KEY_PARTS):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_provider_payload(value)
        return redacted
    if isinstance(payload, list):
        return [redact_provider_payload(value) for value in payload]
    return payload


def save_failed_provider_response(
    *,
    job_id: str,
    payload: Any,
    directory: Path,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{job_id}-failed.json"
    temporary = directory / f"{job_id}-failed.json.tmp"
    try:
        temporary.write_text(
            json.dumps(
                redact_provider_payload(payload),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(destination)
        return destination
    finally:
        temporary.unlink(missing_ok=True)


def cleanup_stale_raw_responses(
    directory: Path,
    *,
    older_than_seconds: float,
    now: float | None = None,
) -> int:
    if not directory.exists():
        return 0
    cutoff = (time.time() if now is None else now) - older_than_seconds
    removed = 0
    for path in directory.glob("*-failed.json"):
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)
            removed += 1
    return removed
