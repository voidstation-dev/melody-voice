import pytest
import asyncio

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


@pytest.mark.asyncio
async def test_delayed_enqueue_does_not_block_caller():
    manager = TTSQueueManager(concurrency=1)
    started_at = asyncio.get_running_loop().time()

    await manager.enqueue_after("job-1", delay_seconds=0.05)

    assert asyncio.get_running_loop().time() - started_at < 0.02
    assert manager.queue.empty()
    await asyncio.sleep(0.06)
    assert await manager.queue.get() == "job-1"
    manager.queue.task_done()
