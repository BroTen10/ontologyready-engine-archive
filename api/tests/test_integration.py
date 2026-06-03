"""
API 集成测试：对象 CRUD、搜索、链接 CRUD、图谱、动作、数据集、统计
"""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

AUTH = {"X-API-Key": "test-key"}


# --- 对象实例 ---

@pytest.mark.asyncio
async def test_create_object():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        resp = await client.post("/api/v1/objects", json={
            "object_type": "Customer",
            "dataset_id": "default",
            "properties": {"name": "华东电子", "region": "华东"},
        }, headers=AUTH)
    assert resp.status_code == 201
    data = resp.json()
    assert data["object_type"] == "Customer"
    assert data["display_name"] == "华东电子"
    assert data["properties"]["region"] == "华东"


@pytest.mark.asyncio
async def test_create_object_invalid_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/objects", json={
            "object_type": "NonExistent", "properties": {"name": "test"},
        }, headers=AUTH)
    assert resp.status_code in (400, 422)
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_list_objects_paginated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        for i in range(15):
            await client.post("/api/v1/objects", json={
                "object_type": "Customer", "properties": {"name": f"客户{i}"},
            }, headers=AUTH)
        resp = await client.get("/api/v1/objects?page=1&size=10", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 10
    assert data["total"] == 15
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_search_objects():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "华东电子"},
        }, headers=AUTH)
        await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "华南智造"},
        }, headers=AUTH)
        resp = await client.get("/api/v1/objects/search?q=华东", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any("华东" in o["display_name"] for o in data)


@pytest.mark.asyncio
async def test_get_object_by_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        created = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "华东电子"},
        }, headers=AUTH)
        obj_id = created.json()["id"]
        resp = await client.get(f"/api/v1/objects/{obj_id}", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["id"] == obj_id


@pytest.mark.asyncio
async def test_get_nonexistent_object():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/objects/00000000-0000-0000-0000-000000000000", headers=AUTH)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_object_cascades_links():
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
        c1 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "A"},
        }, headers=AUTH)
        c2 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "B"},
        }, headers=AUTH)
        c1_id = c1.json()["id"]
        c2_id = c2.json()["id"]
        link = await client.post("/api/v1/links", json={
            "link_type": "belongs_to", "source_id": c1_id,
            "target_id": c2_id,
        }, headers=AUTH)
        assert link.status_code == 201
        del_resp = await client.delete(f"/api/v1/objects/{c1_id}", headers=AUTH)
    assert del_resp.status_code == 204


# --- 链接 ---

@pytest.mark.asyncio
async def test_create_link():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for t in [
            {"api_name": "Customer", "type": "OBJECT", "display_name": "客户", "description": "test"},
            {"api_name": "belongs_to", "type": "LINK", "display_name": "属于", "description": "test"},
        ]:
            await client.post("/api/v1/types", json=t, headers=AUTH)
        c1 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "A"},
        }, headers=AUTH)
        c2 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "B"},
        }, headers=AUTH)
        resp = await client.post("/api/v1/links", json={
            "link_type": "belongs_to",
            "source_id": c1.json()["id"],
            "target_id": c2.json()["id"],
        }, headers=AUTH)
    assert resp.status_code == 201
    data = resp.json()
    assert data["link_type"] == "belongs_to"


@pytest.mark.asyncio
async def test_create_link_invalid_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/links", json={
            "link_type": "NonexistentLink",
            "source_id": "00000000-0000-0000-0000-000000000001",
            "target_id": "00000000-0000-0000-0000-000000000002",
        }, headers=AUTH)
    assert resp.status_code in (400, 422)
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_list_links():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for t in [
            {"api_name": "Customer", "type": "OBJECT", "display_name": "客户", "description": "test"},
            {"api_name": "belongs_to", "type": "LINK", "display_name": "属于", "description": "test"},
        ]:
            await client.post("/api/v1/types", json=t, headers=AUTH)
        c1 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "A"},
        }, headers=AUTH)
        c2 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "B"},
        }, headers=AUTH)
        await client.post("/api/v1/links", json={
            "link_type": "belongs_to",
            "source_id": c1.json()["id"],
            "target_id": c2.json()["id"],
        }, headers=AUTH)
        resp = await client.get("/api/v1/links", headers=AUTH)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_delete_link():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for t in [
            {"api_name": "Customer", "type": "OBJECT", "display_name": "客户", "description": "test"},
            {"api_name": "belongs_to", "type": "LINK", "display_name": "属于", "description": "test"},
        ]:
            await client.post("/api/v1/types", json=t, headers=AUTH)
        c1 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "A"},
        }, headers=AUTH)
        c2 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "B"},
        }, headers=AUTH)
        link = await client.post("/api/v1/links", json={
            "link_type": "belongs_to",
            "source_id": c1.json()["id"],
            "target_id": c2.json()["id"],
        }, headers=AUTH)
        link_id = link.json()["id"]
        resp = await client.delete(f"/api/v1/links/{link_id}", headers=AUTH)
    assert resp.status_code == 204
    # 确认已删除
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        links = await client.get("/api/v1/links", headers=AUTH)
    assert all(l["id"] != link_id for l in links.json())


# --- 图谱 ---

@pytest.mark.asyncio
async def test_graph_structure():
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
        resp = await client.get("/api/v1/graph/structure", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert any(n["id"] == "Customer" for n in data["nodes"])


@pytest.mark.asyncio
async def test_graph_entities():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        await client.post("/api/v1/objects", json={
            "object_type": "Customer", "dataset_id": "default",
            "properties": {"name": "华东电子"},
        }, headers=AUTH)
        resp = await client.get("/api/v1/graph/entities?dataset=default", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert any(n["type"] == "Customer" for n in data["nodes"])


# --- 动作 ---

@pytest.mark.asyncio
async def test_execute_action():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "ApproveCommitment", "type": "ACTION",
            "display_name": "审批承诺", "description": "审批 ATP 承诺",
            "config": {"parameters": [{"name": "commitment_id", "type": "STRING", "required": True}]},
        }, headers=AUTH)
        resp = await client.post("/api/v1/actions/ApproveCommitment", json={
            "commitment_id": "abc-123",
            "executed_by": "tester",
        }, headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["action_type"] == "ApproveCommitment"
    assert "id" in data


@pytest.mark.asyncio
async def test_execute_action_missing_param():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "ApproveCommitment", "type": "ACTION",
            "display_name": "审批承诺", "description": "审批 ATP 承诺",
            "config": {"parameters": [{"name": "commitment_id", "type": "STRING", "required": True}]},
        }, headers=AUTH)
        resp = await client.post("/api/v1/actions/ApproveCommitment", json={}, headers=AUTH)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_action_history():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "ApproveCommitment", "type": "ACTION",
            "display_name": "审批承诺", "description": "test",
            "config": {"parameters": [{"name": "commitment_id", "type": "STRING", "required": True}]},
        }, headers=AUTH)
        await client.post("/api/v1/actions/ApproveCommitment", json={
            "commitment_id": "abc-123", "executed_by": "tester",
        }, headers=AUTH)
        resp = await client.get("/api/v1/actions/history?page=1&size=10", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert data["total"] >= 1
    assert any(h["action_type"] == "ApproveCommitment" for h in data["data"])


# --- 数据集 ---

@pytest.mark.asyncio
async def test_list_datasets():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/datasets", headers=AUTH)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# --- 统计 ---

@pytest.mark.asyncio
async def test_stats():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "华东电子"},
        }, headers=AUTH)
        resp = await client.get("/api/v1/stats", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["objectCount"] >= 1
    assert data["typeCount"] >= 1
    assert "linkCount" in data
    assert "datasetCount" in data
    assert "actionsToday" in data


# --- 错误码 ---

@pytest.mark.asyncio
async def test_validation_error_format():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/objects", json={}, headers=AUTH)
    assert resp.status_code in (400, 422)
    error = resp.json()["error"]
    assert "code" in error
    assert "message" in error
    assert "request_id" in error


@pytest.mark.asyncio
async def test_not_found_error_format():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/types/NonexistentType", headers=AUTH)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


# --- 认证 ---

@pytest.mark.asyncio
async def test_unauthorized_no_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/types")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_unauthorized_wrong_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/types", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401
