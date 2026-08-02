import pytest
from unittest.mock import AsyncMock, patch
from app.models.tts_job import TTSJobModel
from app.workers.tts_worker import execute_tts_job_step

@pytest.mark.asyncio
async def test_worker_requeues_job_after_provider_error(
    async_session_factory,
):
    async with async_session_factory() as session:
        job = TTSJobModel(
            text="Xin chào",
            text_hash="hash123",
            voice_type="invalid_voice",
            voice_display_name="Unknown",
            language_code="vi-VN",
            rate=1.0,
            status="queued",
        )
        session.add(job)
        await session.commit()
        job_id = job.id

    with (
        patch("app.workers.tts_worker.AsyncSessionLocal", async_session_factory),
        patch(
            "app.providers.capcut_provider.CapCutProvider.synthesize",
            side_effect=Exception("Provider error"),
        ),
        patch("app.workers.tts_worker.asyncio.sleep", new=AsyncMock()),
        patch(
            "app.workers.queue_manager.queue_manager.enqueue",
            new=AsyncMock(),
        ),
    ):
        await execute_tts_job_step(job_id)

    async with async_session_factory() as session:
        reloaded = await session.get(TTSJobModel, job_id)
        assert reloaded is not None
        assert reloaded.status == "queued"
        assert reloaded.attempt_count == 1
