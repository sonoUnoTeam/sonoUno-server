from datetime import datetime
from typing import Any, Iterator, Mapping, Sequence, cast

from beanie import Document, PydanticObjectId
from pydantic import BaseModel

from ..executors import LocalExecutor
from ..models.transforms import Transform
from ..schemas import JSONSchema
from ..types import JSONSchemaType
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

    def get_executor(self, transform: Transform) -> LocalExecutor:
        """Returns transform executor."""
        return LocalExecutor(self, transform)

    def iter_output_values(
        self, values: Mapping[str, Any]
    ) -> Iterator[tuple[OutputWithValue, Any]]:
        """Iterates through the job outputs associated with input values.

        Arguments:
            values: An output id to value mapping.
        """
        for output_id, value in values.items():
            output = next(o for o in self.outputs if o.id == output_id)
            yield output, value

    def update_json_schemas_with_values(self, values: Mapping[str, Any]) -> None:
        """Merges content type information from the actual output values returned by the
        execution of the job.

        Arguments:
            values: An output id to value mapping.
        """
        for output, value in self.iter_output_values(values):
            json_schema = JSONSchema(output.json_schema)
            json_schema.update_with_value(value)
            output.json_schema = cast(JSONSchemaType, json_schema)
