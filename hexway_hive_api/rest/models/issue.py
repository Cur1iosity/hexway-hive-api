from typing import Union, Optional, Dict, List
from uuid import UUID

import pydantic


class Issue(pydantic.BaseModel):
    """Issue model for Hive."""
    id: Union[str, UUID] = pydantic.Field(default=None, alias='uuid')
    name: str
    status: str
    assets: Optional[List[Dict]] = pydantic.Field(default=None)
    weakness_type: Optional[str] = pydantic.Field(default=None, alias='weaknessType')
    project_id: Optional[Union[str, UUID]] = pydantic.Field(default=None)

    cvss_score: Optional[float] = pydantic.Field(default=None, alias='cvssScore')
    cvss_vector: Optional[str] = pydantic.Field(default=None, alias='cvssVector')

    requests: Optional[List[Dict]] = pydantic.Field(default=None)
    files: Optional[List[Dict]] = pydantic.Field(default=None)

    additional_fields: Optional[Dict] = pydantic.Field(default=None, alias='additionalFields')
    model_config = pydantic.ConfigDict(populate_by_name=True)
