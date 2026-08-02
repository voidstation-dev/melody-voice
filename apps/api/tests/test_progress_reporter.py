from app.services.progress_reporter import ProgressReporter


def test_progress_requires_percent_step_and_time_interval():
    reporter = ProgressReporter(
        commit_interval_seconds=1.0,
        commit_step_percent=5,
        started_at=0.0,
    )

    assert reporter.should_commit(completed=2, total=20, now=0.5) is False
    assert reporter.should_commit(completed=2, total=20, now=1.0) is True
    assert reporter.should_commit(completed=3, total=20, now=1.5) is False
    assert reporter.should_commit(completed=4, total=20, now=2.0) is True


def test_progress_commits_ninety_percent_without_waiting():
    reporter = ProgressReporter(
        commit_interval_seconds=10.0,
        commit_step_percent=50,
        started_at=0.0,
    )

    assert reporter.should_commit(completed=9, total=10, now=0.1) is False
    assert reporter.should_commit(completed=10, total=10, now=0.2) is True
