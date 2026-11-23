"""An engine that runs wiki use cases with no application code.

:class:`Engine` holds what its caller grants: a :class:`~.host.Host`
(processes, environment, working directory, clock and output streams), the
:class:`~.pack_interfaces.DomainPack` that classifies, extracts, names and
renders sources, the :class:`~.knowledge_validators.ValidatorRegistry` every
knowledge index must pass, the :class:`~.knowledge_kinds.KindRegistry` of
custom kinds and the :class:`~.integrations.IntegrationSet` of knowledge-core
providers (the pack's, with the engine's own on top). Every call runs inside
one :class:`Operation` that applies those choices to all work beneath it.

Use cases run on the engine and write progress to the host's streams:
:meth:`Engine.bootstrap`, :meth:`Engine.sync` and :meth:`Engine.lint` (see
:mod:`.wiki_operations`). They take a typed request, return a typed result
and never exit the process.

This engine never prepares analysis helpers and serves no publication
targets; an application that needs them builds on its own engine.
Importing this module loads no application code.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from typing import Any, ParamSpec, TypeVar

from .analysis_compatibility import comparison_scope, selected_policy
from .engine_events import EngineEvent, EventKind, operation_identity
from .host import ALL_CAPABILITIES, Host, using_host
from .integrations import DEFAULT_INTEGRATIONS, IntegrationSet, using_integrations
from .knowledge_kinds import DEFAULT_KINDS, KindRegistry, using_kinds
from .knowledge_validators import DEFAULT_VALIDATORS, ValidatorRegistry, using_validators
from .pack_interfaces import DomainPack, using_pack
from . import wiki_operations
from .wiki_operations import (
    BootstrapRequest,
    BootstrapResult,
    LintReport,
    LintRequest,
    SyncRequest,
    SyncResult,
)

#: The format :meth:`Engine.capabilities` returns.
ENGINE_CAPABILITIES_SCHEMA_VERSION = "llm-wiki-engine-capabilities/v1"
# The knowledge core reads the active pack through ``domain_packs``; this
# engine answers it from its own pack scope unless the pack names another.
_ENGINE_INTEGRATIONS = IntegrationSet({"domain_packs": "llm_wiki_engine.pack_interfaces"})
_P = ParamSpec("_P")
_R = TypeVar("_R")


@dataclass(frozen=True)
class Operation:
    """The settings in force for one engine call and everything beneath it."""

    host: Host
    pack: DomainPack
    comparison_policy: str
    validators: ValidatorRegistry = DEFAULT_VALIDATORS
    kinds: KindRegistry = DEFAULT_KINDS
    integrations: IntegrationSet = DEFAULT_INTEGRATIONS


class Engine:
    """One configured engine; independent engines may run side by side."""

    def __init__(
        self,
        *,
        pack: DomainPack,
        host: Host | None = None,
        comparison_policy: str = "auto",
        validators: ValidatorRegistry = DEFAULT_VALIDATORS,
        kinds: KindRegistry = DEFAULT_KINDS,
        integrations: IntegrationSet = DEFAULT_INTEGRATIONS,
    ) -> None:
        host = Host() if host is None else host
        if not isinstance(host, Host):
            raise TypeError("host must be a Host instance")
        if not isinstance(pack, DomainPack):
            raise TypeError("pack must be a DomainPack")
        if not isinstance(validators, ValidatorRegistry):
            raise TypeError("validators must be a ValidatorRegistry")
        if not isinstance(kinds, KindRegistry):
            raise TypeError("kinds must be a KindRegistry")
        if not isinstance(integrations, IntegrationSet):
            raise TypeError("integrations must be an IntegrationSet")
        self._host = host
        self._pack = pack
        self._comparison_policy = selected_policy(comparison_policy)
        self._validators = validators
        self._kinds = kinds
        # The engine's own choices win over the pack's.
        self._integrations = _ENGINE_INTEGRATIONS.merged(pack.integrations).merged(integrations)

    @property
    def host(self) -> Host:
        return self._host

    @property
    def pack(self) -> DomainPack:
        return self._pack

    def capabilities(self) -> dict[str, object]:
        """What this engine may do, as an ``llm-wiki-engine-capabilities/v1`` document."""
        return {
            "schema_version": ENGINE_CAPABILITIES_SCHEMA_VERSION,
            "granted": sorted(self._host.capabilities),
            "missing": sorted(ALL_CAPABILITIES - self._host.capabilities),
            "helper_preparation": "never",
            "comparison_policy": self._comparison_policy,
            "validators": list(self._validators.names),
            "kinds": self._kinds.describe(),
            "pack": self._pack.describe(),
            "publication_targets": {"kinds": []},
        }

    @contextmanager
    def operation(self) -> Iterator[Operation]:
        """Apply this engine's grants to all work inside the block."""
        with ExitStack() as stack:
            stack.enter_context(using_host(self._host))
            stack.enter_context(comparison_scope(self._comparison_policy))
            stack.enter_context(using_validators(self._validators))
            stack.enter_context(using_kinds(self._kinds))
            stack.enter_context(using_pack(self._pack))
            stack.enter_context(using_integrations(self._integrations))
            yield Operation(
                self._host, self._pack, self._comparison_policy,
                self._validators, self._kinds, self._integrations,
            )

    def call(self, function: Callable[_P, _R], /, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        """Run ``function`` in one operation; this reports no events."""
        with self.operation():
            return function(*args, **kwargs)

    def _run(
        self,
        name: str,
        request: object,
        execute: Callable[[], _R],
        describe: Callable[[_R], Mapping[str, Any]],
    ) -> _R:
        """Run one use case in an operation, reporting its lifecycle to the host."""
        operation_id = uuid.uuid4().hex
        with self.operation(), operation_identity(name, operation_id):
            self._report("operation.started", name, operation_id, lambda: _request_data(request))
            try:
                result = execute()
            except BaseException as error:
                failure = _error_data(error)
                self._report("operation.failed", name, operation_id, lambda: failure)
                raise
            self._report("operation.finished", name, operation_id, lambda: {"result": dict(describe(result))})
            return result

    def _report(
        self, kind: EventKind, name: str, operation_id: str, data: Callable[[], Mapping[str, Any]],
    ) -> None:
        if self._host.reports_events:
            self._host.publish(EngineEvent(kind, name, operation_id, data()))


    def bootstrap(self, request: BootstrapRequest) -> BootstrapResult:
        """Create a wiki from the pack's sources; progress goes to the host's streams.

        Raises :class:`~.wiki_operations.WikiOperationError` when it cannot.
        """
        return self._run("bootstrap", request, lambda: wiki_operations.bootstrap(request), _to_dict)

    def sync(self, request: SyncRequest) -> SyncResult:
        """Update the wiki from changed sources, keeping reviewed text."""
        return self._run("sync", request, lambda: wiki_operations.sync(request), _to_dict)

    def lint(self, request: LintRequest) -> LintReport:
        """Check the wiki against its sources; ``report.passed`` is the verdict."""
        return self._run(
            "lint", request, lambda: wiki_operations.lint(request),
            lambda report: {"passed": report.passed, "issue_count": report.issue_count},
        )


def _to_dict(result: Any) -> Mapping[str, Any]:
    return result.to_dict()


def _request_data(request: object) -> dict[str, str]:
    data: dict[str, str] = {}
    for name in ("source_root", "wiki_root"):
        value = getattr(request, name, None)
        if isinstance(value, (str, os.PathLike)):
            data[name] = os.fspath(value)
    return data


def _error_data(error: BaseException) -> dict[str, object]:
    data: dict[str, object] = {"error": type(error).__name__, "message": str(error)}
    exit_code = getattr(error, "exit_code", None)
    if isinstance(exit_code, int) and not isinstance(exit_code, bool):
        data["exit_code"] = exit_code
    return data


__all__ = ["ENGINE_CAPABILITIES_SCHEMA_VERSION", "Engine", "Operation"]
