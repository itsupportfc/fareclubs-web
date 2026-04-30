"""Request + response logging middleware.

Despite the file name (kept for backwards-compatible imports), this also
captures request bodies. Both request and response are emitted as a single
JSON log line per API call so they're trivially correlatable.

Sensitive fields are redacted before logging:
  - full mask: passport, PAN, GST number, password, payment signature
  - last-4 only: payment ids, contact numbers
"""

import json
import logging
import time
from typing import Any

logger = logging.getLogger("app.api.response")

# Cap any single body we serialise into the log — covers SSR responses and
# pathological payloads alike. Larger bodies are truncated with a marker.
_MAX_BODY_LOG_BYTES = 200_000

_FULL_MASK_KEYS = {
    "password",
    "payment_signature",
    "paymentSignature",
    "passport_no",
    "passportNo",
    "pan",
    "PAN",
    "gst_number",
    "gstNumber",
    "GSTNumber",
    "razorpay_signature",
}

_LAST4_KEYS = {
    "payment_id",
    "paymentId",
    "payment_order_id",
    "paymentOrderId",
    "razorpay_payment_id",
    "razorpay_order_id",
    "contact_no",
    "contactNo",
}


def _last4(value: Any) -> str:
    if value is None:
        return None
    s = str(value)
    if len(s) <= 4:
        return "***"
    return "***" + s[-4:]


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in _FULL_MASK_KEYS:
                out[k] = "***REDACTED***"
            elif k in _LAST4_KEYS:
                out[k] = _last4(v)
            else:
                out[k] = _redact(v)
        return out
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    return obj


def _decode_body(raw: bytes) -> Any:
    if not raw:
        return None
    if len(raw) > _MAX_BODY_LOG_BYTES:
        truncated = raw[:_MAX_BODY_LOG_BYTES].decode("utf-8", errors="replace")
        return f"<truncated {len(raw)} bytes; first {_MAX_BODY_LOG_BYTES}> " + truncated
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text) if text else None
    except Exception:
        return text


class ResponseLoggingMiddleware:
    def __init__(self, app, api_prefix: str = "/api/v1"):
        self.app = app
        self.api_prefix = api_prefix

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "")

        # Log only internal API routes
        if not path.startswith(self.api_prefix):
            await self.app(scope, receive, send)
            return

        started_at = time.perf_counter()

        # ---- Capture request body via receive wrapper ----
        request_body_parts: list[bytes] = []

        async def receive_wrapper():
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if body:
                    request_body_parts.append(body)
            return message

        # ---- Capture response status / headers / body via send wrapper ----
        status_code: int | None = None
        response_headers: list = []
        response_body_parts: list[bytes] = []

        async def send_wrapper(message):
            nonlocal status_code, response_headers
            if message["type"] == "http.response.start":
                status_code = message.get("status")
                response_headers = message.get("headers", [])
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    response_body_parts.append(body)
            await send(message)

        await self.app(scope, receive_wrapper, send_wrapper)

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

        request_body = _redact(_decode_body(b"".join(request_body_parts)))
        response_body = _decode_body(b"".join(response_body_parts))

        headers_dict = {
            key.decode("latin-1"): value.decode("latin-1")
            for key, value in response_headers
        }

        log_payload = {
            "event": "api_call",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "request_body": request_body,
            "response_headers": headers_dict,
            "response_body": response_body,
        }

        logger.info(json.dumps(log_payload, ensure_ascii=False, default=str, indent=2))
