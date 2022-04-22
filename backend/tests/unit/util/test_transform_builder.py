import pytest

from sonouno_server.models import TransformIn
from sonouno_server.util.transform_builder import TransformBuilder

from tests.data import create_user


def test_transform_builder():
    source = """
from sonouno_server import exposed

@exposed
def c(param_c: int):
    pass

def b(param_b: str):
    c(2)
    c(3)

@exposed
def pipeline(param1_pipeline: str = 'default1', param2_pipeline: int = 42):
    b(param1_pipeline)
    return 'ok'
    """
    user = create_user()
    transform_in = TransformIn(
        name='Test transform',
        language='python',
        source=source,
        entry_point={'name': 'pipeline'},
    )
    transform = TransformBuilder(transform_in, user).create()
    pytest.xfail('Write me')
