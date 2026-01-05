from fastapi import Request

from app.clients.tbo_client import TBOClient
from app.transformers.tbo_transformer import TBOTransformer


def get_tbo_client() -> TBOClient:
    """Dependency to get TBOClient instance"""
    return TBOClient()


def get_tbo_transformer() -> TBOTransformer:
    """Dependency to get TBOTransformer instance"""
    return TBOTransformer()


def get_end_user_ip(request: Request) -> str:
    # X-Forwarded-For may contain multiple IPs: client, proxy1, proxy2...
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "0.0.0.0"
