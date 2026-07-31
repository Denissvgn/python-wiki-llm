"""Deterministic lifecycle contract for agent-driven documentation workspaces."""

from __future__ import annotations

import sys as _sys
import types as _types

# Preserve the historical import surface while keeping lifecycle roles
# independently reviewable.
from . import dependencies as _dependencies
from . import contracts as _contracts
from . import schema as _schema
from . import workspace as _workspace
from . import integrity as _integrity
from . import refresh as _refresh
from . import prepare as _prepare
from . import packet as _packet
from . import record as _record
from . import verify as _verify
from . import export as _export

import typing as _typing

if _typing.TYPE_CHECKING:
    from .contracts import (
        DEFAULT_DOCUMENTATION_SKILLS,
        DocumentationAgentPacket,
        DocumentationAgentResult,
        DocumentationIntegrityError,
        DocumentationIntakeBrief,
        DocumentationRun,
        DocumentationRunError,
        DocumentationRunStatus,
        DocumentationSchemaError,
        DocumentationTransitionError,
        DocumentationVerificationReport,
        RUN_CONTROL_DIR,
        SUPPORTED_AGENT_STAGES,
        SUPPORTED_BASELINE_STRATEGIES,
        SUPPORTED_DOCUMENTATION_KNOWLEDGE_MODES,
        SUPPORTED_FRESHNESS_POLICIES,
        workspace_paths,
    )
    from .prepare import (
        prepare_documentation_run,
    )
    from .packet import (
        build_documentation_agent_packet,
    )
    from .record import (
        record_documentation_agent_result,
    )
    from .verify import (
        verify_documentation_run,
    )
    from .export import (
        export_documentation_run,
    )
    from .integrity import (
        capture_generated_ownership,
        compare_generated_ownership,
    )
    from .workspace import (
        documentation_run_path,
        get_documentation_run_status,
        load_documentation_run,
        save_documentation_run,
        transition_documentation_run,
    )
    from .refresh import (
        source_identity,
    )

del _typing

_COMPATIBILITY_MODULES = (
    _dependencies,
    _contracts,
    _schema,
    _workspace,
    _integrity,
    _refresh,
    _prepare,
    _packet,
    _record,
    _verify,
    _export,
)

# Preserve the monolith's module-level annotation metadata without exposing
# annotations owned by implementation-only role modules.
__annotations__ = dict(_contracts.__annotations__)
if hasattr(_contracts, "__conditional_annotations__"):
    __conditional_annotations__ = set(_contracts.__conditional_annotations__)

for _module in _COMPATIBILITY_MODULES:
    for _name in _module.__all__:
        globals()[_name] = getattr(_module, _name)

# Dataclass methods retain their original late-bound helper lookups. Populate
# those lookups after every role module has loaded to avoid import cycles.
for _module in _COMPATIBILITY_MODULES:
    if _module is _contracts:
        continue
    for _name in _module.__all__:
        _contracts.__dict__.setdefault(_name, getattr(_module, _name))

_MISSING = object()
_HISTORICAL_MODULE = __name__
_HISTORICAL_MODULE_PREFIX = __name__ + "."
_HISTORICAL_CLASS_FIRSTLINENO = dict(
    [
        ("DocumentationRunError", 295),
        ("DocumentationSchemaError", 299),
        ("DocumentationTransitionError", 303),
        ("DocumentationIntegrityError", 307),
        ("DocumentationPersistedStateError", 311),
        ("DocumentationIntakeBrief", 318),
        ("DocumentationRun", 620),
        ("DocumentationRunStatus", 769),
        ("DocumentationAgentPacket", 796),
        ("DocumentationAgentResult", 818),
        ("DocumentationVerificationReport", 947),
        ("_RefreshContinuationSnapshot", 969),
        ("_RefreshArchiveTransaction", 980),
        ("_NativeEvidenceTransaction", 994),
        ("_InitialPrepareTransaction", 1004),
    ]
)


def _restore_definition_module(
    value: object,
    owner: str,
    seen: set[int] | None = None,
) -> None:
    """Preserve historical introspection and pickle lookup paths."""

    if seen is None:
        seen = set()
    marker = id(value)
    if marker in seen:
        return
    seen.add(marker)
    if isinstance(value, _types.FunctionType):
        if value.__module__ != owner:
            return
        annotate = getattr(value, "__annotate__", None)
        value.__module__ = _HISTORICAL_MODULE
        if isinstance(annotate, _types.FunctionType):
            _restore_definition_module(annotate, owner, seen)
        for nested in vars(value).values():
            if isinstance(nested, (_types.FunctionType, type)):
                _restore_definition_module(nested, owner, seen)
        return
    if not isinstance(value, type) or value.__module__ != owner:
        return
    role_firstlineno = getattr(value, "__firstlineno__", _MISSING)
    value.__module__ = _HISTORICAL_MODULE
    if role_firstlineno is not _MISSING:
        value.__firstlineno__ = _HISTORICAL_CLASS_FIRSTLINENO.get(
            value.__qualname__,
            role_firstlineno,
        )
    for member in vars(value).values():
        if isinstance(member, (classmethod, staticmethod)):
            if getattr(member, "__module__", None) == owner:
                try:
                    member.__module__ = _HISTORICAL_MODULE
                except (AttributeError, TypeError):
                    pass
            _restore_definition_module(member.__func__, owner, seen)
        elif isinstance(member, property):
            for accessor in (member.fget, member.fset, member.fdel):
                if accessor is not None:
                    _restore_definition_module(accessor, owner, seen)
        elif isinstance(member, (_types.FunctionType, type)):
            _restore_definition_module(member, owner, seen)
    for dataclass_field in getattr(value, "__dataclass_fields__", {}).values():
        default_factory = dataclass_field.default_factory
        if isinstance(default_factory, _types.FunctionType):
            _restore_definition_module(default_factory, owner, seen)


for _module in _COMPATIBILITY_MODULES:
    if not _module.__name__.startswith(_HISTORICAL_MODULE_PREFIX):
        continue
    for _name in _module.__all__:
        _value = getattr(_module, _name)
        if getattr(_value, "__module__", None) == _module.__name__:
            _restore_definition_module(_value, _module.__name__)

_COMPATIBILITY_NAMES = tuple(
    dict.fromkeys(
        name
        for module in _COMPATIBILITY_MODULES
        for name in module.__all__
    )
)
_COMPATIBILITY_OWNERS = dict()
for _name in _COMPATIBILITY_NAMES:
    _value = globals()[_name]
    _COMPATIBILITY_OWNERS[_name] = tuple(
        module
        for module in _COMPATIBILITY_MODULES
        if module.__dict__.get(_name, _MISSING) is _value
    )
_DELETED_COMPATIBILITY_OWNERS = dict()
del _module, _name, _value


class _CompatibilityModule(_types.ModuleType):
    """Mirror compatibility monkeypatches into the owning role modules."""

    def __setattr__(self, name: str, value: object) -> None:
        previous = self.__dict__.get(name, _MISSING)
        super().__setattr__(name, value)
        if previous is _MISSING:
            for module in _DELETED_COMPATIBILITY_OWNERS.pop(name, ()):
                setattr(module, name, value)
            return
        for module in _COMPATIBILITY_OWNERS.get(name, ()):
            if module.__dict__.get(name, _MISSING) is previous:
                setattr(module, name, value)

    def __delattr__(self, name: str) -> None:
        previous = self.__dict__.get(name, _MISSING)
        if previous is _MISSING:
            super().__delattr__(name)
            return
        owners = tuple(
            module
            for module in _COMPATIBILITY_OWNERS.get(name, ())
            if module.__dict__.get(name, _MISSING) is previous
        )
        super().__delattr__(name)
        deleted = []
        for module in owners:
            delattr(module, name)
            deleted.append(module)
        if deleted:
            _DELETED_COMPATIBILITY_OWNERS[name] = tuple(deleted)


_sys.modules[__name__].__class__ = _CompatibilityModule

__all__ = [
    "DEFAULT_DOCUMENTATION_SKILLS",
    "DocumentationAgentPacket",
    "DocumentationAgentResult",
    "DocumentationIntegrityError",
    "DocumentationIntakeBrief",
    "DocumentationRun",
    "DocumentationRunError",
    "DocumentationRunStatus",
    "DocumentationSchemaError",
    "DocumentationTransitionError",
    "DocumentationVerificationReport",
    "RUN_CONTROL_DIR",
    "SUPPORTED_AGENT_STAGES",
    "SUPPORTED_BASELINE_STRATEGIES",
    "SUPPORTED_DOCUMENTATION_KNOWLEDGE_MODES",
    "SUPPORTED_FRESHNESS_POLICIES",
    "build_documentation_agent_packet",
    "capture_generated_ownership",
    "compare_generated_ownership",
    "documentation_run_path",
    "export_documentation_run",
    "get_documentation_run_status",
    "load_documentation_run",
    "prepare_documentation_run",
    "record_documentation_agent_result",
    "save_documentation_run",
    "source_identity",
    "transition_documentation_run",
    "verify_documentation_run",
    "workspace_paths",
]
