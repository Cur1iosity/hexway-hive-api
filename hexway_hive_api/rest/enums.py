"""Enumerations describing client states and guard checks."""

from enum import StrEnum, auto


class ClientState(StrEnum):
    """Enumeration of states."""
    NOT_CONNECTED = auto()
    CONNECTED = auto()
    DISCONNECTED = auto()


class Guard(StrEnum):
    """Enumeration of controls."""
    # ClientControl = auto()
    # USER_INPUT = auto()
    SERVER_PROVIDING = auto()  # Whether server address was provided by the user
    CONNECTION = auto()  # Indicates if the client is connected
