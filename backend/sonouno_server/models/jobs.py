from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel


class JobIn(BaseModel):
    transform_id: PydanticObjectId
    inputs: dict[str, Any]


class Job(JobIn, Document):
    user_id: PydanticObjectId
    done_at: datetime | None = None
    results: Any | None = None

    @property
    def created_at(self) -> datetime:
        """Datetime job was created from ID"""
        if self.id is None:
            raise RuntimeError('Job has not been inserted in the database yet.')
        return self.id.generation_time
