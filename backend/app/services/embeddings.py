"""HuggingFace Inference wrappers for BAAI/bge-m3 embeddings and
BAAI/bge-reranker-v2-m3 cross-encoder reranker.

HuggingFace replaced the classic api-inference.huggingface.co endpoint with
the router.huggingface.co provider-routing system. We use:
  - huggingface_hub.InferenceClient for embeddings (library handles routing)
  - direct POST to router.huggingface.co for the reranker (cross-encoder
    text-classification pipeline — InferenceClient has no first-class rerank).

bge-m3 embedding dimension: 1024.

If HF_API_KEY is not set, every method raises DishaError(EMBEDDING_UNAVAILABLE)
and the chat router falls back to LLM-only cleanly.
"""
from __future__ import annotations

import logging
from functools import lru_cache

import httpx
import numpy as np
from huggingface_hub import InferenceClient

from app.config import Settings
from app.errors import DishaError, ErrorCode

_log = logging.getLogger("disha.embeddings")

BGE_M3_DIMENSION = 1024

_RERANK_BASE = "https://router.huggingface.co/hf-inference/models"


def _require_key(settings: Settings) -> str:
    if not settings.hf_api_key:
        raise DishaError(
            ErrorCode.EMBEDDING_UNAVAILABLE,
            "Embedding service is not configured on the server.",
            status_code=503,
        )
    return settings.hf_api_key


@lru_cache(maxsize=1)
def _client_cached(api_key: str) -> InferenceClient:
    return InferenceClient(api_key=api_key)


def embed_texts(settings: Settings, texts: list[str]) -> list[list[float]]:
    """Batch-embed texts through bge-m3. Returns list of 1024-dim vectors."""
    key = _require_key(settings)
    if not texts:
        return []
    client = _client_cached(key)
    try:
        raw = client.feature_extraction(texts, model=settings.hf_embedding_model)
    except Exception as e:  # noqa: BLE001
        _log.exception("HF feature_extraction failed")
        raise DishaError(
            ErrorCode.EMBEDDING_UNAVAILABLE,
            "Embedding service did not respond.",
            status_code=503,
            details={"reason": str(e)},
        ) from e

    arr = np.asarray(raw)
    # Single input → shape (1024,). Batch → shape (N, 1024).
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2 or arr.shape[1] != BGE_M3_DIMENSION:
        raise DishaError(
            ErrorCode.EMBEDDING_UNAVAILABLE,
            f"Unexpected embedding shape {arr.shape}.",
            status_code=502,
        )
    return arr.tolist()


def rerank(
    settings: Settings, query: str, passages: list[str], top_k: int | None = None
) -> list[tuple[int, float]]:
    """Cross-encode (query, passage) pairs; return (index, score) desc by score."""
    key = _require_key(settings)
    if not passages:
        return []

    url = f"{_RERANK_BASE}/{settings.hf_reranker_model}"
    headers = {"Authorization": f"Bearer {key}"}
    payload = {
        "inputs": [{"text": query, "text_pair": p} for p in passages],
        "options": {"wait_for_model": True},
    }
    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=60.0)
    except httpx.HTTPError as e:
        _log.exception("HF reranker request failed")
        raise DishaError(
            ErrorCode.EMBEDDING_UNAVAILABLE,
            "Reranker service did not respond.",
            status_code=503,
            details={"reason": str(e)},
        ) from e
    if resp.status_code != 200:
        raise DishaError(
            ErrorCode.EMBEDDING_UNAVAILABLE,
            f"Reranker service returned HTTP {resp.status_code}.",
            status_code=503,
            details={"body": resp.text[:200]},
        )
    data = resp.json()
    # Observed shape: [[{label, score}, {label, score}, ...]]  — one outer
    # batch wrapping all N pair scores. Fall back to flatter shapes defensively.
    flat: list = []
    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], list):
        flat = data[0]
    elif isinstance(data, list):
        flat = data

    scores: list[float] = []
    for item in flat:
        if isinstance(item, dict):
            scores.append(float(item.get("score", 0.0)))
        elif isinstance(item, list) and item and isinstance(item[0], dict):
            scores.append(float(item[0].get("score", 0.0)))
        else:
            scores.append(0.0)

    if len(scores) != len(passages):
        raise DishaError(
            ErrorCode.EMBEDDING_UNAVAILABLE,
            "Unexpected response from reranker service.",
            status_code=502,
        )

    ranked = sorted(enumerate(scores), key=lambda t: t[1], reverse=True)
    if top_k is not None:
        ranked = ranked[:top_k]
    return [(i, s) for i, s in ranked]
