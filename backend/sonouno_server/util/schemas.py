import re
from io import BytesIO
from typing import Any, Mapping, TypeVar, cast

import numpy
from PIL import Image

from ..types import JSONSchema

DEFAULT_CONTENT_TYPE = {
    'application/*': 'application/octet-stream',
    'audio/*': 'audio/x-wav',
    'image/*': 'image/png',
    'text/*': 'text/plain',
    'video/*': 'video/mp4',
}
REGEX_MIME_TYPE = re.compile(r'(application|audio|image|text|video)/(\*|[a-z0-9-]+)$')


def is_known_schema(schema: JSONSchema) -> bool:
    """Returns true if the input schema does not validate any instance.

    Arguments:
        schema: The input JSON schema.

    Returns:
       True when the JSON schema has a `type`, `enum` or `const` property.
    """
    return 'type' in schema or 'enum' in schema or 'const' in schema


def is_known_content_type(schema: JSONSchema) -> bool:
    """Returns true if the content media type is defined in the JSON schema.

    Arguments:
        schema: The input JSON schema.

    Returns:
        True when the JSON schema has the `contentMediaType` property.
    """
    return 'contentMediaType' in schema


def merge_schemas(schema: JSONSchema, requested_schema: JSONSchema) -> JSONSchema:
    merged_schema = schema | requested_schema

    content_type = merge_transform_and_job_content_type(
        schema.get('contentMediaType'), requested_schema.get('contentMediaType')
    )
    if content_type:
        merged_schema['contentMediaType'] = content_type

    encoding = merge_dicts_or_nones(
        schema.get('x-contentMediaEncoding'),
        requested_schema.get('x-contentMediaEncoding'),
    )
    if encoding:
        merged_schema['x-contentMediaEncoding'] = encoding

    return merged_schema


def merge_transform_and_job_content_type(
    content_type: str | None, requested_content_type: str | None
) -> str | None:
    """Combines the output content type stored in the transform with the one
    requested by the job.

    Arguments:
        content_type: The content media type of the output, as stored in the
            transform, i.e as defined by code annotations.
        requested_content_type: The content media type of the output, as
            requested by the job.

    Returns:
        The content type

    Raises:
        ValueError: When the content types are not compatible.
    """
    if requested_content_type is None or content_type is None:
        return requested_content_type or content_type

    if incompatible_content_types(content_type, requested_content_type):
        raise ValueError(
            f'The requested media type {requested_content_type!r} is incompatible with '
            f'the actual media type {content_type}.'
        )
    if requested_content_type.endswith('/*'):
        return content_type
    return requested_content_type


def incompatible_content_types(type1: str, type2: str) -> bool:
    """Checks if two MIME types are compatible."""
    type1, subtype1 = split_content_type(type1)
    type2, subtype2 = split_content_type(type2)
    return (
        type1 != type2 or subtype1 != '*' and subtype2 != '*' and subtype1 != subtype2
    )


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


T = TypeVar('T', bound=Mapping)


def merge_dicts_or_nones(value1: T | None, value2: T | None) -> T | None:
    """Merges two dictionaries potentially equal to None."""
    return cast(T, {**(value1 or {}), **(value2 or {})})  # Mappings do not support |


def merge_schema_with_value(schema: JSONSchema, value: Any) -> JSONSchema:
    """Includes the content type information that can be inferred from the job output
    value in the job output schema.

    Arguments:
        schema: The JSON schema of the output.
        value: The value of the output.

    Returns:
        The JSON schema enriched from the content type information that can be inferred
        from the actual value of the job output.
    """
    if is_known_schema(schema):
        return schema

    requested_content_type = schema.get('contentMediaType')
    content_type = merge_content_type_with_value(requested_content_type, value)
    if content_type is None:
        return schema

    try:
        content_type = DEFAULT_CONTENT_TYPE[content_type]
    except KeyError:
        pass

    return schema | {'contentMediaType': content_type}  # type: ignore[return-value]


def merge_content_type_with_value(content_type: str | None, value: Any) -> str | None:
    """Infers the content type by combining information from the output schema
    and its actual value.

    Arguments:
        content_type: The content media type of the output, as stored in the
            transform, i.e as defined by code annotations.
        value: The output actual value.

    Returns:
        The MIME type inferred for the transform output.
    """
    if isinstance(value, Image.Image):
        if content_type is not None and not content_type.startswith('image/'):
            raise TypeError(
                f'The transform has returned a PIL image, which is incompatible with '
                f'the MIME type {content_type!r} specified in the source code.'
            )
        if value.format:
            content_type_from_value = Image.MIME[value.format]
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

    if isinstance(value, (BytesIO, numpy.ndarray)):
        if content_type is None:
            content_type = 'application/octet-stream'

    return content_type
