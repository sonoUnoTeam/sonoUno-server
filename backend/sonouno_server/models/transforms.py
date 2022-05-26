"""User Pydantic and Document models.
"""
from __future__ import annotations

from typing import Annotated, Literal

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel
from pydantic import Field as F

from .variables import Input, Output


class ExposedFunction(BaseModel):
    id: Annotated[str, F(title='The unique identifier of the exposed function.')] = ''
    name: Annotated[str, F(title='The name of the function.')] = ''
    description: str = F('', title='The description of the exposed function.')
    inputs: Annotated[list[Input], F(title='The inputs of the exposed function.')] = []
    outputs: Annotated[
        list[Output], F(title='The outputs of the exposed function.')
    ] = []
    callees: Annotated[
        list[ExposedFunction], F(title='The functions called by the exposed function.')
    ] = []

    def walk_callees(self) -> list[ExposedFunction]:
        """Walks the callee dependency graph depth-first."""
        return sum((c.walk_callees() for c in self.callees), [])

    class Config:
        fields = {'json_schema': 'schema'}
        schema_extra = {
            'description': """An exposed function is a function for which the sonouno
server may capture its inputs or outputs, and that the front-end can display as
a pipeline component.""",
            'examples': [],
        }


class TransformIn(BaseModel):
    """The transform, as input by the user."""

    name: Annotated[str, F(title='The name of the transform.')]
    description: Annotated[str, F(title='The description of the transform.')] = ''
    public: Annotated[bool, F(title='True if the transform access is public.')] = True
    language: Annotated[
        Literal['python'], F(title='The programming language of the source code.')
    ]
    source: Annotated[str, F(title='The source code of the transform.')]
    entry_point: Annotated[ExposedFunction, F(title='The entry point of the pipeline.')]

    class Config:
        schema_extra = {
            'description': """Input to create a transformation.""",
            'examples': [
                {
                    'name': 'Test transformation',
                    'public': True,
                    'language': 'python',
                    'source': 'from typing import Annotated\n\nimport numpy as np\n\nfrom streamunolib import exposed, media_type\nfrom sonounolib import Track\n\n\ndef get_cluster_sound() -> Track:\n    """Obtains a generic cluster sound."""\n    track = Track()\n    frequencies = [300, 350, 600, 800, 1000, 800, 800, 1000, 700, 600]\n    for frequency in frequencies:\n        track.add_sine_wave(frequency, 0.1)\n    return track\n\n\nOut = Annotated[\n    np.ndarray,\n    media_type(\'audio\', rate=44100, format=\'int16\'),\n]\n\n\n# Out = Annotated[\n#     Track,\n#     {\'title\': \'LHC sonification\'},\n# ]\n\n@exposed\ndef pipeline(repeat: int = 1) -> Out:\n    track = Track(max_amplitude=\'int16\')\n    track.add_sine_wave(\'D6\', 4, 1/8)\n    track.set_cue_write(2).add_sine_wave(\'C6\', 2, 1/8)\n    track.add_blank(1)\n    track.add_track(get_cluster_sound())\n    track.repeat(repeat)\n\n    return track.get_data()\n',  # noqa: E501
                    'entry_point': {'name': 'pipeline'},
                }
            ],
        }


class Transform(TransformIn, Document):
    """The transform, as stored in the database and returned to the user."""

    user_id: Indexed(PydanticObjectId) = F(title='The owner of this transform.')  # type: ignore[valid-type]  # noqa: E501

    def walk_callees(self) -> list[ExposedFunction]:
        """Walks the callee dependency graph depth-first, including the entry point."""
        return [self.entry_point] + self.entry_point.walk_callees()

    class Config:
        schema_extra = {
            'description': """The transformation, as stored in the database.""",
            'examples': [
                {
                    '_id': '628f4b1f2adff4274a708523',
                    'name': 'Test transformation',
                    'description': '',
                    'public': True,
                    'language': 'python',
                    'source': '# -*- coding: utf-8 -*-\nfrom typing import Annotated\n\nimport numpy as np\n\nfrom streamunolib import exposed, media_type\nfrom sonounolib import Track\n\n\ndef get_cluster_sound() -> Track:\n    """Obtains a generic cluster sound."""\n    track = Track()\n    frequencies = [300, 350, 600, 800, 1000, 800, 800, 1000, 700, 600]\n    for frequency in frequencies:\n        track.add_sine_wave(frequency, 0.1)\n    return track\n\n\nOut = Annotated[\n    np.ndarray,\n    media_type(\'audio\', rate=44100, format=\'int16\'),\n]\n\n\n# Out = Annotated[\n#     Track,\n#     {\'title\': \'LHC sonification\'},\n# ]\n\n@exposed\ndef pipeline(repeat: int = 1) -> Out:\n    track = Track(max_amplitude=\'int16\')\n    track.add_sine_wave(\'D6\', 4, 1/8)\n    track.set_cue_write(2).add_sine_wave(\'C6\', 2, 1/8)\n    track.add_blank(1)\n    track.add_track(get_cluster_sound())\n    track.repeat(repeat)\n\n    return track.get_data()\n',  # noqa: E501
                    'entry_point': {
                        'id': 'pipeline',
                        'name': 'pipeline',
                        'description': '',
                        'inputs': [
                            {
                                'id': 'pipeline.repeat',
                                'value': 1,
                                'name': 'repeat',
                                'schema': {
                                    '$schema': 'http://json-schema.org/draft/2020-12/schema#',  # noqa: E501
                                    'type': 'integer',
                                    'default': True,
                                },
                                'required': False,
                                'modifiable': True,
                            }
                        ],
                        'outputs': [
                            {
                                'id': 'pipeline.0',
                                'schema': {
                                    '$schema': 'http://json-schema.org/draft/2020-12/schema#',  # noqa: E501
                                    'contentMediaType': 'audio/*',
                                    'x-contentMediaEncoding': {
                                        'format': 'int16',
                                        'rate': 44100,
                                    },
                                },
                                'transfer': 'uri',
                                'name': '0',
                            }
                        ],
                        'callees': [],
                    },
                    'user_id': '628f0baa98125a42409ae3bd',
                }
            ],
        }
