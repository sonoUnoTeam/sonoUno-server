"""
Server app config
"""

# pylint: disable=import-error

from beanie import init_beanie
from fastapi import FastAPI
from minio import Minio
from motor.motor_asyncio import AsyncIOMotorClient

from .config import CONFIG
from .models import Job, Transform, User
from .util.minio import make_public_bucket

tags_metadata = [
    {
        'name': 'IAM',
        'description': 'Identity and Access Management.',
    },
    {
        'name': 'Users',
        'description': 'Operations with users.',
    },
    {
        'name': 'Transforms',
        'description': 'Operations with sonification transforms.',
    },
]

app = FastAPI(openapi_tags=tags_metadata)


@app.on_event('startup')
async def app_init() -> None:
    """Initialize application services"""
    motor_client = AsyncIOMotorClient(CONFIG.mongo_uri)
    app.state.db = getattr(motor_client, CONFIG.mongo_database)
    models = [Job, Transform, User]
    await init_beanie(app.state.db, document_models=models)  # type: ignore[arg-type]
    print('Init minio:')
    print(CONFIG.minio_endpoint + ':9000')
    minio_client = Minio(
        CONFIG.minio_endpoint + ':9000',
        CONFIG.minio_access_key,
        CONFIG.minio_secret_key,
        secure=False,
    )
    make_public_bucket(minio_client, 'jobs')

    print('Local Minio buckets:', minio_client.list_buckets())
    app.state.minio = minio_client
