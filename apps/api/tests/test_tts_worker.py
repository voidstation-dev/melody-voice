import pytest
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tts_job import TTSJobModel
from app.workers.tts_worker import execute_tts_job_step

@pytest.mark.asyncio
async def test_worker_updates_job_status_failed_on_error(async_session: AsyncSession):
    job = TTSJobModel(
        text="Xin chào",
        text_hash="hash123",
        voice_type="invalid_voice",
        voice_display_name="Unknown",
        language_code="vi-VN",
        rate=1.0,
        status="queued"
    )
    async_session.add(job)
    await async_session.commit()

    with patch("app.providers.capcut_provider.CapCutProvider.synthesize", side_effect=Exception("Provider error")):
        await execute_tts_job_step(job.id, async_session)

    await async_session.refresh(job)
    assert job.status == "failed"
    assert job.error_code == "PROVIDER_UNAVAILABLE"
