import pytest
from sqlalchemy import select
from app.database import get_async_session, init_database
from app.models.tts_job import TTSJobModel

@pytest.mark.asyncio
async def test_init_db_creates_tables():
    await init_database()
    async for session in get_async_session():
        result = await session.execute(select(TTSJobModel))
        assert result.scalars().all() == []
