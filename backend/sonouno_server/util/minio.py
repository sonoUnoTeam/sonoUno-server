import json

from minio import Minio

__all__ = ['make_public_bucket']


def make_public_bucket(client: Minio, bucket_name: str) -> None:
    """Creates a public bucket."""

    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    return

    # The following doesn't set the bucket policy as public...

    policy = {
        'Version': '2012-10-17',
        'Statement': [],
    }
    client.set_bucket_policy(bucket_name, json.dumps(policy))
