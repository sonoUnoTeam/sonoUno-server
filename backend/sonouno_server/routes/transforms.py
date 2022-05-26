"""Transforms router.
"""

from beanie import PydanticObjectId
from beanie.operators import Or
from fastapi import APIRouter, Depends, HTTPException

from ..models.transforms import Transform, TransformIn
from ..models.users import User
from ..util.current_user import current_user
from ..util.transform_builder import TransformBuilder

router = APIRouter(prefix='/transforms', tags=['Transforms'])


@router.post('', summary='Creates a transform.', response_model=Transform)
async def create(transform_in: TransformIn, user: User = Depends(current_user)):
    """Creates a new transform in the database."""
    transform = TransformBuilder(transform_in, user).create()
    await transform.create()
    return transform


@router.get('', summary='Lists transforms.', response_model=list[Transform])
async def list_(user: User = Depends(current_user)):
    """Lists the transforms that are either public or belonging to the current user."""
    criteria = Or(Transform.user_id == user.id, Transform.public == True)  # type: ignore[arg-type]  # noqa: E712, E501
    transforms = await Transform.find(criteria).to_list()
    return transforms


@router.get(
    '/{id}',
    summary='Gets a transform.',
    response_model=Transform,
    responses={
        403: {'description': 'Access is not authorized.'},
        404: {'description': 'Unknown transform.'},
    },
)
async def get(id: PydanticObjectId, user: User = Depends(current_user)):
    """Gets the transform specified by its identifier."""
    transform = await Transform.get(document_id=id)
    if not transform:
        raise HTTPException(404, 'Unknown transform.')
    if transform.user_id != user.id and not transform.public:
        raise HTTPException(403, 'Access forbidden.')
    return transform


@router.delete(
    '/{id}',
    summary='Deletes a transform.',
    status_code=204,
    responses={403: {'description': 'Operation is not authorized.'}},
)
async def delete(id: PydanticObjectId, user: User = Depends(current_user)):
    """Deletes the transform speficied by its identifier."""
    transform = await Transform.get(document_id=id)
    if transform:
        if transform.user_id != user.id:
            raise HTTPException(403, 'Operation forbidden.')
        await transform.delete()
