import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

log = logging.getLogger("disha.request")


async def request_id_and_timing(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("unhandled in middleware req_id=%s path=%s", req_id, request.url.path)
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.1f}"
    log.info(
        "%s %s -> %d in %.1fms req_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        req_id,
    )
    return response


def register_middleware(app: FastAPI, frontend_origin: str) -> None:
    # FRONTEND_ORIGIN can be a comma-separated list so production can allow
    # both the Vercel URL and any preview deployments without a redeploy.
    origins = [o.strip() for o in (frontend_origin or "").split(",") if o.strip()]
    # Always keep local dev ports working regardless of env config.
    for dev in ("http://localhost:5173", "http://localhost:5175", "http://localhost:3000"):
        if dev not in origins:
            origins.append(dev)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
    )
    app.middleware("http")(request_id_and_timing)
