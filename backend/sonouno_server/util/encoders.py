from io import BytesIO
from typing import Any

import numpy as np
from PIL import Image
from scipy.io import wavfile

from ..types import JSONSchema, MediaEncoding

DEFAULT_CONTENT_TYPE = {
    'application/*': 'application/octet-stream',
    'audio/*': 'audio/x-wav',
    'image/*': 'image/png',
    'text/*': 'text/plain',
    'video/*': 'video/mp4',
}


class NumpyEncoder:
    def encode(
        self, value: np.ndarray, content_type: str, encoding: MediaEncoding
    ) -> BytesIO:
        if content_type == 'audio/x-wav':
            return NumpyWaveEncoder().encode(value, encoding)

        if content_type == 'application/octet-stream':
            return NumpyNPZEncoder().encode(value, encoding)

        raise NotImplementedError(f'Cannot encode {content_type} ndarrays.')


class NumpyWaveEncoder:
    DEFAULT_RATE = 44100
    DEFAULT_FORMAT = 'int16'
    VALID_FORMATS = {'uint8', 'int16', 'int32', 'float32', 'float64'}

    def encode(self, value: np.ndarray, encoding: MediaEncoding) -> BytesIO:
        rate = encoding.get('rate', self.DEFAULT_RATE)
        range = encoding.get('range', value.dtype.name)
        format = encoding.get('format')
        if format is not None and format not in self.VALID_FORMATS:
            raise ValueError(f'Invalid wave format: {format}')
        if format is None:
            format = self.infer_format_from_value(value)
        if format is None:
            format = self.DEFAULT_FORMAT

        if range != format:
            if not isinstance(range, str):
                raise NotImplementedError(
                    'Range can only take the value of the data type, such as float32.'
                )
            data_range_in = self.get_data_range(range)  # noqa
            data_range_out = self.get_data_range(format)  # noqa
            raise NotImplementedError(f'The data must be rescaled {range}->{format}')

        value = value.astype(format, copy=False)

        buffer = BytesIO()
        wavfile.write(buffer, rate, value)
        return buffer

    def infer_format_from_value(self, value: np.ndarray) -> str | None:
        format = value.dtype.name
        if format == 'float64':
            # for float64, which is the default type for computing, we don't assume
            # that's the intended format
            return None
        if format not in self.VALID_FORMATS:
            return None
        return format

    def infer_range_from_value(self, value: np.ndarray) -> str | None:
        format = value.dtype.name
        if format not in self.VALID_FORMATS:
            return None
        return format

    def get_data_range(self, dtype_name: str) -> tuple[float, float]:
        if dtype_name.startswith('float'):
            return -1, 1
        iinfo = np.iinfo(dtype_name)
        return iinfo.min, iinfo.max


class NumpyNPZEncoder:
    def encode(self, value: np.ndarray, encoding: MediaEncoding) -> BytesIO:
        buffer = BytesIO()
        np.savez(buffer, value=value)
        return buffer


def get_content_type(value: Any, schema: JSONSchema) -> str | None:
    if 'type' in schema:
        return None

    requested_content_type = schema.get('contentMediaType')
    content_type = merge_content_type_with_value(value, requested_content_type)
    if content_type is None:
        return None

    try:
        return DEFAULT_CONTENT_TYPE[content_type]
    except KeyError:
        pass

    return content_type


def merge_content_type_with_value(value: Any, content_type: str | None) -> str | None:
    """Infers the content type by combining information from the output schema
    and its actual value.

    Arguments:
        value: The output actual value.
        content_type: The content media type of the output, as stored in the
            transform, i.e as defined by code annotations.

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

    return content_type
