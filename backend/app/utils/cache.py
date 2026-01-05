import time
from typing import Any, Optional


class FlightCache:
    # stores data as {"fare_id": {"data": ..., "expiry": ...}}
    def __init__(self):
        self._storage: dict[str, dict[str, Any]] = {}

    def set(self, fare_id: str, data: Any, ttl: int = 900):
        self._storage[fare_id] = {"data": data, "expiry": time.time() + ttl}

    def get(self, fare_id: str) -> Optional[Any]:
        item = self._storage.get(fare_id)
        if not item:
            return None
        if time.time() > item["expiry"]:
            del self._storage[fare_id]
            return None
        return item["data"]


# Global cache instance
flight_cache = FlightCache()


def get_flight_cache() -> FlightCache:
    return flight_cache
