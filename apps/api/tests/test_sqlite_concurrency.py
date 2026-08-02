import asyncio

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database import Base, create_database_engine
from app.models.tts_job import TTSJobModel


@pytest.mark.asyncio
async def test_sqlite_writers_complete_without_database_locked(tmp_path):
    engine = create_database_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'concurrent.db'}"
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def insert_job(index: int) -> None:
        async with session_factory() as session:
            session.add(
                TTSJobModel(
                    text=f"text-{index}",
                    text_hash=f"hash-{index}",
                    voice_type="voice",
                    voice_display_name="Voice",
                    language_code="vi-VN",
                    status="queued",
                )
            )
            await session.commit()

    try:
        await asyncio.gather(*(insert_job(index) for index in range(20)))
        async with session_factory() as session:
            count = (
                await session.execute(
                    select(func.count()).select_from(TTSJobModel)
                )
            ).scalar_one()
        assert count == 20
    finally:
        await engine.dispose()
