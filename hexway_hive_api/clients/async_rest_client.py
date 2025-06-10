import json
from contextlib import asynccontextmanager
from typing import Optional, Dict, MutableMapping, List, Union, Self, AsyncGenerator
from uuid import UUID

from hexway_hive_api.rest import exceptions
from hexway_hive_api.rest.enums import ClientState
from hexway_hive_api.rest.http_client.async_http_client import AsyncHTTPClient
from hexway_hive_api.rest.models.project import Project


class AsyncRestClient:
    """Asynchronous Rest client for Hive."""
    def __init__(self,
                 *,
                 server: Optional[str] = None,
                 api_url: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 proxies: Optional[Dict] = None,
                 **other,
                 ) -> None:
        self.http_client: AsyncHTTPClient = AsyncHTTPClient()
        self.state: ClientState = ClientState.NOT_CONNECTED

        self.server: Optional[str] = server
        self.api_url: Optional[str] = api_url
        self.username: Optional[str] = username
        self.__password: Optional[str] = password
        self.proxies = proxies

        self.http_client.update_params(**other)

    async def connect(self,
                      *,
                      server: Optional[str] = None,
                      api_url: Optional[str] = None,
                      username: Optional[str] = None,
                      password: Optional[str] = None,
                      **other,
                      ) -> None:
        if not any([server, self.server]) and not any([api_url, self.api_url]):
            raise exceptions.ServerNotFound()

        if not any([username, self.username]) and not any([password, self.__password]):
            raise exceptions.RestConnectionError('You must provide username and password.')

        self.http_client.update_params(**other)

        self.server = server or self.server
        self.api_url = api_url or self.api_url or self.make_api_url_from(self.server)

        username = username or self.username
        password = password or self.__password

        if '@' not in username:
            username = f'{username}@ro.ot'

        response = await self.http_client.session.post(f"{self.api_url}/session", json={
            'userLogin': username,
            'userPassword': password,
        })

        cookie = response.cookies.get('BSESSIONID')
        if not cookie:
            raise exceptions.RestConnectionError('Could not get authentication cookie. Something wrong with credentials or server.')

        self.http_client.add_headers({'Cookie': f'BSESSIONID={cookie}'})
        self.state = ClientState.CONNECTED

    async def disconnect(self) -> bool:
        await self.http_client.session.delete(f"{self.api_url}/session")
        self.state = ClientState.DISCONNECTED
        await self.http_client.clear_session()
        return True

    @asynccontextmanager
    async def connection(self, **kwargs) -> AsyncGenerator[Self, None]:
        await self.connect(**kwargs)
        try:
            yield self
        finally:
            await self.disconnect()

    @staticmethod
    def make_api_url_from(server: str, port: Optional[int] = None) -> str:
        try:
            proto, hostname, *str_port = server.split(':')
        except ValueError:
            raise exceptions.IncorrectServerUrl('Protocol not defined in server URL.')

        if not proto:
            raise exceptions.IncorrectServerUrl('Protocol not defined in server URL.')

        if str_port:
            port = int(str_port[0])
            server = f'{proto}://{hostname}'

        if server.startswith('https') and not port:
            port = 443
        elif server.startswith('http') and not port:
            port = 80

        return f'{server.strip("/")}:{port}/api'

    async def get_project(self, project_id: str) -> Dict[str, Union[str, List, Dict]]:
        return await self.http_client.get(f'{self.api_url}/project/{project_id}')

    async def get_projects(self, **params) -> Dict[str, Union[str, Dict]]:
        return await self.http_client.post(f'{self.api_url}/project/filter/', params=params, json={})

    async def get_file(self, project_id: str, file_id: str) -> bytes:
        return await self.http_client.get(f'{self.api_url}/project/{project_id}/graph/file/{file_id}')

    async def get_issues(self, project_id: str, offset: int = 0, limit: int = 100) -> Dict[str, str]:
        response = await self.http_client.post(
            url=f'{self.api_url}/project/{project_id}/graph/issue_list?offset={offset}&limit={limit}',
            json={})
        return response

    async def get_users(self) -> List[Dict]:
        return await self.http_client.get(f'{self.api_url}/user/')

    async def update_project(self, project_id: Union[str, UUID], fields: Dict) -> Dict[str, str]:
        project = await self.get_project(project_id)
        merged_data = project.pop('data', {}) | fields.pop('data', {})
        merged_project = project | fields | {'data': merged_data}
        merged_project = Project(**merged_project | {'id': project_id}).model_dump()
        merged_project['data'] = json.dumps(merged_project['data'])
        files = {k: (None, v) for k, v in merged_project.items()}
        return await self.http_client.put(f'{self.api_url}/project/{project_id}', files=files)

    async def update_issue(self, project_id: Union[str, UUID], issue_id: Union[str, UUID], fields: Dict) -> Dict[str, str]:
        return await self.http_client.patch(f'{self.api_url}/project/{project_id}/graph/issues/{issue_id}', json=fields)

    async def archive_project(self, project_id: Union[str, UUID]) -> Dict[str, str]:
        return await self.http_client.put(f'{self.api_url}/project/{project_id}/archive', json={'archived': True})

    async def activate_project(self, project_id: Union[str, UUID]) -> Dict[str, str]:
        return await self.http_client.put(f'{self.api_url}/project/{project_id}/archive', json={'archived': False})

    async def get_statuses(self) -> List[Dict]:
        return await self.http_client.get(f'{self.api_url}/settings/issues/statuses/')

    @property
    def proxies(self) -> MutableMapping[str, str]:
        return self.http_client.proxies

    @proxies.setter
    def proxies(self, proxies: Dict) -> None:
        self.http_client.proxies = proxies

