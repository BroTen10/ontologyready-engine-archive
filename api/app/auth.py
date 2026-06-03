import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .database import get_pool
from .errors import ErrorCode, error_response
from .jwt_auth import decode_token


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/v1/") or request.url.path.startswith("/admin/"):
            # 1. Try API Key (global static key from env)
            api_key = request.headers.get("X-API-Key", "")
            if api_key and api_key == settings.api_key:
                return await call_next(request)

            # 2. Try JWT Bearer token
            auth = request.headers.get("Authorization", "")
            if auth.lower().startswith("bearer "):
                token = auth[7:]
                try:
                    payload = decode_token(token)
                    request.state.user = payload
                    return await call_next(request)
                except Exception:
                    pass

            # 3. Try database API key (ork_ prefix)
            if api_key.startswith("ork_"):
                try:
                    h = _hash_token(api_key)
                    pool = await get_pool()
                    row = await pool.fetchrow(
                        "SELECT * FROM api_keys WHERE key_hash = $1 AND is_active = TRUE", h
                    )
                    if row:
                        r = dict(row)
                        if r.get("expires_at") and r["expires_at"] < datetime.now(timezone.utc):
                            pass  # Expired
                        else:
                            await pool.execute(
                                "UPDATE api_keys SET last_used_at = now() WHERE id = $1", r["id"]
                            )
                            request.state.api_key_user = str(r["user_id"]) if r.get("user_id") else None
                            return await call_next(request)
                except Exception:
                    pass

            # 4. Try Personal Access Token (orp_ prefix)
            if api_key.startswith("orp_"):
                try:
                    h = _hash_token(api_key)
                    pool = await get_pool()
                    row = await pool.fetchrow(
                        "SELECT * FROM personal_access_tokens WHERE token_hash = $1 AND is_active = TRUE", h
                    )
                    if row:
                        r = dict(row)
                        if r.get("expires_at") and r["expires_at"] < datetime.now(timezone.utc):
                            pass  # Expired
                        else:
                            await pool.execute(
                                "UPDATE personal_access_tokens SET last_used_at = now() WHERE id = $1", r["id"]
                            )
                            request.state.user = {"sub": str(r["user_id"])}
                            return await call_next(request)
                except Exception:
                    pass

            request_id = str(uuid.uuid4())
            return JSONResponse(
                status_code=401,
                content=error_response(
                    ErrorCode.UNAUTHORIZED,
                    "Missing or invalid API Key / JWT token",
                    request_id=request_id,
                ),
            )
        return await call_next(request)

    @staticmethod
    async def authenticate_pat(token: str):
        """Validate a PAT and return user payload or None."""
        try:
            h = _hash_token(token)
            pool = await get_pool()
            row = await pool.fetchrow(
                "SELECT * FROM personal_access_tokens WHERE token_hash = $1 AND is_active = TRUE", h
            )
            if row:
                r = dict(row)
                if r.get("expires_at") and r["expires_at"] < datetime.now(timezone.utc):
                    return None
                await pool.execute(
                    "UPDATE personal_access_tokens SET last_used_at = now() WHERE id = $1", r["id"]
                )
                return {"sub": str(r["user_id"]), "scopes": r.get("scopes", [])}
        except Exception:
            pass
        return None
