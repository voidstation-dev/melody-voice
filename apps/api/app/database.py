from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


def create_database_engine(database_url: str) -> AsyncEngine:
    database_engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
    )

    if database_url.startswith("sqlite"):

        @event.listens_for(database_engine.sync_engine, "connect")
        def configure_sqlite_connection(dbapi_connection, connection_record):
            del connection_record
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=5000")
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()

    return database_engine


engine = create_database_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
