"""Transforms router.
"""

from beanie import PydanticObjectId
from beanie.operators import Or
from fastapi import APIRouter, Depends, HTTPException, Response

from ..models.transforms import Transform, TransformIn
from ..models.users import User
from ..util.current_user import current_user
from ..util.transform_builder import TransformBuilder

router = APIRouter(prefix='/transforms', tags=['Transforms'])


@router.post('', response_model=Transform)
async def create(transform_in: TransformIn, user: User = Depends(current_user)):
    """Creates a new transform."""
    transform = TransformBuilder(transform_in, user).create()
    await transform.create()
    return transform


@router.get('', response_model=list[Transform])
async def list_(user: User = Depends(current_user)):
    """Lists the transforms either public or belonging to a user."""
    criteria = Or(Transform.user_id == user.id, Transform.public == True)  # noqa: E712
    transforms = await Transform.find(criteria).to_list()
    return transforms


@router.get('/{id}', response_model=Transform)
async def get(id: PydanticObjectId, user: User = Depends(current_user)):
    """Gets a transform."""
    transform = await Transform.get(document_id=id)
    if not transform:
        raise HTTPException(404, 'Unknown transform.')
    if transform.user_id != user.id and not transform.public:
        raise HTTPException(403, 'Access forbidden.')
    return transform


@router.delete('/{id}')
async def delete(id: PydanticObjectId, user: User = Depends(current_user)):
    """Deletes a transform."""
    transform = await Transform.get(document_id=id)
    if transform:
        if transform.user_id != user.id:
            raise HTTPException(403, 'Operation forbidden.')
        await transform.delete()
    return Response(status_code=204)
