"""
Server app config
"""

# pylint: disable=import-error

from beanie import init_beanie
from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from minio import Minio
from motor.motor_asyncio import AsyncIOMotorClient

from . import __version__
from .config import CONFIG
from .models import Job, Transform, User
from .util.minio import make_public_bucket

description = """
The sonoUno server is a sonification-as-a-service platform. The main resources are:

### Transforms
A transform specifies through source code how scientific data will be transformed into
sound or other media such as images or videos, and how data should be transmitted.

### Jobs
By specifying the transform identifier and its inputs, the user can create a job that
will be executed remotely. The outputs of the job are made available in the response if
they are JSON-serializable, otherwise they can be retrieved as files, served by
sonoUno's MinIO object store.
"""

tags_metadata = [
    {
        'name': 'IAM',
        'description': 'Identity and Access Management.',
    },
    {
        'name': 'Users',
        'description': 'Operations on users.',
    },
    {
        'name': 'Transforms',
        'description': 'Operations on sonification transforms.',
    },
]

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Overrides FastAPI default status code for validation errors from 422 to 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({'detail': exc.errors(), 'body': exc.body}),
    )


def custom_openapi():
    """Change validation error status code 422 -> 400."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title='sonoUno Server',
        description=description,
        version=__version__,
        tags=tags_metadata,
        routes=app.routes,
    )
    for path in openapi_schema['paths']:
        for method in openapi_schema['paths'][path]:
            if openapi_schema['paths'][path][method]['responses'].get('422'):
                openapi_schema['paths'][path][method]['responses'][
                    '400'
                ] = openapi_schema['paths'][path][method]['responses']['422']
                openapi_schema['paths'][path][method]['responses'].pop('422')
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[assignment]


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
