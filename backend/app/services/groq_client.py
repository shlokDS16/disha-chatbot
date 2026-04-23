"""Groq chat completion wrapper.

Two model tiers:
  - llama-3.3-70b-versatile: main reasoning model for chat.
  - llama-3.1-8b-instant: fast model for language detect fallback / crisis
    classification / triage tasks where latency matters more than depth.

If GROQ_API_KEY is missing, LLM_UNAVAILABLE is raised.
"""
from __future__ import annotations

import logging
from typing import Any

from groq import Groq

from app.config import Settings
from app.errors import DishaError, ErrorCode

_log = logging.getLogger("disha.groq")


def _client(settings: Settings) -> Groq:
    if not settings.groq_api_key:
        raise DishaError(
            ErrorCode.LLM_UNAVAILABLE,
            "LLM service is not configured on the server.",
            status_code=503,
        )
    return Groq(api_key=settings.groq_api_key)


def chat_complete(
    settings: Settings,
    system_prompt: str,
    user_text: str,
    prior_messages: list[dict[str, str]] | None = None,
    kb_context: str | None = None,
    fast: bool = False,
    max_tokens: int = 800,
    temperature: float = 0.4,
) -> tuple[str, dict[str, Any]]:
    """Return (answer_text, meta)."""
    client = _client(settings)
    model = settings.groq_model_fast if fast else settings.groq_model_primary

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if prior_messages:
        messages.extend(prior_messages)
    user_payload = user_text
    if kb_context:
        user_payload = f"{kb_context}\n\nUser question: {user_text}"
    messages.append({"role": "user", "content": user_payload})

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except Exception as e:  # noqa: BLE001
        _log.exception("Groq completion failed")
        raise DishaError(
            ErrorCode.LLM_UNAVAILABLE,
            "LLM service failed to respond.",
            status_code=503,
            details={"reason": str(e)},
        ) from e

    choice = resp.choices[0]
    text = (choice.message.content or "").strip()
    usage = getattr(resp, "usage", None)
    meta: dict[str, Any] = {
        "model": model,
        "finish_reason": choice.finish_reason,
        "usage": (
            {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
            if usage
            else None
        ),
    }
    return text, meta
