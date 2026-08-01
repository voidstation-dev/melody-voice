from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def init_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    from app.models.tts_job import TTSJobModel
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(TTSJobModel).where(TTSJobModel.status.in_(["processing", "queued"])))
        stuck_jobs = result.scalars().all()
        for job in stuck_jobs:
            job.status = "failed"
            job.error_code = "SERVER_RESTARTED"
            job.error_message = "Server restarted before job could complete."
        if stuck_jobs:
            await session.commit()
            print(f"Cleaned up {len(stuck_jobs)} stuck jobs.")

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
