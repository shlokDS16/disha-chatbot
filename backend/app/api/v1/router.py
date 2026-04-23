from fastapi import APIRouter

from app.api.v1 import (
    chat,
    content,
    facilities,
    files,
    language,
    meta,
    privacy,
    rag_admin,
    session,
    tools,
    voice,
)

api_v1_router = APIRouter()

api_v1_router.include_router(meta.router)
api_v1_router.include_router(session.router)
api_v1_router.include_router(tools.router)
api_v1_router.include_router(language.router)
api_v1_router.include_router(files.router)
api_v1_router.include_router(content.router)
api_v1_router.include_router(facilities.router)
api_v1_router.include_router(voice.router)
api_v1_router.include_router(chat.router)
api_v1_router.include_router(privacy.router)
api_v1_router.include_router(rag_admin.router)
