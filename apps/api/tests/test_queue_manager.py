import pytest

from app.workers.queue_manager import TTSQueueManager


@pytest.mark.asyncio
async def test_queue_manager_starts_only_configured_worker_count():
    manager = TTSQueueManager(concurrency=2)

    await manager.start()
    try:
        assert len(manager.workers) == 2
        assert all(not worker.done() for worker in manager.workers)
    finally:
        await manager.stop()
