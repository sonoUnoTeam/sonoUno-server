from typing import Any

from pydantic import BaseModel

from ..types import JSONSchema, TransferType


class InputIn(BaseModel):
    id: str
    value: Any


class Input(InputIn):
    name: str
    json_schema: JSONSchema
    required: bool
    modifiable: bool


class OutputIn(BaseModel):
    id: str
    json_schema: JSONSchema
    transfer: TransferType = 'ignore'


class Output(OutputIn):
    name: str


class OutputWithValue(Output):
    value: Any
