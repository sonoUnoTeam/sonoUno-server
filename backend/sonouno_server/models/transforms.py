"""User Pydantic and Document models.
"""
from __future__ import annotations

from typing import Literal

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel

from .variables import Input, Output

# pylint: disable=too-few-public-methods


class ExposedFunction(BaseModel):
    id: str = ''
    name: str = ''
    description: str = ''
    inputs: list[Input] = []
    outputs: list[Output] = []
    callees: list[ExposedFunction] = []

    def walk_callees(self) -> list[ExposedFunction]:
        """Walks the callee dependency graph depth-first."""
        return sum((c.walk_callees() for c in self.callees), [])


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

    def walk_callees(self) -> list[ExposedFunction]:
        """Walks the callee dependency graph depth-first, including the entry point."""
        return [self.entry_point] + self.entry_point.walk_callees()
