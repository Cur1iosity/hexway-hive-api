"""Asynchronous version of the Hive REST client."""

import json
import ssl
from contextlib import asynccontextmanager
from typing import Optional, MutableMapping, Union, Self, AsyncGenerator
from uuid import UUID

from hexway_hive_api.rest import exceptions
from hexway_hive_api.rest.enums import ClientState
from hexway_hive_api.rest.http_client.async_http_client import AsyncHTTPClient
from hexway_hive_api.rest.models.project import Project


class AsyncRestClient:
    """Asynchronous REST client used to communicate with Hive.

    Attributes:
        http_client (AsyncHTTPClient): HTTP client used for requests.
        state (ClientState): Current state of the client.
    """
    def __init__(self,
                 *,
                 server: Optional[str] = None,
                 api_url: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 proxies: Optional[dict] = None,
                 **other,
                 ) -> None:
        """Initialize asynchronous client instance.

        Parameters
        ----------
        server: str | None
            Address of the Hive instance.
        api_url: str | None
            Full API URL. If omitted it will be derived from ``server``.
        username: str | None
            User login name.
        password: str | None
            User password.
        proxies: dict | None
            Optional mapping with proxy configuration.
        other: dict
            Additional parameters forwarded to :class:`aiohttp.ClientSession`.
            The ``cert`` key may specify a certificate path or ``(cert, key)``
            tuple for TLS authentication.
        """

        self.http_client: AsyncHTTPClient = AsyncHTTPClient()
        self.state: ClientState = ClientState.NOT_CONNECTED

        self.server: Optional[str] = server
        self.api_url: Optional[str] = api_url
        self.username: Optional[str] = username
        self.__password: Optional[str] = password
        self.proxies = proxies

        cert = other.pop('cert', None)
        self.cert: Optional[Union[str, tuple[str, str]]] = cert
        self.http_client.update_params(**other)
        if cert:
            context = self._make_ssl_context(cert)
            self.http_client.update_params(ssl=context)

    async def connect(self,
                      *,
                      server: Optional[str] = None,
                      api_url: Optional[str] = None,
                      username: Optional[str] = None,
                      password: Optional[str] = None,
                      **other,
                      ) -> None:
        """Authenticate asynchronously with the Hive server.

        ``cert`` may be supplied in ``other`` for client TLS configuration.
        """

        if not any([server, self.server]) and not any([api_url, self.api_url]):
            raise exceptions.ServerNotFound()

        if not any([username, self.username]) and not any([password, self.__password]):
            raise exceptions.RestConnectionError('You must provide username and password.')

        cert = other.pop('cert', None) or self.cert
        self.http_client.update_params(**other)
        if cert:
            self.cert = cert
            context = self._make_ssl_context(cert)
            self.http_client.update_params(ssl=context)

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
        """Close connection and clean up client session."""

        await self.http_client.session.delete(f"{self.api_url}/session")
        self.state = ClientState.DISCONNECTED
        await self.http_client.clear_session()
        await self.http_client.close()
        return True

    @asynccontextmanager
    async def connection(self, **kwargs) -> AsyncGenerator[Self, None]:
        """Asynchronous context manager for automatic connect/disconnect."""

        await self.connect(**kwargs)
        try:
            yield self
        finally:
            await self.disconnect()

    @staticmethod
    def _make_ssl_context(cert: Union[str, tuple[str, str]]) -> ssl.SSLContext:
        """Create SSL context from certificate chain."""

        context = ssl.create_default_context()
        if isinstance(cert, (list, tuple)):
            context.load_cert_chain(cert[0], cert[1])
        else:
            context.load_cert_chain(cert)
        return context

    @staticmethod
    def make_api_url_from(server: str, port: Optional[int] = None) -> str:
        """Build API URL from server string.

        Parameters
        ----------
        server: str
            Server address in ``protocol://host[:port]`` format.
        port: int | None
            Optional port override.

        Returns
        -------
        str
            Full API endpoint URL.
        """

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

    async def get_project(self, project_id: str) -> dict[str, Union[str, list, dict]]:
        """Retrieve project information."""

        return await self.http_client.get(f'{self.api_url}/project/{project_id}')

    async def get_projects(self, **params) -> dict[str, Union[str, dict]]:
        """Return list of projects using provided filters."""

        return await self.http_client.post(f'{self.api_url}/project/filter/', params=params, json={})

    async def get_file(self, project_id: str, file_id: str) -> bytes:
        """Download raw file from project storage."""

        return await self.http_client.get(f'{self.api_url}/project/{project_id}/graph/file/{file_id}')

    async def get_issues(self, project_id: str, offset: int = 0, limit: int = 100) -> dict[str, str]:
        """Retrieve paginated issues list for the given project."""

        response = await self.http_client.post(
            url=f'{self.api_url}/project/{project_id}/graph/issue_list?offset={offset}&limit={limit}',
            json={})
        return response

    async def get_users(self) -> list[dict]:
        """Return list of users registered in Hive."""

        return await self.http_client.get(f'{self.api_url}/user/')

    async def update_project(self, project_id: Union[str, UUID], fields: dict) -> dict[str, str]:
        """Update project fields while preserving existing ``data`` section."""

        project = await self.get_project(project_id)
        merged_data = project.pop('data', {}) | fields.pop('data', {})
        merged_project = project | fields | {'data': merged_data}
        merged_project = Project(**merged_project | {'id': project_id}).model_dump()
        merged_project['data'] = json.dumps(merged_project['data'])
        files = {k: (None, v) for k, v in merged_project.items()}
        return await self.http_client.put(f'{self.api_url}/project/{project_id}', files=files)

    async def update_issue(self, project_id: Union[str, UUID], issue_id: Union[str, UUID], fields: dict) -> dict[str, str]:
        """Update issue data within a project."""

        return await self.http_client.patch(f'{self.api_url}/project/{project_id}/graph/issues/{issue_id}', json=fields)

    async def archive_project(self, project_id: Union[str, UUID]) -> dict[str, str]:
        """Move project to archive."""

        return await self.http_client.put(f'{self.api_url}/project/{project_id}/archive', json={'archived': True})

    async def activate_project(self, project_id: Union[str, UUID]) -> dict[str, str]:
        """Restore archived project."""

        return await self.http_client.put(f'{self.api_url}/project/{project_id}/archive', json={'archived': False})

    async def get_statuses(self) -> list[dict]:
        """Return available issue statuses."""

        return await self.http_client.get(f'{self.api_url}/settings/issues/statuses/')

    @property
    def proxies(self) -> MutableMapping[str, str]:
        """Return proxy configuration."""

        return self.http_client.proxies

    @proxies.setter
    def proxies(self, proxies: dict) -> None:
        """Set proxy configuration for HTTP requests."""

        self.http_client.proxies = proxies

