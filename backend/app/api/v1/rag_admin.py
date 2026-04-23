from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.dependencies import admin_key_dep
from app.models.schemas import (
    RagIngestRequest,
    RagIngestResponse,
    RagStatsResponse,
    RagCollectionStats,
    Disease,
)
from app.services import rag as rag_service

router = APIRouter(prefix="/rag", tags=["rag-admin"])


@router.post("/ingest", response_model=RagIngestResponse)
def ingest(
    body: RagIngestRequest,
    settings: Settings = Depends(get_settings),
    _: None = Depends(admin_key_dep),
) -> RagIngestResponse:
    rag_service.ensure_collection(settings)
    chunks = [
        {"text": c.text, "metadata": c.metadata.model_dump(mode="json")}
        for c in body.chunks
    ]
    ids, failed = rag_service.upsert_chunks(settings, body.disease, chunks)
    return RagIngestResponse(ingested=len(ids), failed=failed, chunk_ids=ids)


@router.get("/stats", response_model=RagStatsResponse)
def stats(
    settings: Settings = Depends(get_settings),
    _: None = Depends(admin_key_dep),
) -> RagStatsResponse:
    raw = rag_service.stats(settings)
    return RagStatsResponse(
        collections=[
            RagCollectionStats(
                disease=Disease.SICKLE_CELL,
                total_chunks=r["total_chunks"],
                by_language=r["by_language"],
                by_source=r["by_source"],
            )
            for r in raw
        ]
    )
