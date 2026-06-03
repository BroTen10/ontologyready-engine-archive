import json
import uuid

from fastapi import APIRouter, Depends

from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode
from ..jwt_auth import hash_password, verify_password

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Users ─────────────────────────────────────────────────────

@router.get("/users")
async def list_users(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch("SELECT id, username, email, full_name, is_active, is_superuser, created_at, updated_at FROM users ORDER BY created_at DESC")
    return [
        {
            "id": str(r["id"]),
            "username": r["username"],
            "email": r["email"],
            "full_name": r.get("full_name", ""),
            "is_active": r["is_active"],
            "is_superuser": r["is_superuser"],
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
            "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
        }
        for r in rows
    ]


@router.post("/users", status_code=201)
async def create_user(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    email = body.get("email", "").strip()
    full_name = body.get("full_name", "")
    is_superuser = body.get("is_superuser", False)

    if not username or not password:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Fields 'username' and 'password' are required")

    pool = await get_pool()
    existing = await pool.fetchrow("SELECT id FROM users WHERE username = $1", username)
    if existing:
        raise AppError(ErrorCode.CONFLICT, f"User '{username}' already exists")

    hashed = hash_password(password)
    user_id = str(uuid.uuid4())
    row = await pool.fetchrow(
        """INSERT INTO users (id, username, email, hashed_password, full_name, is_active, is_superuser)
           VALUES ($1::uuid, $2, $3, $4, $5, TRUE, $6) RETURNING id, username, email, full_name, is_active, is_superuser, created_at, updated_at""",
        user_id, username, email, hashed, full_name, is_superuser,
    )
    r = dict(row)
    return {
        "id": str(r["id"]), "username": r["username"], "email": r["email"],
        "full_name": r.get("full_name", ""), "is_active": r["is_active"],
        "is_superuser": r["is_superuser"],
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
    }


@router.put("/users/{user_id}")
async def update_user(user_id: str, body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    existing = await pool.fetchrow("SELECT * FROM users WHERE id = $1::uuid", user_id)
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"User {user_id} not found")

    updates = []
    values = []
    idx = 1
    for field in ("email", "full_name"):
        if field in body:
            updates.append(f"{field} = ${idx}")
            values.append(body[field])
            idx += 1

    for bool_field in ("is_active", "is_superuser"):
        if bool_field in body:
            updates.append(f"{bool_field} = ${idx}")
            values.append(body[bool_field])
            idx += 1

    if "password" in body and body["password"]:
        updates.append(f"hashed_password = ${idx}")
        values.append(hash_password(body["password"]))
        idx += 1

    if updates:
        updates.append("updated_at = now()")
        values.append(user_id)
        await pool.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ${idx}::uuid",
            *values,
        )

    row = await pool.fetchrow("SELECT id, username, email, full_name, is_active, is_superuser, created_at, updated_at FROM users WHERE id = $1::uuid", user_id)
    r = dict(row)
    return {
        "id": str(r["id"]), "username": r["username"], "email": r["email"],
        "full_name": r.get("full_name", ""), "is_active": r["is_active"],
        "is_superuser": r["is_superuser"],
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
    }


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    result = await pool.execute("DELETE FROM users WHERE id = $1::uuid", user_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"User {user_id} not found")
    return {"message": f"User {user_id} deleted"}


# ── Roles ─────────────────────────────────────────────────────

@router.get("/roles")
async def list_roles(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch("SELECT * FROM roles ORDER BY id")
    return [
        {
            "id": r["id"], "name": r["name"], "description": r.get("description", ""),
            "permissions": json.loads(r["permissions"]) if isinstance(r.get("permissions"), str) else r.get("permissions", []),
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        }
        for r in rows
    ]


@router.post("/roles", status_code=201)
async def create_role(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    name = body.get("name", "").strip()
    if not name:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'name' is required")

    pool = await get_pool()
    existing = await pool.fetchrow("SELECT id FROM roles WHERE name = $1", name)
    if existing:
        raise AppError(ErrorCode.CONFLICT, f"Role '{name}' already exists")

    permissions = body.get("permissions", [])
    row = await pool.fetchrow(
        "INSERT INTO roles (name, description, permissions) VALUES ($1, $2, $3::jsonb) RETURNING *",
        name, body.get("description", ""), json.dumps(permissions),
    )
    r = dict(row)
    return {
        "id": r["id"], "name": r["name"], "description": r.get("description", ""),
        "permissions": json.loads(r["permissions"]) if isinstance(r.get("permissions"), str) else r.get("permissions", []),
    }


@router.put("/roles/{role_id}")
async def update_role(role_id: int, body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    existing = await pool.fetchrow("SELECT * FROM roles WHERE id = $1", role_id)
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"Role {role_id} not found")

    updates = []
    values = []
    idx = 1
    for field in ("name", "description"):
        if field in body:
            updates.append(f"{field} = ${idx}")
            values.append(body[field])
            idx += 1
    if "permissions" in body:
        updates.append(f"permissions = ${idx}::jsonb")
        values.append(json.dumps(body["permissions"]))
        idx += 1

    if updates:
        updates.append("updated_at = now()")
        values.append(role_id)
        await pool.execute(f"UPDATE roles SET {', '.join(updates)} WHERE id = ${idx}", *values)

    row = await pool.fetchrow("SELECT * FROM roles WHERE id = $1", role_id)
    r = dict(row)
    return {
        "id": r["id"], "name": r["name"], "description": r.get("description", ""),
        "permissions": json.loads(r["permissions"]) if isinstance(r.get("permissions"), str) else r.get("permissions", []),
    }


@router.delete("/roles/{role_id}")
async def delete_role(role_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    await pool.execute("DELETE FROM role_assignments WHERE role_id = $1", role_id)
    result = await pool.execute("DELETE FROM roles WHERE id = $1", role_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"Role {role_id} not found")
    return {"message": f"Role {role_id} deleted"}


# ── Role Assignments ──────────────────────────────────────────

@router.post("/users/{user_id}/roles")
async def assign_role(user_id: str, body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    role_id = body.get("role_id")
    if not role_id:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'role_id' is required")

    pool = await get_pool()
    try:
        await pool.execute(
            "INSERT INTO role_assignments (user_id, role_id) VALUES ($1::uuid, $2)",
            user_id, role_id,
        )
    except Exception:
        raise AppError(ErrorCode.CONFLICT, "Assignment already exists or invalid user/role")
    return {"user_id": user_id, "role_id": role_id, "status": "assigned"}


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role(user_id: str, role_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    await pool.execute(
        "DELETE FROM role_assignments WHERE user_id = $1::uuid AND role_id = $2",
        user_id, role_id,
    )
    return {"user_id": user_id, "role_id": role_id, "status": "removed"}


@router.get("/users/{user_id}/roles")
async def get_user_roles(user_id: str, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT r.* FROM roles r
           JOIN role_assignments ra ON r.id = ra.role_id
           WHERE ra.user_id = $1::uuid""",
        user_id,
    )
    return [
        {
            "id": r["id"], "name": r["name"],
            "permissions": json.loads(r["permissions"]) if isinstance(r.get("permissions"), str) else r.get("permissions", []),
        }
        for r in rows
    ]


# ── Groups ────────────────────────────────────────────────────

@router.get("/groups")
async def list_groups(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch("SELECT * FROM groups_table ORDER BY name")
    return [
        {
            "id": r["id"], "name": r["name"], "description": r.get("description", ""),
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        }
        for r in rows
    ]


@router.post("/groups", status_code=201)
async def create_group(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    name = body.get("name", "").strip()
    if not name:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'name' is required")

    pool = await get_pool()
    existing = await pool.fetchrow("SELECT id FROM groups_table WHERE name = $1", name)
    if existing:
        raise AppError(ErrorCode.CONFLICT, f"Group '{name}' already exists")

    row = await pool.fetchrow(
        "INSERT INTO groups_table (name, description) VALUES ($1, $2) RETURNING *",
        name, body.get("description", ""),
    )
    r = dict(row)
    return {"id": r["id"], "name": r["name"], "description": r.get("description", "")}


@router.put("/groups/{group_id}")
async def update_group(group_id: int, body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    existing = await pool.fetchrow("SELECT * FROM groups_table WHERE id = $1", group_id)
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"Group {group_id} not found")

    updates = []
    values = []
    idx = 1
    for field in ("name", "description"):
        if field in body:
            updates.append(f"{field} = ${idx}")
            values.append(body[field])
            idx += 1
    if updates:
        updates.append("updated_at = now()")
        values.append(group_id)
        await pool.execute(f"UPDATE groups_table SET {', '.join(updates)} WHERE id = ${idx}", *values)

    row = await pool.fetchrow("SELECT * FROM groups_table WHERE id = $1", group_id)
    r = dict(row)
    return {"id": r["id"], "name": r["name"], "description": r.get("description", "")}


@router.delete("/groups/{group_id}")
async def delete_group(group_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    await pool.execute("DELETE FROM group_members WHERE group_id = $1", group_id)
    result = await pool.execute("DELETE FROM groups_table WHERE id = $1", group_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"Group {group_id} not found")
    return {"message": f"Group {group_id} deleted"}


# ── Group Members ─────────────────────────────────────────────

@router.post("/groups/{group_id}/members")
async def add_group_member(group_id: int, body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    user_id = body.get("user_id", "")
    if not user_id:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'user_id' is required")

    pool = await get_pool()
    try:
        await pool.execute(
            "INSERT INTO group_members (group_id, user_id) VALUES ($1, $2::uuid)",
            group_id, user_id,
        )
    except Exception:
        raise AppError(ErrorCode.CONFLICT, "Membership already exists or invalid group/user")
    return {"group_id": group_id, "user_id": user_id, "status": "added"}


@router.delete("/groups/{group_id}/members/{user_id}")
async def remove_group_member(group_id: int, user_id: str, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    await pool.execute(
        "DELETE FROM group_members WHERE group_id = $1 AND user_id = $2::uuid",
        group_id, user_id,
    )
    return {"group_id": group_id, "user_id": user_id, "status": "removed"}


@router.get("/groups/{group_id}/members")
async def list_group_members(group_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT u.id, u.username, u.email, u.full_name, u.is_active
           FROM users u JOIN group_members gm ON u.id = gm.user_id
           WHERE gm.group_id = $1 ORDER BY u.username""",
        group_id,
    )
    return [
        {"id": str(r["id"]), "username": r["username"], "email": r["email"],
         "full_name": r.get("full_name", ""), "is_active": r["is_active"]}
        for r in rows
    ]
