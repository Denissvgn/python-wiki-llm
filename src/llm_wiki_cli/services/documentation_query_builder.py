"""Shared construction for supported documentation query services."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from itertools import islice
import os
from pathlib import Path
import shlex
from time import perf_counter_ns
from typing import Any

from .concept_identity import (
    ConceptIdentityError,
    validate_concept_uid,
    validate_natural_key,
)
from . import wiki_surface
from .dependencies import analyze_dependencies
from .documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
    QUERY_IDENTITY_BYTE_LIMIT,
)
from .entrypoints import build_flow
from .knowledge_consumption import KnowledgeReadView, load_knowledge_read_view
from .knowledge_verification import (
    attach_machine_verification_read_view,
    verification_summaries_for_concepts,
)
from .source_selection import (
    SourceSelectionError,
    resolve_source_selection,
    validate_persisted_source_selection_identity,
)
from .sync_manifest import SyncManifest, SyncManifestError
from .validation import require_portable_relative_path
from .wiki_surface_index import evaluate_surface_index
from .source_snapshot import build_source_snapshot, capture_source_selection_inputs

_UNSET_LIVE_SELECTION_INPUTS = object()
_UNSET_DIFF_HEADER = object()
DEFAULT_DOCUMENTATION_QUERY_LIMIT = 20
MAX_DOCUMENTATION_QUERY_LIMIT = 100
MAX_SUPPLIED_PATHS = 100
MAX_SUPPLIED_DIFF_BYTES = 1_048_576


def normalize_documentation_query_limit(value: object) -> int:
    """Return the shared bounded query limit before any source work starts."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DocumentationQueryError("limit must be a positive integer.")
    return min(value, MAX_DOCUMENTATION_QUERY_LIMIT)


def normalize_documentation_query_text(value: object, *, field: str) -> str:
    """Return one non-empty exact query coordinate."""

    if not isinstance(value, str) or not value.strip():
        raise DocumentationQueryError(f"{field} must be a non-empty string.")
    selected = value.strip()
    if len(selected.encode("utf-8")) > QUERY_IDENTITY_BYTE_LIMIT:
        raise DocumentationQueryError(
            f"{field} must not exceed {QUERY_IDENTITY_BYTE_LIMIT} UTF-8 bytes."
        )
    return selected


def normalize_concept_coordinate(value: object) -> str:
    """Validate a concept coordinate without attempting fuzzy resolution."""

    selected = normalize_documentation_query_text(
        value,
        field="locator_or_exact_route",
    )
    try:
        return wiki_surface.validate_exact_page_coordinate(selected)
    except wiki_surface.WikiSurfaceError:
        pass
    for validator in (validate_concept_uid, validate_natural_key):
        try:
            return validator(selected)
        except ConceptIdentityError:
            continue
    raise DocumentationQueryError(
        "locator_or_exact_route must be an exact canonical wiki path or "
        "llm-wiki URI, durable concept UID, or natural-key alias."
    )


def _supplied_path_values(values: object) -> list[object]:
    """Consume no more than the declared supplied-path request bound."""

    if isinstance(values, (str, bytes, Mapping)) or not isinstance(values, Iterable):
        raise DocumentationQueryError("paths must be an array of source paths.")
    try:
        requested = list(islice(iter(values), MAX_SUPPLIED_PATHS + 1))
    except Exception as exc:
        raise DocumentationQueryError(
            "paths must be an array of source paths."
        ) from exc
    if len(requested) > MAX_SUPPLIED_PATHS:
        raise DocumentationQueryError(
            f"paths must contain at most {MAX_SUPPLIED_PATHS} entries."
        )
    return requested


def _portable_supplied_path(value: object) -> str:
    """Adapt shared portable-path validation to the query error contract."""

    error = DocumentationQueryError(
        "paths must contain normalized portable relative source paths."
    )
    return require_portable_relative_path(
        value,
        text_error=error,
        relative_error=error,
        escape_error=error,
        traversal_error=error,
        separator_error=error,
        utf8_error=error,
        control_error=error,
        non_nfc_error=error,
        nonportable_error=error,
        reserved_error=error,
    )


def normalize_supplied_paths(values: object) -> tuple[str, ...]:
    """Validate, deduplicate, and deterministically order supplied source paths."""

    normalized = {
        _portable_supplied_path(value) for value in _supplied_path_values(values)
    }
    return tuple(
        sorted(
            normalized,
            key=lambda item: (item.casefold(), item),
        )
    )


def _diff_metadata_path(value: str, *, prefixed: bool) -> str | None:
    if value.startswith('"'):
        try:
            decoded = shlex.split(value, posix=True)
        except ValueError as exc:
            raise DocumentationQueryError(
                "diff contains an invalid quoted path."
            ) from exc
        if len(decoded) != 1:
            raise DocumentationQueryError("diff contains an invalid quoted path.")
        value = decoded[0]
    if value == "/dev/null":
        return None
    if prefixed:
        if not value.startswith(("a/", "b/")):
            raise DocumentationQueryError(
                "diff paths must use canonical a/ and b/ prefixes."
            )
        value = value[2:]
    return normalize_supplied_paths((value,))[0]


def supplied_paths_from_unified_diff(value: object) -> tuple[str, ...]:
    """Extract bounded exact paths from supplied unified-diff metadata only."""

    if not isinstance(value, str):
        raise DocumentationQueryError("diff must be a UTF-8 text string.")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise DocumentationQueryError("diff must be valid UTF-8 text.") from exc
    if len(encoded) > MAX_SUPPLIED_DIFF_BYTES:
        raise DocumentationQueryError(
            f"diff must be at most {MAX_SUPPLIED_DIFF_BYTES} UTF-8 bytes."
        )

    selected: set[str] = set()
    saw_diff_block = False
    in_diff_block = False
    in_hunk = False
    block_paths: tuple[str, str] | None = None
    pending_old_path: object = _UNSET_DIFF_HEADER
    for line in value.splitlines():
        if line.startswith("diff --git "):
            if pending_old_path is not _UNSET_DIFF_HEADER:
                raise DocumentationQueryError(
                    "diff contains unpaired file-header metadata."
                )
            try:
                parts = shlex.split(line[len("diff --git ") :], posix=True)
            except ValueError as exc:
                raise DocumentationQueryError(
                    "diff contains invalid diff --git metadata."
                ) from exc
            if len(parts) != 2:
                raise DocumentationQueryError(
                    "diff contains invalid diff --git metadata."
                )
            parsed_paths = tuple(
                _diff_metadata_path(raw, prefixed=True) for raw in parts
            )
            if any(path is None for path in parsed_paths):
                raise DocumentationQueryError(
                    "diff --git metadata must identify both repository paths."
                )
            block_paths = (str(parsed_paths[0]), str(parsed_paths[1]))
            selected.update(block_paths)
            saw_diff_block = True
            in_diff_block = True
            in_hunk = False
            continue
        if not in_diff_block or in_hunk:
            continue
        if line.startswith("@@"):
            if pending_old_path is not _UNSET_DIFF_HEADER:
                raise DocumentationQueryError(
                    "diff contains unpaired file-header metadata."
                )
            in_hunk = True
            continue
        if line.startswith("--- "):
            if pending_old_path is not _UNSET_DIFF_HEADER:
                raise DocumentationQueryError(
                    "diff contains unpaired file-header metadata."
                )
            pending_old_path = _diff_metadata_path(
                line[4:].split("\t", 1)[0],
                prefixed=True,
            )
            continue
        if line.startswith("+++ "):
            if pending_old_path is _UNSET_DIFF_HEADER:
                raise DocumentationQueryError(
                    "diff contains unpaired file-header metadata."
                )
            new_path = _diff_metadata_path(
                line[4:].split("\t", 1)[0],
                prefixed=True,
            )
            assert block_paths is not None
            if (
                pending_old_path is not None and pending_old_path != block_paths[0]
            ) or (new_path is not None and new_path != block_paths[1]):
                raise DocumentationQueryError(
                    "diff file headers do not match their diff --git metadata."
                )
            pending_old_path = _UNSET_DIFF_HEADER
            continue
        if pending_old_path is not _UNSET_DIFF_HEADER:
            raise DocumentationQueryError(
                "diff contains unpaired file-header metadata."
            )

    if pending_old_path is not _UNSET_DIFF_HEADER:
        raise DocumentationQueryError("diff contains unpaired file-header metadata.")
    if not saw_diff_block:
        raise DocumentationQueryError(
            "diff must contain canonical unified-diff path metadata."
        )
    return normalize_supplied_paths(selected)


def _wiki_has_persisted_read_state(wiki_root: Path) -> bool:
    """Return whether a wiki contains anything beyond empty scaffolding."""

    try:
        if not wiki_root.is_dir():
            return False
        for root, directories, files in os.walk(wiki_root, followlinks=False):
            directories[:] = [
                name for name in directories if not (Path(root) / name).is_symlink()
            ]
            if any(name not in {".gitkeep", ".llm-wiki-agent"} for name in files):
                return True
    except OSError:
        return True
    return False


def validate_live_query_source_selection(
    *,
    source_root: Path,
    wiki_root: Path,
    live_identity: Mapping[str, object] | None,
    live_selection_inputs: Mapping[str, object] | None | object = (
        _UNSET_LIVE_SELECTION_INPUTS
    ),
    operation: str,
    allow_empty_wiki: bool = False,
) -> None:
    """Require a live query profile to match the persisted wiki boundary."""

    try:
        manifest = SyncManifest.load(wiki_root)
    except FileNotFoundError as exc:
        if live_identity is None or (
            allow_empty_wiki and not _wiki_has_persisted_read_state(wiki_root)
        ):
            return
        raise DocumentationQueryError(
            f"{operation} cannot validate the active source-selection profile "
            "because the wiki has no usable sync manifest; run `llm-wiki sync` "
            "with the same --src-dir, --wiki-dir, and --source-selection first"
        ) from exc
    except SyncManifestError as exc:
        raise DocumentationQueryError(
            f"{operation} cannot validate the active source-selection profile "
            "because the wiki sync manifest is invalid; restore it or run "
            "`llm-wiki sync` with the same active profile before querying"
        ) from exc
    except (OSError, TypeError, UnicodeError, ValueError) as exc:
        raise DocumentationQueryError(
            f"{operation} cannot validate the active source-selection profile "
            "because the wiki sync manifest is invalid; restore it or run "
            "`llm-wiki sync` with the same active profile before querying"
        ) from exc

    try:
        if live_selection_inputs is _UNSET_LIVE_SELECTION_INPUTS:
            validate_persisted_source_selection_identity(
                manifest.generation_inputs,
                live_identity,
                operation=operation,
            )
        else:
            validate_persisted_source_selection_identity(
                manifest.generation_inputs,
                live_identity,
                operation=operation,
                live_selection_inputs=live_selection_inputs,
            )
    except SourceSelectionError as exc:
        raise DocumentationQueryError(str(exc)) from exc


def _live_source_selection_identity(
    source_root: Path,
    source_selection: str | Path | None,
    inventory_result: object,
) -> Mapping[str, object] | None:
    source_snapshot = getattr(inventory_result, "source_snapshot", None)
    snapshot_identity = getattr(
        source_snapshot,
        "source_selection_identity",
        None,
    )
    if snapshot_identity is not None:
        return snapshot_identity
    policy = resolve_source_selection(source_root, source_selection)
    return policy.identity if policy is not None else None


def assemble_documentation_query_service(
    *,
    inventory: Mapping[str, Mapping[str, Any]],
    call_edges: Iterable[Mapping[str, Any]],
    flows: Iterable[Mapping[str, Any]],
    data_flows: object,
    dependency_analysis: Mapping[str, Any] | None,
    surface_index: Mapping[str, Any] | None,
    limit: int,
    knowledge_view: object,
    machine_verification: Mapping[str, Mapping[str, Any]],
    service_factory: Any = DocumentationGraphQueryService,
) -> DocumentationGraphQueryService:
    """Assemble the shared service with a caller-supplied service factory."""

    return service_factory(
        inventory,
        call_edges=call_edges,
        flows=flows,
        data_flows=data_flows,
        dependency_analysis=dependency_analysis,
        surface_index=surface_index,
        limit=limit,
        knowledge_view=knowledge_view,
        machine_verification=machine_verification,
    )


def build_documentation_query_service_from_view(
    *,
    wiki_root: Path,
    knowledge_view: KnowledgeReadView,
    limit: int,
    inventory: Mapping[str, Mapping[str, Any]] | None = None,
    call_edges: Iterable[Mapping[str, Any]] = (),
    flows: Iterable[Mapping[str, Any]] = (),
    data_flows: object = (),
    dependency_analysis: Mapping[str, Any] | None = None,
    surface_index: Mapping[str, Any] | None = None,
) -> DocumentationGraphQueryService:
    """Assemble one service around an already evaluated native read view."""

    evaluated_view = attach_machine_verification_read_view(
        wiki_root,
        knowledge_view,
    )
    return assemble_documentation_query_service(
        inventory=inventory or {},
        call_edges=call_edges,
        flows=flows,
        data_flows=data_flows,
        dependency_analysis=dependency_analysis,
        surface_index=surface_index,
        limit=limit,
        knowledge_view=evaluated_view,
        machine_verification=verification_summaries_for_concepts(evaluated_view),
    )


def build_snapshot_documentation_query_service(
    *,
    wiki_root: Path,
    limit: int,
) -> DocumentationGraphQueryService:
    """Build a snapshot-only service without source extraction."""

    view = load_knowledge_read_view(
        wiki_root,
        snapshot_only=True,
        include_machine_verification=True,
    )
    return build_documentation_query_service_from_view(
        wiki_root=wiki_root,
        knowledge_view=view,
        limit=limit,
        surface_index=view.surface,
    )


def build_live_documentation_query_service(
    *,
    source_root: Path,
    wiki_root: Path,
    limit: int,
    read_only: bool,
    helper_cache_dir: Path | None = None,
    include_plugins: bool = True,
    source_plugins_only: bool = False,
    require_live_freshness: bool = False,
    source_selection: str | Path | None = None,
    paths: Iterable[str] | None = None,
    extract_payload_builder: Callable[..., Any] | None = None,
    source_snapshot_builder: Callable[..., Any] | None = None,
    call_edge_resolver: Callable[[Any], Any] | None = None,
    flow_builder: Callable[[Any, Any], Any] = build_flow,
    surface_evaluator: Callable[..., Any] = evaluate_surface_index,
    knowledge_view_builder: Callable[..., Any] | None = None,
    query_surface_builder: Callable[..., Any] | None = None,
    dependency_analyzer: Callable[..., Any] = analyze_dependencies,
    verification_view_attacher: Callable[..., Any] = (
        attach_machine_verification_read_view
    ),
    verification_summarizer: Callable[..., Any] = (verification_summaries_for_concepts),
    snapshot_view_loader: Callable[..., Any] = load_knowledge_read_view,
    metrics_observer: Callable[[Mapping[str, Any]], None] | None = None,
    service_factory: Any = DocumentationGraphQueryService,
) -> DocumentationGraphQueryService:
    """Build a live service using one operation-scoped extraction."""

    # Keep heavyweight extraction/context modules out of this builder's import
    # path until a live query service is requested.
    from . import context_service, extraction_service

    selected_extract_builder = (
        extract_payload_builder or extraction_service.build_extract_payload
    )
    selected_snapshot_builder = source_snapshot_builder or build_source_snapshot
    selected_call_edge_resolver = (
        call_edge_resolver or extraction_service.resolve_call_edges
    )
    selected_paths = None if paths is None else normalize_supplied_paths(paths)
    if selected_paths is not None and require_live_freshness:
        raise DocumentationQueryError(
            "targeted extraction cannot establish full live freshness; use a "
            "full-inventory query or consume the attributed snapshot status"
        )
    selected_view_builder = knowledge_view_builder or (
        context_service._build_context_knowledge_view
    )
    selected_query_surface_builder = (
        query_surface_builder or context_service._context_query_surface
    )
    stage_ns: dict[str, int] = {}
    stage_started = perf_counter_ns()
    try:
        selection_policy = resolve_source_selection(source_root, source_selection)
    except SourceSelectionError as exc:
        raise DocumentationQueryError(str(exc)) from exc
    selection_inputs = capture_source_selection_inputs(
        source_root,
        source_selection=source_selection,
        selection_policy=selection_policy,
    )
    validate_live_query_source_selection(
        source_root=source_root,
        wiki_root=wiki_root,
        live_identity=(
            selection_policy.identity if selection_policy is not None else None
        ),
        live_selection_inputs=selection_inputs,
        operation="live documentation query",
    )
    stage_ns["source_selection"] = perf_counter_ns() - stage_started
    snapshot_options: dict[str, Any] = {
        "source_selection": source_selection,
        "selection_policy": selection_policy,
        "expected_selection_inputs": selection_inputs,
    }
    if selected_paths is not None:
        snapshot_options["only_files"] = selected_paths
    stage_started = perf_counter_ns()
    source_snapshot = selected_snapshot_builder(source_root, **snapshot_options)
    stage_ns["source_snapshot"] = perf_counter_ns() - stage_started
    extract_options: dict[str, Any] = {
        "deep": True,
        "allow_external_src": True,
        "read_only": read_only,
    }
    if source_selection is not None:
        extract_options["source_selection"] = source_selection
    if selected_paths is not None:
        extract_options["paths"] = list(selected_paths)
    if helper_cache_dir is not None:
        extract_options["helper_cache_dir"] = str(helper_cache_dir)
    if not include_plugins:
        extract_options["include_plugins"] = False
    if source_plugins_only:
        extract_options["source_plugins_only"] = True
    extract_options["source_snapshot"] = source_snapshot
    stage_started = perf_counter_ns()
    result = selected_extract_builder(str(source_root), **extract_options)
    stage_ns["extraction"] = perf_counter_ns() - stage_started
    inventory = result.payload["inventory"]
    entrypoints = result.payload.get("entrypoints", [])
    stage_started = perf_counter_ns()
    call_edges = selected_call_edge_resolver(inventory)
    flows = [flow_builder(entrypoint, call_edges) for entrypoint in entrypoints]
    stage_ns["graph_construction"] = perf_counter_ns() - stage_started
    inventory_result = getattr(result, "inventory_result", None)
    try:
        live_identity = _live_source_selection_identity(
            source_root,
            source_selection,
            inventory_result,
        )
    except SourceSelectionError as exc:
        raise DocumentationQueryError(str(exc)) from exc
    validate_live_query_source_selection(
        source_root=source_root,
        wiki_root=wiki_root,
        live_identity=live_identity,
        live_selection_inputs=getattr(
            getattr(inventory_result, "source_snapshot", None),
            "source_selection_inputs",
            None,
        ),
        operation="live documentation query",
    )
    stage_started = perf_counter_ns()
    if selected_paths is None:
        surface_evaluation = surface_evaluator(
            wiki_root,
            inventory,
            src_dir=source_root,
            entry_points=entrypoints,
        )
        knowledge_view = selected_view_builder(
            wiki_root,
            surface_evaluation,
            inventory,
            inventory_result,
        )
        if require_live_freshness and (
            not isinstance(knowledge_view, KnowledgeReadView)
            or not knowledge_view.ready
            or not knowledge_view.freshness_evaluated
        ):
            raise DocumentationQueryError(
                "verified-current claim reconciliation requires a live native "
                "freshness evaluation"
            )
        query_surface_payload = surface_evaluation.payload
    else:
        # A partial inventory is never a sound basis for global freshness or
        # surface-completeness claims.  Keep targeted source extraction useful,
        # but pair it only with the independently validated committed snapshot.
        knowledge_view = snapshot_view_loader(
            wiki_root,
            snapshot_only=True,
            include_machine_verification=True,
        )
        query_surface_payload = (
            knowledge_view.surface
            if isinstance(knowledge_view, KnowledgeReadView)
            else None
        )
    if isinstance(knowledge_view, KnowledgeReadView):
        knowledge_view = verification_view_attacher(
            wiki_root,
            knowledge_view,
        )
        machine_verification = verification_summarizer(knowledge_view)
    else:
        # Preserve the API's test-double adapter contract.
        machine_verification = {}
    if selected_paths is None:
        if not isinstance(query_surface_payload, Mapping):
            raise DocumentationQueryError(
                "live surface evaluation must return a mapping payload"
            )
        query_surface = selected_query_surface_builder(
            query_surface_payload,
            knowledge_view,
        )
    else:
        query_surface = query_surface_payload
    stage_ns["knowledge_surface"] = perf_counter_ns() - stage_started
    stage_started = perf_counter_ns()
    source_snapshot = (
        inventory_result.source_snapshot if inventory_result is not None else None
    )
    dependency_analysis = getattr(result, "dependency_analysis", None)
    if dependency_analysis is None:
        dependency_analysis = dependency_analyzer(
            inventory,
            str(source_root),
            source_snapshot=source_snapshot,
        )
    service = assemble_documentation_query_service(
        inventory=inventory,
        call_edges=call_edges,
        flows=flows,
        data_flows=result.payload.get("data_flows") or [],
        dependency_analysis=dependency_analysis,
        surface_index=query_surface,
        limit=limit,
        knowledge_view=knowledge_view,
        machine_verification=machine_verification,
        service_factory=service_factory,
    )
    stage_ns["service_assembly"] = perf_counter_ns() - stage_started
    if metrics_observer is not None:
        metrics_observer(
            {
                "stages_ns": dict(stage_ns),
                "counts": {
                    "requested_paths": (
                        0 if selected_paths is None else len(selected_paths)
                    ),
                    "captured_files": len(
                        getattr(source_snapshot, "captured_content_hashes", {})
                    ),
                    "inventory_files": len(inventory),
                    "entrypoints": len(entrypoints),
                    "call_edges": len(call_edges),
                    "flows": len(flows),
                },
            }
        )
    return service


__all__ = [
    "assemble_documentation_query_service",
    "DEFAULT_DOCUMENTATION_QUERY_LIMIT",
    "MAX_DOCUMENTATION_QUERY_LIMIT",
    "MAX_SUPPLIED_DIFF_BYTES",
    "MAX_SUPPLIED_PATHS",
    "build_documentation_query_service_from_view",
    "build_live_documentation_query_service",
    "build_snapshot_documentation_query_service",
    "normalize_concept_coordinate",
    "normalize_documentation_query_limit",
    "normalize_documentation_query_text",
    "normalize_supplied_paths",
    "supplied_paths_from_unified_diff",
    "validate_live_query_source_selection",
]
