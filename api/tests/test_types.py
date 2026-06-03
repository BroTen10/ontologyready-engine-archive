import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

AUTH = {"X-API-Key": "test-key"}


@pytest.mark.asyncio
async def test_create_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/types", json={
            "api_name": "Customer",
            "type": "OBJECT",
            "display_name": "客户",
            "description": "企业客户",
            "config": {"color": "#52c41a", "icon": "UserOutlined"},
            "maturity": "ACTIVE",
        }, headers=AUTH)
    assert resp.status_code == 201
    data = resp.json()
    assert data["api_name"] == "Customer"
    assert data["type"] == "OBJECT"
    assert data["maturity"] == "ACTIVE"


@pytest.mark.asyncio
async def test_create_duplicate_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        resp = await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户2", "description": "test",
        }, headers=AUTH)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_list_types():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        await client.post("/api/v1/types", json={
            "api_name": "belongs_to", "type": "LINK",
            "display_name": "属于", "description": "relation",
        }, headers=AUTH)
        resp = await client.get("/api/v1/types", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_types_filter():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        await client.post("/api/v1/types", json={
            "api_name": "belongs_to", "type": "LINK",
            "display_name": "属于", "description": "test",
        }, headers=AUTH)
        resp = await client.get("/api/v1/types?type=LINK", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["api_name"] == "belongs_to"


@pytest.mark.asyncio
async def test_get_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        resp = await client.get("/api/v1/types/Customer", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["api_name"] == "Customer"


@pytest.mark.asyncio
async def test_get_nonexistent_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/types/NotFound", headers=AUTH)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_update_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        resp = await client.put("/api/v1/types/Customer", json={
            "display_name": "企业客户",
            "description": "updated",
        }, headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "企业客户"
    assert data["description"] == "updated"


@pytest.mark.asyncio
async def test_delete_type_with_references():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        from app.database import get_pool
        pool = await get_pool()
        await pool.execute(
            "INSERT INTO ontology_objects (object_type, properties) VALUES ($1, $2)",
            "Customer", '{"name": "test"}',
        )
        resp = await client.delete("/api/v1/types/Customer", headers=AUTH)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_type_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        resp = await client.delete("/api/v1/types/Customer", headers=AUTH)
    assert resp.status_code == 204
