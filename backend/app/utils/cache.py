"""
Redis-backed flight cache with Pydantic model support.

Why Redis instead of in-memory dict:
  - Shared state across multiple uvicorn workers / containers
  - Survives container restarts
  - Inspectable via redis-cli

get()/set() handle plain JSON-serializable dicts.
set_model()/get_model() handle Pydantic BaseModel objects (e.g. TBOSSRResponse).
"""

import json
import logging
from typing import Any, Optional, Type, TypeVar

# this is the async version of redis
import redis.asyncio as aioredis
from app.config import settings

# redis supports storing pydantic models directly
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# generic type for pydantic models
# T must be a BaseModel
T = TypeVar("T", bound=BaseModel)


class FlightCache:
    def __init__(self, redis_url: str):
        # decode_responses=True → get str instead of bytes, simpler for JSON
        self._redis: aioredis.Redis = aioredis.from_url(
            redis_url,
            decode_responses=True,
        )

    # --- Plain dict get/set (fare_id → provider_ref mapping, flags, etc.) ---
    # after 900 seconds => redis will auto-delete the key, no need for manual cleanup
    async def set(self, fare_id: str, data: Any, ttl: int = 900) -> None:
        try:
            # setex => set key with expiry
            # json.dumps(data) => convert python dict to JSON string for storage
            await self._redis.setex(fare_id, ttl, json.dumps(data))
        except Exception:
            logger.warning("Redis SET failed for key=%s", fare_id, exc_info=True)

    async def get(self, fare_id: str) -> Optional[Any]:
        try:
            raw = await self._redis.get(fare_id)
            if raw is None:
                return None
            # deserialize JSON
            return json.loads(raw)
        except Exception:
            logger.warning("Redis GET failed for key=%s", fare_id, exc_info=True)
            return None

    # --- Pydantic model get/set (TBOSSRResponse caching) ---

    async def set_model(self, key: str, model: BaseModel, ttl: int = 900) -> None:
        """Store a Pydantic model. Uses model_dump_json() for correct datetime/enum handling."""
        try:
            # model_dump_json => as pydantic model may have datetime/enum fields that aren't natively JSON-serializable
            await self._redis.setex(key, ttl, model.model_dump_json())
        except Exception:
            logger.warning("Redis SET_MODEL failed for key=%s", key, exc_info=True)

    async def get_model(self, key: str, model_class: Type[T]) -> Optional[T]:
        """Retrieve and reconstruct a Pydantic model from cached JSON."""
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            # Rebuild Pydantic Model
            return model_class.model_validate_json(raw)
        except Exception:
            logger.warning("Redis GET_MODEL failed for key=%s", key, exc_info=True)
            return None

    async def close(self) -> None:
        await self._redis.close()


# Singleton instance
flight_cache = FlightCache(redis_url=settings.REDIS_URL)


def get_flight_cache() -> FlightCache:
    """FastAPI Depends() resolver."""
    return flight_cache
