from enum import Enum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorCode(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_LANGUAGE = "INVALID_LANGUAGE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    ADMIN_KEY_INVALID = "ADMIN_KEY_INVALID"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    NOT_FOUND = "NOT_FOUND"
    CONSENT_REQUIRED = "CONSENT_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    OCR_UNAVAILABLE = "OCR_UNAVAILABLE"
    EMBEDDING_UNAVAILABLE = "EMBEDDING_UNAVAILABLE"
    MAPS_UNAVAILABLE = "MAPS_UNAVAILABLE"
    FEATURE_NOT_CONFIGURED = "FEATURE_NOT_CONFIGURED"


class DishaError(Exception):
    """Base class — always carries an ErrorCode + status + details."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def error_payload(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}


async def disha_error_handler(_: Request, exc: DishaError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code.value, exc.message, exc.details),
    )


async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = {
        400: ErrorCode.INVALID_INPUT,
        401: ErrorCode.ADMIN_KEY_INVALID,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONSENT_REQUIRED,
        429: ErrorCode.RATE_LIMITED,
    }.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(code.value, str(exc.detail)),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_payload(
            ErrorCode.INVALID_INPUT.value,
            "Request validation failed.",
            {"errors": exc.errors()},
        ),
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_payload(
            ErrorCode.INTERNAL_ERROR.value,
            "An unexpected error occurred.",
            {"type": exc.__class__.__name__},
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DishaError, disha_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
