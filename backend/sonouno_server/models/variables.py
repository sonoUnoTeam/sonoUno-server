from typing import Any, Literal, Mapping

from pydantic import BaseModel

TransferType = Literal['ignore', 'json', 'uri']


class InputIn(BaseModel):
    id: str
    value: Any


class Input(InputIn):
    name: str
    json_schema: Mapping[str, Any]
    required: bool
    modifiable: bool


class OutputIn(BaseModel):
    id: str
    content_type: str = '*/*'
    encoding: dict[str, Any] = {}
    transfer: TransferType = 'ignore'


class Output(OutputIn):
    name: str
    json_schema: Mapping[str, Any]


class OutputWithValue(Output):
    value: Any
