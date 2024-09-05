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
    SERVER_PROVIDING = auto()  # Передан ли от пользователя адрес сервера
    CONNECTION = auto()  # Подключен ли к серверу
