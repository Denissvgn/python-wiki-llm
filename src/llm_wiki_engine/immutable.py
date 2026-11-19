"""Detached immutable model graphs that retain ordinary JSON container shapes."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import fields, is_dataclass, replace
from typing import TypeVar, cast

_T = TypeVar("_T")


def _immutable(*args, **kwargs):
    raise TypeError("validated snapshot values are immutable")


class FrozenDict(dict):
    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = (
        __ior__
    ) = _immutable

    def __deepcopy__(self, memo):
        return {
            deepcopy(key, memo): deepcopy(value, memo) for key, value in self.items()
        }


class FrozenList(list):
    __setitem__ = __delitem__ = append = clear = extend = insert = pop = remove = (
        reverse
    ) = sort = __iadd__ = __imul__ = _immutable

    def __deepcopy__(self, memo):
        return [deepcopy(value, memo) for value in self]


def freeze(value: _T) -> _T:
    """Detach parsed, acyclic model data and freeze every mutable descendant."""
    if value is None or isinstance(value, (str, bytes, int, float, bool)):
        return value
    if isinstance(value, (FrozenDict, FrozenList)):
        return value
    if isinstance(value, Mapping):
        return cast(_T, FrozenDict((key, freeze(item)) for key, item in value.items()))
    if isinstance(value, list):
        return cast(_T, FrozenList(freeze(item) for item in value))
    if isinstance(value, tuple):
        return cast(_T, tuple(freeze(item) for item in value))
    if is_dataclass(value) and not isinstance(value, type):
        return replace(
            value,
            **{
                field.name: freeze(getattr(value, field.name))
                for field in fields(value)
                if field.init
            },
        )
    return value
