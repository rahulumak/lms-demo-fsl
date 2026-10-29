import logging
from collections import defaultdict
from time import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import router

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LMS API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
def on_startup():
    from app.db.base import create_tables
    create_tables()


# ── Simple in-process rate limiter (no external deps) ─────────────────────────
_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMITED_PATHS = {"/api/v1/auth/login": 10, "/api/v1/auth/register": 20}  # req/min


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    limit = _RATE_LIMITED_PATHS.get(path)
    if limit:
        ip = request.client.host if request.client else "unknown"
        # Skip rate limiting for testclient (127.0.0.1 / testclient)
        if ip not in ("testclient", "127.0.0.1"):
            key = f"{ip}:{path}"
            now = time()
            window = 60.0
            _rate_store[key] = [t for t in _rate_store[key] if now - t < window]
            if len(_rate_store[key]) >= limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please wait a moment and try again."},
                )
            _rate_store[key].append(now)
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health/live", tags=["health"])
def health_live():
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def health_ready():
    from sqlalchemy import text
    from app.db.base import engine
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database unavailable")
