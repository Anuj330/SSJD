import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# ✅ ABSOLUTE imports only
from app.api.urls import router as api_router
from app.api import auth, society
from app.core.limiter import limiter
from app.core.logging import setup_logging
from app.services.scheduler import start_scheduler, stop_scheduler

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background scheduler on startup, stop on shutdown."""
    logger.info("Application starting up")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Application shutting down")


app = FastAPI(title="SSJD Backend", lifespan=lifespan)

# Rate limiting (slowapi)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Log the full error server-side, return a clean generic message to clients."""
    logger.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(api_router)
app.include_router(auth.router)
app.include_router(society.router)
