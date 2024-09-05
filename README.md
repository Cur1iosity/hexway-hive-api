[![Run Tests](https://github.com/Cur1iosity/hexway-hive-api/actions/workflows/run-tests.yml/badge.svg)](https://github.com/Cur1iosity/hexway-hive-api/actions/workflows/run-tests.yml)
[![PyPI](https://img.shields.io/pypi/v/hexway-hive-api)](https://pypi.org/project/hexway-hive-api/)
[![Hexway](https://img.shields.io/badge/hexway-visit%20site-blue)](https://hexway.io)

# Hexway Hive API

Unofficial flexible library for [HexWay Hive](https://hexway.io/hive/) Rest API.

#### Tested on HexWay Hive 0.62.8

## Installation
```bash
pip install hexway-hive-api
```

## Dependencies

- pydantic ~= 2.4
- requests ~= 2.31.0

## Usage
### Simple HiveClient
```python
from hexway_hive_api import RestClient


def main() -> None:
    auth = {
        'server': 'https://demohive.hexway.io/',
        'username': 'someuser',
        'password': 'somepassword',
        'proxies': {
            'http': 'http://127.0.0.1:8080',
            'https': 'http://127.0.0.1:8080',
        }
    }
    client = RestClient(**auth)

    client.authenticate()
    projects: list = client.get_projects().get('items')
    
    
    client.update_project(project_id=1, fields={'name': 'New Project Name'})
    
if __name__ == "__main__":
    main()


```