from app.clients.tbo_client import TBOClient
from app.transformers.tbo_transformer import TBOTransformer
from fastapi import Request

# process-wide singletons. Instantiated once at module import, reused
# across all requests. this is what makes caching in TBOCLient actually
# meaningfull between diff requests.

_tbo_client = TBOClient()
_tbo_transformer = TBOTransformer()


# ISSUE: returns new instance per request
def get_tbo_client() -> TBOClient:
    """Dependency: return the process-wide TBOClient singleton."""
    return _tbo_client


def get_tbo_transformer() -> TBOTransformer:
    """Dependency: return the process-wide TBOTransformer singleton."""
    return _tbo_transformer


def get_end_user_ip(request: Request) -> str:
    # X-Forwarded-For may contain multiple IPs: client, proxy1, proxy2...
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "0.0.0.0"
