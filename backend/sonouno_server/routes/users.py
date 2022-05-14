"""User router.
"""

from fastapi import APIRouter, Depends, HTTPException, Response

from ..models.users import User, UserAuth, UserOut, UserUpdate
from ..util.current_user import current_user
from ..util.password import hash_password

router = APIRouter(prefix='/users', tags=['Users'])


@router.post('', response_model=UserOut)
async def user_registration(user_auth: UserAuth):
    """Creates a new user."""
    user = await User.by_email(user_auth.email)
    if user is not None:
        raise HTTPException(409, 'User with that email already exists.')
    hashed = hash_password(user_auth.password)
    user = User(email=user_auth.email, password=hashed)
    await user.create()
    return user


@router.get('/me', response_model=UserOut)
async def get_user(user: User = Depends(current_user)):
    """Returns the current user"""
    return user


@router.patch('/me', response_model=UserOut)
async def update_user(update: UserUpdate, user: User = Depends(current_user)):
    """Update allowed user fields"""
    user = user.copy(update=update.dict(exclude_unset=True))
    await user.save()
    return user


@router.delete('/me')
async def delete_user(user: User = Depends(current_user)):
    """Delete current user"""
    await user.delete()
    return Response(status_code=204)
