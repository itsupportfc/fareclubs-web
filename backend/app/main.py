import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path

from app.api.v1 import airports, auth, flight, flight_booking
from app.clients.exceptions import ExternalProviderError
from app.config import settings
from app.utils.cache import FlightCache, flight_cache, get_flight_cache
from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware

backend_root = Path(__file__).resolve().parents[1]
if backend_root.name.lower() == "backend":
    default_logs_dir = backend_root.parent / "logs"
else:
    default_logs_dir = backend_root / "logs"
logs_dir = (
    Path(settings.BACKEND_LOG_DIR) if settings.BACKEND_LOG_DIR else default_logs_dir
)
log_file = (
    Path(settings.BACKEND_LOG_FILE)
    if settings.BACKEND_LOG_FILE
    else logs_dir / "backend.log"
)
log_file.parent.mkdir(parents=True, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": str(log_file),
            "mode": "a",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Redis connects lazily on first use
    yield
    # Shutdown: close Redis connection pool
    await flight_cache.close()


app = FastAPI(
    title="Flight Backend API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )


@app.exception_handler(ExternalProviderError)
async def external_provider_exception_handler(request, exc: ExternalProviderError):
    return JSONResponse(
        status_code=exc.http_status or status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": exc.message,
            "provider": exc.provider,
            "provider_code": exc.provider_code,
        },
    )


app.include_router(auth.router, prefix="/api/v1")
app.include_router(flight.router, prefix="/api/v1")
app.include_router(flight_booking.router, prefix="/api/v1")
app.include_router(airports.router, prefix="/api/v1")


@app.get("/dev/cache-inspect")
async def inspect_cache(cache: FlightCache = Depends(get_flight_cache)):
    try:
        keys = await cache._redis.keys("*")
        data = {}
        for k in keys:
            raw = await cache._redis.get(k)
            data[k] = raw[:200] if raw else None
        return {"count": len(keys), "keys": keys, "data": data}
    except Exception as e:
        return {"error": str(e)}
