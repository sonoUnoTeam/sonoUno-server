"""
Server app config
"""

# pylint: disable=import-error

from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .config import CONFIG
from .models import Job, Transform, User

tags_metadata = [
    {
        "name": "IAM",
        "description": "Identity and Access Management.",
    },
    {
        "name": "Users",
        "description": "Operations with users.",
    },
    {
        "name": "Transforms",
        "description": "Operations with sonification transforms.",
    },
]

app = FastAPI(openapi_tags=tags_metadata)


@app.on_event("startup")
async def app_init():
    """Initialize application services"""
    client = AsyncIOMotorClient(CONFIG.mongo_uri)
    app.db = getattr(client, CONFIG.mongo_database)
    await init_beanie(app.db, document_models=[Job, Transform, User])
