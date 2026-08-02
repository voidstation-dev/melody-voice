import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import text

from app.database import Base, create_database_engine
from app.services.database_migrations import (
    MigrationError,
    run_database_migrations,
)


ALEMBIC_INI = Path(__file__).parents[1] / "alembic.ini"
HEAD_REVISION = "37c7b24d235a"


def sqlite_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path}"


@pytest.mark.asyncio
async def test_sqlite_engine_enables_required_pragmas(tmp_path):
    engine = create_database_engine(sqlite_url(tmp_path / "pragmas.db"))
    try:
        async with engine.connect() as connection:
            journal_mode = (
                await connection.execute(text("PRAGMA journal_mode"))
            ).scalar_one()
            synchronous = (
                await connection.execute(text("PRAGMA synchronous"))
            ).scalar_one()
            busy_timeout = (
                await connection.execute(text("PRAGMA busy_timeout"))
            ).scalar_one()
            foreign_keys = (
                await connection.execute(text("PRAGMA foreign_keys"))
            ).scalar_one()

        assert journal_mode.lower() == "wal"
        assert synchronous == 1
        assert busy_timeout == 5000
        assert foreign_keys == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_migrations_create_fresh_database(tmp_path):
    database_path = tmp_path / "fresh.db"

    await run_database_migrations(
        database_url=sqlite_url(database_path),
        alembic_ini_path=ALEMBIC_INI,
    )

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        revision = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0]
    assert "tts_jobs" in tables
    assert revision == HEAD_REVISION


def create_legacy_database(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE tts_jobs (
                id VARCHAR(36) PRIMARY KEY,
                kind VARCHAR(20) NOT NULL,
                text TEXT NOT NULL,
                text_hash VARCHAR(64) NOT NULL,
                voice_type VARCHAR(100) NOT NULL,
                voice_display_name VARCHAR(150) NOT NULL,
                resource_id VARCHAR(100),
                language_code VARCHAR(20) NOT NULL,
                rate FLOAT NOT NULL,
                status VARCHAR(20) NOT NULL,
                progress INTEGER,
                provider_task_id VARCHAR(100),
                provider_token VARCHAR(255),
                audio_path VARCHAR(255),
                audio_mime_type VARCHAR(50),
                audio_file_size INTEGER,
                raw_response_path VARCHAR(255),
                error_code VARCHAR(50),
                error_message TEXT,
                attempt_count INTEGER NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                completed_at DATETIME
            );
            """
        )


@pytest.mark.asyncio
async def test_migrations_adopt_pre_batch_database_and_create_backup(tmp_path):
    database_path = tmp_path / "legacy.db"
    create_legacy_database(database_path)

    await run_database_migrations(
        database_url=sqlite_url(database_path),
        alembic_ini_path=ALEMBIC_INI,
    )

    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(tts_jobs)")
        }
        revision = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0]
    assert {
        "batch_id",
        "batch_position",
        "source_file_name",
        "source_file_size",
        "cancel_requested",
        "started_at",
    }.issubset(columns)
    assert revision == HEAD_REVISION
    assert len(list(tmp_path.glob("legacy.db.pre-migration-*.bak"))) == 1


@pytest.mark.asyncio
async def test_migrations_adopt_current_unversioned_schema(tmp_path):
    database_path = tmp_path / "current.db"
    engine = create_database_engine(sqlite_url(database_path))
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()

    await run_database_migrations(
        database_url=sqlite_url(database_path),
        alembic_ini_path=ALEMBIC_INI,
    )

    with sqlite3.connect(database_path) as connection:
        revision = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0]
    assert revision == HEAD_REVISION


@pytest.mark.asyncio
async def test_migrations_reject_unrecognized_legacy_schema(tmp_path):
    database_path = tmp_path / "invalid.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE tts_jobs (id VARCHAR(36) PRIMARY KEY)")

    with pytest.raises(MigrationError, match="missing required columns"):
        await run_database_migrations(
            database_url=sqlite_url(database_path),
            alembic_ini_path=ALEMBIC_INI,
        )
