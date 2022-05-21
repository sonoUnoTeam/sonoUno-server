from io import BytesIO

import numpy as np
from scipy.io import wavfile

from ..types import JSONSchema, MediaEncoding


def numpy_encode(value: np.ndarray, schema: JSONSchema):
    content_type = schema.get('contentMediaType')
    assert content_type is not None  # ensured by schemas.merge_content_type_with_value
    encoding = schema.get('x-contentMediaEncoding', {})

    if content_type == 'audio/x-wav':
        return NumpyWaveEncoder().encode(value, encoding)

    if content_type == 'application/octet-stream':
        return NumpyNPZEncoder().encode(value, encoding)

    raise NotImplementedError(
        f'Cannot encode numpy arrays of content type {content_type!r}.'
    )


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
