"""Voice endpoints.

For the prototype we rely on the browser's Web Speech API for STT (microphone
→ text happens in the frontend). This TTS endpoint uses gTTS as a simple
server-side fallback so Marathi/Hindi playback works even on browsers whose
native TTS has poor IN-language voices.

If a file can't be produced, we return a structured error; the frontend then
falls back to the browser's speechSynthesis.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from app.config import Settings, get_settings
from app.errors import DishaError, ErrorCode
from app.models.schemas import (
    Language,
    VoiceSynthesizeRequest,
    VoiceSynthesizeResponse,
    VoiceTranscribeResponse,
)

router = APIRouter(prefix="/voice", tags=["voice"])
_log = logging.getLogger("disha.voice")


_GTTS_LANG: dict[Language, str] = {
    Language.EN: "en",
    Language.HI: "hi",
    Language.MR: "mr",
}


@router.post("/transcribe", response_model=VoiceTranscribeResponse)
async def transcribe(
    audio: UploadFile = File(...),
    _settings: Settings = Depends(get_settings),
) -> VoiceTranscribeResponse:
    """Placeholder — real STT is performed in-browser via Web Speech API.

    We return a 501-equivalent structured error. Browsers that support Web
    Speech should never call this endpoint; it exists for future server-side
    STT (e.g. AI4Bharat IndicWav2Vec) without changing the frontend contract.
    """
    _ = await audio.read(1)  # consume one byte to signal we received the upload
    raise DishaError(
        ErrorCode.FEATURE_NOT_CONFIGURED,
        "Server-side transcription is not enabled. Use the browser's built-in voice input.",
        status_code=501,
    )


@router.post("/synthesize", response_model=VoiceSynthesizeResponse)
def synthesize(
    body: VoiceSynthesizeRequest,
    settings: Settings = Depends(get_settings),
) -> VoiceSynthesizeResponse:
    try:
        from gtts import gTTS
    except ImportError as e:
        raise DishaError(
            ErrorCode.FEATURE_NOT_CONFIGURED,
            "TTS library is not installed.",
            status_code=501,
        ) from e

    audio_id = str(uuid.uuid4())
    out_path = Path(settings.storage_dir) / "audio"
    out_path.mkdir(parents=True, exist_ok=True)
    mp3_path = out_path / f"{audio_id}.mp3"

    try:
        tts = gTTS(text=body.text, lang=_GTTS_LANG[body.language])
        tts.save(str(mp3_path))
    except Exception as e:  # noqa: BLE001
        _log.exception("gTTS synthesis failed")
        raise DishaError(
            ErrorCode.FEATURE_NOT_CONFIGURED,
            "Could not synthesise audio right now.",
            status_code=503,
            details={"reason": str(e)},
        ) from e

    # Rough duration estimate: gTTS speech ~13 chars/sec at default rate.
    approx_sec = max(1.0, len(body.text) / 13.0)
    # Return a relative path; the frontend will join with the API base.
    return VoiceSynthesizeResponse(
        audio_url=f"/api/v1/voice/audio/{audio_id}.mp3",
        duration_sec=round(approx_sec, 1),
    )


@router.get("/audio/{filename}")
def get_audio(filename: str, settings: Settings = Depends(get_settings)):
    from fastapi.responses import FileResponse

    path = Path(settings.storage_dir) / "audio" / filename
    if not path.exists():
        raise DishaError(
            ErrorCode.FILE_NOT_FOUND,
            "Audio not found.",
            status_code=404,
        )
    return FileResponse(str(path), media_type="audio/mpeg")
