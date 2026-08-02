import json
import logging
import os

from app.services.logging_config import JsonFormatter
from app.services.raw_response_storage import (
    cleanup_stale_raw_responses,
    redact_provider_payload,
)


def test_json_formatter_excludes_sensitive_extra_fields():
    record = logging.LogRecord(
        name="tts",
        level=logging.ERROR,
        pathname=__file__,
        lineno=10,
        msg="job failed",
        args=(),
        exc_info=None,
    )
    record.job_id = "job-1"
    record.error_code = "PROVIDER_TIMEOUT"
    record.provider_token = "secret"
    record.signed_url = "https://signed.example/secret"
    record.user_text = "private text"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["job_id"] == "job-1"
    assert payload["error_code"] == "PROVIDER_TIMEOUT"
    assert "provider_token" not in payload
    assert "signed_url" not in payload
    assert "user_text" not in payload
    assert "secret" not in json.dumps(payload)


def test_provider_payload_redaction_removes_tokens_urls_devices_and_text():
    payload = {
        "token": "secret-token",
        "audio_url": "https://signed.example/audio?sig=secret",
        "device_id": "device-secret",
        "nested": {"ssml": "private text", "status": "failed"},
    }

    redacted = redact_provider_payload(payload)
    serialized = json.dumps(redacted)

    assert redacted["nested"]["status"] == "failed"
    assert "secret-token" not in serialized
    assert "signed.example" not in serialized
    assert "device-secret" not in serialized
    assert "private text" not in serialized


def test_raw_response_retention_removes_only_stale_files(tmp_path):
    stale = tmp_path / "stale-failed.json"
    recent = tmp_path / "recent-failed.json"
    unrelated = tmp_path / "notes.txt"
    for path in (stale, recent, unrelated):
        path.write_text("payload", encoding="utf-8")
    os.utime(stale, (100.0, 100.0))
    os.utime(recent, (190.0, 190.0))
    os.utime(unrelated, (100.0, 100.0))

    removed = cleanup_stale_raw_responses(
        tmp_path,
        older_than_seconds=50,
        now=200.0,
    )

    assert removed == 1
    assert not stale.exists()
    assert recent.exists()
    assert unrelated.exists()
