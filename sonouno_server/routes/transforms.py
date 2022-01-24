"""User router.
"""

from fastapi import APIRouter, Depends
from beanie.operators import Or

from ..models.transforms import TransformIn, Transform
from ..models.users import User
from ..util.current_user import current_user

router = APIRouter(prefix="/transforms", tags=["Transforms"])


@router.post("", response_model=Transform)
async def create(transform_in: TransformIn, user: User = Depends(current_user)):
    """Creates a new transform."""
    transform = Transform(
        user_id=str(user.id),
        name=transform_in.name,
        description=transform_in.description,
        public=transform_in.public,
        nodes=transform_in.nodes,
        edges=transform_in.edges,
    )
    await transform.create()
    return transform


@router.get("", response_model=list[Transform])
async def list_(user: User = Depends(current_user)):
    """Lists the transforms either public or belonging to a user."""
    criteria = Or(Transform.user_id == user.id, Transform.public == True)
    transforms = await Transform.find(criteria).to_list()
    return transforms
