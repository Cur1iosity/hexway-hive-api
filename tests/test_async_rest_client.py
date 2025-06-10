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
