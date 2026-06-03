import base64
import hashlib
import json

from fastapi import APIRouter, Depends
from cryptography.fernet import Fernet

from ..config import settings
from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode
from ..schemas import LLMConfigCreate, LLMConfigUpdate

router = APIRouter(prefix="/api/v1/llm-configs", tags=["llm"])


def _get_fernet() -> Fernet:
    key = hashlib.sha256(settings.jwt_secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def _encrypt(value: str) -> str:
    if not value:
        return ""
    return _get_fernet().encrypt(value.encode()).decode()


def _decrypt(value: str) -> str:
    if not value:
        return ""
    return _get_fernet().decrypt(value.encode()).decode()


def _row_to_dict(row: dict, reveal_key: bool = False) -> dict:
    result = {
        "id": row["id"],
        "provider": row["provider"],
        "endpoint": row.get("endpoint", ""),
        "model": row.get("model", ""),
        "settings": json.loads(row["settings"]) if isinstance(row.get("settings"), str) else row.get("settings", {}),
        "is_default": row["is_default"],
        "is_active": row["is_active"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }
    if reveal_key:
        result["api_key"] = _decrypt(row["api_key"])
    else:
        result["api_key"] = "****" if row.get("api_key") else ""
    return result


@router.get("")
async def list_configs(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch("SELECT * FROM llm_configs ORDER BY provider, id")
    return [_row_to_dict(dict(r)) for r in rows]


@router.post("")
async def create_config(body: LLMConfigCreate, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()

    encrypted_key = _encrypt(body.api_key)
    settings_json = json.dumps(body.settings)

    if body.is_default:
        await pool.execute("UPDATE llm_configs SET is_default = FALSE WHERE is_default = TRUE")

    row = await pool.fetchrow(
        """INSERT INTO llm_configs (provider, api_key, endpoint, model, settings, is_default, is_active)
           VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7) RETURNING *""",
        body.provider, encrypted_key, body.endpoint, body.model, settings_json,
        body.is_default, body.is_active,
    )
    return _row_to_dict(dict(row), reveal_key=True)


@router.get("/{config_id}")
async def get_config(config_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM llm_configs WHERE id = $1", config_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"LLM config {config_id} not found")
    return _row_to_dict(dict(row), reveal_key=True)


@router.put("/{config_id}")
async def update_config(config_id: int, body: LLMConfigUpdate, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()

    existing = await pool.fetchrow("SELECT * FROM llm_configs WHERE id = $1", config_id)
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"LLM config {config_id} not found")

    updates = []
    values = []
    idx = 1

    for field in ("provider", "endpoint", "model"):
        val = getattr(body, field)
        if val is not None:
            updates.append(f"{field} = ${idx}")
            values.append(val)
            idx += 1

    if body.api_key is not None:
        updates.append(f"api_key = ${idx}")
        values.append(_encrypt(body.api_key))
        idx += 1

    if body.settings is not None:
        updates.append(f"settings = ${idx}::jsonb")
        values.append(json.dumps(body.settings))
        idx += 1

    for field in ("is_default", "is_active"):
        val = getattr(body, field)
        if val is not None:
            updates.append(f"{field} = ${idx}")
            values.append(val)
            idx += 1

    if body.is_default:
        await pool.execute("UPDATE llm_configs SET is_default = FALSE WHERE is_default = TRUE AND id != $1", config_id)

    if updates:
        updates.append(f"updated_at = now()")
        values.append(config_id)
        await pool.execute(
            f"UPDATE llm_configs SET {', '.join(updates)} WHERE id = ${idx}",
            *values,
        )

    row = await pool.fetchrow("SELECT * FROM llm_configs WHERE id = $1", config_id)
    return _row_to_dict(dict(row), reveal_key=True)


@router.delete("/{config_id}")
async def delete_config(config_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    result = await pool.execute("DELETE FROM llm_configs WHERE id = $1", config_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"LLM config {config_id} not found")
    return {"message": f"LLM config {config_id} deleted"}


@router.post("/{config_id}/test-connection")
async def test_connection(config_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM llm_configs WHERE id = $1", config_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"LLM config {config_id} not found")

    config = dict(row)
    api_key = _decrypt(config["api_key"])
    endpoint = config.get("endpoint", "")
    model = config.get("model", "")

    try:
        import httpx
        provider = config["provider"].lower()

        if provider == "openai":
            url = endpoint or "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
        elif provider == "tongyi":
            url = endpoint or "https://dashscope.aliyuncs.com/compatible-mode/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
        elif provider == "deepseek":
            url = endpoint or "https://api.deepseek.com/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
        else:
            url = f"{endpoint}/models" if endpoint else None
            if not url:
                return {"status": "unknown_provider", "message": f"No default endpoint for provider '{provider}'"}
            headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code in (200, 401):
                is_ok = resp.status_code == 200
                return {
                    "status": "ok" if is_ok else "auth_error",
                    "http_status": resp.status_code,
                    "message": "Connection successful" if is_ok else "Authentication failed — check API key",
                }
            return {
                "status": "error",
                "http_status": resp.status_code,
                "message": f"Unexpected response: {resp.status_code}",
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}
