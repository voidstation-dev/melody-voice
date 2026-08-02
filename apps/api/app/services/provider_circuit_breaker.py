import threading
import time
from collections import deque

from app.exceptions import TTSJobError


class ProviderCircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        window_seconds: float = 60.0,
        cooldown_seconds: float = 30.0,
    ):
        self.failure_threshold = failure_threshold
        self.window_seconds = window_seconds
        self.cooldown_seconds = cooldown_seconds
        self._lock = threading.Lock()
        self._failure_times: deque[float] = deque()
        self._state = "closed"
        self._open_until = 0.0
        self._half_open_in_flight = False

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._failure_times and self._failure_times[0] < cutoff:
            self._failure_times.popleft()

    def _open_error(self, now: float) -> TTSJobError:
        return TTSJobError(
            code="PROVIDER_UNAVAILABLE",
            message="Provider circuit breaker is open.",
            retryable=True,
            retry_after_seconds=max(0.0, self._open_until - now),
        )

    def before_call(self, *, now: float | None = None) -> None:
        current_time = time.monotonic() if now is None else now
        with self._lock:
            if self._state == "open":
                if current_time < self._open_until:
                    raise self._open_error(current_time)
                self._state = "half_open"
                self._half_open_in_flight = True
                return
            if self._state == "half_open":
                raise self._open_error(current_time)

    def record_success(self) -> None:
        with self._lock:
            self._state = "closed"
            self._failure_times.clear()
            self._open_until = 0.0
            self._half_open_in_flight = False

    def record_failure(
        self,
        error: TTSJobError,
        *,
        now: float | None = None,
    ) -> None:
        current_time = time.monotonic() if now is None else now
        with self._lock:
            if not error.retryable:
                if self._state == "half_open":
                    self._state = "closed"
                    self._half_open_in_flight = False
                return

            if self._state == "half_open":
                self._state = "open"
                self._open_until = current_time + self.cooldown_seconds
                self._half_open_in_flight = False
                return

            self._prune(current_time)
            self._failure_times.append(current_time)
            if len(self._failure_times) >= self.failure_threshold:
                self._state = "open"
                self._open_until = current_time + self.cooldown_seconds

    def snapshot(self, *, now: float | None = None) -> dict[str, object]:
        current_time = time.monotonic() if now is None else now
        with self._lock:
            self._prune(current_time)
            return {
                "state": self._state,
                "failure_count": len(self._failure_times),
                "retry_after_seconds": (
                    max(0.0, self._open_until - current_time)
                    if self._state == "open"
                    else None
                ),
            }
