"""Synchronous client used for interacting with the Hive REST API."""

import json
from contextlib import contextmanager
from typing import Optional, MutableMapping, Union, Self, ContextManager
from uuid import UUID

from hexway_hive_api.rest import exceptions
from hexway_hive_api.rest.enums import ClientState
from hexway_hive_api.rest.http_client import HTTPClient
from hexway_hive_api.rest.models.project import Project


class RestClient:
    """Synchronous REST client for Hive.

    Attributes:
        http_client (HTTPClient): Underlying HTTP client instance.
        state (ClientState): Current state of the client.
    """
    def __init__(self,
                 *,
                 server=None,
                 api_url=None,
                 username=None,
                 password=None,
                 proxies=None,
                 **other
                 ) -> None:
        """Create REST client instance.

        Parameters
        ----------
        server: str | None
            Address of the Hive instance.
        api_url: str | None
            Full API URL. If not provided it will be generated from ``server``.
        username: str | None
            User login name.
        password: str | None
            Password for the user.
        proxies: dict | None
            Optional mapping with HTTP and HTTPS proxy definitions.
        other: dict
            Additional parameters passed directly to :class:`requests.Session`.
        """
        self.http_client: HTTPClient = HTTPClient()
        self.state: ClientState = ClientState.NOT_CONNECTED

        self.server: Optional[str] = server
        self.api_url: Optional[str] = api_url  # In case server uses not standard api-route
        self.username: Optional[str] = username
        self.__password: Optional[str] = password
        self.proxies = proxies

        self.http_client.update_params(**other)

    def connect(self,
                     *,
                     server: Optional[str] = None,
                     api_url: Optional[str] = None,
                     username: Optional[str] = None,
                     password: Optional[str] = None,
                     **other
                     ) -> None:
        """Authenticate against the Hive server.

        Parameters
        ----------
        server: str | None
            Server address. If not provided the value from object state will be
            used.
        api_url: str | None
            Explicit API URL. Overrides ``server`` if supplied.
        username: str | None
            Login name used for authentication.
        password: str | None
            Password for the account.
        other: dict
            Additional options passed directly to ``requests.Session``.
        """
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

        response = self.http_client.session.post(f"{self.api_url}/session", json={
            'userLogin': username,
            'userPassword': password,
        })

        if not (cookie := response.cookies.get('BSESSIONID')):
            raise exceptions.RestConnectionError('Could not get authentication cookie. Something wrong with credentials'
                                                 ' or server.')

        self.http_client.add_headers({'Cookie': f'BSESSIONID={cookie}'})
        self.state = ClientState.CONNECTED


    def disconnect(self) -> bool:
        """Terminate authenticated session with Hive."""
        self.http_client.session.delete(f"{self.api_url}/session")
        self.state = ClientState.DISCONNECTED
        self.http_client.clear_session()
        return True

    @contextmanager
    def connection(self, **kwargs) -> ContextManager[Self]:
        """Yield connected client instance and ensure cleanup."""
        self.connect(**kwargs)
        try:
            yield self
        finally:
            self.disconnect()

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

    def get_project(self, project_id: str) -> dict[str, Union[str, list, dict]]:
        """Retrieve project information.

        Parameters
        ----------
        project_id: str
            Identifier of the project to retrieve.
        """
        return self.http_client.get(f'{self.api_url}/project/{project_id}')

    def get_projects(self, **params) -> dict[str, Union[str, dict]]:
        """Return list of projects using provided filters."""
        return self.http_client.post(f'{self.api_url}/project/filter/', params=params, json={})

    def get_file(self, project_id: str, file_id: str) -> bytes:
        """Download raw file from project storage."""
        return self.http_client.get(f'{self.api_url}/project/{project_id}/graph/file/{file_id}')

    def get_issues(self, project_id: str, offset: int = 0, limit: int = 100) -> dict[str, str]:
        """Retrieve paginated issues list for the given project."""
        response = self.http_client.post(
            url=f'{self.api_url}/project/{project_id}/graph/issue_list?offset={offset}&limit={limit}',
            json={})
        return response

    def get_users(self) -> list[dict]:
        """Return list of users registered in Hive."""
        return self.http_client.get(f'{self.api_url}/user/')

    def update_project(self, project_id: Union[str, UUID], fields: dict) -> dict[str, str]:
        """Update project fields.

        Only fields present in ``fields`` will be updated. Project ``data`` is
        merged to avoid removing existing values.
        """
        project = self.get_project(project_id)
        # We need to merge data from project and fields to safely update project
        # We also need model to adapt data because of its specific serialized structure ¯\_(ツ)_/¯
        merged_data = project.pop('data', {}) | fields.pop('data', {})
        merged_project = project | fields | {'data': merged_data}
        merged_project = Project(**merged_project | {'id': project_id}).model_dump()
        merged_project['data'] = json.dumps(merged_project['data'])
        files = {k: (None, v) for k, v in merged_project.items()}
        return self.http_client.put(f'{self.api_url}/project/{project_id}', files=files)

    def update_issue(self, project_id: Union[str, UUID], issue_id: Union[str, UUID], fields: dict) -> dict[str, str]:
        """Update issue data within a project."""
        return self.http_client.patch(f'{self.api_url}/project/{project_id}/graph/issues/{issue_id}', json=fields)

    def archive_project(self, project_id: Union[str, UUID]) -> dict[str, str]:
        """Move project to archive."""
        return self.http_client.put(f'{self.api_url}/project/{project_id}/archive', json={'archived': True})

    def activate_project(self, project_id: Union[str, UUID]) -> dict[str, str]:
        """Restore archived project."""
        return self.http_client.put(f'{self.api_url}/project/{project_id}/archive', json={'archived': False})

    def get_statuses(self) -> list[dict]:
        """Return available issue statuses."""
        return self.http_client.get(f'{self.api_url}/settings/issues/statuses/')

    @property
    def proxies(self) -> MutableMapping[str, str]:
        """Return proxy configuration."""
        return self.http_client.proxies

    @proxies.setter
    def proxies(self, proxies: dict) -> None:
        """Set proxy configuration for HTTP requests."""
        self.http_client.proxies = proxies
