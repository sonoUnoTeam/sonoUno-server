"""Job router.
"""
from datetime import datetime
from typing import Any

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from ..models import Job, JobIn, Transform, User
from ..util.current_user import current_user

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post('', response_model=Job)
async def create(job_in: JobIn, user: User = Depends(current_user)):
    """Creates a new job."""
    transform = await Transform.get(document_id=job_in.transform_id)
    if not transform:
        raise HTTPException(404, 'Unknown transform.')

    job = Job(
        transform_id=job_in.transform_id,
        user_id=user.id,
        inputs=job_in.inputs,
    )
    await job.create()

    job.results = run_job(job, transform)
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


def run_job(job: Job, transform: Transform) -> Any:
    locals_ = {'zzz_inputs': job.inputs}
    # XXX it should be executed in a container
    source = transform.source + f'\nzzz_results = {transform.entry_point.name}(**zzz_inputs)\n'
    exec(source, locals_, locals_)
    return locals_['zzz_results']
