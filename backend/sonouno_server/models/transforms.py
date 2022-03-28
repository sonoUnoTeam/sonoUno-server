"""User Pydantic and Document models.
"""

# pylint: disable=too-few-public-methods

from datetime import datetime
from typing import Optional, Any

from beanie import Document, Link, Indexed, PydanticObjectId
from pydantic import BaseModel

from .users import UserOut


class Edge(BaseModel):
    id: str
    input_node_id: str
    input_fields: list[str] | None = None
    output_node_id: str
    output_fields: list[str] | None = None


class Node(BaseModel):
    id: str
    description: str
    type: str
    parameters: dict[str, Any]


class TransformIn(BaseModel):
    """The transform, as input by the user."""
    name: str
    description: str = ''
    public: bool = True
    nodes: list[Node]
    edges: list[Edge]


class Transform(TransformIn, Document):
    """The transform, as stored in the database and returned to the user."""
    user_id: Indexed(PydanticObjectId)
