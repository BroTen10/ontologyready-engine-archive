"""
Phase D 集成测试：后台任务、文档引擎、RAG 评测、OSS 对象存储
"""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

AUTH = {"X-API-Key": "test-key"}


async def _get_admin_token(client: AsyncClient) -> str:
    resp = await client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return ""


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Background Tasks ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_task():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/tasks/submit", json={
            "task_type": "data_export",
            "params": {"format": "json", "dataset": "default"},
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_type"] == "data_export"
    assert data["status"] in ("PENDING", "RUNNING", "COMPLETED")
    assert "id" in data


@pytest.mark.asyncio
async def test_list_tasks():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        await client.post("/api/v1/tasks/submit", json={
            "task_type": "bulk_import",
            "params": {"count": 100},
        }, headers=_auth(token))
        resp = await client.get("/api/v1/tasks", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_task():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/tasks/submit", json={
            "task_type": "graph_reindex",
            "params": {},
        }, headers=_auth(token))
        task_id = create.json()["id"]
        resp = await client.get(f"/api/v1/tasks/{task_id}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == task_id
    assert data["task_type"] == "graph_reindex"


@pytest.mark.asyncio
async def test_cancel_task():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/tasks/submit", json={
            "task_type": "data_export",
            "params": {},
        }, headers=_auth(token))
        task_id = create.json()["id"]
        resp = await client.post(f"/api/v1/tasks/{task_id}/cancel", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELED"


@pytest.mark.asyncio
async def test_get_task_logs():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/tasks/submit", json={
            "task_type": "data_export",
            "params": {},
        }, headers=_auth(token))
        task_id = create.json()["id"]
        resp = await client.get(f"/api/v1/tasks/{task_id}/logs", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["task_id"] == task_id
    assert "status" in resp.json()


# ── Document Engine ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_doc_engine_default():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.get("/admin/doc-engine", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "engine_type" in data


@pytest.mark.asyncio
async def test_configure_doc_engine():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.put("/admin/doc-engine", json={
            "engine_type": "pgvector",
            "config": {"similarity_threshold": 0.7},
            "is_active": True,
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["engine_type"] == "pgvector"


@pytest.mark.asyncio
async def test_doc_engine_test_connection():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        await client.put("/admin/doc-engine", json={
            "engine_type": "pgvector",
            "config": {},
            "is_active": True,
        }, headers=_auth(token))
        resp = await client.post("/admin/doc-engine/test-connection", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["engine"] == "pgvector"


# ── OSS Object Storage ────────────────────────────────────────

@pytest.mark.asyncio
async def test_configure_oss():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.put("/admin/oss", json={
            "provider": "s3",
            "endpoint": "https://s3.amazonaws.com",
            "access_key": "AKIATEST123",
            "secret_key": "testsecretkey",
            "bucket": "ontologyready-test",
            "region": "us-east-1",
            "is_active": True,
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "s3"
    assert data["access_key"] == "****"


@pytest.mark.asyncio
async def test_get_oss_config():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        await client.put("/admin/oss", json={
            "endpoint": "https://s3.amazonaws.com",
            "access_key": "AKIA123",
            "secret_key": "secret",
            "bucket": "test-bucket",
        }, headers=_auth(token))
        resp = await client.get("/admin/oss", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_key"] == "****"


# ── RAG Evaluation ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_eval_dataset():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/eval/datasets", json={
            "name": "Test QA Dataset",
            "description": "A test dataset for RAG evaluation",
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test QA Dataset"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_eval_datasets():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        await client.post("/api/v1/eval/datasets", json={
            "name": "List Test Dataset",
        }, headers=_auth(token))
        resp = await client.get("/api/v1/eval/datasets", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_create_eval_run():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        ds = await client.post("/api/v1/eval/datasets", json={
            "name": "Run Test Dataset",
        }, headers=_auth(token))
        dataset_id = ds.json()["id"]
        resp = await client.post("/api/v1/eval/runs", json={
            "dataset_id": dataset_id,
            "config": {"model": "gpt-4", "top_k": 5},
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert "metrics" in data
    assert "faithfulness" in data["metrics"]


@pytest.mark.asyncio
async def test_list_eval_runs():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.get("/api/v1/eval/runs", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_compare_runs():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        ds = await client.post("/api/v1/eval/datasets", json={"name": "Compare Dataset"}, headers=_auth(token))
        ds_id = ds.json()["id"]
        r1 = await client.post("/api/v1/eval/runs", json={"dataset_id": ds_id}, headers=_auth(token))
        r2 = await client.post("/api/v1/eval/runs", json={"dataset_id": ds_id}, headers=_auth(token))
        run_ids = f"{r1.json()['id']},{r2.json()['id']}"
        resp = await client.get(f"/api/v1/eval/comparisons?run_ids={run_ids}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["runs"]) == 2
    assert "comparison" in data


@pytest.mark.asyncio
async def test_update_eval_dataset():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        ds = await client.post("/api/v1/eval/datasets", json={"name": "Old Name"}, headers=_auth(token))
        ds_id = ds.json()["id"]
        resp = await client.put(f"/api/v1/eval/datasets/{ds_id}", json={
            "name": "Updated Name",
            "description": "Updated description",
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_eval_dataset():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        ds = await client.post("/api/v1/eval/datasets", json={"name": "To Delete"}, headers=_auth(token))
        ds_id = ds.json()["id"]
        resp = await client.delete(f"/api/v1/eval/datasets/{ds_id}", headers=_auth(token))
    assert resp.status_code == 200
