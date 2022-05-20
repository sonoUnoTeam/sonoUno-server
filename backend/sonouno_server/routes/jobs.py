"""Job router.
"""
import json
import mimetypes
import pickle
from datetime import datetime
from io import BytesIO
from logging import getLogger
from typing import Any, Mapping
from uuid import uuid4

import numpy as np
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from ..app import app
from ..config import CONFIG
from ..models import Job, JobIn, OutputWithValue, Transform, User
from ..types import JSONSchema
from ..util.current_user import current_user
from ..util.encoders import numpy_encode
from ..util.job_builder import JobBuilder
from ..util.schemas import merge_schema_with_value

router = APIRouter(prefix='/jobs', tags=['Jobs'])
logger = getLogger(__name__)


@router.post('', response_model=Job)
async def create(job_in: JobIn, user: User = Depends(current_user)):
    """Creates a new job."""
    transform = await Transform.get(document_id=job_in.transform_id)
    if not transform:
        raise HTTPException(404, 'Unknown transform.')

    job = JobBuilder(job_in, user, transform).create()
    await job.create()

    values = run_job(job, transform)
    update_job_schemas_with_values(job, values)
    transfer_values(job, values)

    job.done_at = datetime.utcnow()
    await job.replace()
    return job


@router.get('/{id}', response_model=Job)
async def get(id: PydanticObjectId, user: User = Depends(current_user)):
    """Gets a job.

    Notes:
        The schema of the returned outputs are ensured to have at least one of the
        following properties defined:
            * `type`
            * `enum`
            * `const`
            * `contentMediaType`
        It proceeds that if the schema validates against all instances (when `type`,
        `enum` and `const` are not set), a content type is defined (contentMediaType has
        the value of a MIME type).

    """
    job = await Job.get(document_id=id)
    if not job:
        raise HTTPException(404, 'Unknown job.')
    if job.user_id != user.id:
        raise HTTPException(403, 'Access forbidden.')
    return job


def run_job(job: Job, transform: Transform) -> Mapping[str, Any]:
    """Very naively injects the inputs and extracts the outputs of the job."""
    locals_ = {'zzz_inputs': prepare_inputs(job)}
    # XXX it should be executed in a container
    source = (
        transform.source
        + f'\nzzz_results = {transform.entry_point.name}(**zzz_inputs)\n'
    )
    exec(source, locals_, locals_)
    return prepare_outputs(locals_['zzz_results'], transform)


def prepare_inputs(job: Job) -> Mapping[str, Any]:
    # XXX only the values of the entry point inputs can be modified
    return {i.name: i.value for i in job.inputs}


def prepare_outputs(results: Any, transform: Transform) -> Mapping[str, Any]:
    """Unpacks the value returned by the transform entry point.

    Arguments:
        results: The returned value of the transform entry point.
        transform: The current transform.

    Returns:
        A mapping output id to value.
    """
    expected_outputs = transform.entry_point.outputs
    if len(expected_outputs) == 0:
        return {}
    if len(expected_outputs) == 1:
        return {expected_outputs[0].id: results}
    if not isinstance(results, tuple) or len(expected_outputs) != len(results):
        raise HTTPException(
            422, 'The entry point does not return the expected number of outputs.'
        )
    return dict(zip((o.id for o in transform.entry_point.outputs), results))


def update_job_schemas_with_values(job: Job, values: Mapping[str, Any]) -> None:
    for output_id, value in values.items():
        output = next(o for o in job.outputs if o.id == output_id)
        output.json_schema = merge_schema_with_value(output.json_schema, value)


def transfer_values(job: Job, values: Mapping[str, Any]) -> None:
    """Copies job output values to the current job or MinIO.

    Arguments:
        job: The executed job.
        values: The output id to value mapping.
    """
    for output_id, value in values.items():
        output = next(o for o in job.outputs if o.id == output_id)
        if 'contentMediaType' in output.json_schema:
            output.value = get_value_with_known_content_type(job, output, value)
        else:
            output.value = get_value_with_known_schema(job, output, value)


def get_value_with_known_content_type(
    job: Job, output: OutputWithValue, value: Any
) -> str | None:
    """Copies an output value with known content type to the current job or MinIO.

    Arguments:
        job: The executed job.
        output: The current job output.
        value: The value of the job output as returned by the job execution.
    """
    if output.transfer == 'ignore':
        return None

    buffer, ext = get_buffer_from_value(output.json_schema, value)

    if output.transfer == 'json':
        raise NotImplementedError('String-encoded JSON is not implemented.')

    if output.transfer == 'uri':
        return store_value(job, output, buffer, ext)

    raise


def get_buffer_from_value(schema: JSONSchema, value: Any) -> tuple[BytesIO, str]:
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
    assert content_type is not None

    ext = mimetypes.guess_extension(content_type) or ''

    buffer: BytesIO

    if isinstance(value, BytesIO):
        buffer = value

    elif isinstance(value, np.ndarray):
        buffer = numpy_encode(value, schema)
        if content_type == 'application/octet-stream':
            ext = '.npz'

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
    """Copies one output with validated json schema to the current job or MinIO.

    Arguments:
        job: The executed job.
        output: The current job output.
        value: The value of the job output as returned by the job execution.
    """
    if output.transfer == 'ignore':
        return None

    if output.transfer == 'json':
        try:
            json.dumps(value)

        except TypeError:
            raise HTTPException(
                422, f'Output {output.id} is not json-serializable: {value}'
            )

        return value

    if output.transfer == 'uri':
        output.json_schema['contentMediaType'] = 'application/json'
        buffer = BytesIO()
        buffer.write(json.dumps(value).encode())
        return store_value(job, output, buffer, '.json')

    raise


def store_value(job: Job, output: OutputWithValue, buffer: BytesIO, ext: str) -> str:
    """Stores value in MinIO."""

    content_type = output.json_schema.get('contentMediaType')
    assert content_type is not None

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
