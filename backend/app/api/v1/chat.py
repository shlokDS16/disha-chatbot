from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends

from app.config import Settings, get_settings
from app.dependencies import language_dep, session_id_dep
from app.errors import DishaError
from app.models.schemas import (
    ChatFeedbackRequest,
    ChatFeedbackResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    Disease,
    FacilityBlock,
    FacilityData,
    FacilityService,
    Language,
    MessageSource,
    SourceMeta,
    TextBlock,
)
from app.services import maps as maps_service
from app.services import rag as rag_service
from app.services.groq_client import chat_complete
from app.services.prompt_builder import build_system_prompt, wrap_kb_context
from app.services.session_store import get_session_store


def _build_file_context(files: list[dict]) -> str:
    """Format recent uploaded-file OCR text for injection into the chat prompt."""
    if not files:
        return ""
    parts: list[str] = []
    # Cap how much text we inject so we don't blow the model context.
    budget = 6000
    for f in files:
        text = (f.get("ocr_text") or "").strip()
        if not text:
            continue
        chunk = text if len(text) <= budget else text[:budget] + "\n...[truncated]"
        budget -= len(chunk)
        parts.append(
            f"---\nFile: {f.get('filename', 'document')} "
            f"(type: {f.get('type', 'file')})\n{chunk}\n---"
        )
        if budget <= 0:
            break
    if not parts:
        return ""
    return (
        "The user is asking about a document they uploaded in this session. "
        "Use the text below as the authoritative source for their question.\n\n"
        + "\n".join(parts)
    )


# Keywords that signal the user is explicitly asking about an uploaded file.
# Covers EN, HI (Devanagari), and MR (Devanagari/transliterated).
_FILE_QUERY_KEYWORDS: tuple[str, ...] = (
    # English
    "file", "document", "doc", "report", "pdf", "scan", "scanned",
    "upload", "uploaded", "attach", "attached", "attachment",
    "resume", "cv", "letter", "prescription", "my report", "the report",
    "this file", "that file", "this document", "that document",
    "what does it say", "what does this say", "summarize", "summarise",
    "analyse", "analyze", "explain this", "explain the",
    # Hindi (Devanagari)
    "फाइल", "फ़ाइल", "दस्तावेज़", "दस्तावेज", "रिपोर्ट", "पीडीएफ",
    "अटैच", "अपलोड", "कागज", "कागज़", "पर्ची", "जांच", "रिज्यूमे", "सीवी",
    # Marathi (Devanagari)
    "दस्तऐवज", "कागद", "तपासणी", "रिपोर्ट",
)


def _query_mentions_file(query: str) -> bool:
    """True only when the user query explicitly references an uploaded document.

    Returning False keeps file OCR text OUT of the LLM context so a lingering
    resume upload doesn't contaminate unrelated health questions.
    """
    q = (query or "").lower().strip()
    if not q:
        return False
    return any(kw in q for kw in _FILE_QUERY_KEYWORDS)


# ─── Facility-intent detection ───────────────────────────────────────
#
# Maps a user query like "where is the nearest HPLC test centre?" to a
# FacilityService enum value so we can call maps_service.find_nearby(...).
# Order matters: the most specific services are checked first so a query
# like "HPLC test" doesn't fall through to GENERAL_HOSPITAL.
#
# Covers EN, HI (Devanagari), and MR. Transliterated forms (e.g. "najdiki")
# are intentionally omitted — too ambiguous and rarely typed by real users.

_HPLC_KEYWORDS: tuple[str, ...] = (
    "hplc", "sickle test", "sickle cell test", "sickling test",
    "एचपीएलसी", "सिकल टेस्ट", "सिकल जांच", "सिकल तपासणी",
)
_CVS_KEYWORDS: tuple[str, ...] = (
    "cvs", "amnio", "amniocentesis", "chorionic",
    "सीवीएस", "एमनियो", "गर्भ जांच", "गर्भ तपासणी",
)
_HAEMATOLOGY_KEYWORDS: tuple[str, ...] = (
    "haematolog", "hematolog", "blood specialist", "blood doctor",
    "हीमैटोलॉजी", "रक्त रोग", "रक्त विशेषज्ञ", "रक्त तज्ञ",
)
_HU_KEYWORDS: tuple[str, ...] = (
    "hydroxyurea", "hu dispensing", "hu centre", "hu center",
    "हाइड्रोक्सीयूरिया", "हायड्रोक्सीयुरिया",
)
# Any generic ask for a hospital / doctor / clinic / nearby care.
_HOSPITAL_KEYWORDS: tuple[str, ...] = (
    "hospital", "clinic", "doctor", "nearest", "near me", "nearby",
    "primary health centre", "phc", "medical centre", "medical center",
    "अस्पताल", "क्लिनिक", "डॉक्टर", "नजदीकी", "नज़दीकी", "पास का", "पास में",
    "रुग्णालय", "दवाखाना", "जवळचे", "जवळच्या", "जवळ", "जवळील",
)
# Any generic "test centre / lab" that isn't specifically HPLC.
_LAB_KEYWORDS: tuple[str, ...] = (
    "test centre", "test center", "testing centre", "testing center",
    "diagnostic", "laboratory",
    "जाँच केंद्र", "जांच केंद्र", "प्रयोगशाला",
    "तपासणी केंद्र", "प्रयोगशाळा",
)
# Explicit location-intent triggers — require one of these to be present
# alongside a service keyword, so "tell me about hospitals" (information
# question) doesn't trigger a map lookup.
_LOCATION_TRIGGERS: tuple[str, ...] = (
    "where", "nearest", "near me", "nearby", "close by", "find",
    "location of", "where is", "where can i", "closest",
    "कहाँ", "कहां", "नजदीकी", "नज़दीकी", "पास का", "पास में", "पास की", "ढूंढ",
    "कुठे", "जवळ", "जवळचे", "जवळच्या", "जवळील", "सापडेल", "शोधा",
)


def _query_wants_facility(query: str) -> FacilityService | None:
    """Return the FacilityService the user is asking for, or None.

    A query matches only when it contains both a service keyword AND a
    location trigger ("where", "nearest", etc.) — this prevents benign
    informational questions ("what is a hospital?") from triggering a
    Google Places call.
    """
    q = (query or "").lower().strip()
    if not q:
        return None

    has_trigger = any(t in q for t in _LOCATION_TRIGGERS)
    if not has_trigger:
        return None

    if any(kw in q for kw in _HPLC_KEYWORDS):
        return FacilityService.HPLC_CENTRE
    if any(kw in q for kw in _CVS_KEYWORDS):
        return FacilityService.CVS_AMNIO
    if any(kw in q for kw in _HAEMATOLOGY_KEYWORDS):
        return FacilityService.HAEMATOLOGY
    if any(kw in q for kw in _HU_KEYWORDS):
        return FacilityService.HU_DISPENSING
    if any(kw in q for kw in _LAB_KEYWORDS):
        return FacilityService.HPLC_CENTRE
    if any(kw in q for kw in _HOSPITAL_KEYWORDS):
        return FacilityService.GENERAL_HOSPITAL
    return None


def _build_facility_context(items: list, service: FacilityService) -> str:
    """LLM hint describing the facility cards attached to the response."""
    lines = [
        "The user asked where to find a facility. I already looked up "
        f"the {service.value.replace('_', ' ')} options nearest to them "
        "using Google Places — the app will render them below as clickable "
        "cards with Google Maps directions. Your job is to acknowledge the "
        "list in one short sentence (e.g. \"I found these nearby — see "
        "the list below\") and mention the closest one by name. Do NOT "
        "list all of them. Do NOT invent addresses or phone numbers.",
        "",
        "Facilities found (closest first):",
    ]
    for i, it in enumerate(items[:5], 1):
        lines.append(
            f"{i}. {it.name} — {it.address} ({it.distance_km} km)"
        )
    return "\n".join(lines)


router = APIRouter(prefix="/chat", tags=["chat"])

_log = logging.getLogger("disha.chat")


def _store_dep(settings: Settings = Depends(get_settings)):
    return get_session_store(settings)


def _decide_routing(top_score: float, threshold_match: float, threshold_ctx: float) -> str:
    if top_score >= threshold_match:
        return "rag_only"
    if top_score >= threshold_ctx:
        return "hybrid"
    return "llm_only"


@router.post("/message", response_model=ChatMessageResponse)
def send_message(
    body: ChatMessageRequest,
    background: BackgroundTasks,
    language: str = Depends(language_dep),
    session_id: str = Depends(session_id_dep),
    settings: Settings = Depends(get_settings),
    store=Depends(_store_dep),
) -> ChatMessageResponse:
    lang = Language(language)
    session = store.get_session(session_id)
    persona = body.persona_hint or session.persona

    # Save user message first so context reflects real order.
    store.save_message(session_id, role="user", language=lang, text=body.text)

    # Retrieval — best-effort. If embeddings are not configured we fall
    # straight to LLM-only mode.
    retrieved: list[dict] = []
    top_score = 0.0
    try:
        retrieved = rag_service.search(
            settings=settings,
            query=body.text,
            disease=Disease.SICKLE_CELL,
            language=lang,
            persona=persona,
            top_k=20,
            rerank_k=5,
        )
        if retrieved:
            top_score = retrieved[0].get("reranker_score") or retrieved[0].get("score") or 0.0
    except DishaError as e:
        _log.info("retrieval unavailable, falling back to LLM-only: %s", e.message)
    except Exception as e:  # noqa: BLE001
        # Qdrant/embedding network errors (e.g. ResponseHandlingException) must
        # not 500 the chat endpoint — degrade to LLM-only mode.
        _log.warning("retrieval failed with non-DishaError: %s", e)

    routing = _decide_routing(
        top_score, settings.rag_match_threshold, settings.rag_context_threshold
    )

    # Build system prompt + optional KB context.
    kb_block = wrap_kb_context(retrieved) if routing in ("rag_only", "hybrid") else ""

    # Uploaded file OCR is ONLY injected when the user's question explicitly
    # references a document — otherwise a lingering upload (e.g. a resume)
    # would bleed into unrelated health questions.
    if _query_mentions_file(body.text):
        session_files = store.get_session_files(session_id, limit=3, only_done=True)
        file_block = _build_file_context(session_files)
        if file_block and kb_block:
            kb_block = kb_block + "\n\n" + file_block
        elif file_block:
            kb_block = file_block

    # Facility lookup — if the query looks like "where is the nearest X"
    # AND the user has consented to share their location, we call the
    # Google Places layer that already powers /facilities/nearby and
    # attach the results as a FacilityBlock so the UI renders clickable
    # cards (each links straight to Google Maps directions).
    facility_block: FacilityBlock | None = None
    wanted_service = _query_wants_facility(body.text)
    if wanted_service and session.location:
        try:
            items = maps_service.find_nearby(
                settings,
                session.location.lat,
                session.location.lng,
                wanted_service,
                radius_m=15000,
                limit=5,
            )
            if items:
                facility_block = FacilityBlock(
                    data=FacilityData(
                        user_location={
                            "lat": session.location.lat,
                            "lng": session.location.lng,
                        },
                        facilities=items,
                    )
                )
                facility_context = _build_facility_context(items, wanted_service)
                if kb_block:
                    kb_block = kb_block + "\n\n" + facility_context
                else:
                    kb_block = facility_context
        except DishaError as e:
            _log.info("facility lookup unavailable: %s", e.message)
        except Exception as e:  # noqa: BLE001
            _log.warning("facility lookup failed: %s", e)

    system_prompt = build_system_prompt(lang, persona, has_kb_context=bool(kb_block))

    # Prior messages (short window) for conversational memory.
    prior_raw = store.get_recent_messages(session_id, limit=8)
    prior: list[dict[str, str]] = [
        {"role": r["role"], "content": r["text"]} for r in prior_raw if r["role"] in {"user", "assistant"}
    ]
    # drop the just-saved user turn (we re-add it via kb + user_payload)
    if prior and prior[-1]["role"] == "user" and prior[-1]["content"] == body.text:
        prior = prior[:-1]

    try:
        answer, meta = chat_complete(
            settings=settings,
            system_prompt=system_prompt,
            user_text=body.text,
            prior_messages=prior,
            kb_context=kb_block or None,
        )
        source = (
            MessageSource.RAG
            if routing == "rag_only"
            else MessageSource.HYBRID
            if routing == "hybrid"
            else MessageSource.LLM
        )
    except DishaError as e:
        _log.warning("LLM unavailable: %s", e.message)
        answer = (
            "I cannot reach my answer service right now. Please try again in a minute, "
            "or tap a starter question below."
        )
        meta = {"model": None, "finish_reason": "error"}
        source = MessageSource.LLM

    # Persist assistant message. If we looked up nearby facilities, the
    # FacilityBlock rides alongside the TextBlock so a reopened chat
    # still shows the list with working directions links.
    content_blocks: list[dict] = [TextBlock(text=answer).model_dump(mode="json")]
    if facility_block:
        content_blocks.append(facility_block.model_dump(mode="json"))
    message_id = store.save_message(
        session_id,
        role="assistant",
        language=lang,
        text=answer,
        content=content_blocks,
        source=source.value,
    )

    # Auto-enrich whenever a non-RAG answer is produced — next time the same
    # question comes in, retrieval will return the stored Q/A and the LLM can
    # be skipped. Consent is still required for STORE_SESSION (the default);
    # explicit AUTO_RAG_ENRICH opt-out is respected.
    consent = session.consent
    scope_values = {s.value for s in consent.scopes}
    consent_enriches = (
        consent.accepted
        and "store_session" in scope_values
        and "auto_rag_enrich_off" not in scope_values
    )
    if (
        source in (MessageSource.LLM, MessageSource.HYBRID)
        and consent_enriches
        and rag_service.should_auto_enrich(
            body.text, answer, settings, consent_enriches=True
        )
    ):
        background.add_task(
            rag_service.auto_enrich,
            settings,
            Disease.SICKLE_CELL,
            lang,
            body.text,
            answer,
            persona,
        )

    response_content: list = [TextBlock(text=answer)]
    if facility_block:
        response_content.append(facility_block)

    return ChatMessageResponse(
        message_id=message_id,
        language=lang,
        source=source,
        source_meta=SourceMeta(
            chunk_ids=[c["chunk_id"] for c in retrieved][:5],
            confidence=float(top_score),
            model=meta.get("model"),
            reranker_score=retrieved[0].get("reranker_score") if retrieved else None,
        ),
        content=response_content,
        audio_url=None,
        feedback_id=str(uuid.uuid4()),
        suggested_replies=[],
        timestamp=datetime.now(UTC),
    )


@router.get("/history")
def list_history(
    session_id: str = Depends(session_id_dep),
    store=Depends(_store_dep),
) -> dict:
    rows = store.get_recent_messages(session_id, limit=200)
    return {
        "session_id": session_id,
        "messages": [
            {
                "message_id": r["message_id"],
                "role": r["role"],
                "language": r["language"],
                "text": r["text"],
                "source": r.get("source"),
                "created_at": r["created_at"],
            }
            for r in rows
        ],
    }


@router.delete("/history")
def clear_history(
    session_id: str = Depends(session_id_dep),
    store=Depends(_store_dep),
) -> dict:
    removed = store.clear_messages(session_id)
    return {"session_id": session_id, "removed": removed}


@router.get("/export")
def export_history(
    session_id: str = Depends(session_id_dep),
    store=Depends(_store_dep),
) -> dict:
    data = store.export_session(session_id)
    session = data["session"]
    lines = [
        f"# Disha chat export",
        f"Session: {session['session_id']}",
        f"Language: {session['language']}",
        f"Created: {session['created_at']}",
        "",
    ]
    for m in data["messages"]:
        who = "You" if m["role"] == "user" else "Disha"
        lines.append(f"**{who}** ({m['created_at']})")
        lines.append("")
        lines.append(m["text"])
        lines.append("")
    return {
        "session_id": session_id,
        "markdown": "\n".join(lines),
        "raw": data,
    }


@router.post("/feedback", response_model=ChatFeedbackResponse)
def feedback(
    body: ChatFeedbackRequest,
    session_id: str = Depends(session_id_dep),
    store=Depends(_store_dep),
) -> ChatFeedbackResponse:
    store.save_feedback(
        feedback_id=body.feedback_id,
        message_id=body.message_id,
        session_id=session_id,
        rating=body.rating.value,
        reason=body.reason,
        comment=body.comment,
    )
    return ChatFeedbackResponse(recorded=True)
