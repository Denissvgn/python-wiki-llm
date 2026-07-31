"""Supported API for extraction, wiki, native knowledge, and documentation."""

from __future__ import annotations

import inspect
import warnings
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, NoReturn, ParamSpec, TypeVar, cast

from .commands import bootstrap_cmd, context_cmd, extract_cmd
from .api_types import (
    CalleesResult,
    CallersResult,
    ConceptResult,
    ConceptSectionsResult,
    ContextPayload,
    DataFlowForEntrypointResult,
    DependencyNeighborhoodResult,
    DocumentationExportResult,
    DoctorResult,
    EvidenceExplanationResult,
    ExtractSourceResult,
    FlowForEntrypointResult,
    MarkdownContextResult,
    PagesForSymbolResult,
    RelatedConceptsResult,
    TypedGraphTraversalResult,
    WikiPage,
    WikiPageCounts,
    WikiPagesResult,
)
from .config import (
    DEFAULT_WIKI_DIR,
    PathValidationError,
    validate_path,
    validate_source_root,
)
from .services import context_packet as context_packet_service
from .services import wiki_surface
from .services.contracts import (
    BOOTSTRAP_SUMMARY_SCHEMA_VERSION,
    DOCUMENTATION_AGENT_PACKET_SCHEMA_VERSION,
    DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
    DOCUMENTATION_FINAL_REPORT_SCHEMA_VERSION,
    DOCUMENTATION_MODEL_ROUTING_SCHEMA_VERSION,
    DOCUMENTATION_MODEL_SELECTION_SCHEMA_VERSION,
    DOCUMENTATION_RUN_SCHEMA_VERSION,
    DOCUMENTATION_VERIFICATION_SCHEMA_VERSION,
    DOCTOR_SCHEMA_VERSION,
    EXTRACT_SCHEMA_VERSION,
    P0_CALIBRATION_AGENT_PACKET_SCHEMA_VERSION,
    P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION,
    P0_CALIBRATION_DECISION_SCOPE,
    P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION,
    P0_CALIBRATION_RUN_SCHEMA_VERSION,
    P0_CALIBRATION_VERIFICATION_REPORT_SCHEMA_VERSION,
    QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION,
)
from .services.bootstrap_service import (
    BootstrapContractError,
    BootstrapExtractionError,
    BootstrapRequestError,
    BootstrapRequest,
    BootstrapResult,
    BootstrapServiceError,
)
from .services.dependencies import analyze_dependencies
from .services.doctor_service import build_doctor_report
from .services.documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
)
from .services.documentation_query_builder import (
    build_live_documentation_query_service,
)
from .services.knowledge_verification import (
    attach_machine_verification_read_view,
    verification_summaries_for_concepts,
)
from .services.documentation_model_policy import (
    DocumentationModelEscalationRule,
    DocumentationModelOverride,
    DocumentationModelPolicyError,
    DocumentationModelRoute,
    DocumentationModelRoutingPolicy,
    DocumentationModelRoutingRequest,
    DocumentationModelSelection,
    select_documentation_model,
    validate_documentation_model_selection,
)
from .services.documentation_policy import DocumentationPolicyError
from .services.documentation_run import (
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
    build_documentation_agent_packet,
    export_documentation_run,
    get_documentation_run_status,
    prepare_documentation_run,
    record_documentation_agent_result,
    verify_documentation_run,
)
from .services.documentation_wiki_input import (
    DocumentationWikiInputError,
    DocumentationWikiSnapshot,
    adopt_documentation_wiki_snapshot,
    fingerprint_documentation_wiki_input,
)

from .services.entrypoints import build_flow
from .services.wiki_surface_index import evaluate_surface_index

QualifiedContextPacket = context_packet_service.QualifiedContextPacket
ContextPacketValidation = context_packet_service.ContextPacketValidation
ContextBasisComparison = context_packet_service.ContextBasisComparison
ContextPacketReconciliation = context_packet_service.ContextPacketReconciliation
ContextPacketError = context_packet_service.ContextPacketError
ContextPacketMalformedError = context_packet_service.ContextPacketMalformedError
ContextPacketSourceMutationError = (
    context_packet_service.ContextPacketSourceMutationError
)
ContextPacketUnavailableError = (
    context_packet_service.ContextPacketUnavailableError
)
ContextPacketPathPolicyError = (
    context_packet_service.ContextPacketPathPolicyError
)

_CALIBRATION_CONTROLLER_TYPE_EXPORTS = frozenset(
    {
        "P0CalibrationAgentPacket",
        "P0CalibrationAgentResult",
        "P0CalibrationDispatchReceipt",
        "P0CalibrationError",
        "P0CalibrationIntegrityError",
        "P0CalibrationRecoveryError",
        "P0CalibrationRun",
        "P0CalibrationSchemaError",
        "P0CalibrationStatus",
        "P0CalibrationTransitionError",
        "P0CalibrationVerificationReport",
    }
)
_CALIBRATION_HOST_TYPE_EXPORTS = frozenset(
    {
        "HostBrokerAuthenticationError",
        "HostBrokerAuthenticationProof",
        "HostBrokerAuthenticationUnavailable",
        "HostBrokerAuthenticator",
    }
)
_CALIBRATION_CONTROLLER_MODULES = frozenset(
    {
        "llm_wiki_cli.services.calibration.controller",
        "llm_wiki_cli.services.documentation_calibration_controller",
    }
)
_CALIBRATION_HOST_MODULES = frozenset(
    {
        "llm_wiki_cli.services.calibration.host_broker",
        "llm_wiki_cli.services.documentation_calibration_host_broker",
    }
)
_CALIBRATION_TYPE_EXPORTS = (
    _CALIBRATION_CONTROLLER_TYPE_EXPORTS | _CALIBRATION_HOST_TYPE_EXPORTS
)


def _load_calibration_type_exports(names: frozenset[str]) -> None:
    """Populate explicitly requested calibration types for runtime introspection."""

    controller_names = names & _CALIBRATION_CONTROLLER_TYPE_EXPORTS
    if controller_names:
        from .services.calibration import controller

        globals().update(
            (name, getattr(controller, name))
            for name in controller_names
        )
    host_names = names & _CALIBRATION_HOST_TYPE_EXPORTS
    if host_names:
        from .services.calibration import host_broker

        globals().update(
            (name, getattr(host_broker, name))
            for name in host_names
        )


class _LazyCalibrationAnnotations(dict[str, Any]):
    """Load calibration types only when an annotation consumer evaluates them."""

    def __init__(
        self,
        annotations: Mapping[str, Any],
        *,
        exports: frozenset[str],
    ) -> None:
        super().__init__(annotations)
        self._exports = exports

    def _resolve(self) -> None:
        _load_calibration_type_exports(self._exports)

    def __getitem__(self, key: str) -> Any:
        self._resolve()
        return super().__getitem__(key)

    def __iter__(self) -> Iterator[str]:
        self._resolve()
        return super().__iter__()

    def copy(self) -> dict[str, Any]:
        self._resolve()
        return super().copy()

    def items(self) -> Any:
        self._resolve()
        return super().items()

    def keys(self) -> Any:
        self._resolve()
        return super().keys()

    def values(self) -> Any:
        self._resolve()
        return super().values()


def _defer_calibration_annotations(
    function: Callable[..., Any],
) -> None:
    """Keep type hints lazy and resolvable across a public wrapper chain."""

    current: Any = function
    seen: set[int] = set()
    while callable(current) and id(current) not in seen:
        seen.add(id(current))
        annotations = dict(getattr(current, "__annotations__", {}))
        exports = frozenset(
            export
            for export in _CALIBRATION_TYPE_EXPORTS
            if any(
                export in str(annotation)
                for annotation in annotations.values()
            )
        )
        current.__annotations__ = _LazyCalibrationAnnotations(
            annotations,
            exports=exports,
        )
        current = getattr(current, "__wrapped__", None)


def __getattr__(name: str) -> Any:
    """Resolve supported calibration types only when callers request them."""

    if name not in _CALIBRATION_TYPE_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    _load_calibration_type_exports(frozenset({name}))
    return globals()[name]


def __dir__() -> list[str]:
    """Include lazy public types in module introspection."""

    return sorted(
        set(globals())
        | _CALIBRATION_CONTROLLER_TYPE_EXPORTS
        | _CALIBRATION_HOST_TYPE_EXPORTS
    )


class LlmWikiApiError(RuntimeError):
    """Base exception raised by the supported Python API."""


class InvalidRequestError(LlmWikiApiError):
    """Raised when arguments or a submitted request contract are invalid."""


class WorkspaceStateError(LlmWikiApiError):
    """Raised when workspace state or an operational dependency is unusable."""


class ArtifactIntegrityError(LlmWikiApiError):
    """Raised when persisted or supplied artifact integrity cannot be trusted."""


# Compatibility aliases retain the original catch points while making every
# raised API exception one of the stable taxonomy leaves above.
PathPolicyError = InvalidRequestError
ExtractionError = WorkspaceStateError
BootstrapError = WorkspaceStateError

_API_ERROR_LEAVES = (
    InvalidRequestError,
    WorkspaceStateError,
    ArtifactIntegrityError,
)

_WIKI_INPUT_ARTIFACT_CATEGORIES = frozenset(
    {
        "input_changed_during_snapshot",
        "knowledge_artifact_orphan",
        "knowledge_schema_unsupported",
        "manifest_schema_invalid",
        "manifest_schema_unsupported",
        "metadata_corrupt",
        "metadata_pair_incomplete",
        "native_artifact_form_invalid",
        "native_artifact_invalid",
        "native_artifact_marker_mismatch",
        "native_artifact_marker_missing",
        "native_artifact_set_incomplete",
        "native_markdown_snapshot_invalid",
        "native_markdown_snapshot_mismatch",
        "native_page_parity_mismatch",
        "snapshot_hash_mismatch",
        "surface_schema_invalid",
        "surface_schema_unsupported",
    }
)
_WIKI_INPUT_WORKSPACE_CATEGORIES = frozenset(
    {
        "input_missing",
        "input_not_directory",
        "input_unreadable",
        "secure_copy_unavailable",
        "secure_input_traversal_unavailable",
        "source_not_directory",
        "source_unavailable",
        "workspace_copy_failed",
        "workspace_rollback_failed",
        "workspace_unreadable",
        "workspace_unwritable",
    }
)


_P = ParamSpec("_P")
_R = TypeVar("_R")


def _caused_by(exc: BaseException, expected: type[BaseException]) -> bool:
    """Return whether an explicitly chained cause has the requested type."""

    current = exc.__cause__
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        if isinstance(current, expected):
            return True
        seen.add(id(current))
        current = current.__cause__
    return False


def _has_exception_origin(
    exc: BaseException,
    module_names: frozenset[str],
) -> bool:
    """Return whether one exception inherits from a named service module."""

    return any(
        base.__module__ in module_names
        for base in type(exc).__mro__
    )


def _calibration_error_category(exc: Exception) -> str | None:
    """Classify calibration failures without importing calibration on core paths."""

    if _has_exception_origin(exc, _CALIBRATION_CONTROLLER_MODULES):
        from .services.calibration import controller

        if isinstance(
            exc,
            (
                controller.P0CalibrationIntegrityError,
                controller.P0CalibrationRecoveryError,
            ),
        ):
            return "artifact"
        if isinstance(exc, controller.P0CalibrationSchemaError):
            return "invalid"
        if isinstance(
            exc,
            (
                controller.P0CalibrationTransitionError,
                controller.P0CalibrationError,
            ),
        ):
            return "workspace"
    if _has_exception_origin(exc, _CALIBRATION_HOST_MODULES):
        from .services.calibration import host_broker

        if isinstance(exc, host_broker.HostBrokerAuthenticationError):
            return "invalid"
    return None


def _raise_api_error(exc: Exception) -> NoReturn:
    """Translate one internal exception at the supported API boundary."""

    for leaf in _API_ERROR_LEAVES:
        if isinstance(exc, leaf):
            raise leaf(str(exc)) from exc
    calibration_category = _calibration_error_category(exc)
    if calibration_category == "artifact":
        raise ArtifactIntegrityError(str(exc)) from exc
    if calibration_category == "invalid":
        raise InvalidRequestError(str(exc)) from exc
    if calibration_category == "workspace":
        raise WorkspaceStateError(str(exc)) from exc
    if isinstance(exc, (PathValidationError, DocumentationPolicyError)) and (
        _caused_by(exc, OSError)
    ):
        raise WorkspaceStateError(str(exc)) from exc
    if isinstance(exc, DocumentationWikiInputError):
        category = getattr(exc, "category", "invalid_wiki_input")
        if category in _WIKI_INPUT_ARTIFACT_CATEGORIES:
            raise ArtifactIntegrityError(str(exc)) from exc
        if category in _WIKI_INPUT_WORKSPACE_CATEGORIES:
            raise WorkspaceStateError(str(exc)) from exc
        raise InvalidRequestError(str(exc)) from exc
    if isinstance(
        exc,
        (
            DocumentationIntegrityError,
        ),
    ):
        raise ArtifactIntegrityError(str(exc)) from exc
    if isinstance(
        exc,
        (
            DocumentationSchemaError,
            PathValidationError,
            DocumentationQueryError,
            DocumentationPolicyError,
            DocumentationModelPolicyError,
            BootstrapRequestError,
            wiki_surface.WikiSurfaceError,
            context_cmd.ProtocolRequestError,
            AttributeError,
            ValueError,
            TypeError,
            LookupError,
        ),
    ):
        raise InvalidRequestError(str(exc)) from exc
    if isinstance(
        exc,
        (
            BootstrapExtractionError,
            BootstrapContractError,
            BootstrapServiceError,
            DocumentationTransitionError,
            DocumentationRunError,
            extract_cmd.ExtractorFailureError,
            OSError,
            RuntimeError,
        ),
    ):
        raise WorkspaceStateError(str(exc)) from exc
    raise WorkspaceStateError(str(exc)) from exc


def _api_boundary(function: Callable[_P, _R]) -> Callable[_P, _R]:
    """Wrap a synchronous public callable in the stable exception taxonomy."""

    signature = inspect.signature(function)

    @wraps(function)
    def wrapped(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        # Invocation-shape TypeError remains Python's normal call contract; only
        # failures raised after a valid call enters the API taxonomy.
        signature.bind(*args, **kwargs)
        try:
            return function(*args, **kwargs)
        except LlmWikiApiError as exc:
            if type(exc) in _API_ERROR_LEAVES:
                raise
            _raise_api_error(exc)
        except Exception as exc:
            _raise_api_error(exc)

    setattr(wrapped, "__llm_wiki_api_boundary__", True)
    return wrapped


@_api_boundary
def bootstrap_wiki(
    source_root: str,
    wiki_root: str,
    *,
    depth: str = "full",
    skip_workflows: bool = False,
    skip_flows: bool = False,
    skip_data_flow: bool = False,
    skip_dependencies: bool = False,
    api_contracts: bool = False,
    openapi_file: str | None = None,
    dependency_graph_detail: str = "auto",
    overwrite: bool = False,
    helper_cache_dir: str | None = None,
    include_tests: list[str] | None = None,
    trust_source_plugins: bool = False,
) -> BootstrapResult:
    """Build a first-use deterministic wiki through the typed service boundary.

    The library boundary always uses source-adapter behavior and therefore does
    not install or rewrite target-repository agent instructions. ``overwrite``
    remains in the signature for compatibility, but ``True`` is rejected before
    source extraction or target writes.
    """

    request = BootstrapRequest(
        source_root=source_root,
        wiki_root=wiki_root,
        depth=depth,
        skip_workflows=skip_workflows,
        skip_flows=skip_flows,
        skip_data_flow=skip_data_flow,
        skip_dependencies=skip_dependencies,
        api_contracts=api_contracts,
        openapi_file=openapi_file,
        dependency_graph_detail=dependency_graph_detail,
        overwrite=overwrite,
        source_adapter=True,
        helper_cache_dir=helper_cache_dir,
        include_tests=include_tests,
        trust_source_plugins=trust_source_plugins,
    )
    try:
        return bootstrap_cmd.execute_bootstrap(request)
    except BootstrapRequestError as exc:
        raise InvalidRequestError(str(exc)) from exc
    except BootstrapContractError as exc:
        raise WorkspaceStateError(str(exc)) from exc
    except BootstrapServiceError as exc:
        raise WorkspaceStateError(str(exc)) from exc


@_api_boundary
def extract_source(
    src_dir: str = ".",
    *,
    changed: bool = False,
    summary: bool = False,
    deep: bool = False,
    paths: list[str] | None = None,
    package: str | None = None,
    include_empty: bool = False,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> ExtractSourceResult:
    """Return the stable ``llm-wiki extract`` JSON payload as a dict."""
    try:
        result = extract_cmd.build_extract_payload(
            src_dir,
            changed=changed,
            summary=summary,
            deep=deep,
            paths=paths,
            package_filter=package,
            include_empty=include_empty,
            allow_external_src=allow_external_src,
            read_only=read_only,
        )
    except PathValidationError as exc:
        if _caused_by(exc, OSError):
            raise WorkspaceStateError(str(exc)) from exc
        raise PathPolicyError(str(exc)) from exc
    except extract_cmd.ExtractorFailureError as exc:
        raise WorkspaceStateError(str(exc)) from exc
    except ValueError as exc:
        raise InvalidRequestError(str(exc)) from exc
    return cast(ExtractSourceResult, result.payload)


@_api_boundary
def build_context(
    src_dir: str = ".",
    *,
    budget: int = 32000,
    format: str = "json",
    focus: str | list[str] = "changed",
    filters: dict[str, Any] | None = None,
    wiki_dir: str = DEFAULT_WIKI_DIR,
    prefer_fresh: bool = False,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> ContextPayload | MarkdownContextResult:
    """Return a supported context payload without depending on CLI internals."""
    focus_values = _normalise_focus(focus)
    request = {
        "protocol": context_cmd.PROTOCOL_VERSION,
        "budget_tokens": budget,
        "focus": focus_values,
        "format": format,
        "filters": filters or {},
        "prefer_fresh": prefer_fresh,
    }
    try:
        validated = context_cmd._validate_protocol_request(request)
        payload, warnings = context_cmd._build_context(
            src_dir,
            validated["budget_tokens"],
            validated["format"],
            validated["focus"],
            validated["filters"],
            prefer_fresh=validated["prefer_fresh"],
            emit_warnings=False,
            allow_external_src=allow_external_src,
            read_only=read_only,
            wiki_dir=wiki_dir,
        )
    except PathValidationError as exc:
        if _caused_by(exc, OSError):
            raise WorkspaceStateError(str(exc)) from exc
        raise PathPolicyError(str(exc)) from exc
    except context_cmd.ProtocolRequestError as exc:
        if exc.field == "wiki_dir":
            raise PathPolicyError(str(exc)) from exc
        if exc.field == "src_dir":
            raise WorkspaceStateError(str(exc)) from exc
        raise InvalidRequestError(str(exc)) from exc

    if validated["format"] == "markdown":
        return cast(
            MarkdownContextResult,
            {
                "content": context_cmd._render_markdown(payload),
                "payload": payload,
                "warnings": warnings,
            },
        )

    result: dict[str, Any] = dict(payload)
    if warnings:
        result["warnings"] = warnings
    return cast(ContextPayload, result)


@_api_boundary
def build_qualified_context(
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    request: Mapping[str, Any] | None = None,
    *,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> QualifiedContextPacket:
    """Build a canonical in-memory qualified-context packet."""

    try:
        packet = context_packet_service.build_qualified_context(
            src_dir,
            wiki_dir,
            request,
            allow_external_src=allow_external_src,
            read_only=read_only,
        )
    except PathValidationError as exc:
        if _caused_by(exc, OSError):
            raise WorkspaceStateError(str(exc)) from exc
        raise PathPolicyError(str(exc)) from exc
    except context_packet_service.ContextPacketPathPolicyError as exc:
        raise PathPolicyError(str(exc)) from exc
    except (
        context_packet_service.ContextPacketSourceMutationError,
        context_packet_service.ContextPacketUnavailableError,
    ) as exc:
        raise WorkspaceStateError(str(exc)) from exc
    except context_cmd.ProtocolRequestError as exc:
        if exc.field == "wiki_dir":
            raise PathPolicyError(str(exc)) from exc
        if exc.field == "src_dir":
            raise WorkspaceStateError(str(exc)) from exc
        raise InvalidRequestError(str(exc)) from exc
    return packet


@_api_boundary
def validate_context_packet(
    packet_bytes: bytes | bytearray | memoryview,
) -> ContextPacketValidation:
    """Validate canonical packet bytes without claiming live currentness."""

    try:
        validation = context_packet_service.validate_context_packet(packet_bytes)
    except context_packet_service.ContextPacketPathPolicyError as exc:
        raise PathPolicyError(str(exc)) from exc
    except context_packet_service.ContextPacketError as exc:
        raise InvalidRequestError(str(exc)) from exc
    return validation


@_api_boundary
def compare_context_packet_basis(
    packet_bytes: bytes | bytearray | memoryview,
    expected_basis: Mapping[str, Any],
) -> ContextBasisComparison:
    """Compare caller basis without upgrading it to a currentness claim."""

    try:
        comparison = context_packet_service.compare_context_packet_basis(
            packet_bytes,
            expected_basis,
        )
    except context_packet_service.ContextPacketPathPolicyError as exc:
        raise PathPolicyError(str(exc)) from exc
    except context_packet_service.ContextPacketError as exc:
        raise InvalidRequestError(str(exc)) from exc
    return comparison


@_api_boundary
def reconcile_context_packet(
    packet_bytes: bytes | bytearray | memoryview,
    src_dir: str = ".",
    *,
    wiki_dir: str = DEFAULT_WIKI_DIR,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> ContextPacketReconciliation:
    """Reconcile packet facets against one fresh official read."""

    try:
        reconciliation = context_packet_service.reconcile_context_packet(
            packet_bytes,
            src_dir,
            wiki_dir,
            allow_external_src=allow_external_src,
            read_only=read_only,
        )
    except PathValidationError as exc:
        if _caused_by(exc, OSError):
            raise WorkspaceStateError(str(exc)) from exc
        raise PathPolicyError(str(exc)) from exc
    except context_packet_service.ContextPacketPathPolicyError as exc:
        raise PathPolicyError(str(exc)) from exc
    except (
        context_packet_service.ContextPacketSourceMutationError,
        context_packet_service.ContextPacketUnavailableError,
    ) as exc:
        raise WorkspaceStateError(str(exc)) from exc
    except context_packet_service.ContextPacketError as exc:
        raise InvalidRequestError(str(exc)) from exc
    except context_cmd.ProtocolRequestError as exc:
        if exc.field == "wiki_dir":
            raise PathPolicyError(str(exc)) from exc
        if exc.field == "src_dir":
            raise WorkspaceStateError(str(exc)) from exc
        raise InvalidRequestError(str(exc)) from exc
    return reconciliation


@_api_boundary
def list_wiki_pages(wiki_dir: str = DEFAULT_WIKI_DIR) -> WikiPagesResult:
    """Return registry-backed wiki page metadata without source extraction."""
    try:
        wiki_root = _validate_wiki_dir(wiki_dir)
        pages = [
            _wiki_page_payload(page)
            for page in wiki_surface.collect_wiki_pages(wiki_root)
        ]
    except PathValidationError as exc:
        raise PathPolicyError(str(exc)) from exc
    except wiki_surface.WikiSurfaceError as exc:
        raise InvalidRequestError(str(exc)) from exc
    except OSError as exc:
        raise WorkspaceStateError(str(exc)) from exc

    return {
        "wiki_dir": _display_path(wiki_root),
        "counts": _wiki_page_counts(pages),
        "pages": pages,
    }


@_api_boundary
def doctor(
    src_dir: str = ".",
    *,
    wiki_dir: str = DEFAULT_WIKI_DIR,
    strict: bool = False,
    allow_external_src: bool = False,
) -> DoctorResult:
    """Return the stable read-only knowledge health report."""

    report = build_doctor_report(
        wiki_dir,
        src_dir,
        strict=strict,
        allow_external_src=allow_external_src,
    )
    return cast(DoctorResult, report.to_payload())


@_api_boundary
def build_documentation_query_service(
    src_dir: str = ".",
    *,
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> DocumentationGraphQueryService:
    """Build a supported graph query service over derived documentation data."""
    try:
        src_root = validate_source_root(
            src_dir,
            "--src-dir",
            allow_external=allow_external_src,
        )
        wiki_root = _validate_wiki_dir(wiki_dir)
        return build_live_documentation_query_service(
            source_root=src_root,
            wiki_root=wiki_root,
            limit=limit,
            read_only=read_only,
            extract_payload_builder=extract_cmd.build_extract_payload,
            call_edge_resolver=extract_cmd.resolve_call_edges,
            flow_builder=build_flow,
            surface_evaluator=evaluate_surface_index,
            knowledge_view_builder=context_cmd._build_context_knowledge_view,
            query_surface_builder=context_cmd._context_query_surface,
            dependency_analyzer=analyze_dependencies,
            verification_view_attacher=attach_machine_verification_read_view,
            verification_summarizer=verification_summaries_for_concepts,
            service_factory=DocumentationGraphQueryService,
        )
    except PathValidationError as exc:
        if _caused_by(exc, OSError):
            raise WorkspaceStateError(str(exc)) from exc
        raise PathPolicyError(str(exc)) from exc
    except extract_cmd.ExtractorFailureError as exc:
        raise WorkspaceStateError(str(exc)) from exc
    except DocumentationQueryError as exc:
        raise InvalidRequestError(str(exc)) from exc
    except ValueError as exc:
        raise InvalidRequestError(str(exc)) from exc
    except OSError as exc:
        raise WorkspaceStateError(str(exc)) from exc


@_api_boundary
def flow_for_entrypoint(
    id_or_symbol: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> FlowForEntrypointResult:
    """Return a bounded user-flow query result for an entry point."""
    return cast(
        FlowForEntrypointResult,
        _run_query(
            lambda: _query_service(
                service,
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                limit=limit,
                allow_external_src=allow_external_src,
                read_only=read_only,
            ).flow_for_entrypoint(id_or_symbol)
        ),
    )


@_api_boundary
def data_flow_for_entrypoint(
    id_or_symbol: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> DataFlowForEntrypointResult:
    """Return a bounded data-flow query result for an entry point."""
    return cast(
        DataFlowForEntrypointResult,
        _run_query(
            lambda: _query_service(
                service,
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                limit=limit,
                allow_external_src=allow_external_src,
                read_only=read_only,
            ).data_flow_for_entrypoint(id_or_symbol)
        ),
    )


@_api_boundary
def callers(
    symbol: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> CallersResult:
    """Return bounded callers for one callable symbol."""
    return cast(
        CallersResult,
        _run_query(
            lambda: _query_service(
                service,
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                limit=limit,
                allow_external_src=allow_external_src,
                read_only=read_only,
            ).callers(symbol)
        ),
    )


@_api_boundary
def callees(
    symbol: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> CalleesResult:
    """Return bounded callees for one callable symbol."""
    return cast(
        CalleesResult,
        _run_query(
            lambda: _query_service(
                service,
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                limit=limit,
                allow_external_src=allow_external_src,
                read_only=read_only,
            ).callees(symbol)
        ),
    )


@_api_boundary
def dependency_neighborhood(
    path: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> DependencyNeighborhoodResult:
    """Return bounded dependency neighbors for one source path."""
    return cast(
        DependencyNeighborhoodResult,
        _run_query(
            lambda: _query_service(
                service,
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                limit=limit,
                allow_external_src=allow_external_src,
                read_only=read_only,
            ).dependency_neighborhood(path)
        ),
    )


@_api_boundary
def pages_for_symbol(
    symbol: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> PagesForSymbolResult:
    """Return wiki surface pages related to one symbol."""
    return cast(
        PagesForSymbolResult,
        _run_query(
            lambda: _query_service(
                service,
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                limit=limit,
                allow_external_src=allow_external_src,
                read_only=read_only,
            ).pages_for_symbol(symbol)
        ),
    )


@_api_boundary
def get_concept(
    locator_or_exact_route: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> ConceptResult:
    """Return one concept by current coordinate, durable UID, or alias."""
    return cast(
        ConceptResult,
        _run_query(
            lambda: _query_service(
                service,
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                limit=limit,
                allow_external_src=allow_external_src,
                read_only=read_only,
            ).get_concept(locator_or_exact_route)
        ),
    )


@_api_boundary
def list_concept_sections(
    locator_or_exact_route: object,
    *,
    ownership: str | None = None,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> ConceptSectionsResult:
    """Return bounded document-order sections for one exact concept."""
    return cast(
        ConceptSectionsResult,
        _run_query(
            lambda: _query_service(
                service,
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                limit=limit,
                allow_external_src=allow_external_src,
                read_only=read_only,
            ).list_concept_sections(
                locator_or_exact_route,
                ownership=ownership,
            )
        ),
    )


@_api_boundary
def related_concepts(
    locator_or_exact_route: object,
    *,
    direction: str = "both",
    kinds: Iterable[str] | None = None,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> RelatedConceptsResult:
    """Return bounded knowledge relationships for one exact concept identity."""
    return cast(
        RelatedConceptsResult,
        _run_query(
            lambda: _query_service(
                service,
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                limit=limit,
                allow_external_src=allow_external_src,
                read_only=read_only,
            ).related_concepts(
                locator_or_exact_route,
                direction=direction,
                kinds=kinds,
            )
        ),
    )


@_api_boundary
def traverse_typed_graph(
    locator_or_exact_route: object,
    *,
    direction: str = "both",
    kinds: Iterable[str] | None = None,
    origins: Iterable[str] | None = None,
    resolutions: Iterable[str] | None = None,
    include_evidence: bool = False,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> TypedGraphTraversalResult:
    """Traverse persisted typed relationships for one exact concept."""
    return cast(
        TypedGraphTraversalResult,
        _run_query(
            lambda: _query_service(
                service,
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                limit=limit,
                allow_external_src=allow_external_src,
                read_only=read_only,
            ).traverse_typed_graph(
                locator_or_exact_route,
                direction=direction,
                kinds=kinds,
                origins=origins,
                resolutions=resolutions,
                include_evidence=include_evidence,
            )
        ),
    )


@_api_boundary
def explain_evidence(
    locator_or_exact_route: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> EvidenceExplanationResult:
    """Return stored and computed evidence for one exact concept identity."""
    return cast(
        EvidenceExplanationResult,
        _run_query(
            lambda: _query_service(
                service,
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                limit=limit,
                allow_external_src=allow_external_src,
                read_only=read_only,
            ).explain_evidence(locator_or_exact_route)
        ),
    )


def _normalise_focus(focus: str | list[str]) -> list[str]:
    if isinstance(focus, str):
        if focus == "all":
            return ["all"]
        if focus == "changed":
            return ["changed", "neighbors"]
        return [focus]
    return list(focus)


def _validate_wiki_dir(wiki_dir: str) -> Path:
    return validate_path(wiki_dir, "--wiki-dir")


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _wiki_page_payload(page: wiki_surface.WikiSurfacePage) -> WikiPage:
    return {
        "kind": page.kind.value,
        "id": page.page_id,
        "label": page.label,
        "canonical_path": page.relative_path,
        "mcp_uri": page.mcp_uri,
        "role": page.role.value,
        "obsidian_mirror_dir": page.obsidian_mirror_dir,
    }


def _wiki_page_counts(pages: list[WikiPage]) -> WikiPageCounts:
    by_kind = {entry.kind.value: 0 for entry in wiki_surface.iter_page_kinds()}
    for page in pages:
        by_kind[str(page["kind"])] += 1
    architecture_pages = (
        by_kind[wiki_surface.PageKind.API_CONTRACTS.value]
        + by_kind[wiki_surface.PageKind.DEPENDENCIES.value]
        + by_kind[wiki_surface.PageKind.LOAD_ORDER.value]
    )
    return {
        "total": len(pages),
        "by_kind": by_kind,
        "architecture_pages": architecture_pages,
    }


def _query_service(
    service: DocumentationGraphQueryService | None,
    *,
    src_dir: str,
    wiki_dir: str,
    limit: int,
    allow_external_src: bool,
    read_only: bool,
) -> DocumentationGraphQueryService:
    if service is not None:
        return service
    return build_documentation_query_service(
        src_dir,
        wiki_dir=wiki_dir,
        limit=limit,
        allow_external_src=allow_external_src,
        read_only=read_only,
    )


def _run_query(callback: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return callback()
    except DocumentationQueryError as exc:
        raise InvalidRequestError(str(exc)) from exc


# Public service functions are adapted here rather than requiring callers to
# understand each service's private exception family.
_adopt_documentation_wiki_snapshot_impl = adopt_documentation_wiki_snapshot
adopt_documentation_wiki_snapshot = _api_boundary(
    _adopt_documentation_wiki_snapshot_impl
)
_fingerprint_documentation_wiki_input_impl = fingerprint_documentation_wiki_input
fingerprint_documentation_wiki_input = _api_boundary(
    _fingerprint_documentation_wiki_input_impl
)

_prepare_documentation_run_impl = prepare_documentation_run
prepare_documentation_run = _api_boundary(_prepare_documentation_run_impl)
_get_documentation_run_status_impl = get_documentation_run_status
get_documentation_run_status = _api_boundary(_get_documentation_run_status_impl)
_build_documentation_agent_packet_impl = build_documentation_agent_packet
build_documentation_agent_packet = _api_boundary(
    _build_documentation_agent_packet_impl
)
_record_documentation_agent_result_impl = record_documentation_agent_result
record_documentation_agent_result = _api_boundary(
    _record_documentation_agent_result_impl
)
_verify_documentation_run_impl = verify_documentation_run
verify_documentation_run = _api_boundary(_verify_documentation_run_impl)

_export_documentation_run_impl = export_documentation_run


@_api_boundary
def export_documentation_run(
    workspace: str | Path,
    *,
    build: bool = False,
    builder_command: Iterable[str] | None = None,
    knowledge_mode: str | None = None,
    knowledge_public_repository_identity: str | None = None,
) -> DocumentationExportResult:
    """Export a documentation workspace through the stable API boundary."""

    return cast(
        DocumentationExportResult,
        _export_documentation_run_impl(
            workspace,
            build=build,
            builder_command=builder_command,
            knowledge_mode=knowledge_mode,
            knowledge_public_repository_identity=(
                knowledge_public_repository_identity
            ),
        ),
    )


def _call_calibration_controller(
    name: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Call one isolated calibration operation after an explicit API request."""

    from .services.calibration import controller

    return getattr(controller, name)(*args, **kwargs)


@_api_boundary
def prepare_calibration_run(
    root: str | Path,
    *,
    control_workspaces: Sequence[str | Path],
    execution_manifest: Mapping[str, Any],
) -> P0CalibrationRun:
    """Freeze two matching documentation controls into a fresh cohort."""

    return _call_calibration_controller(
        "prepare_calibration_run",
        root,
        control_workspaces=control_workspaces,
        execution_manifest=execution_manifest,
    )


@_api_boundary
def admit_calibration_run(
    root: str | Path,
    *,
    authority_grant: Mapping[str, Any],
    broker_attestation: Mapping[str, Any] | None = None,
) -> P0CalibrationRun:
    """Authorize one frozen calibration cohort."""

    return _call_calibration_controller(
        "admit_calibration_run",
        root,
        authority_grant=authority_grant,
        broker_attestation=broker_attestation,
    )


@_api_boundary
def get_calibration_run_status(
    root: str | Path,
) -> P0CalibrationStatus:
    """Return verified calibration status without advancing the lifecycle."""

    return _call_calibration_controller("get_calibration_run_status", root)


@_api_boundary
def build_calibration_agent_packet(
    root: str | Path,
    *,
    role: str,
) -> P0CalibrationAgentPacket:
    """Build one bounded calibration role packet."""

    return _call_calibration_controller(
        "build_calibration_agent_packet",
        root,
        role=role,
    )


@_api_boundary
def dispatch_calibration_agent(
    root: str | Path,
    *,
    role: str,
) -> P0CalibrationDispatchReceipt:
    """Dispatch one issued calibration packet."""

    return _call_calibration_controller(
        "dispatch_calibration_agent",
        root,
        role=role,
    )


@_api_boundary
def record_calibration_agent_result(
    root: str | Path,
    *,
    dispatch_receipt: P0CalibrationDispatchReceipt | Mapping[str, Any],
    result: P0CalibrationAgentResult | Mapping[str, Any],
) -> P0CalibrationRun:
    """Import one authenticated calibration result."""

    return _call_calibration_controller(
        "record_calibration_agent_result",
        root,
        dispatch_receipt=dispatch_receipt,
        result=result,
    )


@_api_boundary
def verify_calibration_run(
    root: str | Path,
    *,
    advance: bool = True,
) -> P0CalibrationVerificationReport:
    """Recompute calibration gates and optionally advance the lifecycle."""

    return _call_calibration_controller(
        "verify_calibration_run",
        root,
        advance=advance,
    )

_select_documentation_model_impl = select_documentation_model
select_documentation_model = _api_boundary(_select_documentation_model_impl)
_validate_documentation_model_selection_impl = (
    validate_documentation_model_selection
)
validate_documentation_model_selection = _api_boundary(
    _validate_documentation_model_selection_impl
)

@contextmanager
def use_calibration_host_broker_authenticator(
    authenticator: HostBrokerAuthenticator,
) -> Iterator[None]:
    """Scope a host authenticator while preserving caller-block exceptions."""

    try:
        from .services.calibration.host_broker import (
            use_calibration_host_broker_authenticator as implementation,
        )

        manager = implementation(authenticator)
        manager.__enter__()
    except Exception as exc:
        _raise_api_error(exc)

    try:
        yield
    except BaseException as body_exc:
        try:
            suppressed = manager.__exit__(
                type(body_exc),
                body_exc,
                body_exc.__traceback__,
            )
        except BaseException as exit_exc:
            if exit_exc is body_exc:
                raise
            if isinstance(exit_exc, Exception):
                _raise_api_error(exit_exc)
            raise
        if not suppressed:
            raise
    else:
        try:
            manager.__exit__(None, None, None)
        except Exception as exc:
            _raise_api_error(exc)


setattr(
    use_calibration_host_broker_authenticator,
    "__llm_wiki_api_boundary__",
    True,
)

for _calibration_api_function in (
    prepare_calibration_run,
    admit_calibration_run,
    get_calibration_run_status,
    build_calibration_agent_packet,
    dispatch_calibration_agent,
    record_calibration_agent_result,
    verify_calibration_run,
    use_calibration_host_broker_authenticator,
):
    _defer_calibration_annotations(_calibration_api_function)
del _calibration_api_function


def _deprecated_api_alias(
    replacement: Callable[..., Any],
    *,
    legacy_name: str,
    replacement_name: str,
) -> Callable[..., Any]:
    @wraps(replacement)
    def legacy(*args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            f"{legacy_name} is deprecated; use {replacement_name} instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return replacement(*args, **kwargs)

    legacy.__name__ = legacy_name
    legacy.__qualname__ = legacy_name
    legacy.__annotations__ = replacement.__annotations__
    setattr(legacy, "__llm_wiki_api_boundary__", True)
    return legacy


prepare_p0_calibration_run = _deprecated_api_alias(
    prepare_calibration_run,
    legacy_name="prepare_p0_calibration_run",
    replacement_name="prepare_calibration_run",
)
admit_p0_calibration_run = _deprecated_api_alias(
    admit_calibration_run,
    legacy_name="admit_p0_calibration_run",
    replacement_name="admit_calibration_run",
)
get_p0_calibration_run_status = _deprecated_api_alias(
    get_calibration_run_status,
    legacy_name="get_p0_calibration_run_status",
    replacement_name="get_calibration_run_status",
)
build_p0_calibration_agent_packet = _deprecated_api_alias(
    build_calibration_agent_packet,
    legacy_name="build_p0_calibration_agent_packet",
    replacement_name="build_calibration_agent_packet",
)
dispatch_p0_calibration_agent = _deprecated_api_alias(
    dispatch_calibration_agent,
    legacy_name="dispatch_p0_calibration_agent",
    replacement_name="dispatch_calibration_agent",
)
record_p0_calibration_agent_result = _deprecated_api_alias(
    record_calibration_agent_result,
    legacy_name="record_p0_calibration_agent_result",
    replacement_name="record_calibration_agent_result",
)
verify_p0_calibration_run = _deprecated_api_alias(
    verify_calibration_run,
    legacy_name="verify_p0_calibration_run",
    replacement_name="verify_calibration_run",
)
use_p0_calibration_host_broker_authenticator = _deprecated_api_alias(
    use_calibration_host_broker_authenticator,
    legacy_name="use_p0_calibration_host_broker_authenticator",
    replacement_name="use_calibration_host_broker_authenticator",
)


__all__ = [
    "ArtifactIntegrityError",
    "BOOTSTRAP_SUMMARY_SCHEMA_VERSION",
    "BootstrapError",
    "BootstrapRequest",
    "BootstrapResult",
    "BootstrapServiceError",
    "CalleesResult",
    "CallersResult",
    "ConceptResult",
    "ConceptSectionsResult",
    "ContextBasisComparison",
    "ContextPacketError",
    "ContextPacketMalformedError",
    "ContextPacketPathPolicyError",
    "ContextPacketReconciliation",
    "ContextPacketSourceMutationError",
    "ContextPacketUnavailableError",
    "ContextPacketValidation",
    "ContextPayload",
    "DataFlowForEntrypointResult",
    "DependencyNeighborhoodResult",
    "DocumentationAgentPacket",
    "DocumentationAgentResult",
    "DocumentationExportResult",
    "DoctorResult",
    "DOCTOR_SCHEMA_VERSION",
    "EXTRACT_SCHEMA_VERSION",
    "DocumentationGraphQueryService",
    "DocumentationIntegrityError",
    "DocumentationIntakeBrief",
    "DocumentationModelEscalationRule",
    "DocumentationModelOverride",
    "DocumentationModelPolicyError",
    "DocumentationModelRoute",
    "DocumentationModelRoutingPolicy",
    "DocumentationModelRoutingRequest",
    "DocumentationModelSelection",
    "DocumentationPolicyError",
    "DOCUMENTATION_AGENT_PACKET_SCHEMA_VERSION",
    "DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION",
    "DOCUMENTATION_FINAL_REPORT_SCHEMA_VERSION",
    "DOCUMENTATION_MODEL_ROUTING_SCHEMA_VERSION",
    "DOCUMENTATION_MODEL_SELECTION_SCHEMA_VERSION",
    "DOCUMENTATION_RUN_SCHEMA_VERSION",
    "DOCUMENTATION_VERIFICATION_SCHEMA_VERSION",
    "P0_CALIBRATION_AGENT_PACKET_SCHEMA_VERSION",
    "P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION",
    "P0_CALIBRATION_DECISION_SCOPE",
    "P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION",
    "P0_CALIBRATION_RUN_SCHEMA_VERSION",
    "P0_CALIBRATION_VERIFICATION_REPORT_SCHEMA_VERSION",
    "QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION",
    "DocumentationRun",
    "DocumentationRunError",
    "DocumentationRunStatus",
    "DocumentationSchemaError",
    "DocumentationTransitionError",
    "DocumentationVerificationReport",
    "DocumentationWikiInputError",
    "DocumentationWikiSnapshot",
    "EvidenceExplanationResult",
    "ExtractionError",
    "ExtractSourceResult",
    "FlowForEntrypointResult",
    "LlmWikiApiError",
    "InvalidRequestError",
    "PathPolicyError",
    "WorkspaceStateError",
    "P0CalibrationAgentPacket",
    "P0CalibrationAgentResult",
    "P0CalibrationDispatchReceipt",
    "P0CalibrationError",
    "P0CalibrationIntegrityError",
    "P0CalibrationRecoveryError",
    "P0CalibrationRun",
    "P0CalibrationSchemaError",
    "P0CalibrationStatus",
    "P0CalibrationTransitionError",
    "P0CalibrationVerificationReport",
    "MarkdownContextResult",
    "PagesForSymbolResult",
    "QualifiedContextPacket",
    "RelatedConceptsResult",
    "TypedGraphTraversalResult",
    "WikiPage",
    "WikiPageCounts",
    "WikiPagesResult",
    "HostBrokerAuthenticationError",
    "HostBrokerAuthenticationProof",
    "HostBrokerAuthenticationUnavailable",
    "HostBrokerAuthenticator",
    "admit_calibration_run",
    "admit_p0_calibration_run",
    "adopt_documentation_wiki_snapshot",
    "build_calibration_agent_packet",
    "build_documentation_agent_packet",
    "build_p0_calibration_agent_packet",
    "build_context",
    "build_qualified_context",
    "bootstrap_wiki",
    "build_documentation_query_service",
    "callees",
    "callers",
    "compare_context_packet_basis",
    "data_flow_for_entrypoint",
    "dependency_neighborhood",
    "dispatch_calibration_agent",
    "dispatch_p0_calibration_agent",
    "doctor",
    "explain_evidence",
    "export_documentation_run",
    "extract_source",
    "flow_for_entrypoint",
    "fingerprint_documentation_wiki_input",
    "get_concept",
    "get_calibration_run_status",
    "get_documentation_run_status",
    "get_p0_calibration_run_status",
    "list_concept_sections",
    "list_wiki_pages",
    "pages_for_symbol",
    "prepare_calibration_run",
    "prepare_documentation_run",
    "prepare_p0_calibration_run",
    "record_documentation_agent_result",
    "record_calibration_agent_result",
    "record_p0_calibration_agent_result",
    "reconcile_context_packet",
    "related_concepts",
    "select_documentation_model",
    "traverse_typed_graph",
    "use_calibration_host_broker_authenticator",
    "use_p0_calibration_host_broker_authenticator",
    "validate_context_packet",
    "validate_documentation_model_selection",
    "verify_documentation_run",
    "verify_calibration_run",
    "verify_p0_calibration_run",
]
