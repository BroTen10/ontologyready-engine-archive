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


# --- 高级图谱操作 ---


@pytest.mark.asyncio
async def test_graph_path():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for t in [
            {"api_name": "Customer", "type": "OBJECT", "display_name": "客户", "description": "test"},
            {"api_name": "belongs_to", "type": "LINK", "display_name": "属于", "description": "test"},
        ]:
            await client.post("/api/v1/types", json=t, headers=AUTH)
        c1 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "dataset_id": "default", "properties": {"name": "A"},
        }, headers=AUTH)
        c2 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "dataset_id": "default", "properties": {"name": "B"},
        }, headers=AUTH)
        await client.post("/api/v1/links", json={
            "link_type": "belongs_to", "source_id": c1.json()["id"],
            "target_id": c2.json()["id"], "dataset_id": "default",
        }, headers=AUTH)
        resp = await client.get(
            f"/api/v1/graph/path?source={c1.json()['id']}&target={c2.json()['id']}&dataset=default",
            headers=AUTH,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is True
    assert data["length"] == 1


@pytest.mark.asyncio
async def test_graph_path_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/graph/path?source=00000000-0000-0000-0000-000000000001&target=00000000-0000-0000-0000-000000000002",
            headers=AUTH,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is False


# --- 暂存工作流 ---


@pytest.mark.asyncio
async def test_staging_store_and_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Store a change
        resp = await client.post("/api/v1/staging/store", json={
            "user_id": "tester",
            "target_type": "object",
            "change_type": "create",
            "payload": {
                "object_type": "Customer",
                "properties": {"name": "暂存客户"},
            },
        }, headers=AUTH)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "staged"
    assert data["change_type"] == "create"

    # List staged changes
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_resp = await client.get("/api/v1/staging?status=staged", headers=AUTH)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


@pytest.mark.asyncio
async def test_staging_commit_create_object():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create the type first
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        # Stage a create
        store_resp = await client.post("/api/v1/staging/store", json={
            "user_id": "tester",
            "target_type": "object",
            "change_type": "create",
            "payload": {
                "object_type": "Customer",
                "properties": {"name": "通过暂存创建"},
            },
        }, headers=AUTH)
        change_id = store_resp.json()["id"]
        # Commit
        commit_resp = await client.post("/api/v1/staging/commit", json={
            "ids": [change_id],
        }, headers=AUTH)
    assert commit_resp.status_code == 200
    assert commit_resp.json()["committed"] == 1
    # Verify object was created
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        objects_resp = await client.get("/api/v1/objects", headers=AUTH)
    assert objects_resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_staging_discard():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        store_resp = await client.post("/api/v1/staging/store", json={
            "user_id": "tester",
            "target_type": "object",
            "change_type": "create",
            "payload": {"object_type": "Customer", "properties": {"name": "丢弃"}},
        }, headers=AUTH)
        change_id = store_resp.json()["id"]
        discard_resp = await client.delete("/api/v1/staging/discard", json={
            "ids": [change_id],
        }, headers=AUTH)
    assert discard_resp.status_code == 200
    # Verify status changed
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_resp = await client.get(f"/api/v1/staging?status=discarded", headers=AUTH)
    assert any(c["id"] == change_id for c in list_resp.json())


@pytest.mark.asyncio
async def test_staging_revert():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        # Create object first
        obj_resp = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "原始"},
        }, headers=AUTH)
        obj_id = obj_resp.json()["id"]
        # Stage update with previous_state
        store_resp = await client.post("/api/v1/staging/store", json={
            "user_id": "tester",
            "target_type": "object",
            "target_id": obj_id,
            "change_type": "update",
            "payload": {"properties": {"name": "已修改"}},
        }, headers=AUTH)
        change_id = store_resp.json()["id"]
        # Commit the update
        await client.post("/api/v1/staging/commit", json={"ids": [change_id]}, headers=AUTH)
        # Revert
        revert_resp = await client.post("/api/v1/staging/revert", json={
            "ids": [change_id],
        }, headers=AUTH)
    assert revert_resp.status_code == 200
    assert revert_resp.json()["reverted"] == 1


@pytest.mark.asyncio
async def test_graph_neighbors():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for t in [
            {"api_name": "Customer", "type": "OBJECT", "display_name": "客户", "description": "test"},
            {"api_name": "belongs_to", "type": "LINK", "display_name": "属于", "description": "test"},
        ]:
            await client.post("/api/v1/types", json=t, headers=AUTH)
        c1 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "dataset_id": "default", "properties": {"name": "A"},
        }, headers=AUTH)
        c2 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "dataset_id": "default", "properties": {"name": "B"},
        }, headers=AUTH)
        await client.post("/api/v1/links", json={
            "link_type": "belongs_to", "source_id": c1.json()["id"],
            "target_id": c2.json()["id"], "dataset_id": "default",
        }, headers=AUTH)
        resp = await client.get(
            f"/api/v1/graph/neighbors?node={c1.json()['id']}&dataset=default&direction=both",
            headers=AUTH,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1


@pytest.mark.asyncio
async def test_graph_traverse():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for t in [
            {"api_name": "Customer", "type": "OBJECT", "display_name": "客户", "description": "test"},
            {"api_name": "belongs_to", "type": "LINK", "display_name": "属于", "description": "test"},
        ]:
            await client.post("/api/v1/types", json=t, headers=AUTH)
        c1 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "dataset_id": "default", "properties": {"name": "A"},
        }, headers=AUTH)
        c2 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "dataset_id": "default", "properties": {"name": "B"},
        }, headers=AUTH)
        await client.post("/api/v1/links", json={
            "link_type": "belongs_to", "source_id": c1.json()["id"],
            "target_id": c2.json()["id"], "dataset_id": "default",
        }, headers=AUTH)
        resp = await client.get(
            f"/api/v1/graph/traverse?start={c1.json()['id']}&dataset=default&max_depth=3&strategy=bfs",
            headers=AUTH,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["nodeCount"] >= 1
    assert "nodes" in data
    assert "edges" in data


@pytest.mark.asyncio
async def test_graph_stats():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for t in [
            {"api_name": "Customer", "type": "OBJECT", "display_name": "客户", "description": "test"},
            {"api_name": "belongs_to", "type": "LINK", "display_name": "属于", "description": "test"},
        ]:
            await client.post("/api/v1/types", json=t, headers=AUTH)
        c1 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "dataset_id": "default", "properties": {"name": "A"},
        }, headers=AUTH)
        c2 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "dataset_id": "default", "properties": {"name": "B"},
        }, headers=AUTH)
        await client.post("/api/v1/links", json={
            "link_type": "belongs_to", "source_id": c1.json()["id"],
            "target_id": c2.json()["id"], "dataset_id": "default",
        }, headers=AUTH)
        resp = await client.get("/api/v1/graph/stats?dataset=default", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["nodeCount"] == 2
    assert data["edgeCount"] == 1
    assert "density" in data
    assert "averageDegree" in data
    assert "degreeDistribution" in data


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


# --- 批量操作 ---


@pytest.mark.asyncio
async def test_batch_create_objects():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        resp = await client.post("/api/v1/objects/batch/create", json={
            "items": [
                {"object_type": "Customer", "properties": {"name": "客户A"}},
                {"object_type": "Customer", "properties": {"name": "客户B"}},
                {"object_type": "Customer", "properties": {"name": "客户C"}},
            ],
        }, headers=AUTH)
    assert resp.status_code == 201
    data = resp.json()
    assert data["created"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["display_name"] == "客户A"


@pytest.mark.asyncio
async def test_batch_create_objects_invalid_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/objects/batch/create", json={
            "items": [
                {"object_type": "Customer", "properties": {"name": "valid"}},
                {"object_type": "NonExistent", "properties": {"name": "invalid"}},
            ],
        }, headers=AUTH)
    assert resp.status_code in (400, 422)
    # Transaction should roll back, so no partial data
    async with AsyncClient(transport=transport, base_url="http://test") as client2:
        list_resp = await client2.get("/api/v1/objects", headers=AUTH)
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_batch_create_objects_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/objects/batch/create", json={
            "items": [],
        }, headers=AUTH)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_batch_create_links():
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
        c3 = await client.post("/api/v1/objects", json={
            "object_type": "Customer", "properties": {"name": "C"},
        }, headers=AUTH)
        resp = await client.post("/api/v1/links/batch/create", json={
            "items": [
                {"link_type": "belongs_to", "source_id": c1.json()["id"], "target_id": c2.json()["id"]},
                {"link_type": "belongs_to", "source_id": c2.json()["id"], "target_id": c3.json()["id"]},
            ],
        }, headers=AUTH)
    assert resp.status_code == 201
    data = resp.json()
    assert data["created"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_batch_create_links_rollback():
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
        # Second item references non-existent object
        resp = await client.post("/api/v1/links/batch/create", json={
            "items": [
                {"link_type": "belongs_to", "source_id": c1.json()["id"], "target_id": c1.json()["id"]},
                {"link_type": "belongs_to", "source_id": c1.json()["id"], "target_id": "00000000-0000-0000-0000-000000000000"},
            ],
        }, headers=AUTH)
    assert resp.status_code in (400, 422)
    # Verify no links were created (full rollback)
    async with AsyncClient(transport=transport, base_url="http://test") as client2:
        list_resp = await client2.get("/api/v1/links", headers=AUTH)
    assert len(list_resp.json()) == 0


# ── Phase B: 版本管理 ──


@pytest.mark.asyncio
async def test_version_snapshot_and_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        resp = await client.post("/api/v1/versions/snapshot?comment=Phase B 测试快照", headers=AUTH)
    assert resp.status_code == 201
    data = resp.json()
    assert data["version_number"] >= 1
    assert data["type_count"] >= 1

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_resp = await client.get("/api/v1/versions", headers=AUTH)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


@pytest.mark.asyncio
async def test_version_compare():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        v1 = await client.post("/api/v1/versions/snapshot?comment=v1", headers=AUTH)
        v1_id = v1.json()["id"]
        # Add another type
        await client.post("/api/v1/types", json={
            "api_name": "belongs_to", "type": "LINK",
            "display_name": "属于", "description": "test",
        }, headers=AUTH)
        v2 = await client.post("/api/v1/versions/snapshot?comment=v2", headers=AUTH)
        v2_id = v2.json()["id"]
        resp = await client.post(f"/api/v1/versions/compare?base={v1_id}&target={v2_id}", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "added_types" in data
    assert "belongs_to" in data["added_types"]


@pytest.mark.asyncio
async def test_version_detail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/types", json={
            "api_name": "Customer", "type": "OBJECT",
            "display_name": "客户", "description": "test",
        }, headers=AUTH)
        v1 = await client.post("/api/v1/versions/snapshot?comment=detail test", headers=AUTH)
        v1_id = v1.json()["id"]
        resp = await client.get(f"/api/v1/versions/{v1_id}", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "snapshot" in data
    assert len(data["snapshot"]["types"]) >= 1


# ── Phase B: ACR 访问控制 ──


@pytest.mark.asyncio
async def test_acr_create_and_list_rules():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/acr/rules", json={
            "rule_name": "test_deny_delete",
            "description": "禁止删除操作",
            "conditions": {"type": "action", "values": ["delete"]},
            "permissions": {"deny": ["delete"]},
            "priority": 10,
        }, headers=AUTH)
    assert resp.status_code == 201
    data = resp.json()
    assert data["rule_name"] == "test_deny_delete"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_resp = await client.get("/api/v1/acr/rules", headers=AUTH)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


@pytest.mark.asyncio
async def test_acr_create_group_and_binding():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create rule first
        rule = await client.post("/api/v1/acr/rules", json={
            "rule_name": "allow_read_all",
            "description": "允许所有读取",
            "conditions": {"type": "always"},
            "permissions": {"actions": ["read"]},
            "priority": 5,
        }, headers=AUTH)
        rule_id = rule.json()["id"]
        # Create group with rule
        group = await client.post("/api/v1/acr/groups", json={
            "group_name": "read_only_users",
            "description": "只读用户组",
            "rules": [rule_id],
        }, headers=AUTH)
        assert group.status_code == 201
        group_id = group.json()["id"]
        # Create binding
        binding = await client.post("/api/v1/acr/bindings", json={
            "user_id": "test_user",
            "group_id": group_id,
            "target_type": "*",
            "target_id": "*",
        }, headers=AUTH)
    assert binding.status_code == 201
    assert binding.json()["user_id"] == "test_user"


@pytest.mark.asyncio
async def test_acr_evaluate():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create deny-delete rule
        rule = await client.post("/api/v1/acr/rules", json={
            "rule_name": "deny_delete_eval",
            "description": "Test deny delete",
            "conditions": {"type": "action", "values": ["delete"]},
            "permissions": {"deny": ["delete"]},
            "priority": 10,
        }, headers=AUTH)
        rule_id = rule.json()["id"]
        # Create group and binding
        group = await client.post("/api/v1/acr/groups", json={
            "group_name": "eval_group",
            "rules": [rule_id],
        }, headers=AUTH)
        group_id = group.json()["id"]
        await client.post("/api/v1/acr/bindings", json={
            "user_id": "eval_user",
            "group_id": group_id,
        }, headers=AUTH)
        # Evaluate: delete should be denied
        resp = await client.post("/api/v1/acr/evaluate", json={
            "user_id": "eval_user",
            "action": "delete",
            "target_type": "object",
        }, headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is False
    assert "Denied" in data["reason"]

    # Evaluate: read should be allowed (no rule matches)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp2 = await client.post("/api/v1/acr/evaluate", json={
            "user_id": "eval_user",
            "action": "read",
            "target_type": "object",
        }, headers=AUTH)
    assert resp2.status_code == 200
    assert resp2.json()["allowed"] is True


# ── Phase B: 端到端工作流测试 ──


@pytest.mark.asyncio
async def test_phase_b_e2e_workflow():
    """端到端测试：创建类型(带增强属性) → 批量创建对象 → 创建链接 → 路径查找 → 暂存变更 → 提交 → 快照"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create type with enhanced properties
        await client.post("/api/v1/types", json={
            "api_name": "Customer",
            "type": "OBJECT",
            "display_name": "客户",
            "description": "测试客户",
            "properties": [
                {"name": "name", "type": "string", "required": True, "pg_type": "VARCHAR(200)", "index": True},
                {"name": "credit_limit", "type": "number", "pg_type": "NUMERIC", "constraints": {"min": 0}},
            ],
        }, headers=AUTH)
        await client.post("/api/v1/types", json={
            "api_name": "belongs_to", "type": "LINK",
            "display_name": "属于", "description": "test",
        }, headers=AUTH)

        # 2. Batch create objects
        batch = await client.post("/api/v1/objects/batch/create", json={
            "items": [
                {"object_type": "Customer", "dataset_id": "default", "properties": {"name": "客户A", "credit_limit": 10000}},
                {"object_type": "Customer", "dataset_id": "default", "properties": {"name": "客户B", "credit_limit": 50000}},
            ],
        }, headers=AUTH)
        assert batch.status_code == 201
        obj_ids = [item["id"] for item in batch.json()["items"]]

        # 3. Create link
        link = await client.post("/api/v1/links", json={
            "link_type": "belongs_to",
            "source_id": obj_ids[0],
            "target_id": obj_ids[1],
            "dataset_id": "default",
        }, headers=AUTH)
        assert link.status_code == 201

        # 4. Find path
        path = await client.get(
            f"/api/v1/graph/path?source={obj_ids[0]}&target={obj_ids[1]}&dataset=default",
            headers=AUTH,
        )
        assert path.status_code == 200
        assert path.json()["found"] is True

        # 5. Stage a change
        staged = await client.post("/api/v1/staging/store", json={
            "user_id": "e2e_tester",
            "target_type": "object",
            "change_type": "create",
            "payload": {
                "object_type": "Customer",
                "dataset_id": "default",
                "properties": {"name": "客户C", "credit_limit": 30000},
            },
        }, headers=AUTH)
        assert staged.status_code == 201
        staged_id = staged.json()["id"]

        # 6. Commit staged change
        committed = await client.post("/api/v1/staging/commit", json={"ids": [staged_id]}, headers=AUTH)
        assert committed.status_code == 200
        assert committed.json()["committed"] == 1

        # 7. Create version snapshot
        snapshot = await client.post("/api/v1/versions/snapshot?comment=E2E workflow snapshot", headers=AUTH)
        assert snapshot.status_code == 201
        assert snapshot.json()["type_count"] >= 2

        # 8. Verify final state
        stats = await client.get("/api/v1/graph/stats?dataset=default", headers=AUTH)
        assert stats.status_code == 200
        assert stats.json()["nodeCount"] >= 3  # 3 customers created
