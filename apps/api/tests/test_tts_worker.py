import asyncio
import threading
import time

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base
from app.models.tts_job import TTSJobModel
from app.providers.base import ProviderResult
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


class CommitGuardSession(AsyncSession):
    active_commits = 0

    async def commit(self):
        type(self).active_commits += 1
        try:
            if type(self).active_commits > 1:
                raise AssertionError("AsyncSession.commit called concurrently")
            await asyncio.sleep(0.01)
            return await super().commit()
        finally:
            type(self).active_commits -= 1


class ConcurrentFakeProvider:
    def __init__(self):
        self._lock = threading.Lock()
        self.active = 0
        self.max_active = 0

    def synthesize(self, **kwargs):
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        time.sleep(0.03)
        with self._lock:
            self.active -= 1
        return ProviderResult(
            raw_response={"audio_url": "https://cdn.example/audio.mp3"},
            audio_urls=["https://cdn.example/audio.mp3"],
        )


@pytest.mark.asyncio
async def test_worker_chunk_tasks_never_commit_shared_session(
    tmp_path,
    monkeypatch,
):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'worker.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        engine,
        class_=CommitGuardSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        job = TTSJobModel(
            text="first. second.",
            text_hash="hash-concurrent",
            voice_type="voice",
            voice_display_name="Voice",
            language_code="vi-VN",
            status="queued",
        )
        session.add(job)
        await session.commit()
        job_id = job.id

    async def fake_download(*, url, destination, max_bytes):
        destination.write_bytes(b"ID3audio")
        return "audio/mpeg", 8

    async def fake_combine(*, parts, destination, rate):
        destination.write_bytes(b"ID3combined")

    provider = ConcurrentFakeProvider()
    monkeypatch.setattr("app.workers.tts_worker.AsyncSessionLocal", session_factory)
    monkeypatch.setattr(
        "app.workers.tts_worker.split_text_into_chunks",
        lambda text: ["first", "second"],
    )
    monkeypatch.setattr("app.workers.tts_worker.download_audio", fake_download)
    monkeypatch.setattr(
        "app.workers.tts_worker.combine_audio_parts",
        fake_combine,
        raising=False,
    )
    monkeypatch.setattr(settings, "audio_storage_dir", tmp_path)
    monkeypatch.setattr(settings, "tts_chunk_concurrency", 2, raising=False)
    monkeypatch.setattr(settings, "save_raw_provider_responses", False)

    try:
        await execute_tts_job_step(job_id, provider=provider, worker_id=7)
        async with session_factory() as session:
            reloaded = await session.get(TTSJobModel, job_id)
            assert reloaded is not None
            assert reloaded.status == "completed"
            assert reloaded.progress == 100
            assert provider.max_active == 2
    finally:
        await engine.dispose()
