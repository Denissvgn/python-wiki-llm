"""Embeddable engine: run wiki operations on behalf of a host application.

An :class:`Engine` holds what the caller grants: a :class:`Host` (processes,
environment, working directory, clock), whether bundled analysis helpers may
be prepared automatically, the analysis comparison policy, the
:class:`ValidatorRegistry` every knowledge index must pass and the
:class:`KindRegistry` of custom concept, relationship and graph-edge kinds
it declares, the :class:`DomainPack` that classifies sources, names
pages, renders them, builds budgeted context, serves publication
reference kinds and prepares analysis helpers, and the
:class:`PublicationTargetRegistry` of places a reviewed documentation
candidate may be published to. Every call runs
inside one :class:`Operation` that applies those choices to all work beneath
it, including calls into :mod:`llm_wiki_cli.api`.

Unlike the CLI and the public API, an engine never prepares helpers unless the
caller grants ``helper_preparation="auto"``. Importing this module loads
neither the CLI, command modules nor the public API.

Use cases run directly on the engine and write progress to the host's
streams: :meth:`Engine.bootstrap`, :meth:`Engine.sync`, :meth:`Engine.lint`,
:meth:`Engine.migrate` and :meth:`Engine.upgrade`.
They take a typed request, return a typed result and never exit the process.
A host built with ``events=`` also receives structured
:class:`EngineEvent` objects for each use-case call: started, one
``message`` per line written, then finished or failed.

    from llm_wiki_cli import api
    from llm_wiki_cli.engine import Engine, NoProcessHost

    engine = Engine(host=NoProcessHost())
    result = engine.call(api.search_wiki, "billing", wiki_dir="docs/llm_wiki")
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, ParamSpec, TypeVar

from ..services.context_response_format import (
    CONTEXT_RESPONSE_PROTOCOLS,
    ContextResponseError,
    validate_context_response,
)
from ..services.query_result_format import (
    DOCUMENTATION_QUERY_SCHEMA_VERSION,
    SEARCH_RESULT_SCHEMA_VERSION,
    QueryResultError,
    validate_documentation_query_result,
    validate_search_result,
)
from ..services.extract_format import (
    EXTRACT_SCHEMA_VERSION,
    ExtractPayloadError,
    validate_extract_payload,
)
from ..services.maintenance_queue_format import (
    MAINTENANCE_QUEUE_SCHEMA_VERSION,
    MaintenanceQueueError,
    validate_maintenance_queue,
)
from ..services.maintenance_status_format import (
    MAINTENANCE_STATUS_SCHEMA_VERSION,
    MaintenanceStatusError,
    validate_maintenance_status,
)
from ..services.surface_index_format import (
    SURFACE_INDEX_SCHEMA_VERSION,
    SurfaceIndexError,
    validate_surface_index,
)
from ..services.engine_events import (
    ENGINE_EVENT_SCHEMA_VERSION,
    EVENT_KINDS,
    EngineEvent,
    EventKind,
    EventSink,
    operation_identity,
    validate_engine_event,
)
from ..services.host import (
    ALL_CAPABILITIES,
    Host,
    HostCapabilityError,
    MessageStream,
    NoProcessHost,
    current_host,
    using_host,
)
from ..services.bootstrap_service import (
    BootstrapContractError,
    BootstrapRequest,
    BootstrapRequestError,
    BootstrapResult,
    BootstrapServiceError,
)
from ..services.domain_pack import (
    CODE_DOCS_PACK,
    BuiltInPageRenderer,
    BundledHelperToolchain,
    CodeContextSource,
    ContextSource,
    DomainPack,
    EntityPageRequest,
    ExtensionSourceClassifier,
    HelperToolchain,
    ModulePageRequest,
    NoHelperToolchain,
    PageNamer,
    PageRenderer,
    PageRequest,
    SourceClassifier,
    StemPageNamer,
)
from ..services.knowledge_kinds import DEFAULT_KINDS, ConceptKindSpec, KindRegistry, RelationshipKindSpec
from ..services.knowledge_validators import DEFAULT_VALIDATORS, ModelValidator, ValidatorRegistry
from ..services.lint_request import LintRequest, LintRequestError
from ..services.reference_providers import (
    BUILTIN_REFERENCE_PROVIDERS,
    BehaviorFactsProvider,
    CliContractProvider,
    ContractFileProvider,
    ReferenceProvider,
)
from ..services.publication_targets import (
    DEFAULT_PUBLICATION_TARGETS,
    GitHubWikiTarget,
    PublicationTarget,
    PublicationTargetRegistry,
)
from ..services.migrate_service import MigrateError, MigrateOutcome, MigrateRequest, MigrateRequestError
from ..services.sync_service import SyncError, SyncOutcome, SyncRequest, SyncRequestError
from ..services.upgrade_service import UpgradeError, UpgradeOutcome, UpgradeRequest, UpgradeRequestError

if TYPE_CHECKING:
    from ..services.lint_service import LintReport

__all__ = [
    "ALL_CAPABILITIES",
    "ENGINE_CAPABILITIES_SCHEMA_VERSION",
    "ENGINE_EVENT_SCHEMA_VERSION",
    "BUILTIN_REFERENCE_PROVIDERS",
    "CONTEXT_RESPONSE_PROTOCOLS",
    "BehaviorFactsProvider",
    "BootstrapContractError",
    "BootstrapRequest",
    "BootstrapRequestError",
    "BootstrapResult",
    "BootstrapServiceError",
    "BuiltInPageRenderer",
    "BundledHelperToolchain",
    "CODE_DOCS_PACK",
    "CliContractProvider",
    "CodeContextSource",
    "ConceptKindSpec",
    "ContextResponseError",
    "ContextSource",
    "ContractFileProvider",
    "DEFAULT_KINDS",
    "DOCUMENTATION_QUERY_SCHEMA_VERSION",
    "DEFAULT_PUBLICATION_TARGETS",
    "DEFAULT_VALIDATORS",
    "DomainPack",
    "EVENT_KINDS",
    "Engine",
    "EngineEvent",
    "EntityPageRequest",
    "EventSink",
    "ExtensionSourceClassifier",
    "GitHubWikiTarget",
    "Host",
    "HelperToolchain",
    "HostCapabilityError",
    "KindRegistry",
    "LintRequest",
    "LintRequestError",
    "MigrateError",
    "MigrateOutcome",
    "MigrateRequest",
    "MigrateRequestError",
    "ModelValidator",
    "ModulePageRequest",
    "NoHelperToolchain",
    "NoProcessHost",
    "Operation",
    "PageNamer",
    "PageRenderer",
    "PageRequest",
    "PublicationTarget",
    "PublicationTargetRegistry",
    "QueryResultError",
    "EXTRACT_SCHEMA_VERSION",
    "ExtractPayloadError",
    "MAINTENANCE_QUEUE_SCHEMA_VERSION",
    "MAINTENANCE_STATUS_SCHEMA_VERSION",
    "MaintenanceQueueError",
    "MaintenanceStatusError",
    "ReferenceProvider",
    "SEARCH_RESULT_SCHEMA_VERSION",
    "SURFACE_INDEX_SCHEMA_VERSION",
    "SurfaceIndexError",
    "RelationshipKindSpec",
    "SourceClassifier",
    "StemPageNamer",
    "SyncError",
    "SyncOutcome",
    "SyncRequest",
    "SyncRequestError",
    "UpgradeError",
    "UpgradeOutcome",
    "UpgradeRequest",
    "UpgradeRequestError",
    "ValidatorRegistry",
    "current_host",
    "validate_context_response",
    "validate_documentation_query_result",
    "validate_engine_event",
    "validate_extract_payload",
    "validate_maintenance_queue",
    "validate_maintenance_status",
    "validate_search_result",
    "validate_surface_index",
]

HelperPreparation = Literal["auto", "never"]

#: The format :meth:`Engine.capabilities` returns.
ENGINE_CAPABILITIES_SCHEMA_VERSION = "llm-wiki-engine-capabilities/v1"
_P = ParamSpec("_P")
_R = TypeVar("_R")


@dataclass(frozen=True)
class Operation:
    """The settings in force for one engine call and everything beneath it."""

    host: Host
    helper_preparation: HelperPreparation
    helper_cache_dir: str | None
    comparison_policy: str
    validators: ValidatorRegistry = DEFAULT_VALIDATORS
    kinds: KindRegistry = DEFAULT_KINDS
    pack: DomainPack = CODE_DOCS_PACK
    publication_targets: PublicationTargetRegistry = DEFAULT_PUBLICATION_TARGETS


class Engine:
    """One configured engine; independent engines may run side by side."""

    def __init__(
        self,
        *,
        host: Host | None = None,
        helper_preparation: HelperPreparation = "never",
        helper_cache_dir: str | Path | None = None,
        comparison_policy: str = "auto",
        validators: ValidatorRegistry = DEFAULT_VALIDATORS,
        kinds: KindRegistry = DEFAULT_KINDS,
        pack: DomainPack = CODE_DOCS_PACK,
        publication_targets: PublicationTargetRegistry = DEFAULT_PUBLICATION_TARGETS,
    ) -> None:
        from ..services.analysis_compatibility import selected_policy

        host = Host() if host is None else host
        if not isinstance(host, Host):
            raise TypeError("host must be a Host instance")
        if helper_preparation not in ("auto", "never"):
            raise ValueError("helper_preparation must be 'auto' or 'never'")
        if helper_preparation == "auto" and "subprocess" not in host.capabilities:
            raise ValueError("automatic helper preparation requires a host that grants subprocess")
        if helper_cache_dir is not None and not isinstance(helper_cache_dir, (str, Path)):
            raise TypeError("helper_cache_dir must be a path")
        if not isinstance(validators, ValidatorRegistry):
            raise TypeError("validators must be a ValidatorRegistry")
        if not isinstance(kinds, KindRegistry):
            raise TypeError("kinds must be a KindRegistry")
        if not isinstance(pack, DomainPack):
            raise TypeError("pack must be a DomainPack")
        if not isinstance(publication_targets, PublicationTargetRegistry):
            raise TypeError("publication_targets must be a PublicationTargetRegistry")
        self._host = host
        self._helper_preparation: HelperPreparation = helper_preparation
        self._helper_cache_dir = None if helper_cache_dir is None else str(helper_cache_dir)
        self._comparison_policy = selected_policy(comparison_policy)
        self._validators = validators
        self._kinds = kinds
        self._pack = pack
        self._publication_targets = publication_targets

    @property
    def host(self) -> Host:
        return self._host

    def capabilities(self) -> dict[str, object]:
        """What this engine may do, so a caller can explain a refused operation.

        The result is an ``llm-wiki-engine-capabilities/v1`` document (JSON
        Schema ``llm-wiki-engine-capabilities-v1.schema.json``).
        """
        return {
            "schema_version": ENGINE_CAPABILITIES_SCHEMA_VERSION,
            "granted": sorted(self._host.capabilities),
            "missing": sorted(ALL_CAPABILITIES - self._host.capabilities),
            "helper_preparation": self._helper_preparation,
            "comparison_policy": self._comparison_policy,
            "validators": list(self._validators.names),
            "kinds": self._kinds.describe(),
            "pack": self._pack.describe(),
            "publication_targets": self._publication_targets.describe(),
        }

    @contextmanager
    def operation(self) -> Iterator[Operation]:
        """Apply this engine's grants to all work inside the block."""
        from ..services.analysis_compatibility import comparison_scope
        from ..services.domain_pack import using_pack
        from ..services.helper_runtime import helper_operation, helper_policy
        from ..services.knowledge_kinds import using_kinds
        from ..services.knowledge_validators import using_validators
        from ..services.publication_targets import using_publication_targets

        with ExitStack() as stack:
            stack.enter_context(using_host(self._host))
            stack.enter_context(comparison_scope(self._comparison_policy))
            stack.enter_context(helper_policy(self._helper_preparation, cache_dir=self._helper_cache_dir))
            stack.enter_context(helper_operation(fresh=True))
            stack.enter_context(using_validators(self._validators))
            stack.enter_context(using_kinds(self._kinds))
            stack.enter_context(using_pack(self._pack))
            stack.enter_context(using_publication_targets(self._publication_targets))
            yield Operation(
                self._host, self._helper_preparation, self._helper_cache_dir, self._comparison_policy,
                self._validators, self._kinds, self._pack, self._publication_targets,
            )

    def call(self, function: Callable[_P, _R], /, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        """Run ``function`` (typically from :mod:`llm_wiki_cli.api`) in one operation.

        Unlike the use-case methods, this reports no events.
        """
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

    def sync(self, request: SyncRequest) -> SyncOutcome:
        """Incrementally update a managed wiki; progress goes to the host's streams.

        Raises :class:`SyncError` (or :class:`SyncRequestError`) when sync stops.
        """
        from ..services.sync_runtime import execute_sync

        return self._run("sync", request, lambda: execute_sync(request), _to_dict)

    def bootstrap(self, request: BootstrapRequest) -> BootstrapResult:
        """Create a first-use wiki; progress goes to the host's streams.

        Raises :class:`BootstrapRequestError` for invalid options and
        :class:`BootstrapServiceError` when bootstrap cannot complete.
        """
        from ..services.bootstrap_runtime import execute_bootstrap

        def run() -> BootstrapResult:
            progress = MessageStream("stdout")
            try:
                return execute_bootstrap(request, progress_stream=progress)  # type: ignore[arg-type]
            finally:
                progress.close()

        return self._run("bootstrap", request, run, _to_dict)

    def lint(self, request: LintRequest) -> LintReport:
        """Check a wiki against its source; ``report.passed`` is the verdict.

        Extractor failures are report issues. Raises :class:`LintRequestError`
        when a path breaks the workspace policy.
        """
        from ..services.lint_service import execute_lint

        return self._run(
            "lint", request, lambda: execute_lint(request),
            lambda report: {"passed": report.passed, "issue_count": report.issue_count},
        )

    def migrate(self, request: MigrateRequest) -> MigrateOutcome:
        """Bring an older wiki to current page naming; progress goes to the host.

        Raises :class:`MigrateError` (or :class:`MigrateRequestError`) when the
        migration stops.
        """
        from ..services.migrate_runtime import execute_migrate

        return self._run("migrate", request, lambda: execute_migrate(request), _to_dict)

    def upgrade(self, request: UpgradeRequest) -> UpgradeOutcome:
        """Refresh the managed agent schema, skills and wiki layout in place.

        Unlike the other use cases this changes the repository's agent setup:
        it rewrites the agent instruction file, refreshes managed skills and
        removes retired git hooks. Raises :class:`UpgradeError` when the
        upgrade stops.
        """
        from ..services.upgrade_runtime import execute_upgrade

        return self._run("upgrade", request, lambda: execute_upgrade(request), _to_dict)


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
