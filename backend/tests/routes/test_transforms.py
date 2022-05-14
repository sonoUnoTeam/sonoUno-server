import pytest

from sonouno_server.models import ExposedFunction, Transform

from ..data import added_transform


def test_create(user, public_transform):
    assert user.id == public_transform.user_id
    assert public_transform.public
    assert public_transform.language == 'python'
    assert isinstance(public_transform.entry_point, ExposedFunction)


async def test_get_public_from_creator(client, user_auth, public_transform):
    response = await client.get(f'/transforms/{public_transform.id}', headers=user_auth)
    assert response.status_code == 200
    actual_transform = Transform(**response.json())
    assert actual_transform == public_transform


async def test_get_private_from_creator(client, user_auth, private_transform):
    response = await client.get(
        f'/transforms/{private_transform.id}', headers=user_auth
    )
    assert response.status_code == 200
    actual_transform = Transform(**response.json())
    assert actual_transform == private_transform


async def test_get_public_from_other(client, user2_auth, public_transform):
    response = await client.get(
        f'/transforms/{public_transform.id}', headers=user2_auth
    )
    assert response.status_code == 200
    actual_transform = Transform(**response.json())
    assert actual_transform == public_transform


async def test_get_private_from_other(client, user2_auth, private_transform):
    response = await client.get(
        f'/transforms/{private_transform.id}', headers=user2_auth
    )
    assert response.status_code == 403


async def test_get_unknown(client, user_auth):
    response = await client.get(
        '/transforms/62421e941458ac389cf3b087', headers=user_auth
    )
    assert response.status_code == 404


async def test_delete_from_creator(client, user, user_auth):
    async with added_transform(user=user) as transform:
        response = await client.get(f'/transforms/{transform.id}', headers=user_auth)
        assert response.status_code == 200
        response = await client.delete(f'/transforms/{transform.id}', headers=user_auth)
        assert response.status_code == 204
        response = await client.get(f'/transforms/{transform.id}', headers=user_auth)
        assert response.status_code == 404


async def test_delete_from_other(client, user, user2_auth):
    async with added_transform(user=user) as transform:
        response = await client.delete(
            f'/transforms/{transform.id}', headers=user2_auth
        )
        assert response.status_code == 403
