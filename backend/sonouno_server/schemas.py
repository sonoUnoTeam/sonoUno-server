from __future__ import annotations

import re
from collections.abc import Mapping
from io import BytesIO
from typing import Any

import numpy
import PIL.Image

import sonounolib
from sonouno_server.types import AnyType

from .util import merge_dicts_or_nones

__all__ = ['JSONSchema']

DEFAULT_CONTENT_TYPE = {
    'application/*': 'application/octet-stream',
    'audio/*': 'audio/x-wav',
    'image/*': 'image/png',
    'text/*': 'text/plain',
    'video/*': 'video/mp4',
}
REGEX_MIME_TYPE = re.compile(r'(application|audio|image|text|video)/(\*|[a-z0-9-]+)$')


class JSONSchema(dict):
    """Class JSON Schema, for JSON schema manipulation.

    Notes:
        Ideally, we should not have both classes JSONSchemaType and JSONSchema defined.
        That's because TypedDict can only subclass dict and not one of its subclasses.
        See https://github.com/python/mypy/issues/4201 and
        https://github.com/python/mypy/issues/2087
    """

    def __or__(self, other: Mapping[Any, Any]) -> JSONSchema:
        """Combines two JSON schemas."""
        merged_schema = JSONSchema(super().__or__(other))

        content_type = self._merge_content_types(other.get('contentMediaType'))
        if content_type:
            merged_schema['contentMediaType'] = content_type

        encoding = merge_dicts_or_nones(
            self.get('x-contentMediaEncoding'),
            other.get('x-contentMediaEncoding'),
        )
        if encoding:
            merged_schema['x-contentMediaEncoding'] = encoding

        return merged_schema

    def _merge_content_types(self, other_content_type: str | None) -> str | None:
        """Combines the content type with another one.

        Arguments:
            other_content_type: The content media type of the output, as
                requested by the job.

        Returns:
            The content type

        Raises:
            ValueError: When the content types are not compatible.
        """
        content_type = self.get('contentMediaType')
        if other_content_type is None or content_type is None:
            return other_content_type or content_type

        if not self.compatible_content_types(content_type, other_content_type):
            raise ValueError(
                f'The requested media type {other_content_type!r} is incompatible with '
                f'the actual media type {content_type}.'
            )
        if other_content_type.endswith('/*'):
            return content_type
        return other_content_type

    @staticmethod
    def compatible_content_types(type1: str, type2: str) -> bool:
        """Checks if two MIME types are compatible."""
        type1, subtype1 = JSONSchema.split_content_type(type1)
        type2, subtype2 = JSONSchema.split_content_type(type2)
        return type1 == type2 and (
            subtype1 == '*' or subtype2 == '*' or subtype1 == subtype2
        )

    @staticmethod
    def split_content_type(content_type: str) -> tuple[str, str]:
        """Splits a content type in type and subtype.

        Arguments:
            content_type: The input MIME type.

        Returns:
            A tuple containing the type and subtype of the input MIME type.

        Raises:
            ValueError: When the content type is not a valid MIME type.
        """
        match = REGEX_MIME_TYPE.match(content_type)
        if not match:
            raise ValueError(f'Invalid media type: {content_type!r}')
        return match[1], match[2]

    def has_content_type(self) -> bool:
        """Returns true if the content media type is defined in the schema.

        Returns:
            True when the JSON schema has the `contentMediaType` property.
        """
        return 'contentMediaType' in self

    def has_json_schema(self) -> bool:
        """Returns true if the schema does not validate any instance.

        Returns:
           True when the JSON schema has a `type`, `enum` or `const` property.
        """
        return 'type' in self or 'enum' in self or 'const' in self

    def update_with_type(self, tp: AnyType) -> None:
        """Updates the content type information from the parameter type hint.

        Arguments:
            tp: The type hint of the parameter.
        """
        content_type = self.get('contentMediaType')
        content_type = _merge_content_type_with_type(content_type, tp)
        if content_type is None:
            return
        self['contentMediaType'] = content_type

    def update_with_value(self, value: Any) -> None:
        """Updates the content type information from a job output value

        Arguments:
            value: The value of the output.
        """
        if self.has_json_schema():
            return

        requested_content_type = self.get('contentMediaType')
        content_type = _merge_content_type_with_value(requested_content_type, value)
        if content_type is None:
            return

        try:
            content_type = DEFAULT_CONTENT_TYPE[content_type]
        except KeyError:
            pass

        self['contentMediaType'] = content_type


def _merge_content_type_with_type(content_type: str | None, tp: AnyType) -> str | None:
    """Infers the content type by combining information from the type of the parameter
    and its potential content media type.

    Arguments:
        content_type: The potential content media type of the parameter, as stored in
            the transform, as annotations.
        tp: The type hint of the parameter.

    Returns:
        The inferred content media type.
    """
    if not isinstance(tp, type):
        return content_type

    if issubclass(tp, PIL.Image.Image):
        if content_type is None:
            content_type = 'image/*'
        if not content_type.startswith('image/'):
            raise TypeError(
                f'The parameter is of type PIL image, which is incompatible with the '
                f'annotated content media type {content_type!r}.'
            )
        return content_type

    if issubclass(tp, sonounolib.Track):
        if content_type is None:
            content_type = 'audio/*'
        if not content_type.startswith('audio/'):
            raise TypeError(
                f'The parameter is of type sonounolib.Track, which is incompatible with'
                f' the annotated content media type {content_type!r}.'
            )
        return content_type

    return content_type


def _merge_content_type_with_value(content_type: str | None, value: Any) -> str | None:
    """Infers the content type by combining information from the output schema
    and its actual value.

    Arguments:
        content_type: The content media type of the output, as stored in the
            transform, i.e as defined by code annotations.
        value: The output actual value.

    Returns:
        The MIME type inferred for the transform output.
    """
    if isinstance(value, PIL.Image.Image):
        if content_type is not None and not content_type.startswith('image/'):
            raise TypeError(
                f'The transform has returned a PIL image, which is incompatible with '
                f'the MIME type {content_type!r} specified in the source code.'
            )
        if value.format:
            content_type_from_value = PIL.Image.MIME[value.format]
        else:
            content_type_from_value = 'image/*'
        if (
            content_type is not None
            and content_type != 'image/*'
            and content_type_from_value != 'image/*'
        ):
            if content_type != content_type_from_value:
                raise TypeError(
                    f'The transform has returned an object of content type '
                    f'{content_type_from_value!r}, which is incompatible with the media'
                    f' type specified in the source code {content_type!r}.'
                )
        if content_type_from_value != 'image/*':
            return content_type_from_value
        return content_type

    elif isinstance(value, sonounolib.Track):
        if content_type is None:
            content_type = 'audio/*'
        if not content_type.startswith('audio/'):
            raise TypeError(
                f'The transform has returned a sonoUno Track, which is incompatible '
                f'with the requested MIME type {content_type!r}.'
            )

    if isinstance(value, (BytesIO, numpy.ndarray)):
        if content_type is None:
            content_type = 'application/octet-stream'

    return content_type
