"""
Pytest fixtures
"""

# pylint: disable=wrong-import-position

from typing import Iterator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from sonouno_server.main import app
from sonouno_server.models import Transform, User
from tests.data import added_transform, added_user

from .util import auth_headers


async def clear_database(server: FastAPI) -> None:
    """Empties the test database"""
    for collection in await server.db.list_collections():
        await server.db[collection["name"]].delete_many({})


@pytest.fixture
async def client() -> Iterator[AsyncClient]:
    """Async server client that handles lifespan and teardown"""
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as _client:
            try:
                yield _client
            except Exception as exc:  # pylint: disable=broad-except
                print(exc)
            finally:
                await clear_database(app)


@pytest.fixture
async def user(client) -> User:
    async with added_user() as user:
        yield user


@pytest.fixture
async def user_auth(client, user: User) -> dict[str, str]:
    return await auth_headers(client, user.email)


@pytest.fixture
async def user2(client) -> User:
    async with added_user() as user:
        yield user


@pytest.fixture
async def user2_auth(client, user2: User) -> dict[str, str]:
    return await auth_headers(client, user2.email)


@pytest.fixture
async def public_transform(user) -> Transform:
    """Adds a test transform to the Transform collection"""
    async with added_transform(user=user, public=True) as transform:
        yield transform


@pytest.fixture
async def private_transform(user) -> Transform:
    """Adds a test transform to the Transform collection"""
    async with added_transform(user=user, public=False) as transform:
        yield transform

