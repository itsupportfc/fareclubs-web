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
    allow_origins=["http://localhost:5173"],  # change in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
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
    from app.core.request_context import get_request_id

    request_id = get_request_id()

    # Log full provider details for internal debugging
    # Provider Internals should not be Leaked in Error Responses
    logger.error(
        "Provider error [request_id=%s] provider=%s code=%s message=%s",
        request_id,
        exc.provider,
        exc.provider_code,
        exc.message,
    )

    return JSONResponse(
        status_code=exc.http_status or status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": exc.message,  # This should already be user-friendly
            "request_id": request_id,
        },
    )


# catch-all exception handler
@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    # Import here to avoid circular imports
    from app.core.request_context import get_request_id

    request_id = get_request_id()
    logger.exception(
        "Unhandled exception [request_id=%s] %s %s",
        request_id,
        request.method,
        request.url.path,
    )
    # The client gets a user-friendly message + a `request_id` they can share with support
    # You search your logs for that `request_id` to find the exact stack trace
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again or contact support.",
            "request_id": request_id,
        },
    )


app.include_router(auth.router, prefix="/api/v1")
app.include_router(flight.router, prefix="/api/v1")
app.include_router(flight_booking.router, prefix="/api/v1")
app.include_router(airports.router, prefix="/api/v1")

