"""User Pydantic and Document models.
"""
from __future__ import annotations

from typing import Any, Literal

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel

# pylint: disable=too-few-public-methods


class Input(BaseModel):
    name: str
    fq_name: str
    json_schema: dict[str, Any]


class Output(BaseModel):
    name: str
    content_type: str | None
    json_schema: dict[str, Any]


class ExposedFunction(BaseModel):
    name: str
    description: str = ''
    inputs: list[Input] | None = None
    outputs: list[Output] | None = None
    exposed_functions: list[ExposedFunction] | None = None


class TransformIn(BaseModel):
    """The transform, as input by the user."""

    name: str
    description: str = ''
    public: bool = True
    language: Literal['python']
    source: str
    entry_point: ExposedFunction


class Transform(TransformIn, Document):
    """The transform, as stored in the database and returned to the user."""

    user_id: Indexed(PydanticObjectId)  # type: ignore[valid-type]
