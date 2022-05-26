"""AIM router
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from pydantic import EmailStr

from ..models.iam import AccessToken, RefreshToken
from ..models.users import User, UserAuth, UserOut
from ..util.mail import send_password_reset_email, send_verification_email
from ..util.password import hash_password

router = APIRouter(prefix='/iam', tags=['IAM'])


@router.post(
    '/login',
    summary='Authenticates a user.',
    responses={401: {'description': 'Bad email or password.'}},
    response_model=RefreshToken,
)
async def login(user_auth: UserAuth, auth: AuthJWT = Depends()):
    """Authenticates and returns the user's access and refresh tokens."""
    user = await User.by_email(user_auth.email)
    if user is None or hash_password(user_auth.password) != user.password:
        raise HTTPException(status_code=401, detail='Bad email or password.')
    access_token = auth.create_access_token(subject=user.email)
    refresh_token = auth.create_refresh_token(subject=user.email)
    return RefreshToken(access_token=access_token, refresh_token=refresh_token)


@router.post(
    '/refresh',
    summary='Requests an access token using the refresh token.',
    response_model=AccessToken,
)
async def refresh(auth: AuthJWT = Depends()):
    """Returns a new access token from a refresh token."""
    auth.jwt_refresh_token_required()
    access_token = auth.create_access_token(subject=auth.get_jwt_subject())
    return AccessToken(access_token=access_token)


@router.post(
    '/forgot-password', summary='Sends an email to reset the password.', status_code=204
)
async def forgot_password(
    email: EmailStr = Body(..., embed=True), auth: AuthJWT = Depends()
):
    """Sends an email that contains a token to be sent back in order to reset the user's
    password."""
    user = await User.by_email(email)
    if user is None:
        return None
    if user.email_confirmed_at:
        raise HTTPException(400, 'Email is already verified.')
    if user.disabled:
        raise HTTPException(400, 'Your account is disabled.')
    token = auth.create_access_token(user.email)
    await send_password_reset_email(email, token)


@router.post(
    '/reset-password/{token}',
    summary="Resets a user's password.",
    response_model=UserOut,
)
async def reset_password(
    token: str, password: str = Body(..., embed=True), auth: AuthJWT = Depends()
):
    """Resets the user's password by supplying the token sent via email."""
    # Manually assign the token value
    auth._token = token
    user = await User.by_email(auth.get_jwt_subject())
    if user is None:
        raise HTTPException(400, 'User has been deleted from the database.')
    if user.email_confirmed_at is not None:
        raise HTTPException(400, 'Email is already verified.')
    if user.disabled:
        raise HTTPException(400, 'Your account is disabled.')
    user.password = hash_password(password)
    await user.save()
    return user


@router.post('/verify', summary='Sends an verification email.', status_code=204)
async def request_verification_email(
    email: EmailStr = Body(..., embed=True), auth: AuthJWT = Depends()
):
    """Sends the user a verification email that contains a token to be sent back
    to verify the email."""
    user = await User.by_email(email)
    if user is None:
        raise HTTPException(400, 'User has been deleted from the database.')
    if user.email_confirmed_at is not None:
        raise HTTPException(400, 'Email is already verified.')
    if user.disabled:
        raise HTTPException(400, 'Your account is disabled.')
    token = auth.create_access_token(user.email)
    await send_verification_email(email, token)


@router.post(
    '/verify/{token}', summary='Verifies the verification email token.', status_code=204
)
async def verify_email(token: str, auth: AuthJWT = Depends()):
    """Verifies the user's email by supplying the token sent via email."""
    # Manually assign the token value
    auth._token = token  # pylint: disable=protected-access
    user = await User.by_email(auth.get_jwt_subject())
    if user is None:
        raise HTTPException(400, 'User has been deleted from the database.')
    if user.email_confirmed_at is not None:
        raise HTTPException(400, 'Email is already verified.')
    if user.disabled:
        raise HTTPException(400, 'Your account is disabled.')
    user.email_confirmed_at = datetime.now(tz=timezone.utc)
    await user.save()
