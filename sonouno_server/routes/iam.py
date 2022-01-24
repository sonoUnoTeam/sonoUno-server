"""AIM router
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from fastapi_jwt_auth import AuthJWT
from pydantic import EmailStr

from ..models.iam import AccessToken, RefreshToken
from ..models.users import User, UserAuth, UserOut
from ..util.mail import send_password_reset_email
from ..util.password import hash_password
from ..util.mail import send_verification_email

router = APIRouter(prefix="/iam", tags=["IAM"])


@router.post("/login")
async def login(user_auth: UserAuth, auth: AuthJWT = Depends()):
    """Authenticates and returns the user's JWT"""
    user = await User.by_email(user_auth.email)
    if user is None or hash_password(user_auth.password) != user.password:
        raise HTTPException(status_code=401, detail="Bad email or password")
    access_token = auth.create_access_token(subject=user.email)
    refresh_token = auth.create_refresh_token(subject=user.email)
    return RefreshToken(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh")
async def refresh(auth: AuthJWT = Depends()):
    """Returns a new access token from a refresh token"""
    auth.jwt_refresh_token_required()
    access_token = auth.create_access_token(subject=auth.get_jwt_subject())
    return AccessToken(access_token=access_token)


@router.post("/forgot-password")
async def forgot_password(
    email: EmailStr = Body(..., embed=True), auth: AuthJWT = Depends()
):
    """Sends password reset email"""
    user = await User.by_email(email)
    if user.email_confirmed_at is not None:
        raise HTTPException(400, "Email is already verified")
    if user.disabled:
        raise HTTPException(400, "Your account is disabled")
    token = auth.create_access_token(user.email)
    await send_password_reset_email(email, token)
    return Response(status_code=200)


@router.post("/reset-password/{token}", response_model=UserOut)
async def reset_password(
    token: str, password: str = Body(..., embed=True), auth: AuthJWT = Depends()
):
    """Reset user password from token value"""
    # Manually assign the token value
    auth._token = token  # pylint: disable=protected-access
    user = await User.by_email(auth.get_jwt_subject())
    if user.email_confirmed_at is not None:
        raise HTTPException(400, "Email is already verified")
    if user.disabled:
        raise HTTPException(400, "Your account is disabled")
    user.password = hash_password(password)
    await user.save()
    return user


@router.post("/verify")
async def request_verification_email(
    email: EmailStr = Body(..., embed=True), auth: AuthJWT = Depends()
):
    """Send the user a verification email"""
    user = await User.by_email(email)
    if user.email_confirmed_at is not None:
        raise HTTPException(400, "Email is already verified")
    if user.disabled:
        raise HTTPException(400, "Your account is disabled")
    token = auth.create_access_token(user.email)
    await send_verification_email(email, token)
    return Response(status_code=200)


@router.post("/verify/{token}")
async def verify_email(token: str, auth: AuthJWT = Depends()):
    """Verify the user's email with the supplied token"""
    # Manually assign the token value
    auth._token = token  # pylint: disable=protected-access
    user = await User.by_email(auth.get_jwt_subject())
    if user.email_confirmed_at is not None:
        raise HTTPException(400, "Email is already verified")
    if user.disabled:
        raise HTTPException(400, "Your account is disabled")
    user.email_confirmed_at = datetime.now(tz=timezone.utc)
    await user.save()
    return Response(status_code=200)
