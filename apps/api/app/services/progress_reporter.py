import time


class ProgressReporter:
    def __init__(
        self,
        *,
        commit_interval_seconds: float,
        commit_step_percent: int,
        started_at: float | None = None,
    ):
        self.commit_interval_seconds = commit_interval_seconds
        self.commit_step_percent = commit_step_percent
        self._last_commit_at = time.monotonic() if started_at is None else started_at
        self._last_committed_percent = 0

    def should_commit(
        self,
        *,
        completed: int,
        total: int,
        now: float | None = None,
    ) -> bool:
        if total <= 0:
            return False

        current_time = time.monotonic() if now is None else now
        progress = min(90, int((completed / total) * 90))
        reached_final_chunk_progress = progress == 90
        enough_progress = (
            progress - self._last_committed_percent
            >= self.commit_step_percent
        )
        enough_time = (
            current_time - self._last_commit_at
            >= self.commit_interval_seconds
        )

        if not reached_final_chunk_progress and not (
            enough_progress and enough_time
        ):
            return False
        if progress <= self._last_committed_percent:
            return False

        self._last_committed_percent = progress
        self._last_commit_at = current_time
        return True
