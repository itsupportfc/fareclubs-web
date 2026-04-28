import json
import logging
import time

logger = logging.getLogger("app.api.response")


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

        status_code = None
        response_headers = []
        response_body_parts = []

        async def send_wrapper(message):
            nonlocal status_code
            nonlocal response_headers
            nonlocal response_body_parts

            if message["type"] == "http.response.start":
                status_code = message.get("status")
                response_headers = message.get("headers", [])

            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    response_body_parts.append(body)

            await send(message)

        await self.app(scope, receive, send_wrapper)

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

        raw_body = b"".join(response_body_parts)
        body_text = raw_body.decode("utf-8", errors="replace")

        try:
            response_body = json.loads(body_text) if body_text else None
        except Exception:
            response_body = body_text

        headers_dict = {
            key.decode("latin-1"): value.decode("latin-1")
            for key, value in response_headers
        }

        log_payload = {
            "event": "api_response",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "response_headers": headers_dict,
            "response_body": response_body,
        }

        logger.info(json.dumps(log_payload, ensure_ascii=False, default=str, indent=2))
