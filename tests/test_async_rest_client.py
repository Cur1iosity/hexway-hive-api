from hexway_hive_api.clients.async_rest_client import AsyncRestClient


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
            return DummyResponse()

        async def delete(self, *args, **kwargs):
            return DummyResponse()

        async def close(self):
            self.closed = True

    async def run() -> None:
        client = AsyncRestClient()
        old_session = client.http_client.session
        client.http_client.session = DummySession()
        await old_session.close()

        await client.connect(server="http://test", api_url="http://test/api", username="u", password="p")
        await client.disconnect()

        assert client.http_client.session.closed is True

    import asyncio
    asyncio.run(run())


def test_connect_uses_ssl_context(monkeypatch) -> None:
    """SSL context from ``cert`` parameter should be passed to requests."""
    import ssl
    async def run() -> None:
        captured = None

        # avoid loading real certificate
        monkeypatch.setattr(
            AsyncRestClient,
            "_make_ssl_context",
            staticmethod(lambda cert: ssl.create_default_context()),
        )

        client = AsyncRestClient(cert="path/to/cert.pem")

        async def dummy_request(self, method, url, **kwargs):
            nonlocal captured
            captured = kwargs.get("ssl")
            class DummyResponse:
                def __init__(self) -> None:
                    self.cookies = {"BSESSIONID": "cookie"}

                async def json(self):
                    return {}

            return DummyResponse()

        from types import MethodType

        monkeypatch.setattr(
            client.http_client.session,
            "request",
            MethodType(dummy_request, client.http_client.session),
        )

        async def dummy_post(self, url, **kwargs):
            return await self.request("POST", url, ssl=client.http_client.ssl, **kwargs)

        monkeypatch.setattr(
            client.http_client.session,
            "post",
            MethodType(dummy_post, client.http_client.session),
        )

        await client.connect(server="https://hive.local", api_url="https://hive.local/api", username="u", password="p")

        assert isinstance(captured, ssl.SSLContext)
        await client.http_client.session.close()

    import asyncio
    asyncio.run(run())
