"""
Server app config
"""

# pylint: disable=import-error

from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from .config import CONFIG
from .models import Job, Transform, User

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
    client = AsyncIOMotorClient(CONFIG.mongo_uri)
    app.state.db = getattr(client, CONFIG.mongo_database)
    models = [Job, Transform, User]
    await init_beanie(app.state.db, document_models=models)  # type: ignore[arg-type]
