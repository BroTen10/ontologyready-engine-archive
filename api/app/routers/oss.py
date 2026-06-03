import json

from fastapi import APIRouter, Depends

from ..config import settings
from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/admin", tags=["oss"])


def _row_to_dict(row: dict) -> dict:
    return {
        "id": row["id"],
        "provider": row["provider"],
        "endpoint": row.get("endpoint", ""),
        "access_key": "****" if row.get("access_key") else "",
        "bucket": row.get("bucket", ""),
        "region": row.get("region", "us-east-1"),
        "is_active": row["is_active"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


@router.get("/oss")
async def get_oss_config(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM oss_config WHERE is_active = TRUE LIMIT 1")
    if not row:
        return {"configured": False, "message": "No OSS config found"}
    return _row_to_dict(dict(row))


@router.put("/oss")
async def update_oss_config(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    provider = body.get("provider", "s3")
    endpoint = body.get("endpoint", "")
    access_key = body.get("access_key", "")
    secret_key = body.get("secret_key", "")
    bucket = body.get("bucket", "")
    region = body.get("region", "us-east-1")
    is_active = body.get("is_active", True)

    pool = await get_pool()
    existing = await pool.fetchrow("SELECT id FROM oss_config LIMIT 1")
    if existing:
        updates = ["provider = $1", "endpoint = $2", "access_key = $3", "bucket = $4", "region = $5", "is_active = $6", "updated_at = now()"]
        values = [provider, endpoint, access_key, bucket, region, is_active]
        if secret_key:
            updates.append("secret_key = $7")
            values.append(secret_key)
            values.append(existing["id"])
        else:
            values.append(existing["id"])
        await pool.execute(
            f"UPDATE oss_config SET {', '.join(updates)} WHERE id = ${len(values)}",
            *values,
        )
    else:
        await pool.execute(
            """INSERT INTO oss_config (provider, endpoint, access_key, secret_key, bucket, region, is_active)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            provider, endpoint, access_key, secret_key, bucket, region, is_active,
        )

    row = await pool.fetchrow("SELECT * FROM oss_config WHERE is_active = TRUE LIMIT 1")
    return _row_to_dict(dict(row))


@router.post("/oss/test-connection")
async def test_oss_connection(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM oss_config WHERE is_active = TRUE LIMIT 1")
    if not row:
        return {"status": "not_configured", "message": "No OSS config found"}

    r = dict(row)
    try:
        import httpx
        endpoint = r["endpoint"]
        access_key = r["access_key"]
        secret_key = r["secret_key"]
        bucket = r["bucket"]

        url = f"{endpoint}/{bucket}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.head(url)
            return {
                "status": "ok" if resp.status_code in (200, 403) else "error",
                "http_status": resp.status_code,
                "endpoint": endpoint,
                "bucket": bucket,
                "message": "Connection successful" if resp.status_code in (200, 403) else f"Unexpected response: {resp.status_code}",
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}
