import asyncio
import ssl

from hexway_hive_api.rest.http_client.async_http_client import AsyncHTTPClient


class DummyResponse:
    def __init__(self) -> None:
        self.status = 200

    async def json(self):
        return {}

    async def read(self):
        return b""

    async def text(self):
        return ""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


class DummySession:
    def __init__(self) -> None:
        self.headers = {}
        self.kwargs = None
        self.closed = False

    def request(self, *args, **kwargs):
        self.kwargs = kwargs
        return DummyResponse()

    async def close(self):
        self.closed = True


def test_update_params_sets_ssl():
    async def run() -> None:
        client = AsyncHTTPClient()
        context = ssl.create_default_context()
        client.update_params(ssl=context)
        assert client.ssl is context
        await client.close()

    asyncio.run(run())


def test_send_uses_default_ssl():
    async def run() -> None:
        client = AsyncHTTPClient()
        client.session = DummySession()
        context = ssl.create_default_context()
        client.update_params(ssl=context)
        await client.get("http://example.com")
        assert client.session.kwargs.get("ssl") is context
        await client.close()

    asyncio.run(run())


def test_update_params_sets_verify_ssl():
    async def run() -> None:
        client = AsyncHTTPClient()
        client.update_params(verify=False)
        assert client.verify_ssl is False
        await client.close()

    asyncio.run(run())


def test_send_respects_verify_flag():
    async def run() -> None:
        client = AsyncHTTPClient()
        client.session = DummySession()
        await client.get("https://example.com", verify=False)
        context = client.session.kwargs.get("ssl")
        assert isinstance(context, ssl.SSLContext)
        assert context.verify_mode == ssl.CERT_NONE
        await client.close()

    asyncio.run(run())
