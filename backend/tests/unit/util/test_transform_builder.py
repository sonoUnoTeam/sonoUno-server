from typing import Any

import pytest

from sonouno_server.models import TransformIn
from sonouno_server.util.transform_builder import TransformBuilder
from tests.data import create_user


def test_transform_builder():
    source = """
from streamunolib import exposed

@exposed
def c(param_c: int):
    pass

def b(param_b: str):
    c(2)
    c(3)

@exposed
def pipeline(param1_pipeline: str = 'default1', param2_pipeline: int = 42) -> str:
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
    pytest.xfail(f'Write tests for transform {transform.id}')


@pytest.mark.parametrize(
    'return_type, expected_outputs',
    [
        ('', {0: Any}),
        ('-> Any', {0: Any}),
        ('-> str', {0: str}),
        ('-> tuple', {0: tuple}),
        ('-> tuple[int, float]', {0: int, 1: float}),
        ('-> list[int]', {0: list[int]}),
        ('-> namedtuple("Out1", "x, y")', {'x': Any, 'y': Any}),
        ('-> NamedTuple("Out2", x=int, y=float)', {'x': int, 'y': float}),
    ],
)
def test_transform_builder_outputs(return_type, expected_outputs):
    source = f"""
from collections import namedtuple
from typing import Any, NamedTuple
from streamunolib import exposed

@exposed
def pipeline(){return_type}:
    pass
    """
    user = create_user()
    transform_in = TransformIn(
        name='Test transform',
        language='python',
        source=source,
        entry_point={'name': 'pipeline'},
    )
    builder = TransformBuilder(transform_in, user)
    all_funcs = builder.extract_all_functions()
    func = next(_ for _ in all_funcs if _.__name__ == 'pipeline')
    tp_return = func.__annotations__.get('return')
    actual_outputs = builder.extract_output_types(tp_return)
    assert actual_outputs == expected_outputs
