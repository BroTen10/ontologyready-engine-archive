from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode

router = APIRouter(tags=["config"])

PUBLIC_KEYS = {"system.name", "system.version", "system.logo_url", "system.description"}


@router.get("/public-config")
async def public_config():
    pool = await get_pool()
    rows = await pool.fetch("SELECT key, value FROM system_config WHERE key = ANY($1)", list(PUBLIC_KEYS))
    return {r["key"]: r["value"] for r in rows}


@router.get("/admin/config")
async def list_config(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch("SELECT key, value, description, updated_at FROM system_config ORDER BY key")
    return [
        {
            "key": r["key"],
            "value": r["value"],
            "description": r["description"],
            "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
        }
        for r in rows
    ]


@router.put("/admin/config/{key}")
async def update_config(key: str, body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    value = body.get("value")
    if value is None:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'value' is required")

    pool = await get_pool()
    result = await pool.execute(
        "UPDATE system_config SET value = $1, updated_at = now() WHERE key = $2",
        value,
        key,
    )
    if result == "UPDATE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"Config key '{key}' not found")

    row = await pool.fetchrow("SELECT key, value, description, updated_at FROM system_config WHERE key = $1", key)
    r = dict(row)
    return {
        "key": r["key"],
        "value": r["value"],
        "description": r["description"],
        "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
    }
