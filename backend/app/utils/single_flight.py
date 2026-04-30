"""Per-key request coalescing.

When N concurrent callers request the same key, only one upstream call is
made; the others wait on the same result. Also called "stampede protection"
or "thundering-herd protection".
"""

import asyncio
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


class SingleFlight:
    def __init__(self) -> None:
        self._inflight: dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    async def do(self, key: str, factory: Callable[[], Awaitable[T]]) -> T:
        """Run `factory()` exactly once per `key` while a call is in flight.

        Concurrent callers with the same key receive the same result (or the
        same exception). After the call completes, the slot is freed so future
        calls can re-fetch.
        """
        async with self._lock:
            existing = self._inflight.get(key)
            if existing is not None:
                future = existing
                owner = False
            else:
                future = asyncio.get_running_loop().create_future()
                self._inflight[key] = future
                owner = True

        if not owner:
            return await future

        try:
            result = await factory()
            future.set_result(result)
            return result
        except BaseException as exc:
            future.set_exception(exc)
            raise
        finally:
            async with self._lock:
                self._inflight.pop(key, None)


# Module-level instance — shared across requests in the same worker process.
ssr_single_flight = SingleFlight()
