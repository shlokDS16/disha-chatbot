"""Seed the Qdrant collection with the curated FAQ corpus.

Run:  python -m scripts.seed_rag
from the backend directory, after HF_API_KEY is set.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.models.schemas import Disease  # noqa: E402
from app.services import rag as rag_service  # noqa: E402


def main() -> int:
    settings = get_settings()
    seed_path = Path(settings.data_dir) / "seed" / "sickle_cell_faq.json"
    if not seed_path.exists():
        print(f"FAIL: seed file not found at {seed_path}")
        return 1

    with seed_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    disease = Disease(payload["disease"])
    chunks = payload["chunks"]
    print(f"Seeding {len(chunks)} chunks into '{settings.qdrant_collection}' for {disease.value}...")

    try:
        rag_service.ensure_collection(settings)
        ids, failed = rag_service.upsert_chunks(settings, disease, chunks)
        print(f"OK: ingested {len(ids)}, failed {failed}")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"FAIL: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
