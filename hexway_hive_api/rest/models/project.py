"""
Purpose of this model is to provide project model for serialization and deserialization project that
compatible with Hive API PUT method.
"""
from typing import Union, Optional, Dict
from uuid import UUID

import pydantic


class Project(pydantic.BaseModel):
    """Project model for Hive."""
    id: Union[UUID, str]
    group_id: Union[UUID, str] = pydantic.Field(alias='projectGroupId')
    description: Optional[str] = pydantic.Field(default=None, alias='projectDescription')
    name: str = pydantic.Field(alias='projectName')
    start_date: str = pydantic.Field(alias='projectStartDate')
    end_date: str = pydantic.Field(alias='projectEndDate')
    data: Optional[Dict] = pydantic.Field(default=None)

    model_config = pydantic.ConfigDict(populate_by_name=True)

    @pydantic.model_validator(mode='before')
    def preparing(cls, values) -> Dict:
        """Prepare project model before validation."""
        values['projectGroupId'] = values.get('group').get('id')
        return values

    @pydantic.model_serializer(when_used='always')
    def serialize(self) -> Dict:
        """Serialize project model to hive project json."""
        return {
            'projectName': self.name,
            'projectDescription': self.description,
            'projectStartDate': self.start_date,
            'projectEndDate': self.end_date,
            'projectGroupId': self.group_id,
            'data': self.data
        }
