import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

AUTH = {"X-API-Key": "test-key"}


@pytest.mark.asyncio
async def test_health_returns_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "error")
    assert "timestamp" in data
    assert "db" in data


@pytest.mark.asyncio
async def test_api_v1_without_key_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/types")
    assert resp.status_code == 401
    data = resp.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_api_v1_with_wrong_key_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/types", headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_api_v1_with_correct_key_passes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/types", headers=AUTH)
    assert resp.status_code == 200
