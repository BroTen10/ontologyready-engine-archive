import uuid
from http import HTTPStatus
from typing import Any

HTTPStatus.UNAUTHORIZED  # 共享枚举只读引用


class ErrorCode:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_JSON = "INVALID_JSON"
    UNAUTHORIZED = "UNAUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    BUSINESS_RULE_ERROR = "BUSINESS_RULE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


_CODE_STATUS = {
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.INVALID_JSON: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.BUSINESS_RULE_ERROR: 422,
    ErrorCode.INTERNAL_ERROR: 500,
}


class AppError(Exception):
    def __init__(self, code: str, message: str, details: list[dict[str, Any]] | None = None):
        self.code = code
        self.message = message
        self.details = details or []
        self.status_code = _CODE_STATUS.get(code, 500)


def error_response(code: str, message: str, details: list[dict[str, Any]] | None = None, request_id: str = "") -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "request_id": request_id,
        }
    }
