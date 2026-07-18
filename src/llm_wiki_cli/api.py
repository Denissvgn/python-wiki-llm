"""Supported Python API for deterministic wiki and documentation workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .commands import bootstrap_cmd, context_cmd, extract_cmd
from .config import (
    DEFAULT_WIKI_DIR,
    PathValidationError,
    validate_path,
    validate_source_root,
)
from .services.contracts import (
    BOOTSTRAP_SUMMARY_SCHEMA_VERSION,
    DOCUMENTATION_AGENT_PACKET_SCHEMA_VERSION,
    DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
    DOCUMENTATION_FINAL_REPORT_SCHEMA_VERSION,
    DOCUMENTATION_MODEL_ROUTING_SCHEMA_VERSION,
    DOCUMENTATION_MODEL_SELECTION_SCHEMA_VERSION,
    DOCUMENTATION_RUN_SCHEMA_VERSION,
    DOCUMENTATION_VERIFICATION_SCHEMA_VERSION,
    EXTRACT_SCHEMA_VERSION,
)
from .services.bootstrap_service import (
    BootstrapRequest,
    BootstrapResult,
    BootstrapServiceError,
)
from .services.dependencies import analyze_dependencies
from .services.documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
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
from .services import wiki_surface
from .services.wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
    build_surface_index,
)


class LlmWikiApiError(RuntimeError):
    """Base exception raised by the supported Python API."""


class PathPolicyError(LlmWikiApiError):
    """Raised when a source path violates the configured path policy."""


class ExtractionError(LlmWikiApiError):
    """Raised when source extraction fails."""


class BootstrapError(LlmWikiApiError):
    """Raised when deterministic library bootstrap fails."""


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
    """Build a deterministic wiki through the typed service boundary.

    The library boundary always uses source-adapter behavior and therefore does
    not install or rewrite target-repository agent instructions.
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
    except BootstrapServiceError as exc:
        raise BootstrapError(str(exc)) from exc


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
) -> dict[str, Any]:
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
        raise PathPolicyError(str(exc)) from exc
    except extract_cmd.ExtractorFailureError as exc:
        raise ExtractionError(str(exc)) from exc
    except ValueError as exc:
        raise LlmWikiApiError(str(exc)) from exc
    return result.payload


def build_context(
    src_dir: str = ".",
    *,
    budget: int = 32000,
    format: str = "json",
    focus: str | list[str] = "changed",
    filters: dict | None = None,
    wiki_dir: str = DEFAULT_WIKI_DIR,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> dict[str, Any]:
    """Return a supported context payload without depending on CLI internals."""
    focus_values = _normalise_focus(focus)
    request = {
        "protocol": context_cmd.PROTOCOL_VERSION,
        "budget_tokens": budget,
        "focus": focus_values,
        "format": format,
        "filters": filters or {},
    }
    try:
        validated = context_cmd._validate_protocol_request(request)
        payload, warnings = context_cmd._build_context(
            src_dir,
            validated["budget_tokens"],
            validated["format"],
            validated["focus"],
            validated["filters"],
            emit_warnings=False,
            allow_external_src=allow_external_src,
            read_only=read_only,
            wiki_dir=wiki_dir,
        )
    except PathValidationError as exc:
        raise PathPolicyError(str(exc)) from exc
    except context_cmd.ProtocolRequestError as exc:
        if exc.field == "wiki_dir":
            raise PathPolicyError(str(exc)) from exc
        if exc.field == "src_dir":
            raise ExtractionError(str(exc)) from exc
        raise LlmWikiApiError(str(exc)) from exc

    if validated["format"] == "markdown":
        return {
            "content": context_cmd._render_markdown(payload),
            "payload": payload,
            "warnings": warnings,
        }

    result = dict(payload)
    if warnings:
        result["warnings"] = warnings
    return result


def list_wiki_pages(wiki_dir: str = DEFAULT_WIKI_DIR) -> dict[str, Any]:
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
        raise LlmWikiApiError(str(exc)) from exc
    except OSError as exc:
        raise LlmWikiApiError(str(exc)) from exc

    return {
        "wiki_dir": _display_path(wiki_root),
        "counts": _wiki_page_counts(pages),
        "pages": pages,
    }


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
        result = extract_cmd.build_extract_payload(
            str(src_root),
            deep=True,
            allow_external_src=True,
            read_only=read_only,
        )
        inventory = result.payload["inventory"]
        entrypoints = result.payload.get("entrypoints", [])
        call_edges = extract_cmd.resolve_call_edges(inventory)
        flows = [build_flow(entrypoint, call_edges) for entrypoint in entrypoints]
        surface_index = _load_or_build_surface_index(
            wiki_root,
            inventory,
            src_root=src_root,
            entrypoints=entrypoints,
        )
        return DocumentationGraphQueryService(
            inventory,
            call_edges=call_edges,
            flows=flows,
            data_flows=result.payload.get("data_flows") or [],
            dependency_analysis=analyze_dependencies(inventory, str(src_root)),
            surface_index=surface_index,
            limit=limit,
        )
    except PathValidationError as exc:
        raise PathPolicyError(str(exc)) from exc
    except extract_cmd.ExtractorFailureError as exc:
        raise ExtractionError(str(exc)) from exc
    except DocumentationQueryError as exc:
        raise LlmWikiApiError(str(exc)) from exc
    except ValueError as exc:
        raise LlmWikiApiError(str(exc)) from exc
    except OSError as exc:
        raise LlmWikiApiError(str(exc)) from exc


def flow_for_entrypoint(
    id_or_symbol: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> dict[str, Any]:
    """Return a bounded user-flow query result for an entry point."""
    return _run_query(
        lambda: _query_service(
            service,
            src_dir=src_dir,
            wiki_dir=wiki_dir,
            limit=limit,
            allow_external_src=allow_external_src,
            read_only=read_only,
        ).flow_for_entrypoint(id_or_symbol)
    )


def data_flow_for_entrypoint(
    id_or_symbol: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> dict[str, Any]:
    """Return a bounded data-flow query result for an entry point."""
    return _run_query(
        lambda: _query_service(
            service,
            src_dir=src_dir,
            wiki_dir=wiki_dir,
            limit=limit,
            allow_external_src=allow_external_src,
            read_only=read_only,
        ).data_flow_for_entrypoint(id_or_symbol)
    )


def callers(
    symbol: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> dict[str, Any]:
    """Return bounded callers for one callable symbol."""
    return _run_query(
        lambda: _query_service(
            service,
            src_dir=src_dir,
            wiki_dir=wiki_dir,
            limit=limit,
            allow_external_src=allow_external_src,
            read_only=read_only,
        ).callers(symbol)
    )


def callees(
    symbol: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> dict[str, Any]:
    """Return bounded callees for one callable symbol."""
    return _run_query(
        lambda: _query_service(
            service,
            src_dir=src_dir,
            wiki_dir=wiki_dir,
            limit=limit,
            allow_external_src=allow_external_src,
            read_only=read_only,
        ).callees(symbol)
    )


def dependency_neighborhood(
    path: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> dict[str, Any]:
    """Return bounded dependency neighbors for one source path."""
    return _run_query(
        lambda: _query_service(
            service,
            src_dir=src_dir,
            wiki_dir=wiki_dir,
            limit=limit,
            allow_external_src=allow_external_src,
            read_only=read_only,
        ).dependency_neighborhood(path)
    )


def pages_for_symbol(
    symbol: object,
    *,
    service: DocumentationGraphQueryService | None = None,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    limit: int = 20,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> dict[str, Any]:
    """Return wiki surface pages related to one symbol."""
    return _run_query(
        lambda: _query_service(
            service,
            src_dir=src_dir,
            wiki_dir=wiki_dir,
            limit=limit,
            allow_external_src=allow_external_src,
            read_only=read_only,
        ).pages_for_symbol(symbol)
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


def _wiki_page_payload(page: wiki_surface.WikiSurfacePage) -> dict[str, Any]:
    return {
        "kind": page.kind.value,
        "id": page.page_id,
        "label": page.label,
        "canonical_path": page.relative_path,
        "mcp_uri": page.mcp_uri,
        "role": page.role.value,
        "obsidian_mirror_dir": page.obsidian_mirror_dir,
    }


def _wiki_page_counts(pages: list[dict[str, Any]]) -> dict[str, Any]:
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


def _load_or_build_surface_index(
    wiki_root: Path,
    inventory: dict[str, Any],
    *,
    src_root: Path,
    entrypoints: list[dict[str, Any]],
) -> dict[str, Any]:
    index_path = wiki_root / SURFACE_INDEX_FILENAME
    if index_path.is_file():
        try:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise LlmWikiApiError(f"Invalid wiki surface index: {index_path}") from exc
        if payload.get(
            "schema_version"
        ) == WIKI_SURFACE_INDEX_SCHEMA_VERSION and isinstance(
            payload.get("pages"), list
        ):
            return payload

    return build_surface_index(
        wiki_root,
        inventory,
        src_dir=src_root,
        entry_points=entrypoints,
    )


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


def _run_query(callback) -> dict[str, Any]:
    try:
        return callback()
    except DocumentationQueryError as exc:
        raise LlmWikiApiError(str(exc)) from exc


__all__ = [
    "BOOTSTRAP_SUMMARY_SCHEMA_VERSION",
    "BootstrapError",
    "BootstrapRequest",
    "BootstrapResult",
    "BootstrapServiceError",
    "DocumentationAgentPacket",
    "DocumentationAgentResult",
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
    "DocumentationRun",
    "DocumentationRunError",
    "DocumentationRunStatus",
    "DocumentationSchemaError",
    "DocumentationTransitionError",
    "DocumentationVerificationReport",
    "DocumentationWikiInputError",
    "DocumentationWikiSnapshot",
    "ExtractionError",
    "LlmWikiApiError",
    "PathPolicyError",
    "adopt_documentation_wiki_snapshot",
    "build_documentation_agent_packet",
    "build_context",
    "bootstrap_wiki",
    "build_documentation_query_service",
    "callees",
    "callers",
    "data_flow_for_entrypoint",
    "dependency_neighborhood",
    "export_documentation_run",
    "extract_source",
    "flow_for_entrypoint",
    "fingerprint_documentation_wiki_input",
    "get_documentation_run_status",
    "list_wiki_pages",
    "pages_for_symbol",
    "prepare_documentation_run",
    "record_documentation_agent_result",
    "select_documentation_model",
    "validate_documentation_model_selection",
    "verify_documentation_run",
]
