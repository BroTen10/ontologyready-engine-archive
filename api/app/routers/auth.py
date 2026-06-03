import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ..database import get_pool
from ..errors import AppError, ErrorCode
from ..jwt_auth import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from ..schemas import (
    LoginRequest,
    PasswordChangeRequest,
    RefreshRequest,
    TokenResponse,
    UserProfile,
)
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _token_exp_as_datetime(exp_timestamp: int) -> datetime:
    return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)


def _row_to_profile(row: dict) -> UserProfile:
    return UserProfile(
        id=str(row["id"]),
        username=row["username"],
        email=row["email"],
        full_name=row.get("full_name", ""),
        is_active=row["is_active"],
        is_superuser=row["is_superuser"],
        created_at=row["created_at"].isoformat() if row.get("created_at") else "",
        updated_at=row["updated_at"].isoformat() if row.get("updated_at") else "",
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM users WHERE username = $1", body.username
    )
    if not row:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid username or password")

    user = dict(row)
    if not verify_password(body.password, user["hashed_password"]):
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid username or password")

    if not user["is_active"]:
        raise AppError(ErrorCode.UNAUTHORIZED, "Account is disabled")

    user_id = str(user["id"])
    access_token = create_access_token(user_id)
    refresh_token_str = create_refresh_token(user_id)

    await pool.execute(
        "INSERT INTO refresh_tokens (token, user_id, expires_at) VALUES ($1, $2, $3)",
        refresh_token_str,
        user["id"],
        _token_exp_as_datetime(decode_token(refresh_token_str)["exp"]),
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid or expired refresh token")

    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise AppError(ErrorCode.UNAUTHORIZED, "Token is not a refresh token")

    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM refresh_tokens WHERE token = $1", body.refresh_token
    )
    if not row:
        raise AppError(ErrorCode.UNAUTHORIZED, "Refresh token has been revoked")

    token_data = dict(row)
    user_id = str(token_data["user_id"])

    await pool.execute(
        "DELETE FROM refresh_tokens WHERE token = $1", body.refresh_token
    )

    new_access = create_access_token(user_id)
    new_refresh_str = create_refresh_token(user_id)
    await pool.execute(
        "INSERT INTO refresh_tokens (token, user_id, expires_at) VALUES ($1, $2, $3)",
        new_refresh_str,
        token_data["user_id"],
        _token_exp_as_datetime(decode_token(new_refresh_str)["exp"]),
    )

    return TokenResponse(access_token=new_access, refresh_token=new_refresh_str)


@router.post("/logout")
async def logout(body: RefreshRequest):
    pool = await get_pool()
    await pool.execute(
        "DELETE FROM refresh_tokens WHERE token = $1", body.refresh_token
    )
    return {"message": "Logged out"}


@router.get("/profile", response_model=UserProfile)
async def profile(payload: dict = Depends(get_current_user)):
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM users WHERE id = $1::uuid", payload["sub"])
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, "User not found")
    return _row_to_profile(dict(row))


@router.put("/password")
async def change_password(body: PasswordChangeRequest, payload: dict = Depends(get_current_user)):
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM users WHERE id = $1::uuid", payload["sub"])
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, "User not found")

    user = dict(row)
    if not verify_password(body.old_password, user["hashed_password"]):
        raise AppError(ErrorCode.UNAUTHORIZED, "Current password is incorrect")

    new_hash = hash_password(body.new_password)
    await pool.execute(
        "UPDATE users SET hashed_password = $1, updated_at = now() WHERE id = $2::uuid",
        new_hash,
        payload["sub"],
    )
    return {"message": "Password changed"}
