"""Specific type hints used by the sonoUno server project."""

from typing import Any, Literal, TypedDict

__all__ = ['AnyType']

AnyType = Any

TransferType = Literal['ignore', 'json', 'uri']


class MediaEncoding(TypedDict, total=False):
    format: str
    range: str | tuple[float, float]
    rate: int


JSONSchema = TypedDict(
    'JSONSchema',
    {
        '$schema': str,
        '$id': str,
        'contentMediaType': str,
        'contentEncoding': str,
        'x-contentMediaEncoding': MediaEncoding,
        'description': str,
        'format': str,
        'title': str,
        'type': str,
    },
    total=False,
)
