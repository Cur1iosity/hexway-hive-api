"""Custom exception hierarchy used by the Hive API wrapper."""



from hexway_hive_api.rest.enums import Guard


class HiveRestError(Exception):
    """Exception raised for API errors.

    Attributes:
        detail (str | None): Detailed error description.
        status (int | None): HTTP status code returned by the server.
        title (str | None): Short error title.
        type (str | None): Error type provided by the server.
    """

    def __init__(self, params: dict) -> None:
        """Store fields from the API response."""
        self.detail = params.get('detail')
        self.status = params.get('status')
        self.title = params.get('title')
        self.type = params.get('type')

    def __str__(self) -> str:
        """Return string representation of the exception."""
        return f'[{self.status}] {self.title}: {self.detail}'


class RestConnectionError(Exception):
    """Base exception for connection errors."""
    pass


class ClientNotConnected(RestConnectionError):
    """Raised when client operations are attempted without authentication."""
    def __init__(self) -> None:
        """Initialize ClientNotConnected."""
        super().__init__('Client is not connected to server. You must authenticate first.')


class ServerNotFound(RestConnectionError):
    """Raised when no server address was supplied."""
    def __init__(self) -> None:
        """Initialize exception instance."""
        super().__init__(f'You must provide server or api_url.')


class IncorrectServerUrl(RestConnectionError):
    """Raised when a server URL cannot be parsed."""
    def __init__(self, message: str = None) -> None:
        """Initialize exception instance."""
        if not message:
            super().__init__('Incorrect server URL.')
        else:
            super().__init__(message)


class GuardError(Exception):
    """Base exception for guard related errors."""
    pass


class GuardIsNotDefined(GuardError):
    """Raised when an undefined guard name is provided."""
    def __init__(self, guard_name: str = None) -> None:
        """Initialize exception instance."""
        super().__init__(f'Control {guard_name} is not defined. You must provide guard from list: {", ".join(Guard)}.')
