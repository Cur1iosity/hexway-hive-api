import os
import sys
import importlib.util
local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
module_path = os.path.join(local_path, 'hexway_hive_api', 'clients', 'async_rest_client.py')
spec = importlib.util.spec_from_file_location('hexway_hive_api.clients.async_rest_client', module_path)
async_rest_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(async_rest_client)
sys.modules['hexway_hive_api.clients.async_rest_client'] = async_rest_client
AsyncRestClient = async_rest_client.AsyncRestClient
from hexway_hive_api.rest import exceptions
import aiohttp
import pytest


def test_make_api_url_from() -> None:
    """Ensure API URL is built correctly from server string."""
    url = AsyncRestClient.make_api_url_from('https://hive.local')
    assert url == 'https://hive.local:443/api'


def test_proxies_property() -> None:
    """Proxy configuration should be stored inside HTTP client."""
    async def run() -> None:
        client = AsyncRestClient()
        client.proxies = {"http": "http://proxy"}
        assert client.proxies.get("http") == "http://proxy"
        await client.http_client.clear_session()

    import asyncio
    asyncio.run(run())


def test_connect_respects_verify_false() -> None:
    """SSL context should disable verification when verify is False."""
    import ssl

    class DummyResponse:
        def __init__(self) -> None:
            self.cookies = {"BSESSIONID": "cookie"}

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}
            self.captured = None
            self.closed = False

        async def post(self, *args, **kwargs):
            self.captured = kwargs.get("ssl")
            return DummyResponse()

        async def close(self):
            self.closed = True

    async def run() -> None:
        client = AsyncRestClient()
        old_session = client.http_client.session
        client.http_client.session = DummySession()
        await old_session.close()
        await client.connect(
            server="https://hive.local",
            api_url="https://hive.local/api",
            username="u",
            password="p",
            verify=False,
        )
        context = client.http_client.session.captured
        assert isinstance(context, ssl.SSLContext)
        assert context.verify_mode == ssl.CERT_NONE
        await client.http_client.session.close()

    import asyncio
    asyncio.run(run())


def test_connect_handles_aiohttp_error() -> None:
    """Client should close session and raise ``RestConnectionError`` on aiohttp failure."""

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}
            self.closed = False

        async def post(self, *args, **kwargs):
            raise aiohttp.ClientConnectionError("boom")

        async def close(self):
            self.closed = True

    async def run() -> None:
        client = AsyncRestClient()
        old_session = client.http_client.session
        dummy = DummySession()
        client.http_client.session = dummy
        await old_session.close()

        with pytest.raises(exceptions.RestConnectionError):
            await client.connect(server="http://test", api_url="http://test/api", username="u", password="p")

        assert dummy.closed is True

    import asyncio
    asyncio.run(run())


def test_disconnect_closes_session() -> None:
    """Client session should be closed after disconnect."""

    class DummyResponse:
        def __init__(self) -> None:
            self.cookies = {"BSESSIONID": "cookie"}

        async def json(self):
            return {}

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}
            self.closed = False

        async def post(self, *args, **kwargs):
            if self.closed:
                raise RuntimeError("Session is closed")
            return DummyResponse()

        async def delete(self, *args, **kwargs):
            if self.closed:
                raise RuntimeError("Session is closed")
            return DummyResponse()

        async def close(self):
            self.closed = True

    async def run() -> None:
        client = AsyncRestClient()
        old_session = client.http_client.session
        dummy = DummySession()
        client.http_client.session = dummy
        await old_session.close()

        await client.connect(server="http://test", api_url="http://test/api", username="u", password="p")
        await client.disconnect()

        assert dummy.closed is True
        assert client.http_client.session is dummy
        assert client.http_client.session.closed is True

    import asyncio
    asyncio.run(run())


def test_disconnect_handles_server_error() -> None:
    """Disconnect should recreate session even if server is already disconnected."""

    class DummyResponse:
        def __init__(self) -> None:
            self.cookies = {"BSESSIONID": "cookie"}

        async def json(self):
            return {}

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}
            self.closed = False

        async def post(self, *args, **kwargs):
            if self.closed:
                raise RuntimeError("Session is closed")
            return DummyResponse()

        async def delete(self, *args, **kwargs):
            raise aiohttp.ServerDisconnectedError()

        async def close(self):
            self.closed = True

    async def run() -> None:
        client = AsyncRestClient()
        old_session = client.http_client.session
        dummy = DummySession()
        client.http_client.session = dummy
        await old_session.close()

        await client.connect(server="http://test", api_url="http://test/api", username="u", password="p")
        await client.disconnect()

        assert dummy.closed is True
        assert client.http_client.session is dummy
        assert client.http_client.session.closed is True

    import asyncio
    asyncio.run(run())


def test_connect_after_disconnect() -> None:
    """Client should be able to reconnect after disconnect."""

    class DummyResponse:
        def __init__(self) -> None:
            self.cookies = {"BSESSIONID": "cookie"}

        async def json(self):
            return {}

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}
            self.closed = False

        async def post(self, *args, **kwargs):
            if self.closed:
                raise RuntimeError("Session is closed")
            return DummyResponse()

        async def delete(self, *args, **kwargs):
            if self.closed:
                raise RuntimeError("Session is closed")
            return DummyResponse()

        async def close(self):
            self.closed = True

    async def run() -> None:
        client = AsyncRestClient()
        old_session = client.http_client.session
        dummy1 = DummySession()
        client.http_client.session = dummy1
        await old_session.close()

        await client.connect(server="http://test", api_url="http://test/api", username="u", password="p")
        await client.disconnect()

        assert dummy1.closed is True
        assert client.http_client.session is dummy1
        assert client.http_client.session.closed is True

        dummy2 = DummySession()
        client.http_client.session = dummy2

        await client.connect(server="http://test", api_url="http://test/api", username="u", password="p")

        assert dummy2.closed is False
        assert client.http_client.session.headers.get("Cookie") == "BSESSIONID=cookie"
        await client.http_client.session.close()

    import asyncio
    asyncio.run(run())


def test_connect_uses_ssl_context(monkeypatch) -> None:
    """SSL context from ``cert`` parameter should be passed to requests."""
    import ssl

    async def run() -> None:
        # avoid loading real certificate
        monkeypatch.setattr(
            AsyncRestClient,
            "_make_ssl_context",
            staticmethod(lambda cert: ssl.create_default_context()),
        )

        class DummyResponse:
            def __init__(self) -> None:
                self.cookies = {"BSESSIONID": "cookie"}

        class DummySession:
            def __init__(self) -> None:
                self.headers = {}
                self.captured = None
                self.closed = False

            async def post(self, *args, **kwargs):
                self.captured = kwargs.get("ssl")
                return DummyResponse()

            async def close(self):
                self.closed = True

        client = AsyncRestClient(cert="path/to/cert.pem")
        old_session = client.http_client.session
        client.http_client.session = DummySession()
        await old_session.close()

        await client.connect(
            server="https://hive.local",
            api_url="https://hive.local/api",
            username="u",
            password="p",
        )

        assert isinstance(client.http_client.session.captured, ssl.SSLContext)
        await client.http_client.session.close()

    import asyncio
    asyncio.run(run())
