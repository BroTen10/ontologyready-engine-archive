import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_access_token(user_id: str) -> str:
    expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return create_token(user_id, ACCESS_TOKEN_TYPE, expires)


def create_refresh_token(user_id: str) -> str:
    expires = timedelta(days=settings.jwt_refresh_token_expire_days)
    return create_token(user_id, REFRESH_TOKEN_TYPE, expires)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
