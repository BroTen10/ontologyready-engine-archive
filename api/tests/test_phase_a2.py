"""
Phase A2 集成测试：多数据集、用户/角色/组管理、API Key/PAT 认证
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


# ── Datasets ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_dataset():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/datasets", json={
            "id": "production",
            "name": "Production Dataset",
            "description": "Real production data",
            "is_default": False,
        }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == "production"
    assert data["name"] == "Production Dataset"


@pytest.mark.asyncio
async def test_list_datasets():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        await client.post("/api/v1/datasets", json={
            "id": "test_ds", "name": "Test DS",
        }, headers=_auth(token))
        resp = await client.get("/api/v1/datasets", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_update_dataset():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        await client.post("/api/v1/datasets", json={
            "id": "ds_update", "name": "Old Name",
        }, headers=_auth(token))
        resp = await client.put("/api/v1/datasets/ds_update", json={
            "name": "Updated Dataset", "description": "Updated desc",
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Dataset"


@pytest.mark.asyncio
async def test_backfill_datasets():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/api/v1/datasets/backfill", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "backfilled" in data
    assert "total_discovered" in data


# ── Users CRUD ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_list_users():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.get("/admin/users", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(u["username"] == "admin" for u in data)


@pytest.mark.asyncio
async def test_admin_create_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/admin/users", json={
            "username": "testuser",
            "password": "testpass123",
            "email": "test@example.com",
            "full_name": "Test User",
        }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_admin_update_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/admin/users", json={
            "username": "updateuser", "password": "pass123",
        }, headers=_auth(token))
        user_id = create.json()["id"]
        resp = await client.put(f"/admin/users/{user_id}", json={
            "email": "updated@example.com", "is_active": False,
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "updated@example.com"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_admin_delete_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/admin/users", json={
            "username": "deleteuser", "password": "pass123",
        }, headers=_auth(token))
        user_id = create.json()["id"]
        resp = await client.delete(f"/admin/users/{user_id}", headers=_auth(token))
    assert resp.status_code == 200


# ── Roles ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_roles():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.get("/admin/roles", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    role_names = {r["name"] for r in data}
    assert "admin" in role_names


@pytest.mark.asyncio
async def test_create_role():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/admin/roles", json={
            "name": "data_manager",
            "description": "Can manage data",
            "permissions": ["objects:read", "objects:write", "links:read", "links:write"],
        }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "data_manager"
    assert len(data["permissions"]) == 4


@pytest.mark.asyncio
async def test_update_role():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/admin/roles", json={
            "name": "temporary_role", "permissions": [],
        }, headers=_auth(token))
        role_id = create.json()["id"]
        resp = await client.put(f"/admin/roles/{role_id}", json={
            "description": "Updated role description",
            "permissions": ["types:read"],
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Updated role description"


@pytest.mark.asyncio
async def test_assign_role_to_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        user = await client.post("/admin/users", json={
            "username": "roleuser", "password": "pass123",
        }, headers=_auth(token))
        user_id = user.json()["id"]
        role = await client.post("/admin/roles", json={
            "name": "assign_test_role", "permissions": ["objects:read"],
        }, headers=_auth(token))
        role_id = role.json()["id"]
        resp = await client.post(f"/admin/users/{user_id}/roles", json={
            "role_id": role_id,
        }, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "assigned"


@pytest.mark.asyncio
async def test_get_user_roles():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        user = await client.post("/admin/users", json={
            "username": "rolesuser2", "password": "pass123",
        }, headers=_auth(token))
        user_id = user.json()["id"]
        role = await client.post("/admin/roles", json={
            "name": "role_for_user2", "permissions": ["links:read"],
        }, headers=_auth(token))
        role_id = role.json()["id"]
        await client.post(f"/admin/users/{user_id}/roles", json={"role_id": role_id}, headers=_auth(token))
        resp = await client.get(f"/admin/users/{user_id}/roles", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


# ── Groups ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_group():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/admin/groups", json={
            "name": "engineering",
            "description": "Engineering team",
        }, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "engineering"


@pytest.mark.asyncio
async def test_list_groups():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        await client.post("/admin/groups", json={"name": "list_group"}, headers=_auth(token))
        resp = await client.get("/admin/groups", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_add_group_member():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        user = await client.post("/admin/users", json={
            "username": "groupmember", "password": "pass123",
        }, headers=_auth(token))
        user_id = user.json()["id"]
        group = await client.post("/admin/groups", json={"name": "test_group_mb"}, headers=_auth(token))
        group_id = group.json()["id"]
        resp = await client.post(f"/admin/groups/{group_id}/members", json={
            "user_id": user_id,
        }, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "added"


@pytest.mark.asyncio
async def test_list_group_members():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        user = await client.post("/admin/users", json={
            "username": "gmember2", "password": "pass123",
        }, headers=_auth(token))
        user_id = user.json()["id"]
        group = await client.post("/admin/groups", json={"name": "mb_list_group"}, headers=_auth(token))
        group_id = group.json()["id"]
        await client.post(f"/admin/groups/{group_id}/members", json={"user_id": user_id}, headers=_auth(token))
        resp = await client.get(f"/admin/groups/{group_id}/members", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["username"] == "gmember2"


# ── API Keys ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_api_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/admin/api-keys", json={
            "name": "Test API Key",
            "permissions": ["api"],
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["key_prefix"].startswith("ork_")
    assert "api_key" in data
    assert data["api_key"].startswith("ork_")


@pytest.mark.asyncio
async def test_list_api_keys():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        await client.post("/admin/api-keys", json={"name": "List Key"}, headers=_auth(token))
        resp = await client.get("/admin/api-keys", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_update_api_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/admin/api-keys", json={"name": "Update Key"}, headers=_auth(token))
        # We can't get the ID from the response directly, so list and find
        keys = await client.get("/admin/api-keys", headers=_auth(token))
        key_id = keys.json()[-1]["id"]
        resp = await client.put(f"/admin/api-keys/{key_id}", json={
            "is_active": False,
        }, headers=_auth(token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_api_key_auth():
    """Test that a created API key can authenticate."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/admin/api-keys", json={"name": "Auth Test Key"}, headers=_auth(token))
        api_key = create.json()["api_key"]
        # Use the API key to access a protected endpoint
        resp = await client.get("/api/v1/datasets", headers={"X-API-Key": api_key})
    assert resp.status_code == 200


# ── Personal Access Tokens ────────────────────────────────────

@pytest.mark.asyncio
async def test_create_pat():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        resp = await client.post("/auth/pat", json={
            "name": "My Dev Token",
            "scopes": ["api"],
            "expires_in_days": 30,
        }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_prefix"].startswith("orp_")
    assert "token" in data
    assert data["token"].startswith("orp_")


@pytest.mark.asyncio
async def test_list_pats():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        await client.post("/auth/pat", json={"name": "List PAT"}, headers=_auth(token))
        resp = await client.get("/auth/pat", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_pat_auth():
    """Test that a PAT can authenticate."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/auth/pat", json={"name": "Auth PAT"}, headers=_auth(token))
        pat = create.json()["token"]
        # Use the PAT to access a protected endpoint
        resp = await client.get("/api/v1/datasets", headers={"X-API-Key": pat})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_pat():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_admin_token(client)
        create = await client.post("/auth/pat", json={"name": "Delete PAT"}, headers=_auth(token))
        pats = await client.get("/auth/pat", headers=_auth(token))
        pat_id = pats.json()[-1]["id"]
        resp = await client.delete(f"/auth/pat/{pat_id}", headers=_auth(token))
    assert resp.status_code == 200


# ── Auth edge cases ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_profile_with_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/auth/login", json={
            "username": "admin", "password": "admin123",
        })
        token = login.json()["access_token"]
        resp = await client.get("/auth/profile", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "admin"


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin_token = await _get_admin_token(client)
        # Create a non-admin user
        await client.post("/admin/users", json={
            "username": "normaluser", "password": "pass123", "is_superuser": False,
        }, headers=_auth(admin_token))
        # Login as normal user
        login = await client.post("/auth/login", json={
            "username": "normaluser", "password": "pass123",
        })
        user_token = login.json()["access_token"]
        # Try to access admin endpoint
        resp = await client.get("/admin/users", headers=_auth(user_token))
    assert resp.status_code in (401, 403)
