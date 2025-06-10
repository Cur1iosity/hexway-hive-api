"""Synchronous HTTP client built on top of :mod:`requests`.

Attributes:
    session (Session): Underlying requests session used for all HTTP calls.
"""

from http import HTTPStatus, HTTPMethod
from typing import Self, Union, MutableMapping, Any

import requests.utils
from requests import Session, Response

from hexway_hive_api.rest.http_client.exceptions import *

SUCCESSFUL_STATUS_CODES = [status for status in HTTPStatus if 200 <= status < 300]


class HTTPClient:
    """Base implementation of the HTTP client."""
    session: Session = Session()

    def _send(self, method: HTTPMethod, *args, **kwargs) -> Union[dict, bytes]:
        """Universal method for sending requests."""
        try:
            response: Response = self.session.request(method, *args, **kwargs)

            if response.status_code not in SUCCESSFUL_STATUS_CODES:
                try:
                    message = response.json()
                except requests.JSONDecodeError:
                    message = response.content
                raise ClientError(f'Request failed with status code {response.status_code}\n{message}')

            try:
                return response.json()
            except requests.JSONDecodeError:
                return response.content

        except requests.ConnectionError as e:
            if 'SOCKSHTTPSConnectionPool' in str(e):
                proxy = self.session.proxies.get('https')
                raise SocksProxyError(f'Couldn\'t connect via "{proxy}". Check it.')
            else:
                raise ClientConnectionError(e)

    def _update_params(self, **kwargs) -> Self:
        """Update session parameters if they are not None and exist in session."""
        [setattr(self.session, key, value) for key, value in kwargs.items()
         if value is not None and hasattr(self.session, key)]
        return self

    def clear_session(self) -> bool:
        """Method to clear session headers."""
        self.session.headers.clear()
        return True

    def get(self, *args, **kwargs) -> Union[dict, list, bytes]:
        """Send GET request."""
        return self._send(HTTPMethod.GET, *args, **kwargs)

    def post(self, *args, **kwargs) -> Union[dict, list, bytes]:
        """Send POST request."""
        return self._send(HTTPMethod.POST, *args, **kwargs)

    def put(self, *args, **kwargs) -> dict:
        """Send PUT request."""
        return self._send(HTTPMethod.PUT, *args, **kwargs)

    def patch(self, *args, **kwargs) -> dict:
        """Send PATCH request."""
        return self._send(HTTPMethod.PATCH, *args, **kwargs)

    def delete(self, *args, **kwargs) -> dict:
        """Send DELETE request."""
        return self._send(HTTPMethod.DELETE, *args, **kwargs)

    def add_headers(self, headers: dict) -> Self:
        """Method injects headers into session."""
        self.session.headers.update(headers)
        return self

    def update_params(self, **kwargs) -> Self:
        """Method updates session parameters."""
        self._update_params(**kwargs)
        return self

    @property
    def proxies(self) -> MutableMapping[str, str]:
        """Method to get session proxies."""
        return self.session.proxies

    @proxies.setter
    def proxies(self, proxies: dict | None) -> None:
        """Set session proxies."""
        if not proxies and not isinstance(proxies, dict):
            proxies = {}
        self.session.proxies.update(proxies)

    @property
    def params(self) -> MutableMapping[str, Any]:
        """Return session parameters."""
        return self.session.__dict__
