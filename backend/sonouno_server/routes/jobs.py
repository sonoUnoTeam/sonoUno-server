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


@router.post('', response_model=Job)
async def create(job_in: JobIn, user: User = Depends(current_user)):
    """Creates a new job.

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
    transform = await Transform.get(document_id=job_in.transform_id)
    if not transform:
        raise HTTPException(404, 'Unknown transform.')

    job = JobBuilder(job_in, user, transform).create()
    await job.create()

    executor = job.get_executor(transform)
    values = executor.run()

    job.update_job_schemas_with_values(values)
    transfer_values(job, values)

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
