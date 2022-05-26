"""System router.
"""
from fastapi import APIRouter

from .. import __version__ as backend_version
from ..models.system import SystemInfo

router = APIRouter(prefix='/system', tags=['System'])


@router.get('', summary='Gets system information.', response_model=SystemInfo)
async def get():
    """Gets system information, such as the backend version."""
    return {'backend_version': backend_version}
