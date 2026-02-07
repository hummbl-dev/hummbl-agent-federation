"""SDK exceptions."""


class FederationError(Exception):
    """Base exception for Federation SDK."""
    pass


class RoutingError(FederationError):
    """Error during task routing."""
    pass


class AuthenticationError(FederationError):
    """Authentication failed."""
    pass


class RateLimitError(FederationError):
    """Rate limit exceeded."""
    pass
