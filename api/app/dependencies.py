from fastapi import Depends, Request

from .config import settings
from .database import get_pool
from .errors import AppError, ErrorCode
from .jwt_auth import ACCESS_TOKEN_TYPE, decode_token


async def get_current_user(request: Request) -> dict:
    """Dependency: extract and verify JWT from Authorization header, return user payload with is_superuser."""
    auth = request.headers.get("Authorization")
    if not auth:
        raise AppError(ErrorCode.UNAUTHORIZED, "Missing Authorization header")

    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AppError(ErrorCode.UNAUTHORIZED, "Authorization header must be: Bearer <token>")

    try:
        payload = decode_token(token)
    except Exception:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid or expired token")

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise AppError(ErrorCode.UNAUTHORIZED, "Token is not an access token")

    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT is_superuser FROM users WHERE id = $1::uuid", payload["sub"]
    )
    if row:
        payload["is_superuser"] = row["is_superuser"]

    return payload


def require_admin(payload: dict) -> None:
    if not payload.get("is_superuser"):
        raise AppError(ErrorCode.UNAUTHORIZED, "Admin privileges required")
