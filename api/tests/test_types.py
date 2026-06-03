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


# ── Enhanced PropertyDef tests ──────────────────────────────


@pytest.mark.asyncio
async def test_create_type_with_enhanced_properties():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/types", json={
            "api_name": "Product",
            "type": "OBJECT",
            "display_name": "产品",
            "description": "产品实体",
            "properties": [
                {
                    "name": "sku",
                    "type": "string",
                    "required": True,
                    "description": "SKU编号",
                    "pg_type": "VARCHAR(100)",
                    "constraints": {"pattern": "^[A-Z0-9-]+$", "minLength": 3, "maxLength": 100},
                    "index": True,
                },
                {
                    "name": "price",
                    "type": "number",
                    "required": True,
                    "description": "价格",
                    "pg_type": "NUMERIC",
                    "constraints": {"min": 0},
                },
                {
                    "name": "tags",
                    "type": "string",
                    "required": False,
                    "pg_type": "TEXT[]",
                    "index": False,
                },
            ],
        }, headers=AUTH)
    assert resp.status_code == 201
    data = resp.json()
    props = data.get("properties", [])
    assert len(props) == 3
    sku = next(p for p in props if p["name"] == "sku")
    assert sku["pg_type"] == "VARCHAR(100)"
    assert sku["constraints"]["pattern"] == "^[A-Z0-9-]+$"
    assert sku["index"] is True
    price = next(p for p in props if p["name"] == "price")
    assert price["pg_type"] == "NUMERIC"
    assert price["constraints"]["min"] == 0
    tags = next(p for p in props if p["name"] == "tags")
    assert tags["pg_type"] == "TEXT[]"
    assert tags["index"] is False


@pytest.mark.asyncio
async def test_invalid_pg_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/types", json={
            "api_name": "BadType",
            "type": "OBJECT",
            "display_name": "坏类型",
            "description": "test",
            "properties": [
                {"name": "field1", "type": "string", "pg_type": "INVALID_TYPE"},
            ],
        }, headers=AUTH)
    assert resp.status_code == 400
    assert "pg_type" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_invalid_constraint_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/types", json={
            "api_name": "BadConstraint",
            "type": "OBJECT",
            "display_name": "坏约束",
            "description": "test",
            "properties": [
                {"name": "field1", "type": "string", "constraints": {"badkey": "value"}},
            ],
        }, headers=AUTH)
    assert resp.status_code == 400
    assert "约束" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_invalid_pattern_constraint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/types", json={
            "api_name": "BadPattern",
            "type": "OBJECT",
            "display_name": "坏正则",
            "description": "test",
            "properties": [
                {"name": "field1", "type": "string", "constraints": {"pattern": "[invalid"}},
            ],
        }, headers=AUTH)
    assert resp.status_code == 400
    assert "pattern" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_constraint_type_mismatch():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/types", json={
            "api_name": "TypeMismatch",
            "type": "OBJECT",
            "display_name": "类型不匹配",
            "description": "test",
            "properties": [
                {"name": "field1", "type": "number", "constraints": {"min": "not_a_number"}},
            ],
        }, headers=AUTH)
    assert resp.status_code == 400
    assert "min" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_duplicate_property_name():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/types", json={
            "api_name": "DupProps",
            "type": "OBJECT",
            "display_name": "重复属性",
            "description": "test",
            "properties": [
                {"name": "field1", "type": "string"},
                {"name": "field1", "type": "number"},
            ],
        }, headers=AUTH)
    assert resp.status_code == 400
    assert "重复" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_update_type_properties_patch():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "PatchTest",
            "type": "OBJECT",
            "display_name": "补丁测试",
            "description": "test",
            "properties": [
                {"name": "old_field", "type": "string", "pg_type": "TEXT"},
            ],
        }, headers=AUTH)
        resp = await client.patch("/api/v1/types/PatchTest/properties", json=[
            {"name": "new_field", "type": "number", "pg_type": "INTEGER", "index": True},
        ], headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    props = data.get("properties", [])
    assert len(props) == 1
    assert props[0]["name"] == "new_field"
    assert props[0]["pg_type"] == "INTEGER"
    assert props[0]["index"] is True
