"""Asynchronous HTTP client built on top of :mod:`aiohttp`.

Attributes:
    session (aiohttp.ClientSession): Session used for all outgoing requests.
    ssl (ssl.SSLContext | None): Default SSL context for requests.
"""

from http import HTTPStatus, HTTPMethod
from typing import Self, Union, MutableMapping, Any, Optional
import ssl
import logging

import aiohttp

from hexway_hive_api.rest.http_client.exceptions import *


logger = logging.getLogger("AsyncHTTPClient")
SUCCESSFUL_STATUS_CODES = [status for status in HTTPStatus if 200 <= status < 300]


class AsyncHTTPClient:
    """Asynchronous implementation of the HTTP client."""
    def __init__(self, *, ssl: Optional[ssl.SSLContext] = None, verify_ssl: bool = True) -> None:
        """Create ``aiohttp`` session used for all requests.

        Parameters
        ----------
        ssl : :class:`ssl.SSLContext` | None
            Default SSL context applied to all requests.
        verify_ssl : bool, optional
            Flag controlling TLS certificate verification. ``True`` by default.
        """

        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
            skip_auto_headers={"Accept-Encoding", "User-Agent"}
        )
        self._proxies: MutableMapping[str, str] = {}
        self.ssl = ssl
        self.verify_ssl = verify_ssl
        self._cookie_header: Optional[str] = None

    async def _send(self, method: HTTPMethod, url: str, **kwargs) -> Union[dict, bytes, list]:
        """Internal helper performing HTTP request and parsing the response.

        The default SSL context is appended to ``kwargs`` if not specified.
        """

        proxy = self._proxies.get('https' if url.startswith('https') else 'http')
        if proxy:
            kwargs.setdefault('proxy', proxy)

        headers = dict(kwargs.get("headers", {}))
        if self._cookie_header and "Cookie" not in headers:
            headers["Cookie"] = self._cookie_header
        if "Accept-Encoding" in headers:
            values = [v.strip() for v in headers["Accept-Encoding"].split(',')]
            headers["Accept-Encoding"] = ", ".join(dict.fromkeys(values))
        kwargs["headers"] = headers

        verify = kwargs.pop("verify", kwargs.pop("verify_ssl", self.verify_ssl))

        if not verify:
            base_context = kwargs.get("ssl") or self.ssl
            if base_context is not None:
                context = ssl.SSLContext(base_context.protocol)
            else:
                context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            kwargs.setdefault("ssl", context)
        else:
            kwargs.setdefault("ssl", self.ssl)
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status not in SUCCESSFUL_STATUS_CODES:
                    try:
                        message = await response.json()
                    except aiohttp.ContentTypeError:
                        message = await response.text()
                    raise ClientError(f'Request failed with status code {response.status}\n{message}', details={
                        'url': url,
                        'method': method,
                        'status': response.status,
                        'headers': response.request_info.headers,
                        'content': message
                    })
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
        self._cookie_header = None
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


    def update_params(self, **kwargs) -> Self:
        """Update session parameters and store ``ssl`` for later use."""
        if "ssl" in kwargs:
            self.ssl = kwargs["ssl"]
        if "verify" in kwargs or "verify_ssl" in kwargs:
            self.verify_ssl = bool(kwargs.get("verify", kwargs.get("verify_ssl")))
            kwargs.pop("verify", None)
            kwargs.pop("verify_ssl", None)
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
