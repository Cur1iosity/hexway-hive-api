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
