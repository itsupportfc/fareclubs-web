"""Domain exceptions raised across services.

Kept here (not in clients/exceptions.py) because these represent backend
state, not provider-side failures.
"""

from __future__ import annotations


class SsrValidationError(Exception):
    """One or more user-selected SSR codes don't match canonical TBO data.

    `missing` is a list of dicts shaped like:
        {"leg": "outbound", "segment": 0, "type": "seat", "code": "15A"}
    The order-creation handler converts this into a 422 response payload.
    """

    def __init__(self, missing: list[dict]):
        self.missing = missing
        super().__init__(f"Invalid SSR codes: {missing}")


class SsrExpiredError(Exception):
    """raw_ssr_{fare_id} cache expired — caller should re-fetch SSR.

    Order-creation converts this into a 410 + code: SSR_EXPIRED so the
    frontend can re-fetch /ssr and prompt the user to re-confirm.
    """
