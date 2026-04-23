import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

from app.config import Settings, get_settings
from app.dependencies import optional_session_id_dep
from app.errors import DishaError, ErrorCode
from app.models.schemas import (
    FileStateResponse,
    FileStatus,
    FileSummarizeRequest,
    FileSummary,
    FileType,
    FileUploadResponse,
)
from app.services.file_summary import summarise_ocr_text, summary_to_dict
from app.services.ocr import run_ocr
from app.services.session_store import get_session_store

router = APIRouter(prefix="/files", tags=["files"])

_log = logging.getLogger("disha.files")

_EXT_TO_TYPE: dict[str, FileType] = {
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".jpg": FileType.IMAGE,
    ".jpeg": FileType.IMAGE,
    ".png": FileType.IMAGE,
    ".webp": FileType.IMAGE,
    ".tiff": FileType.IMAGE,
    ".tif": FileType.IMAGE,
}


def _store_dep(settings: Settings = Depends(get_settings)):
    return get_session_store(settings)


def _detect_type(filename: str) -> FileType:
    ext = Path(filename).suffix.lower()
    if ext not in _EXT_TO_TYPE:
        raise DishaError(
            ErrorCode.UNSUPPORTED_FILE_TYPE,
            "Only PDF, DOCX, and common image formats are supported.",
            status_code=415,
            details={"received_extension": ext},
        )
    return _EXT_TO_TYPE[ext]


def _ocr_background(
    settings: Settings,
    file_id: str,
    path: str,
    ftype: str,
    language: str,
) -> None:
    from app.models.schemas import Language as LangEnum

    store = get_session_store(settings)
    try:
        store.update_file(file_id, status=FileStatus.OCR_PROCESSING.value)
        text = run_ocr(settings, path, ftype, LangEnum(language))
        store.update_file(
            file_id,
            ocr_text=text,
            status=FileStatus.SUMMARIZING.value,
            language=language,
        )
        summary = summarise_ocr_text(text, LangEnum(language), settings=settings)
        store.update_file(
            file_id,
            summary_json=json.dumps(summary_to_dict(summary)),
            status=FileStatus.DONE.value,
        )
    except DishaError as e:
        _log.warning("file %s OCR failed: %s", file_id, e.message)
        store.update_file(file_id, status=FileStatus.FAILED.value, error=e.message)
    except Exception as e:  # noqa: BLE001
        _log.exception("file %s unexpected error", file_id)
        store.update_file(file_id, status=FileStatus.FAILED.value, error=str(e))


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    session_id: str | None = Depends(optional_session_id_dep),
    store=Depends(_store_dep),
) -> FileUploadResponse:
    ftype = _detect_type(file.filename or "")

    file_id = str(uuid.uuid4())
    dest = Path(settings.upload_dir) / f"{file_id}_{Path(file.filename or 'upload').name}"
    dest.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 64):
            total += len(chunk)
            if total > settings.max_file_size_bytes:
                dest.unlink(missing_ok=True)
                raise DishaError(
                    ErrorCode.FILE_TOO_LARGE,
                    f"File exceeds {settings.max_file_size_mb} MB limit.",
                    status_code=413,
                )
            out.write(chunk)

    store.save_file_record(
        file_id=file_id,
        session_id=session_id,
        filename=file.filename or dest.name,
        path=str(dest),
        ftype=ftype.value,
        size_bytes=total,
    )

    background_tasks.add_task(
        _ocr_background,
        settings,
        file_id,
        str(dest),
        ftype.value,
        "en",
    )

    return FileUploadResponse(
        file_id=file_id,
        filename=file.filename or dest.name,
        size_bytes=total,
        type=ftype,
        status=FileStatus.QUEUED,
    )


@router.get("/{file_id}", response_model=FileStateResponse)
def get_file_state(
    file_id: str,
    store=Depends(_store_dep),
) -> FileStateResponse:
    row = store.get_file(file_id)
    summary = None
    if row.get("summary_json"):
        summary = FileSummary.model_validate_json(row["summary_json"])
    return FileStateResponse(
        file_id=file_id,
        status=FileStatus(row["status"]),
        ocr_text=row.get("ocr_text"),
        summary=summary,
        error=row.get("error"),
    )


@router.post("/{file_id}/summarize", response_model=FileStateResponse)
def resummarise(
    file_id: str,
    body: FileSummarizeRequest,
    settings: Settings = Depends(get_settings),
    store=Depends(_store_dep),
) -> FileStateResponse:
    from app.models.schemas import Language as LangEnum

    row = store.get_file(file_id)
    ocr_text = row.get("ocr_text") or ""
    if not ocr_text:
        raise DishaError(
            ErrorCode.INVALID_INPUT,
            "No OCR text available — file not yet processed.",
            status_code=409,
        )
    summary = summarise_ocr_text(ocr_text, LangEnum(body.language), settings=settings)
    store.update_file(
        file_id,
        summary_json=json.dumps(summary_to_dict(summary)),
        language=body.language.value,
        status=FileStatus.DONE.value,
    )
    return FileStateResponse(
        file_id=file_id,
        status=FileStatus.DONE,
        ocr_text=ocr_text,
        summary=summary,
    )
