from typing import Any

from pydantic import BaseModel

from ..types import JSONSchemaType, TransferType


class InputIn(BaseModel):
    id: str
    value: Any


class Input(InputIn):
    name: str
    json_schema: JSONSchemaType
    required: bool
    modifiable: bool

    class Config:
        fields = {'json_schema': 'schema'}


class OutputIn(BaseModel):
    id: str
    json_schema: JSONSchemaType
    transfer: TransferType = 'ignore'

    class Config:
        fields = {'json_schema': 'schema'}


class Output(OutputIn):
    name: str


class OutputWithValue(Output):
    value: Any = None
