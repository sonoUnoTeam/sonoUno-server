import pytest

from sonouno_server.schemas import JSONSchema


@pytest.mark.parametrize('type_', ['application', 'audio', 'image', 'text', 'video'])
@pytest.mark.parametrize('subtype', ['a', '*'])
def test_split_content_type(type_: str, subtype: str) -> None:
    actual_type, actual_subtype = JSONSchema.split_content_type(f'{type_}/{subtype}')
    assert actual_type == type_
    assert actual_subtype == subtype


@pytest.mark.parametrize(
    'content_type',
    ['', 'a', '*', '*/', '*/*', '*/a', 'a/b', 'application', 'application/'],
)
def test_split_content_type_error(content_type: str) -> None:
    with pytest.raises(ValueError, match='Invalid media type'):
        JSONSchema.split_content_type(content_type)
