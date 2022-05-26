"""Job router."""
from datetime import datetime
from logging import getLogger

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from ..models import Job, JobIn, Transform, User
from ..util.current_user import current_user
from ..util.io import transfer_values
from ..util.job_builder import JobBuilder

router = APIRouter(prefix='/jobs', tags=['Jobs'])
logger = getLogger(__name__)


@router.post(
    '',
    summary='Creates a new job.',
    response_model=Job,
    responses={404: {'description': 'The job specifies an unknown transform.'}},
)
async def create(job_in: JobIn, user: User = Depends(current_user)):
    """Creates a job that will execute a transform.

    The job specifies a transform and its inputs. Upon response,
    it contains the execution return values of the transform code.

    Notes:
        The schema property of the outputs in the response either define a valid JSON
        schema (at least one of the properties `type`, `enum` or `const` are defined),
        or has a defined content type (stored in the contentMediaType property as a MIME
        type).
    """
    transform = await Transform.get(document_id=job_in.transform_id)
    if not transform:
        raise HTTPException(404, 'Unknown transform.')

    job = JobBuilder(job_in, user, transform).create()
    await job.create()

    executor = job.get_executor(transform)
    values = executor.run()

    job.update_json_schemas_with_values(values)
    transfer_values(job, values)

    job.done_at = datetime.utcnow()
    await job.replace()
    return job


@router.get('/{id}', summary='Gets a job.', response_model=Job)
async def get(id: PydanticObjectId, user: User = Depends(current_user)):
    """Gets the job specified by its identifier."""
    job = await Job.get(document_id=id)
    if not job:
        raise HTTPException(404, 'Unknown job.')
    if job.user_id != user.id:
        raise HTTPException(403, 'Access forbidden.')
    return job
