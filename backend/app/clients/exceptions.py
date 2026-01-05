class ExternalProviderError(Exception):
    """Raised when an external provider returns an error response."""

    def __init__(
        self,
        provider_code: str,
        message: str,
        http_status: int | None = None,
        provider: str = "TBO",
    ):
        self.provider_code = provider_code
        self.message = message
        self.http_status = http_status
        self.provider = provider
        super().__init__(message)
