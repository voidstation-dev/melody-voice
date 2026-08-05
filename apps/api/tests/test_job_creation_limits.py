import asyncio

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.models.tts_job import TTSJobModel
from app.services.tts_service import (
    assert_batch_capacity,
    create_tts_job,
    create_tts_job_with_batch_limits,
)


@pytest.mark.asyncio
async def test_job_creation_rejects_text_over_configured_limit_before_provider(
    monkeypatch,
):
    monkeypatch.setattr(settings, "tts_max_text_chars", 10)

    def catalog_must_not_be_called(*args, **kwargs):
        raise AssertionError("catalog must not be called for invalid text")

    monkeypatch.setattr(
        "app.api.v1.tts_jobs.voice_catalog.get_voice",
        catalog_must_not_be_called,
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


@pytest.mark.asyncio
async def test_concurrent_batch_admission_never_exceeds_limit(
    async_session_factory,
):
    async def create(position: int):
        async with async_session_factory() as session:
            return await create_tts_job_with_batch_limits(
                session,
                text=f"job-{position}",
                voice_type="voice",
                voice_display_name="Voice",
                language_code="vi-VN",
                batch_id="shared-batch",
                batch_position=position,
                max_files=1,
                max_total_chars=100,
            )

    results = await asyncio.gather(
        create(0),
        create(1),
        return_exceptions=True,
    )

    assert sum(isinstance(result, TTSJobModel) for result in results) == 1
    errors = [result for result in results if isinstance(result, HTTPException)]
    assert len(errors) == 1
    assert errors[0].detail == "BATCH_FILE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_create_tts_job_persists_provider_fields(async_session):
    """The service layer must persist provider_id and VieNeu-specific fields
    so the worker can route jobs (Phase 5) and retries preserve the provider."""
    job = await create_tts_job(
        async_session,
        text="vieneu service text",
        voice_type="Minh Đức",
        voice_display_name="Minh Đức",
        language_code="vi-VN",
        provider_id="vieneu",
        backbone_id="v3turbo",
        style="tu_nhien",
        voice_profile_id="profile-1",
        request_metadata='{"k":1}',
    )
    fetched = await async_session.get(TTSJobModel, job.id)
    assert fetched is not None
    assert fetched.provider_id == "vieneu"
    assert fetched.backbone_id == "v3turbo"
    assert fetched.style == "tu_nhien"
    assert fetched.voice_profile_id == "profile-1"
    assert fetched.request_metadata == '{"k":1}'


@pytest.mark.asyncio
async def test_create_tts_job_defaults_to_capcut_provider(async_session):
    """Omitting provider_id must yield 'capcut' via the model server_default,
    not NULL — otherwise a CapCut job could silently be miscategorized."""
    job = await create_tts_job(
        async_session,
        text="capcut default text",
        voice_type="BV421_vivn_streaming",
        voice_display_name="Voice",
        language_code="vi-VN",
    )
    fetched = await async_session.get(TTSJobModel, job.id)
    assert fetched is not None
    assert fetched.provider_id == "capcut"
    assert fetched.backbone_id is None
    assert fetched.style is None
