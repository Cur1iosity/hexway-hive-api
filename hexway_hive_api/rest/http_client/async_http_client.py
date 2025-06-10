"""Asynchronous HTTP client built on top of :mod:`aiohttp`.

Attributes:
    session (aiohttp.ClientSession): Session used for all outgoing requests.
"""

from http import HTTPStatus, HTTPMethod
from typing import Self, Union, MutableMapping, Any

import aiohttp

from hexway_hive_api.rest.http_client.exceptions import *

SUCCESSFUL_STATUS_CODES = [status for status in HTTPStatus if 200 <= status < 300]


class AsyncHTTPClient:
    """Asynchronous implementation of the HTTP client."""
    def __init__(self) -> None:
        """Create ``aiohttp`` session used for all requests."""

        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self._proxies: MutableMapping[str, str] = {}

    async def _send(self, method: HTTPMethod, url: str, **kwargs) -> Union[dict, bytes, list]:
        """Internal helper performing HTTP request and parsing the response."""

        proxy = self._proxies.get('https' if url.startswith('https') else 'http')
        if proxy:
            kwargs.setdefault('proxy', proxy)
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status not in SUCCESSFUL_STATUS_CODES:
                    try:
                        message = await response.json()
                    except aiohttp.ContentTypeError:
                        message = await response.text()
                    raise ClientError(f'Request failed with status code {response.status}\n{message}')
                try:
                    return await response.json()
                except aiohttp.ContentTypeError:
                    return await response.read()
        except aiohttp.ClientConnectionError as e:
            if 'SOCKSHTTPSConnectionPool' in str(e):
                proxy = self._proxies.get('https')
                raise SocksProxyError(f'Couldn\'t connect via "{proxy}". Check it.')
            else:
                raise ClientConnectionError(e)

    def _update_params(self, **kwargs) -> Self:
        """Update ``aiohttp`` session parameters in-place."""

        [setattr(self.session, key, value) for key, value in kwargs.items()
         if value is not None and hasattr(self.session, key)]
        return self

    async def clear_session(self) -> bool:
        """Remove all custom headers from the session."""

        self.session.headers.clear()
        return True

    async def close(self) -> bool:
        """Close underlying ``aiohttp`` session."""
        await self.session.close()
        return True

    async def get(self, *args, **kwargs) -> Union[dict, list, bytes]:
        """Send HTTP ``GET`` request."""

        return await self._send(HTTPMethod.GET, *args, **kwargs)

    async def post(self, *args, **kwargs) -> Union[dict, list, bytes]:
        """Send HTTP ``POST`` request."""

        return await self._send(HTTPMethod.POST, *args, **kwargs)

    async def put(self, *args, **kwargs) -> dict:
        """Send HTTP ``PUT`` request."""

        return await self._send(HTTPMethod.PUT, *args, **kwargs)

    async def patch(self, *args, **kwargs) -> dict:
        """Send HTTP ``PATCH`` request."""

        return await self._send(HTTPMethod.PATCH, *args, **kwargs)

    async def delete(self, *args, **kwargs) -> dict:
        """Send HTTP ``DELETE`` request."""

        return await self._send(HTTPMethod.DELETE, *args, **kwargs)

    def add_headers(self, headers: dict) -> Self:
        """Inject additional headers into requests session."""

        self.session.headers.update(headers)
        return self

    def update_params(self, **kwargs) -> Self:
        """Public wrapper around :meth:`_update_params`."""

        self._update_params(**kwargs)
        return self

    @property
    def proxies(self) -> MutableMapping[str, str]:
        """Proxy configuration used for outgoing requests."""

        return self._proxies

    @proxies.setter
    def proxies(self, proxies: dict | None) -> None:
        """Set proxy configuration."""

        if not proxies or not isinstance(proxies, dict):
            proxies = {}
        self._proxies.update(proxies)

    @property
    def params(self) -> MutableMapping[str, Any]:
        """Return current ``aiohttp`` session parameters."""

        return self.session.__dict__
