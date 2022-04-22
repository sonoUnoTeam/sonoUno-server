"""Test data handlers
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from beanie import PydanticObjectId

from sonouno_server.models import User, Transform
from sonouno_server.models.users import User
from sonouno_server.util.password import hash_password


def create_user(email: str = '') -> User:
    if not email:
        email = f"{uuid4()}@test.io"
    user = User(
        id=PydanticObjectId(),
        email=email,
        password=hash_password(email),
        email_confirmed_at=datetime.now(tz=timezone.utc),
    )
    return user


async def add_empty_user() -> None:
    """Adds test users to user collection"""
    empty_user = create_user('empty@test.io')
    await empty_user.create()


@asynccontextmanager
async def added_user() -> User:
    """Adds a test user to User collection"""
    user = create_user()
    try:
        yield await user.create()
    finally:
        await user.delete()


def create_transform(user: User, public: bool = True, source: str = '') -> Transform:
    """Transform factory"""
    if not source:
        source = '@exposed\ndef func():\n    pass'
    transform = Transform(
        name=str(uuid4()),
        description=str(uuid4()),
        user_id=user.id,
        public=public,
        language='python',
        source=source,
        entry_point={'name': 'func'},
    )
    return transform


@asynccontextmanager
async def added_transform(user: User, public: bool = True, source: str = '') -> Transform:
    """Adds a test transform to the Transform collection"""
    transform = create_transform(user, public, source)
    try:
        yield await transform.create()
    finally:
        await transform.delete()
