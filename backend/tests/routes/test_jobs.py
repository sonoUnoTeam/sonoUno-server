import pytest

from sonouno_server.models import Job


async def test_create(client, user_auth, public_transform):
    job_in = {
        'transform_id': str(public_transform.id),
        'inputs': {
            'param1': 'test',
        },
    }
    response = await client.post('/jobs', json=job_in, headers=user_auth)
    assert response.status_code == 200
    actual_job = Job(**response.json())
    assert actual_job.results == ['test', [4, 14]]
