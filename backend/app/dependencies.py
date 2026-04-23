from typing import Annotated

from fastapi import Header, HTTPException

from app.config import Settings, get_settings
from app.errors import DishaError, ErrorCode

SUPPORTED_LANGUAGES = {"en", "hi", "mr"}


def language_dep(x_user_language: Annotated[str | None, Header(alias="X-User-Language")] = None) -> str:
    lang = (x_user_language or "en").lower()
    if lang not in SUPPORTED_LANGUAGES:
        raise DishaError(
            ErrorCode.INVALID_LANGUAGE,
            f"Unsupported language. Must be one of: {', '.join(sorted(SUPPORTED_LANGUAGES))}.",
            status_code=400,
            details={"received": x_user_language},
        )
    return lang


def session_id_dep(x_session_id: Annotated[str | None, Header(alias="X-Session-ID")] = None) -> str:
    if not x_session_id:
        raise DishaError(
            ErrorCode.SESSION_NOT_FOUND,
            "X-Session-ID header is required. Call POST /session/start first.",
            status_code=404,
        )
    return x_session_id


def optional_session_id_dep(x_session_id: Annotated[str | None, Header(alias="X-Session-ID")] = None) -> str | None:
    return x_session_id


def admin_key_dep(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
    settings: Settings = None,  # type: ignore[assignment]
) -> None:
    settings = settings or get_settings()
    if not settings.admin_key or x_admin_key != settings.admin_key:
        raise HTTPException(status_code=401, detail="Invalid or missing admin key.")
