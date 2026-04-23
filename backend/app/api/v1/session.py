from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.dependencies import session_id_dep
from app.models.schemas import (
    ConsentRequest,
    ConsentResponse,
    LanguageSwitchRequest,
    LocationUpdateRequest,
    SessionDeleteRequest,
    SessionDeleteResponse,
    SessionStartRequest,
    SessionStartResponse,
    SessionState,
)
from app.services.session_store import get_session_store

router = APIRouter(tags=["session"])


def _store_dep(settings: Settings = Depends(get_settings)):
    return get_session_store(settings)


@router.post("/session/start", response_model=SessionStartResponse)
def start_session(
    body: SessionStartRequest,
    store=Depends(_store_dep),
) -> SessionStartResponse:
    state = store.create_session(body.language, body.persona_hint)
    return SessionStartResponse(
        session_id=state.session_id,
        language=state.language,
        consent_required=not state.consent.accepted,
        created_at=state.created_at,
    )


@router.get("/session", response_model=SessionState)
def get_session_state(
    session_id: str = Depends(session_id_dep),
    store=Depends(_store_dep),
) -> SessionState:
    return store.get_session(session_id)


@router.post("/session/language", response_model=SessionState)
def switch_language(
    body: LanguageSwitchRequest,
    session_id: str = Depends(session_id_dep),
    store=Depends(_store_dep),
) -> SessionState:
    return store.update_language(session_id, body.language)


@router.post("/session/location", response_model=SessionState)
def set_location(
    body: LocationUpdateRequest,
    session_id: str = Depends(session_id_dep),
    store=Depends(_store_dep),
) -> SessionState:
    return store.update_location(session_id, body.lat, body.lng, body.label)


@router.post("/session/consent", response_model=ConsentResponse)
def record_consent(
    body: ConsentRequest,
    session_id: str = Depends(session_id_dep),
    store=Depends(_store_dep),
) -> ConsentResponse:
    record = store.record_consent(session_id, body.accepted, body.method, body.scopes)
    return ConsentResponse(session_id=session_id, consent=record)


@router.delete("/session", response_model=SessionDeleteResponse)
def delete_session(
    body: SessionDeleteRequest = SessionDeleteRequest(),
    session_id: str = Depends(session_id_dep),
    store=Depends(_store_dep),
) -> SessionDeleteResponse:
    ok = store.delete_session(session_id, purge=body.purge_data)
    return SessionDeleteResponse(session_id=session_id, purged=ok and body.purge_data)
