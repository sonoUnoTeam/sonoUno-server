"""Test data handlers
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from beanie import PydanticObjectId

from sonouno_server.models import Transform, User
from sonouno_server.models.transforms import TransformIn
from sonouno_server.util.password import hash_password
from sonouno_server.util.transform_builder import TransformBuilder


def create_user(email: str = '') -> User:
    if not email:
        email = f'{uuid4()}@test.io'
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
async def added_user() -> AsyncIterator[User]:
    """Adds a test user to User collection"""
    user = create_user()
    try:
        yield await user.create()
    finally:
        await user.delete()


def create_transform(user: User, public: bool = True, source: str = '') -> Transform:
    """Transform factory"""
    if not source:
        source = """
from streamunolib import exposed

@exposed
def inner_stage(x):
    return x + 1

@exposed
def pipeline(param1: str, param2: int = 3):
    start = inner_stage(param2)
    return param1, [start, start + 10]
    """
    transform_in = TransformIn(
        name=str(uuid4()),
        description=str(uuid4()),
        public=public,
        language='python',
        source=source,
        entry_point={'name': 'pipeline'},
    )
    return TransformBuilder(transform_in, user).create()


@asynccontextmanager
async def added_transform(
    user: User, public: bool = True, source: str = ''
) -> AsyncIterator[Transform]:
    """Adds a test transform to the Transform collection"""
    transform = create_transform(user, public, source)
    try:
        yield await transform.create()
    finally:
        await transform.delete()
