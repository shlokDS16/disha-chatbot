from fastapi import APIRouter

from app import __version__
from app.models.schemas import (
    Disease,
    DiseaseInfo,
    DiseasesListResponse,
    HealthResponse,
    Language,
    LanguageInfo,
    LanguagesListResponse,
)

router = APIRouter(tags=["meta"])


_LANGUAGES = [
    LanguageInfo(code=Language.EN, name_native="English", name_english="English"),
    LanguageInfo(code=Language.HI, name_native="हिन्दी", name_english="Hindi"),
    LanguageInfo(code=Language.MR, name_native="मराठी", name_english="Marathi"),
]


_DISEASES = [
    DiseaseInfo(id=Disease.SICKLE_CELL, name_en="Sickle Cell Disease", active=True, faq_count=0),
    DiseaseInfo(id=Disease.THALASSEMIA, name_en="Thalassemia", active=False, faq_count=0),
]


@router.get("/")
def index() -> dict[str, str]:
    return {
        "name": "Disha API",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get("/meta/languages", response_model=LanguagesListResponse)
def list_languages() -> LanguagesListResponse:
    return LanguagesListResponse(languages=_LANGUAGES)


@router.get("/meta/diseases", response_model=DiseasesListResponse)
def list_diseases() -> DiseasesListResponse:
    return DiseasesListResponse(diseases=_DISEASES)
