import pytest
from unittest.mock import AsyncMock
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
async def test_migration_failure_prevents_queue_start(monkeypatch):
    migration = AsyncMock(side_effect=RuntimeError("migration failed"))
    queue_start = AsyncMock()
    monkeypatch.setattr("app.main.run_database_migrations", migration)
    monkeypatch.setattr("app.main.queue_manager.start", queue_start)

    with pytest.raises(RuntimeError, match="migration failed"):
        async with app.router.lifespan_context(app):
            pass

    queue_start.assert_not_awaited()
