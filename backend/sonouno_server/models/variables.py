from typing import Annotated, Any

from pydantic import BaseModel
from pydantic import Field as F

from ..types import JSONSchemaType, TransferType


class InputIn(BaseModel):
    id: Annotated[str, F(title='Unique identifier of the exposed function argument.')]
    value: Annotated[Any, F(title='Input value of the exposed function.')]

    class Config:
        schema_extra = {
            'description': 'An exposed function input as sent by the client.',
            'examples': [
                {
                    'id': 'pipeline.input_data_uri',
                    'value': 'https://dataserver.org/experiments/2408ebd6-b84e.json',
                },
                {
                    'id': 'pipeline.filter_number',
                    'value': 2,
                },
            ],
        }


class Input(InputIn):
    name: Annotated[str, F(title='The parameter name.')]
    json_schema: Annotated[JSONSchemaType, F(title='The JSON schema of the argument.')]
    required: Annotated[bool, F(title='True if it is a positional argument.')]
    modifiable: Annotated[bool, F(title='True if it is not set in the source code.')]

    class Config:
        fields = {'json_schema': 'schema'}
        schema_extra = {
            'description': 'An exposed function input, as used by the transforms and jobs.',  # noqa: E501
            'examples': [
                {
                    'title': 'The URI of the main pipeline input.',
                    'id': 'pipeline.input_data_uri',
                    'name': 'input_data_uri',
                    'value': 'https://dataserver.org/experiments/2408ebd6-b84e.json',
                    'json_schema': {
                        'type': 'string',
                        '$schema': 'http://json-schema.org/draft/2020-12/schema#',
                    },
                    'required': True,
                    'modifiable': True,
                },
                {
                    'id': 'pipeline.filter_number',
                    'name': 'filter_number',
                    'value': 2,
                    'json_schema': {
                        'title': 'The filter to be applied to the data.',
                        'type': 'integer',
                        'default': 1,
                        'minimum': 1,
                        'maximum': 8,
                        '$schema': 'http://json-schema.org/draft/2020-12/schema#',
                    },
                    'required': False,
                    'modifiable': True,
                },
            ],
        }


class OutputIn(BaseModel):
    id: Annotated[str, F(title='Unique identifier of the output.')]
    json_schema: Annotated[JSONSchemaType, F(title='The JSON schema of the output.')]
    transfer: Annotated[
        TransferType,
        F(title='Transfer mode for the returned value: `json`, `uri` or `ignore`.'),
    ] = 'ignore'

    class Config:
        fields = {'json_schema': 'schema'}
        schema_extra = {
            'description': """An exposed function output, as specified in the job by the
 client. The content media type and the encoding can be requested if the pipeline
 returns some generic content.""",
            'examples': [
                {
                    'id': 'pipeline.output_0',
                    'json_schema': {
                        'contentMediaType': 'audio/x-wav',
                        'x-contentMediaEncoding': {
                            'format': 'int32',
                        },
                    },
                }
            ],
        }


class Output(OutputIn):
    name: Annotated[str, F(title='Name of the output')]

    class Config:
        schema_extra = {
            'description': 'An exposed function output, as used by the transforms.',
            'examples': [
                {
                    'id': 'pipeline.output_0',
                    'name': 'output_0',
                    'json_schema': {
                        'title': 'The sonified experimental data.',
                        'contentMediaType': 'audio/*',
                        'x-contentMediaEncoding': {
                            'max_amplitude': 'int16',
                        },
                    },
                    'transfer': 'uri',
                }
            ],
        }


class OutputWithValue(Output):
    value: Annotated[Any, F(title='The returned value for this output.')] = None

    class Config:
        schema_extra = {
            'description': 'An exposed function output with its value after execution, as returned by the jobs.',  # noqa: E501
            'examples': [
                {
                    'id': 'pipeline.output_0',
                    'name': 'output_0',
                    'json_schema': {
                        'title': 'The sonified experimental data.',
                        'contentMediaType': 'audio/x-wav',
                        'x-contentMediaEncoding': {
                            'max_amplitude': 'int16',
                            'format': 'float32',
                        },
                    },
                    'transfer': 'uri',
                    'value': 'https://api.sonouno.org.ar/jobs/job-628d6e1da28f6b0c91687372/pipeline-output-0-e8f668.wav',  # noqa: E501
                }
            ],
        }
