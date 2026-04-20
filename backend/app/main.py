import logging
from contextlib import asynccontextmanager

from app.api.v1 import airports, auth, flight, flight_booking
from app.clients.exceptions import ExternalProviderError
from app.core.http_logging import RequestResponseLoggingMiddleware
from app.core.logging import setup_logging
from app.utils.cache import FlightCache, flight_cache, get_flight_cache
from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Flight Backend API")
    yield
    logger.info("Shutting down Flight Backend API")
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
app.add_middleware(RequestResponseLoggingMiddleware)

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

