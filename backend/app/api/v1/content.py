import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.dependencies import language_dep
from app.models.schemas import (
    CrisisData,
    CrisisHelpline,
    Severity,
    StarterChip,
    StarterChipsBlock,
)

router = APIRouter(prefix="/content", tags=["content"])


@lru_cache
def _load(filename: str) -> dict[str, Any]:
    settings = get_settings()
    path = Path(settings.data_dir) / "content" / filename
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/starter-chips")
def starter_chips(language: str = Depends(language_dep)) -> dict[str, Any]:
    data = _load("starter_chips.json")
    raw = data.get(language, data["en"])
    block = StarterChipsBlock(data={"chips": [StarterChip(**c) for c in raw]})
    return {"language": language, "block": block.model_dump(mode="json")}


@router.get("/health-tips")
def health_tips(language: str = Depends(language_dep)) -> dict[str, Any]:
    data = _load("health_tips.json")
    return {"language": language, "tips": data.get(language, data["en"])}


@router.get("/crisis-helplines")
def crisis_helplines(
    language: str = Depends(language_dep),
    _settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    data = _load("crisis_helplines.json")
    helplines = [CrisisHelpline(**h) for h in data["helplines"]]
    message = data["messages"].get(language, data["messages"]["en"])
    crisis = CrisisData(severity=Severity.CRITICAL, helplines=helplines, message=message)
    return {"language": language, "data": crisis.model_dump(mode="json")}


@router.get("/consent-copy")
def consent_copy(language: str = Depends(language_dep)) -> dict[str, Any]:
    data = _load("consent_copy.json")
    return {"language": language, "copy": data.get(language, data["en"])}
