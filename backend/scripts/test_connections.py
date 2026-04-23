"""Smoke tests for external API credentials.

Run:  python -m scripts.test_connections
from the backend directory. Uses env vars from .env.

Exits non-zero on any failure. Output is human-readable, one line per
service: ✓ for OK, ✗ for failure with reason.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running this as a script from backend/ without needing to install the package.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402


def _ok(name: str, detail: str = "") -> None:
    msg = f"  OK  {name}"
    if detail:
        msg += f"  —  {detail}"
    print(msg)


def _fail(name: str, detail: str) -> bool:
    print(f"  FAIL  {name}  —  {detail}")
    return False


def test_groq() -> bool:
    settings = get_settings()
    if not settings.groq_api_key:
        return _fail("Groq", "GROQ_API_KEY missing in .env")
    try:
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)
        resp = client.chat.completions.create(
            model=settings.groq_model_fast,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            temperature=0.0,
        )
        text = (resp.choices[0].message.content or "").strip()
        _ok("Groq", f"{settings.groq_model_fast} replied: {text!r}")
        return True
    except Exception as e:  # noqa: BLE001
        return _fail("Groq", str(e))


def test_qdrant() -> bool:
    settings = get_settings()
    if not settings.qdrant_url or not settings.qdrant_api_key:
        return _fail("Qdrant", "QDRANT_URL or QDRANT_API_KEY missing")
    try:
        from qdrant_client import QdrantClient

        c = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        cols = [col.name for col in c.get_collections().collections]
        _ok("Qdrant", f"reachable, {len(cols)} collection(s): {cols or '[]'}")
        return True
    except Exception as e:  # noqa: BLE001
        return _fail("Qdrant", str(e))


def test_hf() -> bool:
    settings = get_settings()
    if not settings.hf_api_key:
        return _fail("HuggingFace", "HF_API_KEY missing")
    try:
        from app.services.embeddings import embed_texts, rerank

        vecs = embed_texts(settings, ["hello"])
        dim = len(vecs[0]) if vecs else 0
        ranked = rerank(
            settings,
            "sickle cell disease",
            ["Sickle cell is a blood disorder.", "Bananas are yellow."],
        )
        _ok(
            "HuggingFace",
            f"embed dim={dim}, rerank top={ranked[0]} (bge-m3 + bge-reranker-v2-m3)",
        )
        return True
    except Exception as e:  # noqa: BLE001
        return _fail("HuggingFace", str(e))


def test_ocr_space() -> bool:
    settings = get_settings()
    if not settings.ocr_space_api_key:
        return _fail("OCR.space", "OCR_SPACE_API_KEY missing")
    try:
        import httpx

        resp = httpx.post(
            settings.ocr_space_endpoint,
            data={
                "apikey": settings.ocr_space_api_key,
                "url": "https://dl.a9t9.com/ocrbenchmark/eng.png",
                "language": "eng",
                "OCREngine": "2",
            },
            timeout=60.0,
        )
        body = resp.json()
        if body.get("IsErroredOnProcessing"):
            return _fail("OCR.space", str(body.get("ErrorMessage")))
        parsed = (body.get("ParsedResults") or [{}])[0].get("ParsedText", "").strip()
        _ok("OCR.space", f"parsed {len(parsed)} chars")
        return True
    except Exception as e:  # noqa: BLE001
        return _fail("OCR.space", str(e))


def test_google_maps() -> bool:
    settings = get_settings()
    if not settings.google_maps_api_key:
        return _fail("Google Maps", "GOOGLE_MAPS_API_KEY missing (skippable for now)")
    try:
        import httpx

        # Geocode a known location to validate the key.
        resp = httpx.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": "Mumbai", "key": settings.google_maps_api_key},
            timeout=20.0,
        )
        data = resp.json()
        if data.get("status") != "OK":
            return _fail("Google Maps", f"{data.get('status')}: {data.get('error_message', '')}")
        _ok("Google Maps", "geocoding reachable")
        return True
    except Exception as e:  # noqa: BLE001
        return _fail("Google Maps", str(e))


def main() -> int:
    print("Disha backend — credential smoke tests")
    print("=" * 42)
    results = [
        test_groq(),
        test_qdrant(),
        test_hf(),
        test_ocr_space(),
        test_google_maps(),
    ]
    print("=" * 42)
    total = len(results)
    passed = sum(1 for r in results if r)
    print(f"{passed}/{total} services reachable")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
