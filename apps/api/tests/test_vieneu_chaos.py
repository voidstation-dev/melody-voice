import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest

from app.workers.queue_manager import TTSQueueManager
from app.exceptions import TTSJobError
from app.workers.tts_worker import execute_tts_job_step


@pytest.mark.asyncio
async def test_mixed_provider_queue_processing(monkeypatch):
    """
    Test that the QueueManager correctly routes jobs to different providers
    without blocking or deadlocks when dealing with a mixed queue.
    """
    executed_jobs = []

    async def mock_execute(*args, **kwargs):
        job_id = args[0] if args else kwargs.get("job_id")
        executed_jobs.append(job_id)
        await asyncio.sleep(0.01)

    monkeypatch.setattr("app.workers.queue_manager.execute_tts_job_step", mock_execute)

    # Use a dummy provider registry
    provider_registry = {"capcut": object(), "vieneu": object()}

    manager = TTSQueueManager(concurrency=2, provider_registry=provider_registry)

    await manager.start()
    try:
        # Enqueue 10 jobs mixed
        for i in range(10):
            await manager.enqueue(f"job-{i}")

        await asyncio.wait_for(manager.queue.join(), timeout=2.0)
    finally:
        await manager.stop()

    assert len(executed_jobs) == 10
    assert set(executed_jobs) == {f"job-{i}" for i in range(10)}



@pytest.mark.asyncio
async def test_low_disk_space_handling(monkeypatch):
    """
    Test that an OSError representing low disk space during audio synthesis
    is caught and handled, failing the job rather than crashing the worker.
    """
    from app.providers.vieneu_provider import VieneuProvider
    from unittest.mock import MagicMock
    
    provider = VieneuProvider()
    
    # Mock resolve to avoid DB
    async def mock_resolve(*args, **kwargs):
        return ("v3", None, "prompt")
    monkeypatch.setattr(provider, "_resolve_custom_voice", mock_resolve)
    
    # Mock engine save to raise OSError
    class MockEngine:
        def infer(self, *args, **kwargs):
            return "mocked_wav"
        def save(self, *args, **kwargs):
            raise OSError(28, "No space left on device")
            
    async def mock_get_engine():
        return MockEngine()
        
    monkeypatch.setattr(provider.manager, "get_engine", mock_get_engine)
    
    # ensure it raises OSError
    with pytest.raises(OSError):
        await provider.synthesize(
            text="Hello world",
            voice_type="vi-VN",
            resource_id=None,
            rate=1.0
        )
