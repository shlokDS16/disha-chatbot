"""Qdrant-backed retrieval + auto-enrichment.

Single collection `disha_knowledge`. Each chunk has metadata:
  disease, audience, scenario, topic, language, source, confidence.

Search flow:
  1. embed query with bge-m3
  2. Qdrant search with vector + payload filter (disease, language optional)
  3. rerank top-20 with bge-reranker-v2-m3, take top-5
  4. caller decides RAG-only vs RAG+LLM vs LLM-only based on top score

Auto-enrichment flow:
  1. LLM-only answer was produced
  2. quality gate: answer length >= auto_enrich_min_answer_len, no refusal tokens
  3. embed Q+A together, upsert into Qdrant with source="auto_enriched",
     confidence=0.6
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import Settings
from app.errors import DishaError, ErrorCode
from app.models.schemas import Disease, Language, Persona
from app.services.embeddings import BGE_M3_DIMENSION, embed_texts, rerank

_log = logging.getLogger("disha.rag")


_REFUSAL_TOKENS = (
    "i don't know",
    "i'm not sure",
    "i cannot help",
    "as an ai",
    "मुझे नहीं पता",
    "मला माहित नाही",
)


def _client(settings: Settings) -> QdrantClient:
    if not settings.qdrant_url or not settings.qdrant_api_key:
        raise DishaError(
            ErrorCode.FEATURE_NOT_CONFIGURED,
            "Vector DB is not configured.",
            status_code=503,
        )
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def ensure_collection(settings: Settings) -> None:
    c = _client(settings)
    existing = [col.name for col in c.get_collections().collections]
    if settings.qdrant_collection in existing:
        return
    c.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qmodels.VectorParams(
            size=BGE_M3_DIMENSION, distance=qmodels.Distance.COSINE
        ),
    )
    for field in ("disease", "language", "source", "audience"):
        c.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name=field,
            field_schema=qmodels.PayloadSchemaType.KEYWORD,
        )


def _build_filter(
    disease: Disease, language: Language | None, persona: Persona | None
) -> qmodels.Filter:
    must: list[qmodels.FieldCondition] = [
        qmodels.FieldCondition(
            key="disease", match=qmodels.MatchValue(value=disease.value)
        )
    ]
    if language:
        must.append(
            qmodels.FieldCondition(
                key="language", match=qmodels.MatchValue(value=language.value)
            )
        )
    should: list[qmodels.FieldCondition] = []
    if persona:
        should.append(
            qmodels.FieldCondition(
                key="audience", match=qmodels.MatchAny(any=[persona.value])
            )
        )
    return qmodels.Filter(must=must, should=should)


def search(
    settings: Settings,
    query: str,
    disease: Disease,
    language: Language | None,
    persona: Persona | None,
    top_k: int = 20,
    rerank_k: int = 5,
) -> list[dict[str, Any]]:
    c = _client(settings)
    vectors = embed_texts(settings, [query])
    if not vectors:
        return []
    try:
        result = c.query_points(
            collection_name=settings.qdrant_collection,
            query=vectors[0],
            query_filter=_build_filter(disease, language, persona),
            limit=top_k,
            with_payload=True,
        )
    except Exception as e:  # noqa: BLE001
        # Qdrant unreachable (DNS/auth/timeout) — degrade silently so the
        # caller can fall back to LLM-only mode.
        _log.warning("qdrant query_points failed: %s", e)
        return []
    hits = result.points
    if not hits:
        return []

    passages = [h.payload.get("text", "") for h in hits]  # type: ignore[union-attr]
    try:
        ranked = rerank(settings, query, passages, top_k=rerank_k)
    except Exception as e:  # noqa: BLE001
        _log.warning("reranker failed, using raw qdrant order: %s", e)
        ranked = [(i, float(hits[i].score)) for i in range(min(rerank_k, len(hits)))]
    results: list[dict[str, Any]] = []
    for orig_idx, rerank_score in ranked:
        h = hits[orig_idx]
        payload: dict[str, Any] = dict(h.payload or {})
        results.append(
            {
                "chunk_id": str(h.id),
                "text": payload.get("text", ""),
                "score": float(h.score),
                "reranker_score": rerank_score,
                "metadata": {
                    k: v for k, v in payload.items() if k != "text"
                },
            }
        )
    return results


def upsert_chunks(
    settings: Settings,
    disease: Disease,
    chunks: list[dict[str, Any]],
) -> tuple[list[str], int]:
    """chunks: [{text, metadata: {...}}]. Returns (chunk_ids, failed_count)."""
    c = _client(settings)
    texts = [ch["text"] for ch in chunks]
    vectors = embed_texts(settings, texts)
    if len(vectors) != len(chunks):
        raise DishaError(
            ErrorCode.EMBEDDING_UNAVAILABLE,
            "Embedding count mismatch during ingest.",
            status_code=502,
        )
    points: list[qmodels.PointStruct] = []
    ids: list[str] = []
    for ch, vec in zip(chunks, vectors, strict=True):
        cid = str(uuid.uuid4())
        ids.append(cid)
        payload = {"text": ch["text"], "disease": disease.value, **ch.get("metadata", {})}
        points.append(qmodels.PointStruct(id=cid, vector=vec, payload=payload))
    c.upsert(collection_name=settings.qdrant_collection, points=points)
    return ids, 0


def should_auto_enrich(
    question: str, answer: str, settings: Settings, consent_enriches: bool
) -> bool:
    if not consent_enriches:
        return False
    if len(answer) < settings.auto_enrich_min_answer_len:
        return False
    lower = answer.lower()
    return not any(tok in lower for tok in _REFUSAL_TOKENS)


def auto_enrich(
    settings: Settings,
    disease: Disease,
    language: Language,
    question: str,
    answer: str,
    persona: Persona | None,
) -> str | None:
    try:
        combined = f"Q: {question}\nA: {answer}"
        ids, _ = upsert_chunks(
            settings,
            disease,
            [
                {
                    "text": combined,
                    "metadata": {
                        "language": language.value,
                        "audience": [persona.value] if persona else [],
                        "source": "auto_enriched",
                        "confidence": 0.6,
                        "topic": None,
                        "scenario": "qa",
                    },
                }
            ],
        )
        return ids[0] if ids else None
    except DishaError:
        _log.info("auto-enrich skipped: service unavailable")
        return None


def stats(settings: Settings) -> list[dict[str, Any]]:
    c = _client(settings)
    info = c.get_collection(settings.qdrant_collection)
    return [
        {
            "disease": "all",
            "total_chunks": info.points_count or 0,
            "by_language": {},
            "by_source": {},
        }
    ]
