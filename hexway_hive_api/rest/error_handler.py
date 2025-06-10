"""Utilities for converting HTTP client errors into library exceptions."""

import functools
import json
from typing import Callable, Any

from hexway_hive_api.rest import exceptions
from hexway_hive_api.rest.http_client.exceptions import ClientError


def method_decorator(func) -> Callable:
    """Decorate client methods to translate HTTP errors."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        """Execute wrapped method and convert :class:`ClientError` exceptions."""
        try:
            result = func(*args, **kwargs)
        except ClientError as e:
            error = json.loads(e.content)
            raise exceptions.HiveRestError(error)
        return result
    return wrapper


def ErrorHandler(cls) -> Any:
    """Class decorator that applies :func:`method_decorator` to all methods."""
    original_init = cls.__init__

    @functools.wraps(original_init)
    def new_init(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        # Wrap all methods except ``__init__`` with the decorator
        for attr_name in dir(self):
            if not attr_name.startswith("__"):  # Skip dunder methods
                attr_value = getattr(self, attr_name)
                if callable(attr_value):
                    decorated_attr = method_decorator(attr_value)
                    setattr(self, attr_name, decorated_attr)

    cls.__init__ = new_init
    return cls
