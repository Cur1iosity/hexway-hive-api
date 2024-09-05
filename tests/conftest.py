import json
import os
from typing import Type, Dict

import pytest

from hexway_hive_api.rest.models.project import Project
from hexway_hive_api.rest.models.issue import Issue

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'test_data')


def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), 'r') as file:
        return json.load(file)


@pytest.fixture
def get_project() -> Dict:
    """Returns example raw fields data."""
    return load_json('get_project.json')


@pytest.fixture
def project_model() -> Type[Project]:
    return Project


@pytest.fixture
def get_issue() -> Dict:
    """Returns example raw fields data."""
    return load_json('get_issue.json')


@pytest.fixture
def issue_model() -> Type[Issue]:
    return Issue
