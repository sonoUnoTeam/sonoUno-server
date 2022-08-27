import json
import logging
import mimetypes
import pickle
from collections.abc import Mapping
from io import BytesIO
from typing import Any, cast
from uuid import uuid4

import numpy
from fastapi import HTTPException

import sonounolib

from ..app import app
from ..config import CONFIG
from ..models import Job, OutputWithValue
from ..schemas import JSONSchema
from ..types import JSONSchemaType
from ..util.encoders import SonoUnoTrackEncoder, numpy_encode

__all__ = ['transfer_values']

logger = logging.getLogger(__name__)


def transfer_values(job: Job, values: Mapping[str, Any]) -> None:
    """Copies job output values to the current Job instance or MinIO.

    Arguments:
        job: The executed job.
        values: The output id to value mapping.
    """
    for output, value in job.iter_output_values(values):
        if output.transfer == 'ignore':
            continue
        json_schema = JSONSchema(output.json_schema)
        if json_schema.has_content_type():
            output.value = get_value_with_known_content_type(job, output, value)
        elif json_schema.has_json_schema():
            output.value = get_value_with_known_schema(job, output, value)
        else:
            output.value = get_value_unknown(job, output, value)


def get_value_with_known_content_type(
    job: Job, output: OutputWithValue, value: Any
) -> str | None:
    """Copies an output value with known content type to the current Job instance or
    MinIO.

    The output value can be encoded to conform to its content type.

    Arguments:
        job: The executed job.
        output: The current job output.
        value: The value of the job output as returned by the job execution.

    Returns:
        The string-encoded value for JSON transfer, otherwise the URI of the file
        encoding the output value according to its content type.
    """
    buffer, ext = get_buffer_from_value(cast(JSONSchemaType, output.json_schema), value)

    if output.transfer == 'json':
        # note: the schema may define a valid JSON schema, in which case it should
        # be copied to the property contentSchema.
        raise NotImplementedError('String-encoded JSON is not implemented.')

    if output.transfer == 'uri':
        return store_value(job, output, buffer, ext)

    raise


def get_buffer_from_value(schema: JSONSchemaType, value: Any) -> tuple[BytesIO, str]:
    """Returns the content of the job output as a binary buffer.

    Arguments:
        schema: The JSON schema if the job output.
        value: The value of the job output as returned by the job execution.

    Returns: A tuple containing
        * the binary buffer associated to the output value,
        * the file extension for the output value.
    """
    assert 'contentMediaType' in schema
    content_type = schema['contentMediaType']

    ext = mimetypes.guess_extension(content_type) or ''

    buffer: BytesIO

    if isinstance(value, BytesIO):
        buffer = value

    elif isinstance(value, numpy.ndarray):
        buffer = numpy_encode(value, schema)
        if content_type == 'application/octet-stream':
            ext = '.npz'

    elif isinstance(value, sonounolib.Track):
        encoding = schema.get('x-contentMediaEncoding', {})
        buffer = SonoUnoTrackEncoder().encode(value, encoding)

    elif content_type == 'application/json':
        buffer = BytesIO()
        buffer.write(json.dumps(value).encode())

    elif content_type == 'application/octet-stream':
        buffer = BytesIO()
        buffer.write(pickle.dumps(value))
        ext = '.pickle'

    else:
        raise TypeError(
            f'Cannot encode values of type {type(value).__name__!r} into '
            f'{content_type!r}.'
        )

    buffer.seek(0)
    return buffer, ext


def get_value_with_known_schema(job: Job, output: OutputWithValue, value: Any) -> Any:
    """Copies one output with valid json schema to the current Job instance or MinIO.

    Arguments:
        job: The executed job.
        output: The current job output.
        value: The value of the job output as returned by the job execution.

    Returns:
        The output value for JSON transfer, otherwise the URI of the JSON file encoding
        the output value.
    """
    if output.transfer == 'json':
        return value

    if output.transfer == 'uri':
        output.json_schema['contentMediaType'] = 'application/json'
        buffer = BytesIO()
        buffer.write(json.dumps(value).encode())
        return store_value(job, output, buffer, '.json')

    raise


def get_value_unknown(job: Job, output: OutputWithValue, value: Any) -> Any:
    """Copies an output value with no content type and no valid JSON schema
    to the current Job instance or MinIO.

    Arguments:
        job: The executed job.
        output: The current job output.
        value: The value of the job output as returned by the job execution.

    Returns:
        The output value for JSON transfer, otherwise the URI of the pickle file
        encoding the output value.
    """
    if output.transfer == 'json':
        try:
            json.dumps(value)

        except TypeError:
            raise HTTPException(
                422, f'Output {output.id} is not JSON-serializable: {value}'
            )
        return value

    if output.transfer == 'uri':
        output.json_schema['contentMediaType'] = 'application/octet-stream'
        buffer = BytesIO()
        buffer.write(pickle.dumps(value))
        return store_value(job, output, buffer, '.pickle')

    raise


def store_value(job: Job, output: OutputWithValue, buffer: BytesIO, ext: str) -> str:
    """Stores value in MinIO."""

    content_type = output.json_schema.get('contentMediaType')
    if not content_type:
        raise ValueError('A content type is required to store a value.')

    uid = str(uuid4()).replace('-', '')[:6]
    output_id = output.id.replace('.', '-').replace('_', '-')
    name = f'job-{job.id}/{output_id}-{uid}{ext}'

    length = buffer.getbuffer().nbytes

    client = app.state.minio
    result = client.put_object(
        'jobs', name, buffer, length=length, content_type=content_type
    )
    logger.info(f'MinIO: put_object: {dir(result)}')

    return f'{CONFIG.server_host}:9000/jobs/{name}'
