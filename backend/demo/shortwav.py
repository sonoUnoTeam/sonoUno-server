from typing import Annotated

import numpy as np
from sonounolib import Track

from streamunolib import exposed, media_type


def get_cluster_sound() -> Track:
    """Obtains a generic cluster sound."""
    track = Track()
    frequencies = [300, 350, 600, 800, 1000, 800, 800, 1000, 700, 600]
    for frequency in frequencies:
        track.add_sine_wave(frequency, 0.1)
    return track


Out = Annotated[
    np.ndarray,
    media_type('audio', rate=44100, format='int16'),
    {'title': 'The audio output of the pipeline, as an ndarray.'},
]


@exposed
def pipeline(repeat: Annotated[int, {'title': 'Number of repetitions'}] = 1) -> Out:
    """This is a fake pipeline, but you get the idea."""
    track = Track(max_amplitude='int16')
    track.add_sine_wave('D6', 4, 1 / 8)
    track.set_cue_write(2).add_sine_wave('C6', 2, 1 / 8)
    track.add_blank(1)
    track.add_track(get_cluster_sound())
    track.repeat(repeat)

    return track.get_data()
