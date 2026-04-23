"""Language detection for English / Hindi / Marathi.

Hindi and Marathi both use the Devanagari script, so we use the lingua
detector configured with exactly these three languages. Confidence is the
raw posterior from lingua for the top candidate.
"""
from __future__ import annotations

from functools import lru_cache

from lingua import Language as LinguaLanguage, LanguageDetectorBuilder

from app.models.schemas import Language

_LINGUA_TO_OURS: dict[LinguaLanguage, Language] = {
    LinguaLanguage.ENGLISH: Language.EN,
    LinguaLanguage.HINDI: Language.HI,
    LinguaLanguage.MARATHI: Language.MR,
}


@lru_cache(maxsize=1)
def _detector():
    return (
        LanguageDetectorBuilder.from_languages(
            LinguaLanguage.ENGLISH,
            LinguaLanguage.HINDI,
            LinguaLanguage.MARATHI,
        )
        .with_preloaded_language_models()
        .build()
    )


def detect_language(text: str) -> tuple[Language, float]:
    text = text.strip()
    if not text:
        return Language.EN, 0.0

    detector = _detector()
    values = detector.compute_language_confidence_values(text)
    if not values:
        return Language.EN, 0.0
    top = values[0]
    ours = _LINGUA_TO_OURS.get(top.language, Language.EN)
    return ours, float(top.value)
