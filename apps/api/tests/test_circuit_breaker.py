import pytest

from app.exceptions import TTSJobError
from app.services.provider_circuit_breaker import ProviderCircuitBreaker


def retryable_error() -> TTSJobError:
    return TTSJobError(
        code="PROVIDER_TIMEOUT",
        message="timeout",
        retryable=True,
    )


def test_breaker_opens_after_five_retryable_failures_in_window():
    breaker = ProviderCircuitBreaker(
        failure_threshold=5,
        window_seconds=60,
        cooldown_seconds=30,
    )

    for now in (0, 1, 2, 3, 4):
        breaker.record_failure(retryable_error(), now=now)

    assert breaker.snapshot(now=4)["state"] == "open"
    with pytest.raises(TTSJobError) as exc_info:
        breaker.before_call(now=10)
    assert exc_info.value.retryable is True
    assert exc_info.value.retry_after_seconds == 24


def test_breaker_allows_one_half_open_probe_then_closes_on_success():
    breaker = ProviderCircuitBreaker(
        failure_threshold=1,
        window_seconds=60,
        cooldown_seconds=30,
    )
    breaker.record_failure(retryable_error(), now=0)

    breaker.before_call(now=30)
    assert breaker.snapshot(now=30)["state"] == "half_open"
    with pytest.raises(TTSJobError):
        breaker.before_call(now=30)

    breaker.record_success()
    assert breaker.snapshot(now=31)["state"] == "closed"
    breaker.before_call(now=31)


def test_non_retryable_failure_does_not_open_breaker():
    breaker = ProviderCircuitBreaker(
        failure_threshold=1,
        window_seconds=60,
        cooldown_seconds=30,
    )
    breaker.record_failure(
        TTSJobError(
            code="PROVIDER_REJECTED",
            message="invalid voice",
            retryable=False,
        ),
        now=0,
    )

    assert breaker.snapshot(now=0)["state"] == "closed"
