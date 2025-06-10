[![Run Tests](https://github.com/Cur1iosity/hexway-hive-api/actions/workflows/run-tests.yml/badge.svg)](https://github.com/Cur1iosity/hexway-hive-api/actions/workflows/run-tests.yml)
[![PyPI](https://img.shields.io/pypi/v/hexway-hive-api)](https://pypi.org/project/hexway-hive-api/)
[![Hexway](https://img.shields.io/badge/hexway-visit%20site-blue)](https://hexway.io)

# Hexway Hive API

Unofficial flexible library for [HexWay Hive](https://hexway.io/hive/) REST API.

#### Tested on HexWay Hive 0.65.6

## Installation
```bash
pip install hexway-hive-api
```

## Dependencies
- pydantic ~= 2.4
- requests ~= 2.31.0
- aiohttp ~= 3.9.0

## Usage
### Synchronous client
```python
from hexway_hive_api import RestClient


def main() -> None:
    auth = {
        "server": "https://demohive.hexway.io/",
        "username": "someuser",
        "password": "somepassword",
    }
    with RestClient().connection(**auth) as client:
        projects = client.get_projects().get("items")
        client.update_project(project_id=1, fields={"name": "New Project Name"})


if __name__ == "__main__":
    main()
```

### Asynchronous client
```python
import asyncio
from hexway_hive_api import AsyncRestClient


async def main() -> None:
    auth = {
        "server": "https://demohive.hexway.io/",
        "username": "someuser",
        "password": "somepassword",
    }
    async with AsyncRestClient().connection(**auth) as client:
        projects = (await client.get_projects()).get("items")
        await client.update_project(project_id=1, fields={"name": "New Project Name"})


asyncio.run(main())
```

### TLS configuration

``AsyncHTTPClient`` accepts an optional ``ssl`` context in its constructor or
through :meth:`update_params`. This context will be passed to all requests if no
``ssl`` argument is provided explicitly.
