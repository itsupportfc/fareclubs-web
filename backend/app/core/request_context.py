from contextvars import ContextVar, Token

# Thread-safe context variable to store the request ID for each request
_request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return _request_id_ctx_var.get()


def set_request_id(request_id: str) -> Token[str]:
    return _request_id_ctx_var.set(request_id)

# cleans up after request ends
def reset_request_id(token: Token[str]) -> None:
    _request_id_ctx_var.reset(token)
