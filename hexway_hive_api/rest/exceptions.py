from typing import Dict

from hexway_hive_api.rest.enums import Guard


class HiveRestError(Exception):
    """Base exception for Hive rest client."""
    def __init__(self, params: Dict) -> None:
        """Initialize HiveRestError."""
        self.detail = params.get('detail')
        self.status = params.get('status')
        self.title = params.get('title')
        self.type = params.get('type')

    def __str__(self) -> str:
        """Return string representation of the exception."""
        return f'[{self.status}] {self.title}: {self.detail}'


class RestConnectionError(Exception):
    """Exception for connection errors."""
    pass


class ClientNotConnected(RestConnectionError):
    """Exception for client not connected."""
    def __init__(self) -> None:
        """Initialize ClientNotConnected."""
        super().__init__('Client is not connected to server. You must authenticate first.')


class ServerNotFound(RestConnectionError):
    """Exception for server not provided."""
    def __init__(self) -> None:
        """Initialize ServerNotProvided."""
        super().__init__(f'You must provide server or api_url.')


class IncorrectServerUrl(RestConnectionError):
    """Exception for incorrect server URL."""
    def __init__(self, message: str = None) -> None:
        """Initialize IncorrectServerUrl."""
        if not message:
            super().__init__('Incorrect server URL.')
        else:
            super().__init__(message)


class GuardError(Exception):
    """Exception for control errors."""
    pass


class GuardIsNotDefined(GuardError):
    """Exception for control is not defined."""
    def __init__(self, guard_name: str = None) -> None:
        """Initialize ControlIsNotDefined."""
        super().__init__(f'Control {guard_name} is not defined. You must provide guard from list: {", ".join(Guard)}.')
