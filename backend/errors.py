class ExternalServiceError(RuntimeError):
    """An external data or AI provider could not complete the request."""


class AIProviderError(ExternalServiceError):
    """The configured AI provider is unavailable or misconfigured."""


class DataProviderRateLimitError(ExternalServiceError):
    """A financial-data provider rejected requests due to quota."""
