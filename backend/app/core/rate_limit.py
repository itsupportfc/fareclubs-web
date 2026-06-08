"""Shared slowapi Limiter instance.

Defined once so the instance attached to app.state.limiter in main.py and the
instance used by @limiter.limit(...) decorators in routers are the same
object — slowapi enforcement depends on this.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
