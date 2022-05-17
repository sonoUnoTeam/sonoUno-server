from datetime import datetime
from typing import Sequence

from beanie import Document, PydanticObjectId
from pydantic import BaseModel

from .variables import Input, InputIn, OutputIn, OutputWithValue


class JobIn(BaseModel):
    transform_id: PydanticObjectId
    inputs: Sequence[InputIn] = []
    outputs: Sequence[OutputIn] = []


class Job(JobIn, Document):
    user_id: PydanticObjectId
    done_at: datetime | None = None
    inputs: Sequence[Input] = []
    outputs: Sequence[OutputWithValue] = []

    @property
    def created_at(self) -> datetime:
        """Datetime job was created from ID"""
        if self.id is None:
            raise RuntimeError('Job has not been inserted in the database yet.')
        return self.id.generation_time
