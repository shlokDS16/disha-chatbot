"""Privacy endpoints — data export and erasure.

A minimal prototype implementation: /privacy/export returns a JSON bundle of
everything Disha has stored for the current session; /privacy/erase is an
alias for DELETE /session with purge_data=True.
"""
from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.dependencies import session_id_dep
from app.models.schemas import SessionDeleteResponse
from app.services.session_store import get_session_store

router = APIRouter(prefix="/privacy", tags=["privacy"])


def _store_dep(settings: Settings = Depends(get_settings)):
    return get_session_store(settings)


@router.get("/export")
def export_session_data(
    session_id: str = Depends(session_id_dep),
    store=Depends(_store_dep),
) -> dict:
    return store.export_session(session_id)


@router.delete("/erase", response_model=SessionDeleteResponse)
def erase_session_data(
    session_id: str = Depends(session_id_dep),
    store=Depends(_store_dep),
) -> SessionDeleteResponse:
    ok = store.delete_session(session_id, purge=True)
    return SessionDeleteResponse(session_id=session_id, purged=ok)
