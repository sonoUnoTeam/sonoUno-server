from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime
from typing import Any, cast

from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from pydantic import Field as F

from ..executors import LocalExecutor
from ..models.transforms import Transform
from ..schemas import JSONSchema
from ..types import JSONSchemaType
from .variables import Input, InputIn, OutputIn, OutputWithValue


class JobIn(BaseModel):
    transform_id: PydanticObjectId = F(
        title='The identifier of the transform to be executed.'
    )
    inputs: Sequence[InputIn] = F([], title='Specifications of the transform inputs.')
    outputs: Sequence[OutputIn] = F([], title='Specifications fo the transform outputs')

    class Config:
        schema_extra = {
            'description': 'Input to create a job.',
            'examples': [
                {
                    'transform_id': '628f4b1f2adff4274a708523',
                    'inputs': [{'id': 'pipeline.repeat', 'value': 2}],
                },
            ],
        }


class Job(JobIn, Document):
    user_id: PydanticObjectId = F(title='The user requesting the job.')
    done_at: datetime | None = F(None, title='Date and time when the job finished.')
    inputs: Sequence[Input] = F([], title='The specified inputs.')
    outputs: Sequence[OutputWithValue] = F(
        [], title='The resulting fully specified outputs.'
    )

    @property
    def created_at(self) -> datetime:
        """Datetime job was created from ID"""
        if self.id is None:
            raise RuntimeError('Job has not been inserted in the database yet.')
        return self.id.generation_time

    class Config:
        schema_extra = {
            'description': 'The job, as stored in the database.',
            'examples': [
                {
                    '_id': '628f4d4255358f834b9df030',
                    'transform_id': '628f4b1f2adff4274a708523',
                    'inputs': [
                        {
                            'id': 'pipeline.repeat',
                            'value': 2,
                            'name': 'repeat',
                            'schema': {
                                '$schema': 'http://json-schema.org/draft/2020-12/schema#',  # noqa: E501
                                'type': 'integer',
                                'default': True,
                            },
                            'required': False,
                            'modifiable': True,
                        }
                    ],
                    'outputs': [
                        {
                            'id': 'pipeline.0',
                            'schema': {
                                '$schema': 'http://json-schema.org/draft/2020-12/schema#',  # noqa: E501
                                'contentMediaType': 'audio/x-wav',
                                'x-contentMediaEncoding': {
                                    'format': 'int16',
                                    'rate': 44100,
                                },
                            },
                            'transfer': 'uri',
                            'name': '0',
                            'value': 'http://api.sonouno.org.ar:9000/jobs/job-628f4d4255358f834b9df030/pipeline-0-726141.wav',  # noqa: E501
                        }
                    ],
                    'user_id': '628f0baa98325a42409ae3bd',
                    'done_at': '2022-05-26T09:49:55.058357',
                }
            ],
        }

    def get_executor(self, transform: Transform) -> LocalExecutor:
        """Returns the transform executor."""
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
