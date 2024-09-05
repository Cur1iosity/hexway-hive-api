import json
from typing import Optional, Dict, MutableMapping, List, Union
from uuid import UUID

from .rest import exceptions
from .rest.enums import ClientState
from .rest.http_client import HTTPClient
from .rest.models.project import Project


class RestClient:
    """Rest client for Hive."""
    def __init__(self,
                 *,
                 server=None,
                 api_url=None,
                 username=None,
                 password=None,
                 proxies=None,
                 **other
                 ) -> None:
        """Initialize RestClient."""
        self.http_client: HTTPClient = HTTPClient()
        self.state: ClientState = ClientState.NOT_CONNECTED

        self.server: Optional[str] = server
        self.api_url: Optional[str] = api_url  # In case server uses not standard api-route
        self.username: Optional[str] = username
        self.__password: Optional[str] = password
        self.proxies = proxies

        self.http_client.update_params(**other)

    def authenticate(self,
                     *,
                     server: Optional[str] = None,
                     api_url: Optional[str] = None,
                     username: Optional[str] = None,
                     password: Optional[str] = None,
                     **other
                     ) -> None:
        """Authenticate in Hive."""
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

    @staticmethod
    def make_api_url_from(server: str, port: Optional[int] = None) -> str:
        """Create api URL from server and port."""
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

    def get_project(self, project_id: str) -> Dict[str, Union[str, List, Dict]]:
        """Get project by id."""
        return self.http_client.get(f'{self.api_url}/project/{project_id}')

    def get_projects(self, **params) -> Dict[str, str]:
        """Get all projects."""
        return self.http_client.post(f'{self.api_url}/project/filter', params=params)

    def get_file(self, project_id: str, file_id: str) -> bytes:
        """Get file from Hive."""
        return self.http_client.get(f'{self.api_url}/project/{project_id}/graph/file/{file_id}')

    def get_issues(self, project_id: str, offset: int = 0, limit: int = 100) -> Dict[str, str]:
        """Get issues from Hive."""
        response = self.http_client.post(
            url=f'{self.api_url}/project/{project_id}/graph/issue_list?offset={offset}&limit={limit}',
            json={})
        return response

    def update_project(self, project_id: Union[str, UUID], fields: Dict) -> Dict[str, str]:
        """Update project."""
        project = self.get_project(project_id)
        # We need to merge data from project and fields to safely update project
        # We also need model to adapt data because of its specific serialized structure ¯\_(ツ)_/¯
        merged_data = project.pop('data', {}) | fields.pop('data', {})
        merged_project = project | fields | {'data': merged_data}
        merged_project = Project(**merged_project | {'id': project_id}).dict()
        merged_project['data'] = json.dumps(merged_project['data'])
        files = {k: (None, v) for k, v in merged_project.items()}
        return self.http_client.put(f'{self.api_url}/project/{project_id}', files=files)

    def update_issue(self, project_id: Union[str, UUID], issue_id: Union[str, UUID], fields: Dict) -> Dict[str, str]:
        """Update issue."""
        return self.http_client.patch(f'{self.api_url}/project/{project_id}/graph/issues/{issue_id}', json=fields)

    def archive_project(self, project_id: Union[str, UUID]) -> Dict[str, str]:
        """Send to archive project."""
        return self.http_client.put(f'{self.api_url}/project/{project_id}/archive', json={'archived': True})

    def activate_project(self, project_id: Union[str, UUID]) -> Dict[str, str]:
        """Take from archive project."""
        return self.http_client.put(f'{self.api_url}/project/{project_id}/archive', json={'archived': False})

    @property
    def proxies(self) -> MutableMapping[str, str]:
        """Get proxies."""
        return self.http_client.proxies

    @proxies.setter
    def proxies(self, proxies: Dict) -> None:
        """Set proxies."""
        self.http_client.proxies = proxies
