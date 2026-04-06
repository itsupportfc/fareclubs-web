import logging
import time
import uuid

from app.config import settings
from app.core.logging import dump_for_logging, parse_body_for_logging, sanitize_for_logging
from app.core.request_context import reset_request_id, set_request_id
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.internal_api")


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = set_request_id(request_id)
        start = time.perf_counter()

        request_body_bytes = await request.body()
        request_meta = {
            "event": "internal_api.request",
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client": request.client.host if request.client else None,
            "headers": sanitize_for_logging(dict(request.headers)),
        }
        if settings.ENABLE_HTTP_BODY_LOGGING:
            request_meta["body"] = parse_body_for_logging(
                request.headers.get("content-type"), request_body_bytes
            )
        logger.info(dump_for_logging(request_meta))

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                dump_for_logging(
                    {
                        "event": "internal_api.exception",
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": elapsed_ms,
                    }
                )
            )
            reset_request_id(token)
            raise

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response_meta: dict = {
            "event": "internal_api.response",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": elapsed_ms,
        }

        if settings.ENABLE_HTTP_BODY_LOGGING:
            # Only buffer the response body when body logging is enabled
            response_body_chunks = [chunk async for chunk in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body_chunks))
            response_body = b"".join(response_body_chunks)
            response_meta["body"] = parse_body_for_logging(
                response.headers.get("content-type"), response_body
            )

        logger.info(dump_for_logging(response_meta))

        response.headers["X-Request-ID"] = request_id
        reset_request_id(token)
        return response
