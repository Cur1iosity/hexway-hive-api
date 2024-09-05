import uuid
from typing import Dict


def test_rest_issue_deserealization(get_issue, issue_model) -> None:
    """Test deserialization hive issue json to issue model."""
    project_id = uuid.uuid4()
    issue_dict = get_issue | {'issue_id': project_id}
    Issue = issue_model
    issue = Issue(**issue_dict)

    assert issue.id
    assert issue.additional_fields is None or isinstance(issue.additional_fields, Dict)
    assert issue.name == get_issue.get('name')
    assert issue.project_id == project_id


def test_rest_issue_serealization(get_issue, issue_model) -> None:
    """Test serialization issue model to hive issue json."""
    project_id = uuid.uuid4()
    issue_dict = get_issue | {'issue_id': project_id}
    Issue = issue_model
    issue = Issue(**issue_dict)
    issue_dict = issue.model_dump(by_alias=True)

    assert issue_dict.get('uuid') == get_issue.get('uuid')
    assert issue_dict.get('weaknessType') == get_issue.get('weaknessType')
    assert issue_dict.get('cvssScore') == get_issue.get('cvssScore')
    assert issue_dict.get('cvssVector') == get_issue.get('cvssVector')
