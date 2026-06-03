import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .errors import ErrorCode, error_response


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/v1/"):
            api_key = request.headers.get("X-API-Key", "")
            if not api_key or api_key != settings.api_key:
                return JSONResponse(
                    status_code=401,
                    content=error_response(
                        ErrorCode.UNAUTHORIZED,
                        "缺少或无效的 API Key",
                        request_id=str(uuid.uuid4()),
                    ),
                )
        return await call_next(request)
