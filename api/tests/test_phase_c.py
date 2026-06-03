"""
Phase C 集成测试：LLM 配置、文档上传、自动建模、Skills 技能系统
"""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

AUTH = {"X-API-Key": "test-key"}


async def _get_admin_token(client: AsyncClient) -> str:
    """Login as default admin and return access token."""
    resp = await client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return ""


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── LLM Config CRUD ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_llm_config():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/llm-configs", json={
            "provider": "openai",
            "api_key": "sk-test-key-12345",
            "endpoint": "https://api.openai.com/v1",
            "model": "gpt-4",
            "is_default": True,
            "is_active": True,
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "openai"
    assert data["model"] == "gpt-4"
    assert data["is_default"] is True
    # API key should be revealed on create
    assert data["api_key"] == "sk-test-key-12345"


@pytest.mark.asyncio
async def test_list_llm_configs():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        # Create one first
        await client.post("/api/v1/llm-configs", json={
            "provider": "deepseek",
            "api_key": "sk-deepseek-test",
            "model": "deepseek-chat",
        }, headers=_auth(token))
        resp = await client.get("/api/v1/llm-configs", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # API key should be masked in list
    for item in data:
        assert item["api_key"] == "****"


@pytest.mark.asyncio
async def test_get_llm_config():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/llm-configs", json={
            "provider": "tongyi",
            "api_key": "sk-tongyi-test",
            "model": "qwen-max",
        }, headers=_auth(token))
        config_id = create.json()["id"]
        resp = await client.get(f"/api/v1/llm-configs/{config_id}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == config_id
    assert data["api_key"] == "sk-tongyi-test"


@pytest.mark.asyncio
async def test_update_llm_config():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/llm-configs", json={
            "provider": "openai",
            "api_key": "sk-old-key",
            "model": "gpt-3.5",
        }, headers=_auth(token))
        config_id = create.json()["id"]
        resp = await client.put(f"/api/v1/llm-configs/{config_id}", json={
            "model": "gpt-4-turbo",
            "is_default": True,
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "gpt-4-turbo"
    assert data["is_default"] is True


@pytest.mark.asyncio
async def test_delete_llm_config():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/llm-configs", json={
            "provider": "openai",
            "api_key": "sk-to-delete",
            "model": "gpt-4",
        }, headers=_auth(token))
        config_id = create.json()["id"]
        resp = await client.delete(f"/api/v1/llm-configs/{config_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["message"] == f"LLM config {config_id} deleted"


@pytest.mark.asyncio
async def test_llm_config_requires_admin():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # No auth header
        resp = await client.get("/api/v1/llm-configs", headers=AUTH)
    # API Key passes auth middleware, but get_current_user requires JWT
    assert resp.status_code in (401, 403)


# ── Document Upload ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_txt_document():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/documents/upload", files={
            "file": ("test.txt", b"Hello, this is a test document for ontology modeling.", "text/plain"),
        }, data={"extract": "true"}, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["content_type"] == "text/plain"
    assert data["status"] == "EXTRACTED"
    assert "Hello" in data.get("extracted_text_preview", "")


@pytest.mark.asyncio
async def test_upload_invalid_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/documents/upload", files={
            "file": ("test.exe", b"binary content", "application/octet-stream"),
        }, headers=_auth(token))
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_documents():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        await client.post("/api/v1/documents/upload", files={
            "file": ("doc1.txt", b"Test content 1.", "text/plain"),
        }, data={"extract": "true"}, headers=_auth(token))
        resp = await client.get("/api/v1/documents", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_document_detail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/documents/upload", files={
            "file": ("detail.txt", b"Detail content for testing.", "text/plain"),
        }, data={"extract": "true"}, headers=_auth(token))
        doc_id = create.json()["id"]
        resp = await client.get(f"/api/v1/documents/{doc_id}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == doc_id
    assert "Detail content" in data.get("extracted_text", "")


@pytest.mark.asyncio
async def test_delete_document():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/documents/upload", files={
            "file": ("to_delete.txt", b"Delete me.", "text/plain"),
        }, data={"extract": "false"}, headers=_auth(token))
        doc_id = create.json()["id"]
        resp = await client.delete(f"/api/v1/documents/{doc_id}", headers=_auth(token))
    assert resp.status_code == 200


# ── Auto-Modeling ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_describe_table():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.get("/api/v1/auto-model/describe-table?table=ontology_types&schema=public", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["table"] == "public.ontology_types"
    assert len(data["columns"]) > 0
    # Check key columns exist
    col_names = {c["name"] for c in data["columns"]}
    assert "api_name" in col_names
    assert "type" in col_names


@pytest.mark.asyncio
async def test_list_schemas():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.get("/api/v1/auto-model/schemas", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "public" in data


@pytest.mark.asyncio
async def test_list_tables():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.get("/api/v1/auto-model/tables", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "ontology_types" in data
    assert "ontology_objects" in data


@pytest.mark.asyncio
async def test_detect_changes_new_table():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/auto-model/detect-changes", json={
            "table": "ontology_objects",
            "schema": "public",
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["table"] == "public.ontology_objects"


@pytest.mark.asyncio
async def test_detect_changes_missing_table():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/auto-model/detect-changes", json={
            "table": "nonexistent_table",
            "schema": "public",
        }, headers=_auth(token))
    assert resp.status_code == 404


# ── Skills System ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_presets():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.get("/api/v1/skills/presets", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    categories = {s["category"] for s in data}
    assert "data-quality" in categories


@pytest.mark.asyncio
async def test_create_skill():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/skills", json={
            "name": "Test Validator",
            "description": "A test validation skill",
            "skill_config": {"rules": [{"name": "check_fields", "condition": "x > 0"}]},
            "category": "data-quality",
            "status": "active",
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Validator"
    assert data["status"] == "active"
    assert data["category"] == "data-quality"


@pytest.mark.asyncio
async def test_list_skills():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        await client.post("/api/v1/skills", json={
            "name": "List Test Skill",
            "skill_config": {},
            "category": "analysis",
        }, headers=_auth(token))
        resp = await client.get("/api/v1/skills", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_toggle_skill():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/skills", json={
            "name": "Toggle Test",
            "skill_config": {},
            "status": "active",
        }, headers=_auth(token))
        skill_id = create.json()["id"]
        # Toggle to inactive
        resp = await client.put(f"/api/v1/skills/{skill_id}/toggle", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "inactive"


@pytest.mark.asyncio
async def test_clone_skill():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/skills", json={
            "name": "Original Skill",
            "skill_config": {"rules": [{"name": "r1"}]},
            "category": "automation",
        }, headers=_auth(token))
        skill_id = create.json()["id"]
        resp = await client.post(f"/api/v1/skills/{skill_id}/clone", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "Original Skill (Copy)" in data["name"]
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_export_skill():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/skills", json={
            "name": "Export Test",
            "skill_config": {"queries": [{"name": "q1"}]},
        }, headers=_auth(token))
        skill_id = create.json()["id"]
        resp = await client.get(f"/api/v1/skills/export/{skill_id}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["export_version"] == "1.0"
    assert data["skill"]["name"] == "Export Test"


@pytest.mark.asyncio
async def test_import_skill():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/skills/import", json={
            "skill": {
                "name": "Imported Skill",
                "description": "Imported from external source",
                "skill_config": {"rules": [], "workflows": [{"name": "wf1"}]},
                "category": "governance",
            },
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Imported Skill"
    assert data["category"] == "governance"


@pytest.mark.asyncio
async def test_update_skill():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/skills", json={
            "name": "Update Test",
            "skill_config": {},
        }, headers=_auth(token))
        skill_id = create.json()["id"]
        resp = await client.put(f"/api/v1/skills/{skill_id}", json={
            "name": "Updated Skill Name",
            "description": "Updated description",
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Skill Name"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_skill():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/api/v1/skills", json={
            "name": "Delete Me",
            "skill_config": {},
        }, headers=_auth(token))
        skill_id = create.json()["id"]
        resp = await client.delete(f"/api/v1/skills/{skill_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"]


# ── Sync (e2e) ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sync_ontology_types():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/auto-model/sync", json={
            "object_types": [
                {
                    "api_name": "auto_product",
                    "display_name": "Auto Product",
                    "description": "Auto-generated from sync",
                    "properties": [
                        {"name": "sku", "type": "string", "required": True, "pg_type": "VARCHAR"},
                        {"name": "price", "type": "number", "required": False, "pg_type": "NUMERIC"},
                    ],
                }
            ],
            "link_types": [],
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["created_count"] >= 1
    created_names = [c["api_name"] for c in data["created"]]
    assert "auto_product" in created_names


@pytest.mark.asyncio
async def test_sync_duplicate_skipped():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        # First sync
        await client.post("/api/v1/auto-model/sync", json={
            "object_types": [{"api_name": "sync_dup_test", "display_name": "Dup Test", "properties": []}],
            "link_types": [],
        }, headers=_auth(token))
        # Second sync - should skip
        resp = await client.post("/api/v1/auto-model/sync", json={
            "object_types": [{"api_name": "sync_dup_test", "display_name": "Dup Test 2", "properties": []}],
            "link_types": [],
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["errors"]) >= 1
    assert any("already exists" in e for e in data["errors"])


# ── Validation ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validate_ontology():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/auto-model/validate", json={
            "object_types": [
                {"api_name": "valid_type", "display_name": "Valid", "properties": []},
                {"api_name": "valid_type", "display_name": "Duplicate Name", "properties": []},
            ],
            "link_types": [
                {"api_name": "bad_link", "source_type": "missing_type", "target_type": "valid_type"},
            ],
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert len(data["errors"]) >= 1
    assert len(data["warnings"]) >= 1
