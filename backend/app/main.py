import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.v1.router import api_v1_router
from app.config import get_settings
from app.errors import register_error_handlers
from app.middleware import register_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings.ensure_dirs()
    logging.getLogger("disha").info(
        "Disha backend v%s starting in %s mode", __version__, settings.app_env
    )
    yield
    logging.getLogger("disha").info("Disha backend shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Disha — Genetic Counselling Chatbot API",
        description=(
            "Backend for the Disha chatbot (SickleSetu platform). "
            "Multilingual (English / Hindi / Marathi), RAG-first, "
            "Groq fallback, OCR-enabled document summarisation."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    register_middleware(app, settings.frontend_origin)
    register_error_handlers(app)
    app.include_router(api_v1_router, prefix="/api/v1")
    return app


app = create_app()
