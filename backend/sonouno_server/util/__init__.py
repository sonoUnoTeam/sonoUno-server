from collections.abc import Mapping
from typing import TypeVar, cast

__all__ = ['merge_dicts_or_none']

T = TypeVar('T', bound=Mapping)


def merge_dicts_or_nones(value1: T | None, value2: T | None) -> T | None:
    """Merges two dictionaries potentially equal to None."""
    return cast(T, {**(value1 or {}), **(value2 or {})})  # Mappings do not support |
