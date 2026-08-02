import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.models.tts_job import TTSJobModel
from app.services.tts_service import assert_batch_capacity


@pytest.mark.asyncio
async def test_job_creation_rejects_text_over_configured_limit_before_provider(
    monkeypatch,
):
    monkeypatch.setattr(settings, "tts_max_text_chars", 10)

    def provider_must_not_be_called(*args, **kwargs):
        raise AssertionError("provider must not be called for invalid text")

    monkeypatch.setattr(
        "app.api.v1.tts_jobs.CapCutProvider.list_voices",
        provider_must_not_be_called,
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/tts/jobs",
            json={"text": "12345678901", "voiceType": "voice"},
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "TEXT_TOO_LONG"


@pytest.mark.asyncio
async def test_batch_capacity_rejects_next_file_over_file_limit(
    async_session,
):
    for position in range(2):
        async_session.add(
            TTSJobModel(
                text="abc",
                text_hash=f"hash-{position}",
                voice_type="voice",
                voice_display_name="Voice",
                language_code="vi-VN",
                status="queued",
                batch_id="batch-1",
                batch_position=position,
            )
        )
    await async_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await assert_batch_capacity(
            async_session,
            batch_id="batch-1",
            new_text_length=3,
            max_files=2,
            max_total_chars=100,
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "BATCH_FILE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_batch_capacity_rejects_total_text_limit(async_session):
    async_session.add(
        TTSJobModel(
            text="123456",
            text_hash="hash",
            voice_type="voice",
            voice_display_name="Voice",
            language_code="vi-VN",
            status="queued",
            batch_id="batch-2",
            batch_position=0,
        )
    )
    await async_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await assert_batch_capacity(
            async_session,
            batch_id="batch-2",
            new_text_length=5,
            max_files=50,
            max_total_chars=10,
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "BATCH_TEXT_LIMIT_EXCEEDED"
