"""System router.
"""
from fastapi import APIRouter

from .. import __version__ as backend_version
from ..models.system import SystemInfo

router = APIRouter(prefix='/system', tags=['System'])


@router.get('', response_model=SystemInfo)
async def get():
    """Returns the system information."""
    return {'backend_version': backend_version}