import hashlib
from contextlib import asynccontextmanager
from email import message
from typing import List

from app.api.v1 import airports, auth, flight
from app.clients.exceptions import ExternalProviderError
from app.db.database import close_db, get_db, init_db
from app.utils.cache import FlightCache, get_flight_cache
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Flight Backend API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    redoc_url="/api/v1/redoc",
)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# global exception handler for ExternalProviderError
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
app.include_router(airports.router, prefix="/api/v1")


@app.get("/dev/cache-inspect")
async def inspect_cache(cache: FlightCache = Depends(get_flight_cache)):
    # Note: We return the raw _storage dictionary
    # We use a dict comprehension to make it readable
    return {
        "count": len(cache._storage),
        "keys": list(cache._storage.keys()),
        "data": cache._storage,
    }
