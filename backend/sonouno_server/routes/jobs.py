"""Job router.
"""
import json
import mimetypes
from datetime import datetime
from io import BytesIO
from typing import Any
from uuid import uuid4

import numpy as np
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from ..app import app
from ..config import CONFIG
from ..models import Job, JobIn, OutputWithValue, Transform, User
from ..util.current_user import current_user
from ..util.encoders import numpy_encode
from ..util.job_builder import JobBuilder
from ..util.schemas import merge_schema_with_value

router = APIRouter(prefix='/jobs', tags=['Jobs'])


@router.post('', response_model=Job)
async def create(job_in: JobIn, user: User = Depends(current_user)):
    """Creates a new job."""
    transform = await Transform.get(document_id=job_in.transform_id)
    if not transform:
        raise HTTPException(404, 'Unknown transform.')

    job = JobBuilder(job_in, user, transform).create()
    await job.create()

    values = run_job(job, transform)
    transfer_values(values, job)

    job.done_at = datetime.utcnow()
    await job.replace()
    return job


@router.get('/{id}', response_model=Job)
async def get(id: PydanticObjectId, user: User = Depends(current_user)):
    """Gets a job."""
    job = await Job.get(document_id=id)
    if not job:
        raise HTTPException(404, 'Unknown job.')
    if job.user_id != user.id:
        raise HTTPException(403, 'Access forbidden.')
    return job


def run_job(job: Job, transform: Transform) -> dict[str, Any]:
    """Very naively injects the inputs and extracts the outputs of the job."""
    locals_ = {'zzz_inputs': prepare_inputs(job)}
    # XXX it should be executed in a container
    source = (
        transform.source
        + f'\nzzz_results = {transform.entry_point.name}(**zzz_inputs)\n'
    )
    exec(source, locals_, locals_)
    return prepare_values(locals_['zzz_results'], transform)


def prepare_inputs(job: Job) -> dict[str, Any]:
    # XXX only the values of the entry point inputs can be modified
    return {i.name: i.value for i in job.inputs}


def prepare_values(results: Any, transform: Transform) -> dict[str, Any]:
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


def transfer_values(values: dict[str, Any], job: Job) -> None:
    """Copies job output values to job or MinIO.

    Arguments:
        values: The output id to value mapping.
        job: The executed job.
    """
    for output_id, value in values.items():
        output = next(o for o in job.outputs if o.id == output_id)
        transfer_value(value, output, job)


def transfer_value(value: Any, output: OutputWithValue, job: Job) -> None:
    """Copies one output value to job or MinIO.

    Arguments:
        values: The value returned by the job for the current job output.
        output: The current job output.
        job: The executed job.
    """
    if output.transfer == 'json':
        if 'contentEncoding' in output.json_schema:
            raise NotImplementedError('String-encoded JSON is not implemented.')

        try:
            json.dumps(value)

        except TypeError:
            raise HTTPException(
                422, f'Output {output.id} is not json-serializable: {value}'
            )

        output.value = value

    elif output.transfer == 'uri':
        output.value = transfer_uri(value, output, job)


def transfer_uri(value: Any, output: OutputWithValue, job: Job) -> str:
    """Stores value in MinIO."""

    buffer: BytesIO
    output.json_schema = merge_schema_with_value(output.json_schema, value)
    content_type = output.json_schema.get('contentMediaType')
    if content_type is None:
        raise NotImplementedError('Should be pickled in a file')
    output.json_schema['contentMediaType'] = content_type

    uid = str(uuid4()).replace('-', '')[:6]
    ext = mimetypes.guess_extension(content_type)
    output_id = output.id.replace('.', '-').replace('_', '-')
    name = f'job-{job.id}/{output_id}-{uid}{ext}'

    if isinstance(value, np.ndarray):
        buffer = numpy_encode(value, output.json_schema)
        if content_type == 'application/octet-stream':
            ext = '.npz'

    elif isinstance(value, BytesIO):
        buffer = value

    elif content_type == 'application/json':
        buffer = BytesIO()
        buffer.write(json.dumps(value).encode())

    else:
        raise NotImplementedError

    buffer.seek(0)
    length = buffer.getbuffer().nbytes

    client = app.state.minio
    result = client.put_object(
        'jobs', name, buffer, length=length, content_type=content_type
    )
    print(f'MINIO: result put_object: {dir(result)}')

    return f'{CONFIG.server_host}:9000/jobs/{name}'
