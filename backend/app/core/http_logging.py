import uuid

from app.core.request_context import reset_request_id, set_request_id
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


# Middleware to generate and attach a unique request ID to each incoming request for better logging and tracing across the application.
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate a unique request ID for each incoming request.
        # If the client provides an "X-Request-ID" header, use that instead.
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = set_request_id(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            reset_request_id(token)
