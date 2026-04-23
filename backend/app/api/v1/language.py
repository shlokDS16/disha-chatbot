from fastapi import APIRouter

from app.models.schemas import LanguageDetectRequest, LanguageDetectResponse
from app.services.language_detect import detect_language

router = APIRouter(prefix="/language", tags=["language"])


@router.post("/detect", response_model=LanguageDetectResponse)
def detect(body: LanguageDetectRequest) -> LanguageDetectResponse:
    lang, confidence = detect_language(body.text)
    return LanguageDetectResponse(language=lang, confidence=confidence)
