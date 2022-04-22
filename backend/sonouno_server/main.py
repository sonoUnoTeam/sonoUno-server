"""Server main runtime
"""

# pylint: disable=unused-import

from . import jwt
from .app import app
from .routes.iam import router as AIMRouter
from .routes.jobs import router as JobRouter
from .routes.transforms import router as TransformRouter
from .routes.users import router as UserRouter


app.include_router(AIMRouter)
app.include_router(JobRouter)
app.include_router(TransformRouter)
app.include_router(UserRouter)
