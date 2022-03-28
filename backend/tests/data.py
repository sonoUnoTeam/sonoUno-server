"""Test data handlers
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from sonouno_server.models import User, Transform
from sonouno_server.models.users import User
from sonouno_server.util.password import hash_password


async def add_empty_user() -> None:
    """Adds test users to user collection"""
    empty_user = User(
        email="empty@test.io",
        password=hash_password("empty@test.io"),
        email_confirmed_at=datetime.now(tz=timezone.utc),
    )
    await empty_user.create()


@asynccontextmanager
async def added_user() -> User:
    """Adds a test user to User collection"""
    email = f"{uuid4()}@test.io"
    user = User(
        email=email,
        password=hash_password(email),
        email_confirmed_at=datetime.now(tz=timezone.utc),
    )
    try:
        yield await user.create()
    finally:
        await user.delete()


@asynccontextmanager
async def added_transform(user: User, public: bool = True) -> Transform:
    """Adds a test transform to the Transform collection"""
    transform = Transform(
        name=str(uuid4()),
        description=str(uuid4()),
        user_id=user.id,
        public=public,
        nodes=[],
        edges=[],
    )
    try:
        yield await transform.create()
    finally:
        await transform.delete()
