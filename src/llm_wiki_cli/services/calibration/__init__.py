"""Isolated calibration services.

The base CLI must not import this package while it registers ordinary commands.
Calibration command adapters cross this boundary explicitly and lazily.  Keep
this initializer free of implementation imports so contracts, controllers, and
OCI broker code load only when their corresponding capability is requested.

The historical ``services.documentation_calibration*`` modules remain aliases
of the implementation modules for source, monkeypatch, and pickle compatibility.
"""

from __future__ import annotations

import types as _types
from collections.abc import MutableMapping as _MutableMapping


def _restore_legacy_definition_modules(
    namespace: _MutableMapping[str, object],
    *,
    legacy_module: str,
) -> None:
    """Retain historical callable/type module names used by persisted pickles."""

    owner = str(namespace["__name__"])
    seen: set[int] = set()

    def restore(value: object) -> None:
        marker = id(value)
        if marker in seen:
            return
        seen.add(marker)
        if isinstance(value, _types.FunctionType):
            if value.__module__ != owner:
                return
            value.__module__ = legacy_module
            annotate = getattr(value, "__annotate__", None)
            if isinstance(annotate, _types.FunctionType):
                restore(annotate)
            for nested in vars(value).values():
                if isinstance(nested, (_types.FunctionType, type)):
                    restore(nested)
            return
        if not isinstance(value, type) or value.__module__ != owner:
            return
        value.__module__ = legacy_module
        for member in vars(value).values():
            if isinstance(member, (classmethod, staticmethod)):
                restore(member.__func__)
            elif isinstance(member, property):
                for accessor in (member.fget, member.fset, member.fdel):
                    if accessor is not None:
                        restore(accessor)
            elif isinstance(member, (_types.FunctionType, type)):
                restore(member)
        for dataclass_field in getattr(value, "__dataclass_fields__", {}).values():
            default_factory = dataclass_field.default_factory
            if isinstance(default_factory, _types.FunctionType):
                restore(default_factory)

    for candidate in tuple(namespace.values()):
        if isinstance(candidate, (_types.FunctionType, type)):
            restore(candidate)


__all__ = ("broker", "contracts", "controller", "host_broker")
