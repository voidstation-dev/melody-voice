import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock
from app.api.v1.tts_jobs import retry_job_endpoint
from app.config import settings
from app.models.tts_job import TTSJobModel
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["service"] == "capvoice-api"


@pytest.mark.asyncio
async def test_readiness_reports_queue_and_dependency_state():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health/ready")

    assert response.status_code in {200, 503}
    payload = response.json()
    assert payload["status"] in {"ready", "degraded"}
    assert set(payload["checks"]) == {
        "database",
        "queue",
        "voice_catalog",
        "audio_directory",
        "ffmpeg",
        "circuit_breaker",
    }
    assert "queueDepth" in payload


@pytest.mark.asyncio
async def test_migration_failure_prevents_queue_start(monkeypatch):
    migration = AsyncMock(side_effect=RuntimeError("migration failed"))
    queue_start = AsyncMock()
    monkeypatch.setattr("app.main.run_database_migrations", migration)
    monkeypatch.setattr("app.main.queue_manager.start", queue_start)

    with pytest.raises(RuntimeError, match="migration failed"):
        async with app.router.lifespan_context(app):
            pass

    queue_start.assert_not_awaited()


@pytest.mark.asyncio
async def test_manual_retry_creates_new_job_and_preserves_original(
    async_session,
    monkeypatch,
):
    original = TTSJobModel(
        text="original text",
        text_hash="original-hash",
        voice_type="voice",
        voice_display_name="Voice",
        resource_id="resource",
        language_code="vi-VN",
        rate=1.25,
        status="completed",
        progress=100,
        audio_path="/tmp/original.mp3",
        audio_file_size=123,
        batch_id="batch-1",
        batch_position=2,
    )
    async_session.add(original)
    await async_session.commit()
    original_id = original.id
    enqueue = AsyncMock(return_value=True)
    monkeypatch.setattr("app.api.v1.tts_jobs.queue_manager.enqueue", enqueue)

    response = await retry_job_endpoint(original_id, session=async_session)

    await async_session.refresh(original)
    retried = await async_session.get(TTSJobModel, response.id)
    assert response.id != original_id
    assert original.status == "completed"
    assert original.audio_path == "/tmp/original.mp3"
    assert original.audio_file_size == 123
    assert retried is not None
    assert retried.status == "queued"
    assert retried.attempt_count == 0
    assert retried.text == original.text
    assert retried.voice_type == original.voice_type
    assert retried.batch_id == original.batch_id
    enqueue.assert_awaited_once_with(retried.id)


@pytest.mark.asyncio
async def test_manual_retry_cannot_bypass_batch_file_limit(
    async_session,
    monkeypatch,
):
    original = TTSJobModel(
        text="original text",
        text_hash="full-batch",
        voice_type="voice",
        voice_display_name="Voice",
        language_code="vi-VN",
        status="failed",
        batch_id="full-batch",
        batch_position=0,
    )
    async_session.add(original)
    await async_session.commit()
    enqueue = AsyncMock(return_value=True)
    monkeypatch.setattr("app.api.v1.tts_jobs.queue_manager.enqueue", enqueue)
    monkeypatch.setattr(settings, "tts_max_batch_files", 1)

    with pytest.raises(HTTPException) as exc_info:
        await retry_job_endpoint(original.id, session=async_session)

    assert exc_info.value.detail == "BATCH_FILE_LIMIT_EXCEEDED"
    enqueue.assert_not_awaited()
