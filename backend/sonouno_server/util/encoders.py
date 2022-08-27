from io import BytesIO

import numpy as np
from scipy.io import wavfile

import sonounolib

from ..types import JSONSchemaType, MediaEncoding


def numpy_encode(value: np.ndarray, schema: JSONSchemaType):
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
    VALID_FORMATS = {'int16', 'int32', 'float32', 'float64'}

    def encode(self, value: np.ndarray, encoding: MediaEncoding) -> BytesIO:
        rate = encoding.get('rate', self.DEFAULT_RATE)
        format = encoding.get('format')
        max_amplitude = encoding.get('max_amplitude')
        if format is not None and format not in self.VALID_FORMATS:
            raise ValueError(f'Invalid wave format: {format}')
        if format is None:
            format = self.infer_format_from_value(value)
        if format is None and max_amplitude is None:
            raise ValueError(
                'Cannot encode the value audio/x-wav: nor the format, nor the max ampli'
                'tude are specified.'
            )
        if format is None:
            format = self.DEFAULT_FORMAT
        if max_amplitude is None:
            max_amplitude = format

        max_amplitude_in = self.asmax_amplitude(max_amplitude)
        max_amplitude_out = self.asmax_amplitude(format)
        if max_amplitude_in != max_amplitude_out:
            value = (max_amplitude_out / max_amplitude_in) * value

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

    def asmax_amplitude(self, value: float | np.number | str) -> float:
        if isinstance(value, (int, float, np.number)):
            return float(value)

        if value not in self.VALID_FORMATS:
            raise ValueError(f'Cannot infer a maximum amplitude from dtype: {value!r}.')

        if value.startswith('float'):
            return 1
        return np.iinfo(value).max


class NumpyNPZEncoder:
    def encode(self, value: np.ndarray, encoding: MediaEncoding) -> BytesIO:
        buffer = BytesIO()
        np.savez(buffer, value=value)
        return buffer


class SonoUnoTrackEncoder:
    VALID_ENCODING_KEYS = {'format'}

    def encode(self, value: sonounolib.Track, encoding: MediaEncoding) -> BytesIO:
        params = {k: v for k, v in encoding.items() if k in self.VALID_ENCODING_KEYS}
        buffer = BytesIO()
        value.to_wav(buffer, **params)  # type: ignore[arg-type]
        return buffer
