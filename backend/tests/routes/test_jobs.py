from sonouno_server.models import Job


async def test_create(client, user_auth, public_transform):
    job_in = {
        'transform_id': str(public_transform.id),
        'inputs': [
            {
                'id': 'pipeline.param1',
                'value': 'test',
            },
        ],
    }
    response = await client.post('/jobs', json=job_in, headers=user_auth)
    assert response.status_code == 200
    actual_job = Job(**response.json())
    output = next(o for o in actual_job.outputs if o.id == 'pipeline.0')
    assert output.value == ['test', [4, 14]]
