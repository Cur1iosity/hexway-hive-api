"""Exceptions raised by HTTP client implementations."""
from typing import Optional, Any


class ClientError(Exception):
    """Base exception for Client."""

    def __init__(self, message: str, content: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.content = content
        self.details = details

    def __str__(self) -> str:
        base = super().__str__()
        if self.details:
            return f"{base} | Details: {self.details}"
        return base


class ClientConnectionError(ClientError):
    """Exception for connection errors."""

    def __init__(self, message):
        """Initialize ClientConnectionError."""
        super().__init__(message)


class SocksProxyError(ClientConnectionError):
    """Exception for connection errors."""

    def __init__(self, message="Couldn't connect via provided socks proxy. Check it."):
        """Initialize ClientConnectionError."""
        super().__init__(message)
