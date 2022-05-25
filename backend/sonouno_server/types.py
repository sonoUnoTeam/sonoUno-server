"""Specific type hints used by the sonoUno server project."""
from __future__ import annotations

from typing import Any, Literal, TypedDict

__all__ = [
    'AnyType',
    'JSONSchemaType',
    'JSONType',
    'MediaEncoding',
    'TransferType',
]

AnyType = Any

TransferType = Literal['ignore', 'json', 'uri']

# mypy does not support recursive types (https://github.com/python/mypy/issues/731)
# JSONType = bool | int | float | str | dict[str, 'JSONType'] | list['JSONType'] | None
JSONType = bool | int | float | str | dict[str, Any] | list[Any] | None


class MediaEncoding(TypedDict, total=False):
    format: str
    rate: int
    max_amplitude: str | float


JSONSchemaType = TypedDict(
    'JSONSchemaType',
    {
        '$schema': str,
        '$id': str,
        # Validation Keywords for Any Instance Type
        'type': str | list[str],
        'enum': list[JSONType],
        'const': JSONType,
        # Validation Keywords for Numeric Instances
        'multipleOf': float,
        'maximum': float,
        'exclusiveMaximum': float,
        'minimum': float,
        'exclusiveMinimum': float,
        # Validation Keywords for String
        'maxLength': int,
        'minLength': int,
        'pattern': str,
        # Validation Keywords for Arrays
        'maxItems': int,
        'minItems': int,
        'uniqueItems': bool,
        'maxContains': int,
        'minContains': int,
        # Validation Keywords for Objects
        'maxProperties': int,
        'minProperties': int,
        'required': list[str],
        'dependentRequired': dict[str, list[str]],
        # Semantic Content
        'format': str,
        # Contents of String-Encoded Data
        'contentMediaType': str,
        'contentEncoding': str,
        'contentSchema': dict[str, Any],  # should be 'JSONSchemaType'
        'x-contentMediaEncoding': MediaEncoding,
        # Basic Meta-Data Annotations
        'title': str,
        'description': str,
        'default': JSONType,
        'deprecated': bool,
        'readOnly': bool,
        'writeOnly': bool,
        'examples': list[JSONType],
    },
    total=False,
)
