import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.middleware.local_auth import validate_runtime_security


@pytest.mark.asyncio
async def test_production_auth_allows_live_and_protects_business_routes(
    monkeypatch,
):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "melody_api_token", "secret-token", raising=False)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        live = await client.get("/api/v1/health/live")
        missing = await client.get("/api/v1/voices")
        wrong = await client.get(
            "/api/v1/voices",
            headers={"X-Melody-Token": "wrong"},
        )
        allowed = await client.get(
            "/api/v1/voices",
            headers={"X-Melody-Token": "secret-token"},
        )

    assert live.status_code == 200
    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert allowed.status_code == 200


def test_production_startup_rejects_missing_token(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "melody_api_token", None, raising=False)

    with pytest.raises(RuntimeError, match="MELODY_API_TOKEN"):
        validate_runtime_security()


def test_development_allows_missing_token(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "melody_api_token", None, raising=False)

    validate_runtime_security()
