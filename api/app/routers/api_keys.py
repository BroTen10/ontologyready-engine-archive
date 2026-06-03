import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode

router = APIRouter(tags=["api-keys"])


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _generate_key() -> tuple[str, str, str]:
    """Returns (raw_key, hash, prefix). The raw_key is shown only once."""
    raw = "ork_" + secrets.token_urlsafe(32)
    prefix = raw[:12]
    h = _hash_token(raw)
    return raw, h, prefix


def _generate_pat() -> tuple[str, str, str]:
    raw = "orp_" + secrets.token_urlsafe(32)
    prefix = raw[:12]
    h = _hash_token(raw)
    return raw, h, prefix


# ── Admin API Keys ────────────────────────────────────────────

@router.get("/admin/api-keys")
async def list_api_keys(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT ak.id, ak.key_prefix, ak.name, ak.user_id, ak.permissions,
                  ak.expires_at, ak.is_active, ak.last_used_at, ak.created_at,
                  u.username
           FROM api_keys ak LEFT JOIN users u ON ak.user_id = u.id
           ORDER BY ak.created_at DESC"""
    )
    return [
        {
            "id": r["id"], "key_prefix": r["key_prefix"], "name": r["name"],
            "user_id": str(r["user_id"]) if r["user_id"] else None,
            "username": r.get("username", ""),
            "permissions": r["permissions"] if isinstance(r["permissions"], list) else [],
            "expires_at": r["expires_at"].isoformat() if r.get("expires_at") else None,
            "is_active": r["is_active"], "last_used_at": r["last_used_at"].isoformat() if r.get("last_used_at") else None,
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        }
        for r in rows
    ]


@router.post("/admin/api-keys")
async def create_api_key(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    name = body.get("name", "").strip()
    if not name:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'name' is required")

    user_id = body.get("user_id", payload["sub"])
    permissions = body.get("permissions", ["api"])
    expires_at = body.get("expires_at")

    raw, h, prefix = _generate_key()

    pool = await get_pool()
    await pool.execute(
        """INSERT INTO api_keys (key_hash, key_prefix, name, user_id, permissions, expires_at, is_active)
           VALUES ($1, $2, $3, $4::uuid, $5::jsonb, $6, TRUE)""",
        h, prefix, name, user_id, permissions,
        datetime.fromisoformat(expires_at.replace("Z", "+00:00")) if expires_at else None,
    )
    return {
        "name": name, "key_prefix": prefix, "api_key": raw,
        "warning": "Store this API key securely. It will not be shown again.",
    }


@router.put("/admin/api-keys/{key_id}")
async def update_api_key(key_id: int, body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    existing = await pool.fetchrow("SELECT * FROM api_keys WHERE id = $1", key_id)
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"API key {key_id} not found")

    updates = []
    values = []
    idx = 1
    for field in ("name",):
        if field in body:
            updates.append(f"{field} = ${idx}")
            values.append(body[field])
            idx += 1
    if "is_active" in body:
        updates.append(f"is_active = ${idx}")
        values.append(body["is_active"])
        idx += 1
    if "permissions" in body:
        updates.append(f"permissions = ${idx}::jsonb")
        values.append(body["permissions"])
        idx += 1

    if updates:
        values.append(key_id)
        await pool.execute(f"UPDATE api_keys SET {', '.join(updates)} WHERE id = ${idx}", *values)

    return {"id": key_id, "status": "updated"}


@router.delete("/admin/api-keys/{key_id}")
async def delete_api_key(key_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    result = await pool.execute("DELETE FROM api_keys WHERE id = $1", key_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"API key {key_id} not found")
    return {"message": f"API key {key_id} deleted"}


# ── Personal Access Tokens (user self-service) ────────────────

@router.get("/auth/pat")
async def list_pats(payload: dict = Depends(get_current_user)):
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT id, token_prefix, name, scopes, expires_at, is_active, last_used_at, created_at
           FROM personal_access_tokens WHERE user_id = $1::uuid ORDER BY created_at DESC""",
        payload["sub"],
    )
    return [
        {
            "id": r["id"], "token_prefix": r["token_prefix"], "name": r["name"],
            "scopes": r["scopes"] if isinstance(r["scopes"], list) else [],
            "expires_at": r["expires_at"].isoformat() if r.get("expires_at") else None,
            "is_active": r["is_active"],
            "last_used_at": r["last_used_at"].isoformat() if r.get("last_used_at") else None,
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        }
        for r in rows
    ]


@router.post("/auth/pat")
async def create_pat(body: dict, payload: dict = Depends(get_current_user)):
    name = body.get("name", "").strip()
    if not name:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'name' is required")

    scopes = body.get("scopes", ["api"])
    expires_in_days = body.get("expires_in_days")
    expires_at = None
    if expires_in_days:
        expires_at = datetime.now(timezone.utc) + __import__("datetime").timedelta(days=expires_in_days)

    raw, h, prefix = _generate_pat()

    pool = await get_pool()
    await pool.execute(
        """INSERT INTO personal_access_tokens (token_hash, token_prefix, name, user_id, scopes, expires_at, is_active)
           VALUES ($1, $2, $3, $4::uuid, $5::jsonb, $6, TRUE)""",
        h, prefix, name, payload["sub"], scopes, expires_at,
    )
    return {
        "name": name, "token_prefix": prefix, "token": raw,
        "warning": "Store this token securely. It will not be shown again.",
    }


@router.delete("/auth/pat/{pat_id}")
async def delete_pat(pat_id: int, payload: dict = Depends(get_current_user)):
    pool = await get_pool()
    row = await pool.fetchrow("SELECT user_id FROM personal_access_tokens WHERE id = $1", pat_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"PAT {pat_id} not found")
    if str(row["user_id"]) != payload["sub"] and not payload.get("is_superuser"):
        raise AppError(ErrorCode.UNAUTHORIZED, "Cannot delete another user's token")

    await pool.execute("DELETE FROM personal_access_tokens WHERE id = $1", pat_id)
    return {"message": f"PAT {pat_id} deleted"}
