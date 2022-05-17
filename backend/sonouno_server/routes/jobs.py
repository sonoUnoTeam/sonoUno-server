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
from ..util.encoders import NumpyEncoder
from ..util.job_builder import JobBuilder

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
    expected_outputs = transform.entry_point.outputs
    if len(expected_outputs) == 0:
        return {}
    if len(expected_outputs) == 1:
        return {expected_outputs[0].id: results}
    if not isinstance(results, tuple) or len(expected_outputs) != len(results):
        raise HTTPException(
            400, 'The entry point does not return the expected number of outputs.'
        )
    return dict(zip((o.id for o in transform.entry_point.outputs), results))


def transfer_values(values: dict[str, Any], job: Job) -> None:
    """Copies outputs to job or MinIO."""
    for output_id, value in values.items():
        output = next(o for o in job.outputs if o.id == output_id)

        if output.transfer == 'json':
            try:
                json.dumps(value)

            except TypeError:
                if output.content_type != '*/*':
                    raise HTTPException(
                        422, f'Output {output_id} is not json-serializable: {value}'
                    )

                # we cannot send it via JSON, we will pickle it
                output.transfer = 'uri'
                output.content_type = 'application/octet-stream'

            else:
                if output.content_type == '*/*':
                    output.content_type = 'application/json'
                output.value = value
                continue

        if output.transfer == 'uri':
            output.value = transfer_uri(value, output, job)

        else:
            raise


def transfer_uri(value: Any, output: OutputWithValue, job: Job) -> str:
    """Stores value in MinIO."""

    buffer: BytesIO
    content_type = output.content_type
    uid = str(uuid4()).replace('-', '')[:6]
    ext = mimetypes.guess_extension(content_type)
    name = f'job-{job.id}/{output.id}-{uid}{ext}'

    if isinstance(value, np.ndarray):
        encoder = NumpyEncoder()
        buffer = encoder.encode(value, content_type, output.encoding)
        if content_type in {'*/*', 'application/octet-stream'}:
            ext = '.npz'

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
