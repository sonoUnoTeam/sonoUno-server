"""Server main runtime
"""

# pylint: disable=unused-import

from . import jwt  # nopycln: import  # noqa: F401
from .app import app
from .routes.iam import router as aim_router
from .routes.jobs import router as job_router
from .routes.system import router as system_router
from .routes.transforms import router as transform_router
from .routes.users import router as user_router

app.include_router(aim_router)
app.include_router(job_router)
app.include_router(system_router)
app.include_router(transform_router)
app.include_router(user_router)
