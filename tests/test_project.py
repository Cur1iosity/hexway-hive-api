import uuid
from typing import Dict


def test_rest_project_deserealization(get_project, project_model) -> None:
    """Test deserialization hive project json to project model."""
    project_id = uuid.uuid4()
    project_dict = get_project | {'id': project_id}
    Project = project_model
    project = Project(**project_dict)

    assert project.id
    assert project.group_id
    assert project.start_date
    assert project.end_date
    assert project.data is None or isinstance(project.data, Dict)
    assert isinstance(project.start_date, str)
    assert isinstance(project.end_date, str)
    assert project.name == get_project.get('projectName')
    assert project.start_date == get_project.get('projectStartDate')
    assert project.end_date == get_project.get('projectEndDate')
    assert project.id == project_id
    assert project.group_id == get_project.get('group').get('id')


def test_rest_project_serealization(get_project, project_model) -> None:
    """Test serialization project model to hive project json."""
    project_id = uuid.uuid4()
    project_dict = get_project | {'id': project_id}
    Project = project_model
    project = Project(**project_dict)
    project_dict = project.dict()

    assert not project_dict.get('id')
    assert not project_dict.get('group_id')
    assert project_dict.get('projectName') == get_project.get('projectName')
    assert project_dict.get('projectStartDate') == get_project.get('projectStartDate')
    assert project_dict.get('projectEndDate') == get_project.get('projectEndDate')
