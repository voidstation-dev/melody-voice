import requests
import httpx
from capcut_tts_api.exceptions import CapCutAPIError, CapCutTaskError

from app.exceptions import TTSJobError
from app.services.retry_policy import (
    calculate_retry_delay,
    map_download_error,
    map_provider_error,
)


def test_timeout_is_retryable_provider_error():
    mapped = map_provider_error(requests.Timeout("slow provider"))

    assert mapped.code == "PROVIDER_TIMEOUT"
    assert mapped.retryable is True


def test_capcut_task_timeout_is_retryable():
    mapped = map_provider_error(
        CapCutTaskError("TTS Task timed out after 90 seconds")
    )

    assert mapped.code == "PROVIDER_TIMEOUT"
    assert mapped.retryable is True


def test_rate_limit_uses_retry_after_from_response_data():
    mapped = map_provider_error(
        CapCutAPIError(
            "rate limited",
            status_code=429,
            response_data={"retry_after": 7},
        )
    )

    assert mapped.code == "PROVIDER_RATE_LIMITED"
    assert mapped.retryable is True
    assert mapped.retry_after_seconds == 7.0


def test_provider_validation_error_is_not_retryable():
    mapped = map_provider_error(ValueError("invalid voice"))

    assert mapped.code == "PROVIDER_REJECTED"
    assert mapped.retryable is False


def test_retry_delay_uses_exponential_backoff_cap_and_jitter():
    assert calculate_retry_delay(
        attempt=0,
        base_delay_seconds=2,
        jitter=0.25,
    ) == 2.25
    assert calculate_retry_delay(
        attempt=1,
        base_delay_seconds=2,
        jitter=0.25,
    ) == 4.25
    assert calculate_retry_delay(
        attempt=10,
        base_delay_seconds=2,
        jitter=0.25,
    ) == 30.25


def test_retry_after_takes_precedence_over_backoff():
    assert calculate_retry_delay(
        attempt=0,
        base_delay_seconds=2,
        retry_after_seconds=12,
        jitter=0.25,
    ) == 12.25


def test_typed_error_is_not_remapped():
    original = TTSJobError(
        code="FFMPEG_FAILED",
        message="concat failed",
        retryable=False,
    )

    assert map_provider_error(original) is original


def test_download_connection_error_is_retryable():
    request = httpx.Request("GET", "https://cdn.example/audio.mp3")
    mapped = map_download_error(
        httpx.ConnectError("connection reset", request=request)
    )

    assert mapped.code == "AUDIO_DOWNLOAD_FAILED"
    assert mapped.retryable is True


def test_download_invalid_content_is_not_retryable():
    mapped = map_download_error(ValueError("Unexpected content type"))

    assert mapped.code == "AUDIO_INVALID_CONTENT"
    assert mapped.retryable is False
