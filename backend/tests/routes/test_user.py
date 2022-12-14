"""
User information tests
"""

from httpx import AsyncClient

from tests.data import add_empty_user
from tests.util import auth_headers


async def test_user_get(client: AsyncClient) -> None:
    """Test user endpoint returns authorized user"""
    await add_empty_user()
    email = 'empty@test.io'
    auth = await auth_headers(client, email)
    resp = await client.get('/users/me', headers=auth)
    assert resp.status_code == 200
    data = resp.json()
    assert data['email'] == email


async def test_user_update(client: AsyncClient) -> None:
    """Test updating user fields"""
    await add_empty_user()
    email, name, key = 'empty@test.io', 'Empty', 'first_name'
    auth = await auth_headers(client, email)
    resp = await client.get('/users/me', headers=auth)
    assert resp.status_code == 200
    data = resp.json()
    assert data['email'] == email
    assert data[key] is None
    # Update user
    name = 'Tester'
    resp = await client.patch('/users/me', headers=auth, json={key: name})
    assert resp.status_code == 200
    data = resp.json()
    assert data['email'] == email
    assert data[key] == name
    # Check persistance
    resp = await client.get('/users/me', headers=auth)
    assert resp.status_code == 200
    data = resp.json()
    assert data['email'] == email
    assert data[key] == name


async def test_user_delete(client: AsyncClient) -> None:
    """Test deleting a user from the database"""
    await add_empty_user()
    email = 'empty@test.io'
    auth = await auth_headers(client, email)
    resp = await client.get('/users/me', headers=auth)
    assert resp.status_code == 200
    data = resp.json()
    assert data['email'] == email
    # Delete user
    resp = await client.delete('/users/me', headers=auth)
    assert resp.status_code == 204
    # Check deletion
    resp = await client.get('/users/me', headers=auth)
    assert resp.status_code == 404
