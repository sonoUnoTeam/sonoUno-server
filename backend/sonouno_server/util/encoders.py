from io import BytesIO
from typing import Any

import numpy as np
from scipy.io import wavfile


class NumpyEncoder:
    default_sample_rate_wave = 44100

    def encode(
        self, value: np.ndarray, content_type: str, encoding: dict[str, Any]
    ) -> BytesIO:
        buffer = BytesIO()

        if content_type in {'audio/wav', 'audio/x-wav', 'audio/wave'}:
            sample_rate = encoding.get('sample_rate', self.default_sample_rate_wave)
            dtype = encoding.get('dtype')
            if dtype:
                value = value.astype(dtype)
            wavfile.write(buffer, rate=sample_rate, data=value)

        elif content_type in {'*/*', 'application/octet-stream'}:
            np.savez(buffer, value=value)

        else:
            raise NotImplementedError(f'Cannot encode {content_type} ndarrays.')

        return buffer
