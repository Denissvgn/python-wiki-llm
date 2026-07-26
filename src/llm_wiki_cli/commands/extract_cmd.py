from __future__ import annotations

import hashlib
import importlib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterable

from ..config import (
    EXTRACTOR_REGISTRY,
    PathValidationError,
    validate_source_paths,
    validate_source_root,
)
from ..extractors.common import (
    LANGUAGE_EXTENSIONS,
    inventory_language_for_path,
    normalize_include_tests,
)
from ..extractors.go_extractor import GoExtractionRequest
from ..extractors.haskell_extractor import HaskellExtractionRequest

# Re-export ComponentVisitor so existing callers that import it from here
# continue to work without modification.
from ..extractors.python_extractor import ComponentVisitor  # noqa: F401
from ..extractors.rust_extractor import RustExtractionRequest
from ..services.api_contracts import (
    attach_routes_to_entry_points,
    build_api_contracts,
)
from ..services.contracts import EXTRACT_SCHEMA_VERSION
from ..services.data_flow import analyze_data_flow, build_data_flow_context
from ..services.dependencies import analyze_dependencies
from ..services.entrypoints import build_flow, detect_entry_points, read_console_scripts
from ..services.entrypoints import get_entry_points as get_entry_points  # noqa: F401
from ..services.extraction_jobs import ExtractionJobPlan, ExtractionJobRequest
from ..services.imports import build_module_path_resolver
from ..services.inventory_cache import (
    InventoryCache,
    InventoryCacheOptions,
    InventoryCacheStats,
    build_inventory_cache_key,
    is_valid_cache_entry,
    make_cache_entry,
)
from ..services.io import write_text_output
from ..services.packages import discover_packages, stamp_inventory_packages
from ..services.plugins import (
    get_extractor_registry,
    iter_components,
    load_entry_point,
    lock_path,
    parallel_safe_extractor_entry_points,
)
from ..services.resource_diagnostics import format_resource_failure
from ..services.source_snapshot import (
    SourceFile,
    SourceSnapshot,
    SourceSnapshotError,
    build_source_snapshot,
    format_unsupported_source_summary,
    unsupported_source_summary,
)

# ── Extractor loader ─────────────────────────────────────────────────


def _instantiate_extractor(entry_point: str):
    """Instantiate an extractor without using the shared instance cache."""
    module_path, class_name = entry_point.rsplit(":", 1)
    if entry_point not in EXTRACTOR_REGISTRY.values():
        return load_entry_point(entry_point)()
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()


@lru_cache(maxsize=None)
def _load_extractor(entry_point: str):
    """Instantiate an extractor from a ``"module.path:ClassName"`` string."""
    return _instantiate_extractor(entry_point)


@dataclass(frozen=True)
class ExtractorStatus:
    language: str
    state: str  # ok | skipped | failed
    files_found: int
    message: str = ""


@dataclass(frozen=True)
class InventoryRequest:
    src_dir: str | Path
    deep: bool = False
    only_files: list[str] | None = None
    include_empty: bool = False
    source_snapshot: SourceSnapshot | None = None
    cache_options: InventoryCacheOptions | None = None
    parallel_jobs: int = 1
    helper_cache_dir: str | None = None
    include_tests: Iterable[str] | None = None
    job_request: ExtractionJobRequest | None = None
    plan_reporter: Callable[[ExtractionJobPlan], None] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "include_tests", normalize_include_tests(self.include_tests)
        )


@dataclass(frozen=True)
class InventoryResult:
    inventory: dict
    statuses: dict[str, ExtractorStatus]
    cache_stats: InventoryCacheStats | None = None
    extraction_job_plan: ExtractionJobPlan = field(default_factory=ExtractionJobPlan)
    extractor_registry: dict[str, str] = field(default_factory=dict)
    plugin_components: tuple[dict, ...] = ()
    producer_plugin_components: tuple[dict, ...] = ()
    plugin_lock_path: str | None = None
    plugin_lock_hash: str | None = None
    source_snapshot: SourceSnapshot | None = None

    @property
    def job_plan(self) -> ExtractionJobPlan:
        return self.extraction_job_plan

    @property
    def failed(self) -> list[ExtractorStatus]:
        return [s for s in self.statuses.values() if s.state == "failed"]


@dataclass(frozen=True)
class ExtractPayloadResult:
    payload: dict
    inventory_count: int
    docker_count: int
    changed_file_count: int | None = None
    no_changed_files: bool = False
    inventory_result: InventoryResult | None = field(
        default=None,
        repr=False,
        compare=False,
        kw_only=True,
    )
    dependency_analysis: dict | None = field(
        default=None,
        repr=False,
        compare=False,
        kw_only=True,
    )


class ExtractorFailureError(RuntimeError):
    """Raised when one or more extractors fail during payload construction."""

    def __init__(self, result: InventoryResult):
        self.result = result
        super().__init__(_extractor_failure_message(result))


def _extractor_failure_message(result: InventoryResult) -> str:
    details = []
    for status in result.failed:
        detail = f": {status.message}" if status.message else ""
        details.append(f"{status.language} extraction failed{detail}")
    return "; ".join(details) or "Source extraction failed."


def print_inventory_failures(result: InventoryResult, *, file=None) -> None:
    """Print extractor failures in a consistent form."""
    stream = file or sys.stderr
    for status in result.failed:
        detail = f": {status.message}" if status.message else ""
        print(f"Error: {status.language} extraction failed{detail}", file=stream)


@dataclass(frozen=True)
class _ExtractionPlan:
    language: str
    entry_point: str
    is_builtin: bool
    parallel_safe: bool
    source_files: list[str] | None
    fresh_source_files: list[str]
    files_found: int
    kwargs: dict


@dataclass(frozen=True)
class _ExtractionOutcome:
    language: str
    state: str
    files_found: int
    extracted: dict
    message: str = ""


@dataclass
class _InventoryBuildContext:
    request: InventoryRequest
    source_snapshot: SourceSnapshot
    registry: dict[str, str]
    parallel_jobs: int
    cache: InventoryCache | None
    cache_key: dict | None
    cache_files: dict[str, dict]
    updated_cache_files: dict[str, dict]
    source_file_by_path: dict[str, SourceFile]
    source_hashes: dict[str, str]
    parallel_safe_plugin_entry_points: set[str]
    plugin_components: tuple[dict, ...]
    plugin_lock_path: str | None
    plugin_lock_hash: str | None


@dataclass
class _InventoryPlanningResult:
    plans: list[_ExtractionPlan]
    status_by_language: dict[str, ExtractorStatus]
    cached_by_language: dict[str, dict]


def _run_extraction_plan(
    plan: _ExtractionPlan, *, fresh_instance: bool = False
) -> _ExtractionOutcome:
    try:
        extractor = (
            _instantiate_extractor(plan.entry_point)
            if fresh_instance
            else _load_extractor(plan.entry_point)
        )
    except Exception as exc:
        return _ExtractionOutcome(
            plan.language,
            "failed",
            plan.files_found,
            {},
            format_resource_failure(exc),
        )
    if hasattr(extractor, "last_error"):
        extractor.last_error = None
    try:
        extracted = extractor.extract(**plan.kwargs)
    except Exception as exc:
        return _ExtractionOutcome(
            plan.language,
            "failed",
            plan.files_found,
            {},
            format_resource_failure(exc),
        )

    error = getattr(extractor, "last_error", None)
    if error:
        message = (
            format_resource_failure(error)
            if isinstance(error, BaseException)
            else str(error)
        )
        return _ExtractionOutcome(
            plan.language, "failed", plan.files_found, {}, message
        )

    files_found = plan.files_found
    if plan.source_files is None:
        files_found = len(extracted)
    return _ExtractionOutcome(plan.language, "ok", files_found, extracted)


def _merge_language_inventory(
    target: dict, source_order: list[str], *sources: dict
) -> None:
    seen: set[str] = set()
    for rel_path in source_order:
        for source in sources:
            if rel_path in source:
                target[rel_path] = source[rel_path]
                seen.add(rel_path)
                break
    for source in sources:
        for rel_path in sorted(source):
            if rel_path not in seen:
                target[rel_path] = source[rel_path]
                seen.add(rel_path)


# ── Backward-compatible public API ───────────────────────────────────


_MISSING_INVENTORY_REQUEST = object()
_LEGACY_INVENTORY_REQUEST_FIELDS = (
    "deep",
    "only_files",
    "include_empty",
    "source_snapshot",
    "cache_options",
    "parallel_jobs",
    "helper_cache_dir",
    "include_tests",
    "job_request",
    "plan_reporter",
)


def _coerce_inventory_request(
    request,
    legacy_args: tuple,
    legacy_kwargs: dict,
) -> InventoryRequest:
    if request is _MISSING_INVENTORY_REQUEST:
        if "src_dir" not in legacy_kwargs:
            raise TypeError(
                "get_inventory_result() missing required argument: 'src_dir'"
            )
        request = legacy_kwargs.pop("src_dir")

    if isinstance(request, InventoryRequest):
        if legacy_args or legacy_kwargs:
            raise TypeError("InventoryRequest cannot be combined with legacy options.")
        return request

    if len(legacy_args) > len(_LEGACY_INVENTORY_REQUEST_FIELDS):
        raise TypeError(
            "get_inventory_result() takes at most "
            f"{len(_LEGACY_INVENTORY_REQUEST_FIELDS) + 1} positional arguments "
            f"({len(legacy_args) + 1} given)"
        )

    values = dict(zip(_LEGACY_INVENTORY_REQUEST_FIELDS, legacy_args))
    duplicates = sorted(set(values) & set(legacy_kwargs))
    if duplicates:
        raise TypeError(
            f"get_inventory_result() got multiple values for argument '{duplicates[0]}'"
        )

    unexpected = sorted(set(legacy_kwargs) - set(_LEGACY_INVENTORY_REQUEST_FIELDS))
    if unexpected:
        raise TypeError(
            f"get_inventory_result() got an unexpected keyword argument '{unexpected[0]}'"
        )

    values.update(legacy_kwargs)
    return InventoryRequest(src_dir=request, **values)


def get_inventory_result(
    request=_MISSING_INVENTORY_REQUEST,
    *legacy_args,
    **legacy_kwargs,
) -> InventoryResult:
    """Scan source files across all registered languages and return inventory.

    Runs every built-in and installed extractor and merges the
    results into a single dict keyed by file path.

    If deep=True, returns enriched data (docstrings, attributes, methods, imports).
    If deep=False, returns the slim format for backward compatibility.
    If only_files is given, restrict to those relative paths.
    If include_empty=True, include all .py files even without extractable components.

    Each entry is stamped with a ``"package"`` key (package name or
    ``None``) derived from ``pyproject.toml`` / ``setup.py`` markers.
    """
    return _build_inventory_result(
        _coerce_inventory_request(request, legacy_args, legacy_kwargs)
    )


def _build_inventory_result(request: InventoryRequest) -> InventoryResult:
    context = _prepare_inventory_build_context(request)
    planning = _plan_inventory_extractions(context)
    extraction_job_plan = _build_extraction_job_plan(context, planning)
    if request.plan_reporter is not None:
        request.plan_reporter(extraction_job_plan)
    outcomes_by_language = _run_inventory_plans(planning.plans, context.parallel_jobs)
    extracted_by_language = _collect_inventory_outcomes(
        context, planning, outcomes_by_language
    )
    inventory = _merge_inventory_results(
        context, planning.cached_by_language, extracted_by_language
    )
    statuses = _ordered_inventory_statuses(
        context.registry, planning.status_by_language
    )
    (
        selected_plugin_components,
        producer_plugin_components,
        evaluated_source_snapshot,
    ) = _inventory_plugin_state(
        context,
        statuses,
        inventory,
    )
    _save_inventory_cache(context, statuses)
    return InventoryResult(
        inventory=inventory,
        statuses=statuses,
        cache_stats=context.cache.stats if context.cache is not None else None,
        extraction_job_plan=extraction_job_plan,
        extractor_registry=dict(context.registry),
        plugin_components=selected_plugin_components,
        producer_plugin_components=producer_plugin_components,
        plugin_lock_path=(
            context.plugin_lock_path if producer_plugin_components else None
        ),
        plugin_lock_hash=(
            context.plugin_lock_hash if producer_plugin_components else None
        ),
        source_snapshot=evaluated_source_snapshot,
    )


def _inventory_plugin_state(
    context: _InventoryBuildContext,
    statuses: dict[str, ExtractorStatus],
    inventory: dict,
) -> tuple[tuple[dict, ...], tuple[dict, ...], SourceSnapshot]:
    extractors = _selected_extractor_plugin_components(context, statuses)
    producers = extractors + tuple(
        component
        for component in context.plugin_components
        if component.get("type") in {"diagram_style", "entrypoint_detector"}
    )
    return (
        extractors,
        producers,
        _snapshot_with_plugin_inventory_paths(
            context.source_snapshot,
            inventory,
            extractors,
        ),
    )


def _selected_extractor_plugin_components(
    context: _InventoryBuildContext,
    statuses: dict[str, ExtractorStatus],
) -> tuple[dict, ...]:
    return tuple(
        component
        for component in context.plugin_components
        if component.get("type") == "extractor"
        and isinstance(component.get("language"), str)
        and (status := statuses.get(component["language"])) is not None
        and status.state == "ok"
        and context.registry.get(component["language"]) == component.get("entry_point")
    )


def _snapshot_with_plugin_inventory_paths(
    snapshot: SourceSnapshot,
    inventory: dict,
    components: tuple[dict, ...],
) -> SourceSnapshot:
    if not components:
        return snapshot
    plugin_languages = {str(component["language"]) for component in components}
    try:
        return snapshot.with_captured_inventory_paths(
            source_path
            for source_path, file_data in inventory.items()
            if str(file_data.get("language", "")) in plugin_languages
        )
    except SourceSnapshotError:
        # Extract remains backward compatible with virtual plugin records.
        # Knowledge generation will reject any uncommitted source path.
        return snapshot


def _build_extraction_job_plan(
    context: _InventoryBuildContext,
    planning: _InventoryPlanningResult,
) -> ExtractionJobPlan:
    parallel_plan_ids = tuple(
        sorted(plan.language for plan in planning.plans if plan.parallel_safe)
    )
    sequential_plan_ids = tuple(
        sorted(plan.language for plan in planning.plans if not plan.parallel_safe)
    )
    planned_ids = set(parallel_plan_ids) | set(sequential_plan_ids)
    cache_elided_plan_ids = tuple(
        sorted(
            language
            for language, status in planning.status_by_language.items()
            if status.state == "ok" and language not in planned_ids
        )
    )
    if not planning.plans:
        effective_workers = 0
    elif parallel_plan_ids:
        effective_workers = min(context.parallel_jobs, len(parallel_plan_ids))
    else:
        effective_workers = 1
    job_request = context.request.job_request or ExtractionJobRequest.resolved(
        context.parallel_jobs
    )
    return ExtractionJobPlan(
        requested_jobs=job_request.requested_jobs,
        resolved_jobs=context.parallel_jobs,
        eligible_parallel_plans=len(parallel_plan_ids),
        effective_workers=effective_workers,
        parallel_plan_ids=parallel_plan_ids,
        sequential_plan_ids=sequential_plan_ids,
        cache_elided_plan_ids=cache_elided_plan_ids,
    )


def _prepare_inventory_build_context(
    request: InventoryRequest,
) -> _InventoryBuildContext:
    source_snapshot = request.source_snapshot or build_source_snapshot(
        request.src_dir,
        only_files=request.only_files,
        include_tests=request.include_tests,
    )
    registry = get_extractor_registry()
    plugin_components, plugin_root = _selected_runtime_plugin_components(
        request.src_dir
    )
    plugin_lock_path, plugin_lock_hash = _captured_plugin_lock(
        request.src_dir,
        plugin_root=plugin_root,
    )
    cache = (
        InventoryCache(request.src_dir, request.cache_options)
        if request.cache_options is not None
        else None
    )
    source_file_by_path = _source_files_by_path(source_snapshot)
    cache_key, cache_files, source_hashes = _load_inventory_cache_state(
        request, source_snapshot, registry, cache, source_file_by_path
    )
    return _InventoryBuildContext(
        request=request,
        source_snapshot=source_snapshot,
        registry=registry,
        parallel_jobs=max(1, int(request.parallel_jobs or 1)),
        cache=cache,
        cache_key=cache_key,
        cache_files=cache_files,
        updated_cache_files={},
        source_file_by_path=source_file_by_path,
        source_hashes=source_hashes,
        parallel_safe_plugin_entry_points=parallel_safe_extractor_entry_points(),
        plugin_components=plugin_components,
        plugin_lock_path=plugin_lock_path,
        plugin_lock_hash=plugin_lock_hash,
    )


def _captured_plugin_lock(
    source_root: str | Path,
    *,
    plugin_root: str | Path = ".",
) -> tuple[str | None, str | None]:
    """Capture the exact applicable project-local plugin lock without leaking it."""

    path = lock_path(plugin_root)
    if not path.is_file():
        return None, None
    try:
        content = path.read_bytes()
        relative_path = (
            path.resolve().relative_to(Path(source_root).resolve()).as_posix()
        )
    except (OSError, ValueError):
        return None, None
    return (
        relative_path,
        f"sha256:{hashlib.sha256(content).hexdigest()}",
    )


def _selected_runtime_plugin_components(
    source_root: str | Path,
) -> tuple[tuple[dict, ...], str | Path]:
    """Mirror source-root-first documentation-hook selection without loading it."""

    ambient = tuple(iter_components())
    source = (
        ambient
        if Path(source_root).resolve() == Path.cwd().resolve()
        else tuple(iter_components(root=source_root))
    )
    extractors = tuple(
        component for component in ambient if component.get("type") == "extractor"
    )
    generation: list[dict] = []
    source_selected = False
    for component_type in ("diagram_style", "entrypoint_detector"):
        primary = [
            component for component in source if component.get("type") == component_type
        ]
        fallback = [
            component
            for component in ambient
            if component.get("type") == component_type
        ]
        selected = primary or fallback
        generation.extend(selected)
        source_selected = source_selected or bool(primary)
    return extractors + tuple(generation), (source_root if source_selected else ".")


def _source_files_by_path(source_snapshot: SourceSnapshot) -> dict[str, SourceFile]:
    return {
        source_file.rel_path: source_file
        for source_files in source_snapshot.files_by_language.values()
        for source_file in source_files
    }


def _load_inventory_cache_state(
    request: InventoryRequest,
    source_snapshot: SourceSnapshot,
    registry: dict[str, str],
    cache: InventoryCache | None,
    source_file_by_path: dict[str, SourceFile],
) -> tuple[dict | None, dict[str, dict], dict[str, str]]:
    if cache is None or not cache.enabled or request.only_files is not None:
        return None, {}, {}

    cache_key = build_inventory_cache_key(
        request.src_dir,
        source_snapshot,
        deep=request.deep,
        include_empty=request.include_empty,
        extractor_registry=registry,
    )
    cache_files = cache.load(cache_key)
    cache.stats.deleted = len(set(cache_files) - set(source_file_by_path))
    source_hashes = source_snapshot.hashes_for(source_file_by_path)
    return cache_key, cache_files, source_hashes


def _plan_inventory_extractions(
    context: _InventoryBuildContext,
) -> _InventoryPlanningResult:
    status_by_language: dict[str, ExtractorStatus] = {}
    cached_by_language: dict[str, dict] = {}
    plans: list[_ExtractionPlan] = []

    for language, entry_point in context.registry.items():
        plan = _plan_language_extraction(
            context, language, entry_point, status_by_language, cached_by_language
        )
        if plan is not None:
            plans.append(plan)

    return _InventoryPlanningResult(plans, status_by_language, cached_by_language)


def _plan_language_extraction(
    context: _InventoryBuildContext,
    language: str,
    entry_point: str,
    status_by_language: dict[str, ExtractorStatus],
    cached_by_language: dict[str, dict],
) -> _ExtractionPlan | None:
    extensions = LANGUAGE_EXTENSIONS.get(language)
    source_files = (
        context.source_snapshot.language_paths(language)
        if extensions is not None
        else None
    )
    if extensions is not None and not source_files:
        status_by_language[language] = ExtractorStatus(language, "skipped", 0)
        return None

    files_found = len(source_files or [])
    if extensions is None and context.request.only_files:
        files_found = len(context.request.only_files)

    is_builtin = extensions is not None and entry_point == EXTRACTOR_REGISTRY.get(
        language
    )
    cached_by_language.setdefault(language, {})
    fresh_source_files = (
        _fresh_inventory_source_files(
            context, language, source_files, cached_by_language
        )
        if _can_use_inventory_cache(context, is_builtin)
        else list(source_files or [])
    )
    if _can_use_inventory_cache(context, is_builtin) and not fresh_source_files:
        status_by_language[language] = ExtractorStatus(language, "ok", files_found)
        return None

    return _ExtractionPlan(
        language=language,
        entry_point=entry_point,
        is_builtin=is_builtin,
        parallel_safe=(
            is_builtin or entry_point in context.parallel_safe_plugin_entry_points
        ),
        source_files=source_files,
        fresh_source_files=fresh_source_files,
        files_found=files_found,
        kwargs=_build_extraction_kwargs(
            context, language, is_builtin, fresh_source_files
        ),
    )


def _can_use_inventory_cache(context: _InventoryBuildContext, is_builtin: bool) -> bool:
    return (
        is_builtin
        and context.cache is not None
        and context.cache.enabled
        and context.cache_key is not None
    )


def _fresh_inventory_source_files(
    context: _InventoryBuildContext,
    language: str,
    source_files: list[str] | None,
    cached_by_language: dict[str, dict],
) -> list[str]:
    fresh_source_files: list[str] = []
    cache = context.cache
    if cache is None:
        return list(source_files or [])

    for rel_path in source_files or []:
        source_file = context.source_file_by_path[rel_path]
        file_hash = context.source_hashes.get(rel_path)
        cached_entry = context.cache_files.get(rel_path)
        if file_hash is None or cached_entry is None:
            cache.stats.misses += 1
            fresh_source_files.append(rel_path)
            continue
        if is_valid_cache_entry(cached_entry, source_file, file_hash):
            cache.stats.hits += 1
            _record_cached_inventory_entry(
                context, cached_by_language, language, rel_path, cached_entry
            )
            continue
        _record_stale_cache_entry(cache, cached_entry, file_hash)
        fresh_source_files.append(rel_path)

    return fresh_source_files


def _record_cached_inventory_entry(
    context: _InventoryBuildContext,
    cached_by_language: dict[str, dict],
    language: str,
    rel_path: str,
    cached_entry: dict,
) -> None:
    raw_inventory = cached_entry.get("inventory", {})
    if raw_inventory:
        cached_by_language[language][rel_path] = deepcopy(raw_inventory)
    context.updated_cache_files[rel_path] = cached_entry


def _record_stale_cache_entry(
    cache: InventoryCache, cached_entry: dict, file_hash: str
) -> None:
    cached_hash = cached_entry.get("hash") if isinstance(cached_entry, dict) else None
    if cached_hash != file_hash:
        cache.stats.changed += 1
    else:
        cache.stats.stale += 1


def _build_extraction_kwargs(
    context: _InventoryBuildContext,
    language: str,
    is_builtin: bool,
    fresh_source_files: list[str],
) -> dict:
    kwargs = {
        "src_dir": context.request.src_dir,
        "only_files": context.request.only_files,
        "deep": context.request.deep,
    }
    if is_builtin:
        kwargs = _build_builtin_extraction_kwargs(context, language, fresh_source_files)
    if language == "python":
        kwargs["include_empty"] = context.request.include_empty
    return kwargs


def _build_builtin_extraction_kwargs(
    context: _InventoryBuildContext, language: str, fresh_source_files: list[str]
) -> dict:
    src_dir = str(context.request.src_dir)
    if language == "go":
        return {
            "src_dir": GoExtractionRequest(
                src_dir=src_dir,
                only_files=context.request.only_files,
                deep=context.request.deep,
                source_files=fresh_source_files,
                helper_cache_dir=_inventory_helper_cache_dir(context.request),
                include_tests=context.request.include_tests,
            ),
        }
    if language == "rust":
        return {
            "src_dir": RustExtractionRequest(
                src_dir=src_dir,
                only_files=context.request.only_files,
                deep=context.request.deep,
                source_files=fresh_source_files,
                helper_cache_dir=_inventory_helper_cache_dir(context.request),
            ),
        }
    if language == "haskell":
        return {
            "src_dir": HaskellExtractionRequest(
                src_dir=src_dir,
                only_files=context.request.only_files,
                deep=context.request.deep,
                source_files=fresh_source_files,
                helper_cache_dir=_inventory_helper_cache_dir(context.request),
            ),
        }
    return {
        "src_dir": src_dir,
        "only_files": context.request.only_files,
        "deep": context.request.deep,
        "source_files": fresh_source_files,
    }


def _inventory_helper_cache_dir(request: InventoryRequest) -> str | None:
    return request.helper_cache_dir


def _run_inventory_plans(
    plans: list[_ExtractionPlan], parallel_jobs: int
) -> dict[str, _ExtractionOutcome]:
    parallel_safe_plans = [plan for plan in plans if plan.parallel_safe]
    sequential_plans = [plan for plan in plans if not plan.parallel_safe]
    outcomes_by_language: dict[str, _ExtractionOutcome] = {}

    _run_parallel_safe_inventory_plans(
        parallel_safe_plans, parallel_jobs, outcomes_by_language
    )
    for plan in sequential_plans:
        outcome = _run_extraction_plan(plan, fresh_instance=False)
        outcomes_by_language[outcome.language] = outcome
    return outcomes_by_language


def _run_parallel_safe_inventory_plans(
    parallel_safe_plans: list[_ExtractionPlan],
    parallel_jobs: int,
    outcomes_by_language: dict[str, _ExtractionOutcome],
) -> None:
    if parallel_jobs > 1 and len(parallel_safe_plans) > 1:
        max_workers = min(parallel_jobs, len(parallel_safe_plans))
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for outcome in executor.map(
                    lambda plan: _run_extraction_plan(plan, fresh_instance=True),
                    parallel_safe_plans,
                ):
                    outcomes_by_language[outcome.language] = outcome
        except (MemoryError, OSError, RuntimeError) as exc:
            message = format_resource_failure(exc, executor_start=True)
            for plan in parallel_safe_plans:
                outcomes_by_language[plan.language] = _ExtractionOutcome(
                    plan.language,
                    "failed",
                    plan.files_found,
                    {},
                    message,
                )
        return

    use_fresh_instances = parallel_jobs > 1
    for plan in parallel_safe_plans:
        outcome = _run_extraction_plan(plan, fresh_instance=use_fresh_instances)
        outcomes_by_language[outcome.language] = outcome


def _collect_inventory_outcomes(
    context: _InventoryBuildContext,
    planning: _InventoryPlanningResult,
    outcomes_by_language: dict[str, _ExtractionOutcome],
) -> dict[str, dict]:
    extracted_by_language: dict[str, dict] = {}
    for plan in planning.plans:
        outcome = outcomes_by_language[plan.language]
        if outcome.state == "failed":
            planning.status_by_language[plan.language] = ExtractorStatus(
                plan.language, "failed", outcome.files_found, outcome.message
            )
            continue
        extracted_by_language[plan.language] = outcome.extracted
        _update_inventory_cache_entries(context, plan, outcome.extracted)
        planning.status_by_language[plan.language] = ExtractorStatus(
            plan.language, "ok", outcome.files_found
        )
    return extracted_by_language


def _update_inventory_cache_entries(
    context: _InventoryBuildContext, plan: _ExtractionPlan, extracted: dict
) -> None:
    if not _can_use_inventory_cache(context, plan.is_builtin):
        return
    cache = context.cache
    if cache is None:
        return
    cache.stats.fresh_extracted += len(plan.fresh_source_files)
    for rel_path in plan.fresh_source_files:
        source_file = context.source_file_by_path[rel_path]
        file_hash = context.source_hashes.get(rel_path)
        if file_hash is None:
            continue
        raw_entry = deepcopy(extracted.get(rel_path, {}))
        if raw_entry:
            raw_entry.pop("package", None)
        context.updated_cache_files[rel_path] = make_cache_entry(
            source_file, file_hash, raw_entry
        )


def _merge_inventory_results(
    context: _InventoryBuildContext,
    cached_by_language: dict[str, dict],
    extracted_by_language: dict[str, dict],
) -> dict:
    inventory: dict = {}
    for language in context.registry:
        _merge_language_inventory(
            inventory,
            context.source_snapshot.language_paths(language),
            cached_by_language.get(language, {}),
            extracted_by_language.get(language, {}),
        )
    packages = discover_packages(
        str(context.request.src_dir), source_snapshot=context.source_snapshot
    )
    stamp_inventory_packages(inventory, packages)
    return inventory


def _ordered_inventory_statuses(
    registry: dict[str, str], status_by_language: dict[str, ExtractorStatus]
) -> dict[str, ExtractorStatus]:
    return {
        language: status_by_language[language]
        for language in registry
        if language in status_by_language
    }


def _save_inventory_cache(
    context: _InventoryBuildContext, statuses: dict[str, ExtractorStatus]
) -> None:
    cache = context.cache
    if cache is None or not cache.enabled:
        return

    cache.finalize_lookup_status()
    if context.cache_key is None or any(
        status.state == "failed" for status in statuses.values()
    ):
        return
    if _should_save_inventory_cache(cache):
        cache.save(context.cache_key, context.updated_cache_files)


def _should_save_inventory_cache(cache: InventoryCache) -> bool:
    return (
        cache.options.rebuild
        or bool(cache.stats.misses)
        or bool(cache.stats.changed)
        or bool(cache.stats.stale)
        or bool(cache.stats.deleted)
        or bool(cache.stats.fresh_extracted)
    )


def get_inventory(src_dir, deep=False, only_files=None, include_empty=False):
    """Backward-compatible inventory API returning only the inventory dict."""
    return get_inventory_result(
        InventoryRequest(
            src_dir=src_dir,
            deep=deep,
            only_files=only_files,
            include_empty=include_empty,
        )
    ).inventory


def ensure_complete_inventory(result: InventoryResult) -> bool:
    """Return True when all extractors that had matching source files succeeded."""
    return not result.failed


def infer_language_from_path(filepath: str) -> str | None:
    suffix = Path(filepath).suffix
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if suffix in extensions:
            return inventory_language_for_path(language, filepath)
    return None


def languages_with_source(
    src_dir: str, only_files: list[str] | None = None
) -> set[str]:
    snapshot = build_source_snapshot(src_dir, only_files=only_files)
    return {
        language
        for language, source_files in snapshot.files_by_language.items()
        if source_files
    }


def _inventory_or_exit(
    src_dir: str,
    *,
    deep: bool = False,
    only_files=None,
    include_empty: bool = False,
) -> dict:
    result = get_inventory_result(
        InventoryRequest(
            src_dir=src_dir,
            deep=deep,
            only_files=only_files,
            include_empty=include_empty,
        )
    )
    if result.failed:
        print_inventory_failures(result)
        sys.exit(1)
    return result.inventory


def _git_changed_files(src_dir: str) -> list[str] | None:
    """Return list of files changed in the last commit, relative to *src_dir*.

    Returns None if git is unavailable or there are no commits.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1..HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
            cwd=src_dir,
        )
        return [line for line in result.stdout.splitlines() if line.strip()]
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return None


def _compact_summary_names(items: Iterable, key: str | None = None) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = item
        if isinstance(item, dict):
            value = item.get(key or "name")
        if not value:
            continue
        name = str(value)
        if name in seen:
            continue
        names.append(name)
        seen.add(name)
    return names


def _summarize_inventory(inventory: dict) -> dict:
    """Produce a compact one-line-per-symbol summary from a shallow inventory."""
    summary: dict[str, dict] = {}
    for fp, data in inventory.items():
        entry: dict[str, list] = {}
        if data.get("language"):
            entry["language"] = data["language"]
        if data.get("package"):
            entry["package"] = data["package"]
        cls_names = [c["name"] for c in data.get("classes", [])]
        fn_names = [f["name"] for f in data.get("functions", [])]
        if cls_names:
            entry["classes"] = cls_names
        if fn_names:
            entry["functions"] = fn_names
        if data.get("language") in {"javascript", "typescript"}:
            imports = _compact_summary_names(data.get("imports", []), "module")
            exports = _compact_summary_names(data.get("exports", []))
            constants = _compact_summary_names(data.get("constants", []), "name")
            module_calls = _compact_summary_names(data.get("module_calls", []), "name")
            if imports:
                entry["imports"] = imports
            if exports:
                entry["exports"] = exports
            if constants:
                entry["constants"] = constants
            if module_calls:
                entry["module_calls"] = module_calls
        if entry:
            summary[fp] = entry
    return summary


def _dependency_extract_block(analysis: dict) -> dict:
    """Project dependency analysis into the public ``extract --deep`` shape."""
    graph = analysis.get("graph", {})
    load_order = analysis.get("load_order", {})
    reconciliation = analysis.get("reconciliation", {})
    languages = reconciliation.get("languages", {})
    external: dict[str, dict] = {}
    for language, report in sorted(languages.items()):
        entry = {
            "used": {
                package: list(files)
                for package, files in sorted(report.get("used", {}).items())
            },
            "undeclared": list(report.get("undeclared", [])),
            "unused": list(report.get("unused", [])),
        }
        versions = report.get("versions", {})
        if versions:
            entry["versions"] = {
                package: dict(metadata)
                for package, metadata in sorted(versions.items())
                if isinstance(metadata, dict)
            }
        external[language] = entry
    return {
        "edges": [list(edge) for edge in graph.get("edges", [])],
        "cycles": [list(cycle) for cycle in analysis.get("cycles", [])],
        "external": external,
        "load_order": {
            "order": list(load_order.get("order", [])),
            "cycle_groups": [
                list(group) for group in load_order.get("cycle_groups", [])
            ],
        },
    }


def build_extract_payload(
    src_dir: str = ".",
    *,
    changed: bool = False,
    summary: bool = False,
    deep: bool = False,
    paths: list[str] | None = None,
    package_filter: str | None = None,
    include_empty: bool = False,
    helper_cache_dir: str | None = None,
    include_tests: Iterable[str] | None = None,
    openapi_file: str | Path | None = None,
    allow_external_src: bool = False,
    read_only: bool = False,
) -> ExtractPayloadResult:
    """Build the stable extract JSON payload without printing or exiting."""
    src_root = validate_source_root(
        src_dir,
        "--src-dir",
        allow_external=allow_external_src,
    )
    if openapi_file is not None and not deep:
        raise ValueError("--openapi-file requires --deep.")
    if paths:
        validate_source_paths(src_root, paths, "--paths")

    if changed and paths:
        raise ValueError("--changed and --paths are mutually exclusive.")

    only_files = None
    changed_file_count: int | None = None
    no_changed_files = False

    if changed:
        only_files = _git_changed_files(str(src_root))
        if only_files is not None:
            changed_file_count = len(only_files)
        if only_files == []:
            no_changed_files = True
    elif paths:
        only_files = paths

    if no_changed_files:
        empty_output = {"schema_version": EXTRACT_SCHEMA_VERSION, "inventory": {}}
        dependency_analysis = None
        if deep:
            source_snapshot = build_source_snapshot(
                str(src_root),
                only_files=(),
                include_tests=normalize_include_tests(include_tests),
            )
            dependency_analysis = analyze_dependencies(
                {},
                str(src_root),
                source_snapshot=source_snapshot,
            )
            empty_output["api_contracts"] = build_api_contracts(
                {}, openapi_file=openapi_file, source_root=src_root
            )
            empty_output["dependencies"] = _dependency_extract_block(
                dependency_analysis
            )
            empty_output["data_flows"] = []
        return ExtractPayloadResult(
            empty_output,
            inventory_count=0,
            docker_count=0,
            changed_file_count=0,
            no_changed_files=True,
            dependency_analysis=dependency_analysis,
        )

    include_test_languages = normalize_include_tests(include_tests)
    source_snapshot = build_source_snapshot(
        str(src_root),
        only_files=only_files,
        include_tests=include_test_languages,
    )
    result = get_inventory_result(
        InventoryRequest(
            src_dir=str(src_root),
            deep=deep,
            only_files=only_files,
            include_empty=include_empty,
            source_snapshot=source_snapshot,
            helper_cache_dir=helper_cache_dir,
            include_tests=include_test_languages,
        )
    )
    if result.failed:
        raise ExtractorFailureError(result)
    inventory = result.inventory

    if package_filter:
        inventory = {
            fp: data
            for fp, data in inventory.items()
            if data.get("package") == package_filter
        }
        if not inventory:
            raise ValueError(f"No files found for package '{package_filter}'.")

    api_contracts = (
        build_api_contracts(
            inventory,
            openapi_file=openapi_file,
            source_root=src_root,
        )
        if deep
        else None
    )

    # Entry points need the deep fields (decorators, __all__, __main__); detect
    # before any summary collapse.
    entrypoint_warnings: list[str] = []
    if deep:
        entrypoint_result = detect_entry_points(
            inventory,
            console_scripts=read_console_scripts(str(src_root)),
            root=str(src_root),
            fallback_root=Path.cwd(),
        )
        entrypoints = entrypoint_result.entries
        entrypoints = attach_routes_to_entry_points(entrypoints, api_contracts or {})
        entrypoint_warnings = entrypoint_result.warnings
    else:
        entrypoints = []
    call_edges = resolve_call_edges(inventory) if deep and entrypoints else []
    data_flow_context = (
        build_data_flow_context(inventory, call_edges) if deep and entrypoints else None
    )
    data_flows = (
        [
            analyze_data_flow(
                inventory,
                build_flow(entrypoint, call_edges),
                call_edges,
                context=data_flow_context,
            )
            for entrypoint in entrypoints
        ]
        if deep
        else None
    )
    dependency_analysis = (
        analyze_dependencies(
            inventory,
            str(src_root),
            source_snapshot=source_snapshot,
        )
        if deep
        else None
    )
    dependencies = (
        _dependency_extract_block(dependency_analysis)
        if dependency_analysis is not None
        else None
    )

    if summary:
        inventory = _summarize_inventory(inventory)

    docker_inv = get_docker_inventory(str(src_root), source_snapshot=source_snapshot)

    output: dict = {
        "schema_version": EXTRACT_SCHEMA_VERSION,
        "inventory": inventory,
    }
    if docker_inv:
        output["docker"] = docker_inv
    unsupported_sources = unsupported_source_summary(
        source_snapshot, supported_languages=result.statuses
    )
    if unsupported_sources:
        output["unsupported_sources"] = unsupported_sources
    if entrypoints:
        output["entrypoints"] = entrypoints
    if data_flows is not None:
        output["data_flows"] = data_flows
    if dependencies is not None:
        output["dependencies"] = dependencies
    if api_contracts is not None:
        output["api_contracts"] = api_contracts
    if entrypoint_warnings:
        output["warnings"] = entrypoint_warnings

    return ExtractPayloadResult(
        output,
        inventory_count=len(inventory),
        docker_count=len(docker_inv),
        changed_file_count=changed_file_count,
        no_changed_files=False,
        inventory_result=result,
        dependency_analysis=dependency_analysis,
    )


def run(args):
    src_dir: str = getattr(args, "src_dir", ".")
    changed: bool = getattr(args, "changed", False)
    summary: bool = getattr(args, "summary", False)
    deep: bool = getattr(args, "deep", False)
    paths: list[str] | None = getattr(args, "paths", None)
    package_filter: str | None = getattr(args, "package", None)
    include_empty: bool = getattr(args, "include_empty", False)
    output_path: str | None = getattr(args, "output", None)
    read_only: bool = getattr(args, "read_only", False)
    allow_external_src: bool = getattr(args, "allow_external_src", False)
    helper_cache_dir: str | None = getattr(args, "helper_cache_dir", None)
    include_tests = getattr(args, "include_tests", None)
    openapi_file: str | None = getattr(args, "openapi_file", None)

    if changed and paths:
        print("Error: --changed and --paths are mutually exclusive.", file=sys.stderr)
        sys.exit(2)

    if changed:
        print("Extracting changed file(s)...", file=sys.stderr)
    elif paths:
        print(f"Extracting {len(paths)} specified path(s)...", file=sys.stderr)
    else:
        print(f"Extracting inventory from {src_dir}...", file=sys.stderr)

    try:
        result = build_extract_payload(
            src_dir,
            changed=changed,
            summary=summary,
            deep=deep,
            paths=paths,
            package_filter=package_filter,
            include_empty=include_empty,
            helper_cache_dir=helper_cache_dir,
            include_tests=include_tests,
            openapi_file=openapi_file,
            allow_external_src=allow_external_src,
            read_only=read_only,
        )
    except ExtractorFailureError as exc:
        print_inventory_failures(exc.result)
        sys.exit(1)
    except PathValidationError:
        raise
    except ValueError as exc:
        message = str(exc)
        if message.startswith("No files found for package"):
            print(message, file=sys.stderr)
            sys.exit(1)
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(2)

    if changed:
        if result.no_changed_files:
            print("No files changed in the last commit.", file=sys.stderr)
            if not output_path:
                return
        elif result.changed_file_count is None:
            print(
                "Warning: Could not get changed files from git. Falling back to full scan.",
                file=sys.stderr,
            )
        else:
            print(
                f"Extracting {result.changed_file_count} changed file(s)...",
                file=sys.stderr,
            )

    rendered = json.dumps(result.payload, indent=2)
    if output_path:
        write_text_output(output_path, rendered + "\n")
        print(f"Extract output written to: {output_path}", file=sys.stderr)
    else:
        print(rendered)

    for warning in result.payload.get("warnings", []):
        print(f"Warning: {warning}", file=sys.stderr)

    unsupported_message = format_unsupported_source_summary(
        result.payload.get("unsupported_sources", {})
    )
    if unsupported_message:
        print(unsupported_message, file=sys.stderr)

    print(
        f"Extracted {result.inventory_count} files with tracked inventory.",
        file=sys.stderr,
    )
    if result.docker_count:
        print(f"Docker inventory: {result.docker_count} file(s).", file=sys.stderr)
    else:
        print("No Docker/Compose files found.", file=sys.stderr)


# ── Call-graph extraction for workflow detection ──────────────────────


def _module_name(filepath: str) -> str:
    return Path(filepath).stem


_TEST_FILE_STEMS = {"conftest"}
_TEST_DIRS = {"tests", "test", "__tests__"}
_WORKFLOW_MODULE_THRESHOLD = 3


def _build_symbol_file_index(inventory: dict) -> dict[str, set[str]]:
    symbol_to_files: dict[str, set[str]] = {}
    for filepath, data in inventory.items():
        for cls in data.get("classes", []):
            symbol_to_files.setdefault(cls["name"], set()).add(filepath)
        for fn in data.get("functions", []):
            symbol_to_files.setdefault(fn["name"], set()).add(filepath)
    return symbol_to_files


def _is_test_file(filepath: str) -> bool:
    fp_path = Path(filepath)
    if fp_path.stem.startswith("test_") or fp_path.stem in _TEST_FILE_STEMS:
        return True
    return bool(_TEST_DIRS & set(fp_path.parts))


def _resolve_import_candidates(
    imp: dict,
    filepath: str,
    symbol_to_files: dict[str, set[str]],
    module_resolver,
) -> set[str]:
    source_name = imp.get("name", "") or ""
    candidates = set(symbol_to_files.get(source_name, set()))
    module_candidates = module_resolver.candidates(imp.get("module", ""), filepath)

    if candidates and module_candidates:
        candidates &= module_candidates
    elif not candidates and module_candidates:
        candidates = set(module_candidates)

    candidates.discard(filepath)
    return candidates


def _resolve_imported_symbols(
    filepath: str,
    imports: list[dict],
    symbol_to_files: dict[str, set[str]],
    module_resolver,
) -> dict[str, tuple[str, str]]:
    imported_symbols: dict[str, tuple[str, str]] = {}
    for imp in imports:
        source_name = imp.get("name", "") or ""
        visible_name = imp.get("alias") or source_name
        if not visible_name:
            continue
        candidates = _resolve_import_candidates(
            imp, filepath, symbol_to_files, module_resolver
        )
        if len(candidates) == 1:
            imported_symbols[visible_name] = (next(iter(candidates)), source_name)
    return imported_symbols


def _iter_callable_components(data: dict):
    yield from data.get("functions", [])
    for cls in data.get("classes", []):
        yield from cls.get("methods", [])


def _function_references_symbol(fn: dict, visible_name: str) -> bool:
    referenced = False
    for param in fn.get("params", []):
        if visible_name in param.get("type", ""):
            referenced = True
    if visible_name in fn.get("return_type", ""):
        referenced = True
    for decorator in fn.get("decorators", []):
        if visible_name in decorator:
            referenced = True
    if visible_name in fn.get("docstring", ""):
        referenced = True
    return referenced


def _referenced_import_chain(
    fn: dict,
    imported_symbols: dict[str, tuple[str, str]],
) -> tuple[set[str], list[str]]:
    touched_module_paths: set[str] = set()
    chain: list[str] = []
    for visible_name, (src_path, source_name) in imported_symbols.items():
        if _function_references_symbol(fn, visible_name):
            touched_module_paths.add(src_path)
            chain.append(f"{_module_name(src_path)}.{source_name}")
    return touched_module_paths, chain


def _workflow_name(fn_name: str, module_name: str) -> str:
    workflow_name = fn_name.lstrip("_")
    if workflow_name == "run":
        return f"{module_name}_flow"
    return workflow_name


def _workflow_entry(
    filepath: str,
    module_name: str,
    fn: dict,
    touched_module_paths: set[str],
    chain: list[str],
) -> tuple[str, dict]:
    fn_name = fn["name"]
    all_touched_paths = touched_module_paths | {filepath}
    return _workflow_name(fn_name, module_name), {
        "entry": f"{module_name}.{fn_name}",
        "entry_module": module_name,
        "entry_module_path": filepath,
        "chain": chain,
        "modules_touched": sorted({_module_name(path) for path in all_touched_paths}),
        "modules_touched_paths": sorted(all_touched_paths),
        "docstring": fn.get("docstring", ""),
    }


def _workflow_entries_for_file(
    filepath: str,
    data: dict,
    imported_symbols: dict[str, tuple[str, str]],
) -> dict[str, dict]:
    module_name = _module_name(filepath)
    workflows: dict[str, dict] = {}
    for fn in _iter_callable_components(data):
        touched_module_paths, chain = _referenced_import_chain(fn, imported_symbols)
        if len(touched_module_paths) >= _WORKFLOW_MODULE_THRESHOLD:
            workflow_name, workflow = _workflow_entry(
                filepath,
                module_name,
                fn,
                touched_module_paths,
                chain,
            )
            workflows[workflow_name] = workflow
    return workflows


def get_call_graph(inventory: dict) -> dict:
    """Build cross-module call chains from a deep inventory.

    Detects functions that import and reference symbols from 3+ other
    project-internal modules — these are workflow candidates.

    Returns a dict of workflow_name -> {entry, chain, modules_touched}.
    """
    symbol_to_files = _build_symbol_file_index(inventory)
    module_resolver = build_module_path_resolver(inventory)
    workflows: dict[str, dict] = {}

    for filepath, data in inventory.items():
        if _is_test_file(filepath):
            continue
        imported_symbols = _resolve_imported_symbols(
            filepath,
            data.get("imports", []),
            symbol_to_files,
            module_resolver,
        )
        if imported_symbols:
            workflows.update(
                _workflow_entries_for_file(filepath, data, imported_symbols)
            )

    return workflows


# ── Call-edge resolution for flow detection ───────────────────────────


def _file_local_symbols(data: dict) -> set[str]:
    """Names of functions and classes defined in a single file entry."""
    names = {fn["name"] for fn in data.get("functions", [])}
    names |= {cls["name"] for cls in data.get("classes", [])}
    return names


def _caller_components(data: dict):
    """Yield ``(caller_symbol, fn, class_name)`` for every callable in a file.

    ``caller_symbol`` is the bare name for module-level functions and
    ``Class.method`` for methods; ``class_name`` is ``None`` for functions.
    """
    if data.get("main_block_calls"):
        yield "__main__", {"calls": data["main_block_calls"]}, None
    for fn in data.get("functions", []):
        yield fn["name"], fn, None
    for cls in data.get("classes", []):
        for method in cls.get("methods", []):
            yield f"{cls['name']}.{method['name']}", method, cls["name"]
    for fn in data.get("nested_functions", []):
        yield fn["name"], fn, None


def _attr_root(attr: str) -> str:
    return attr.split(".", 1)[0] if attr else ""


def _self_method_target(
    call: dict, class_name: str | None, data: dict, filepath: str
) -> tuple[str, str] | None:
    """Resolve a ``self.x`` / ``cls.x`` call to a method of the same class."""
    if class_name is None or _attr_root(call.get("attr", "")) not in ("self", "cls"):
        return None
    for cls in data.get("classes", []):
        if cls["name"] != class_name:
            continue
        for method in cls.get("methods", []):
            if method["name"] == call["name"]:
                return filepath, f"{class_name}.{call['name']}"
    return None


def _call_uses_import(name: str, attr: str, imported_names: set[str]) -> bool:
    return name in imported_names or _attr_root(attr) in imported_names


def _resolve_call(
    call: dict,
    filepath: str,
    class_name: str | None,
    data: dict,
    imported_internal: dict[str, tuple[str, str]],
    imported_names: set[str],
    local_symbols: set[str],
    symbol_to_files: dict[str, set[str]],
) -> tuple[str | None, str, str]:
    """Return ``(to_file, to_symbol, kind)`` for a single call record."""
    name = call["name"]
    attr = call.get("attr", "")

    target = _self_method_target(call, class_name, data, filepath)
    if target is not None:
        return target[0], target[1], "internal"
    if not attr and name in imported_internal:
        to_file, source_name = imported_internal[name]
        return to_file, source_name, "internal"
    if not attr and name in local_symbols:
        return filepath, name, "internal"
    if not attr:
        candidates = symbol_to_files.get(name, set())
        if len(candidates) == 1:
            return next(iter(candidates)), name, "internal"
    if _call_uses_import(name, attr, imported_names):
        return None, name, "external"
    return None, name, "unresolved"


def _edges_for_file(
    filepath: str,
    data: dict,
    symbol_to_files: dict[str, set[str]],
    module_resolver,
) -> list[dict]:
    """Resolve the call edges that originate in a single file entry."""
    imports = data.get("imports", [])
    imported_internal = _resolve_imported_symbols(
        filepath, imports, symbol_to_files, module_resolver
    )
    imported_names = {
        visible_name
        for imp in imports
        if (visible_name := (imp.get("alias") or imp.get("name")))
    }
    local_symbols = _file_local_symbols(data)

    edges: list[dict] = []
    for caller_symbol, fn, class_name in _caller_components(data):
        for call in fn.get("calls", []):
            to_file, to_symbol, kind = _resolve_call(
                call,
                filepath,
                class_name,
                data,
                imported_internal,
                imported_names,
                local_symbols,
                symbol_to_files,
            )
            edge = {
                "from": {"file": filepath, "symbol": caller_symbol},
                "to": {"file": to_file, "symbol": to_symbol},
                "name": call.get("attr") or call["name"],
                "kind": kind,
                "line": call.get("line", 0),
            }
            for key in ("args", "kwargs"):
                if key in call:
                    edge[key] = call[key]
            edges.append(edge)
    return edges


def resolve_call_edges(inventory: dict) -> list[dict]:
    """Resolve captured ``calls`` records into caller→callee edges.

    Reuses the symbol index and module resolver used for workflow detection.
    Each edge is ``{"from", "to", "name", "kind", "line"}`` where ``kind`` is:

    - ``"internal"`` — resolved to a project ``(file, symbol)``;
    - ``"external"`` — the callee comes from an imported (likely third-party or
      stdlib) name that is not a project symbol;
    - ``"unresolved"`` — could not be tied to a known symbol.

    External and unresolved calls are kept (``to.file`` is ``None``), never
    dropped, so downstream flow assembly can still show boundary crossings.
    """
    symbol_to_files = _build_symbol_file_index(inventory)
    module_resolver = build_module_path_resolver(inventory)
    edges: list[dict] = []
    for filepath, data in inventory.items():
        edges.extend(_edges_for_file(filepath, data, symbol_to_files, module_resolver))
    return edges


# ── Docker / Compose extraction ──────────────────────────────────────

_DOCKERFILE_ENV_PATTERN = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')
_DOCKERFILE_VOLUME_LIST_PATTERN = re.compile(r'"([^"]+)"')
_DOCKERFILE_LABEL_PATTERN = re.compile(r'(\S+)=("(?:[^"\\]|\\.)*"|\S+)')


def _parse_dockerfile(text: str) -> dict:
    """Parse a Dockerfile into a structured dict (line-based, no external deps)."""
    stages: list[dict] = []
    ports: list[str] = []
    env_vars: list[dict] = []
    volumes: list[str] = []
    copies: list[dict] = []
    build_args: list[dict] = []
    labels: dict[str, str] = {}
    entrypoint: str = ""
    cmd: str = ""
    workdir: str = ""
    healthcheck: str = ""

    # Join continuation lines (trailing backslash)
    logical_lines: list[str] = []
    buf = ""
    for raw in text.splitlines():
        stripped = raw.rstrip()
        if stripped.endswith("\\"):
            buf += stripped[:-1] + " "
        else:
            buf += stripped
            logical_lines.append(buf)
            buf = ""
    if buf:
        logical_lines.append(buf)

    for line in logical_lines:
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue

        upper = trimmed.split()[0].upper() if trimmed.split() else ""

        if upper == "FROM":
            parts = trimmed.split()
            image = parts[1] if len(parts) >= 2 else "unknown"
            alias = ""
            if len(parts) >= 4 and parts[2].upper() == "AS":
                alias = parts[3]
            stage = {"image": image, "alias": alias}
            stages.append(stage)

        elif upper == "EXPOSE":
            for token in trimmed.split()[1:]:
                ports.append(token)

        elif upper == "ENV":
            rest = trimmed[4:].strip()
            if "=" in rest:
                for pair in _DOCKERFILE_ENV_PATTERN.findall(rest):
                    env_vars.append({"name": pair[0], "default": pair[1].strip('"')})
            else:
                parts = rest.split(None, 1)
                if len(parts) == 2:
                    env_vars.append({"name": parts[0], "default": parts[1]})
                elif parts:
                    env_vars.append({"name": parts[0], "default": ""})

        elif upper == "VOLUME":
            rest = trimmed[7:].strip()
            if rest.startswith("["):
                for v in _DOCKERFILE_VOLUME_LIST_PATTERN.findall(rest):
                    volumes.append(v)
            else:
                volumes.extend(rest.split())

        elif upper in ("COPY", "ADD"):
            parts = trimmed.split()
            flags = [p for p in parts[1:] if p.startswith("--")]
            non_flag = [p for p in parts[1:] if not p.startswith("--")]
            src = " ".join(non_flag[:-1]) if len(non_flag) >= 2 else ""
            dest = non_flag[-1] if non_flag else ""
            from_stage = ""
            for f in flags:
                if f.startswith("--from="):
                    from_stage = f.split("=", 1)[1]
            copies.append(
                {
                    "src": src,
                    "dest": dest,
                    "from_stage": from_stage,
                    "instruction": upper,
                }
            )

        elif upper == "WORKDIR":
            workdir = trimmed.split(None, 1)[1] if len(trimmed.split()) > 1 else ""

        elif upper == "ARG":
            rest = trimmed[4:].strip()
            if "=" in rest:
                name, default = rest.split("=", 1)
                build_args.append({"name": name.strip(), "default": default.strip()})
            else:
                build_args.append({"name": rest, "default": ""})

        elif upper == "LABEL":
            for pair in _DOCKERFILE_LABEL_PATTERN.findall(trimmed[6:]):
                labels[pair[0]] = pair[1].strip('"')

        elif upper == "ENTRYPOINT":
            entrypoint = trimmed.split(None, 1)[1] if len(trimmed.split()) > 1 else ""

        elif upper == "CMD":
            cmd = trimmed.split(None, 1)[1] if len(trimmed.split()) > 1 else ""

        elif upper == "HEALTHCHECK":
            rest = trimmed.split(None, 1)[1] if len(trimmed.split()) > 1 else ""
            if rest.upper() != "NONE":
                healthcheck = rest

    return {
        "type": "dockerfile",
        "stages": stages,
        "ports": ports,
        "env_vars": env_vars,
        "volumes": volumes,
        "copies": copies,
        "build_args": build_args,
        "labels": labels,
        "entrypoint": entrypoint,
        "cmd": cmd,
        "workdir": workdir,
        "healthcheck": healthcheck,
    }


def _parse_inline_yaml_list(value: str) -> list[str] | None:
    """Parse an inline YAML list like ``["CMD", "curl", "-f", "http://..."]``.

    Returns a list of strings if the value is an inline list, otherwise None.
    """
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1]
        items: list[str] = []
        for item in re.split(r",\s*", inner):
            item = item.strip().strip('"').strip("'")
            if item:
                items.append(item)
        return items
    return None


@dataclass
class _ComposeParserState:
    services: dict[str, dict] = field(default_factory=dict)
    networks: list[str] = field(default_factory=list)
    named_volumes: list[str] = field(default_factory=list)
    current_top: str = ""
    current_service: str = ""
    key_stack: list[str] = field(default_factory=list)


def _strip_yaml_quotes(value: str) -> str:
    """Remove surrounding YAML quotes from a value."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def _compose_path_parent(
    state: _ComposeParserState,
    path: list[str],
    *,
    create: bool = False,
):
    """Return ``(parent_dict, final_key)`` for a nested service path."""
    if not state.current_service or not path:
        return None, None

    target = state.services[state.current_service]
    for part in path[:-1]:
        if part not in target:
            if create:
                target[part] = {}
            else:
                return None, None

        child = target[part]
        if isinstance(child, list) and not child:
            target[part] = {}
            child = target[part]
        if not isinstance(child, dict):
            return None, None
        target = child

    return target, path[-1]


def _start_compose_top_level_section(
    state: _ComposeParserState,
    stripped: str,
    indent: int,
) -> bool:
    if indent != 0 or ":" not in stripped:
        return False
    state.current_top = stripped.split(":", 1)[0].strip()
    state.current_service = ""
    state.key_stack = []
    return True


def _start_compose_service(
    state: _ComposeParserState,
    stripped: str,
    indent: int,
) -> bool:
    if indent != 2 or ":" not in stripped or stripped.startswith("-"):
        return False
    state.current_service = stripped.split(":", 1)[0].strip()
    state.services.setdefault(state.current_service, {})
    state.key_stack = []
    return True


def _compose_service_depth(indent: int) -> int:
    return (indent - 4) // 2


def _append_compose_list_item(state: _ComposeParserState, stripped: str) -> None:
    if not state.key_stack:
        return

    parent, final_key = _compose_path_parent(state, state.key_stack)
    if parent is None or final_key is None:
        return

    existing = parent.get(final_key)
    if isinstance(existing, list):
        existing.append(_strip_yaml_quotes(stripped[2:].strip()))


def _assign_compose_value(parent: dict, final_key: str, value: str) -> None:
    if value:
        inline = _parse_inline_yaml_list(value)
        parent[final_key] = inline if inline is not None else _strip_yaml_quotes(value)
    elif final_key not in parent:
        parent[final_key] = []


def _set_compose_service_key(
    state: _ComposeParserState,
    stripped: str,
    depth: int,
) -> None:
    if ":" not in stripped:
        return

    key, _, value = stripped.partition(":")
    key = key.strip()
    value = value.strip()
    state.key_stack = state.key_stack[:depth] + [key]

    parent, final_key = _compose_path_parent(state, list(state.key_stack), create=True)
    if parent is not None and final_key is not None:
        _assign_compose_value(parent, final_key, value)


def _parse_compose_service_line(
    state: _ComposeParserState,
    stripped: str,
    indent: int,
) -> None:
    if _start_compose_service(state, stripped, indent):
        return

    if not state.current_service:
        return

    depth = _compose_service_depth(indent)
    if depth < 0:
        return

    state.key_stack = state.key_stack[:depth]
    if stripped.startswith("- "):
        _append_compose_list_item(state, stripped)
    else:
        _set_compose_service_key(state, stripped, depth)


def _collect_compose_section_name(names: list[str], stripped: str, indent: int) -> None:
    if indent == 2 and ":" in stripped:
        names.append(stripped.split(":", 1)[0].strip())


def _parse_compose(text: str) -> dict:
    """Parse a docker-compose YAML file using line-based parsing (no PyYAML).

    Handles the most common patterns: top-level keys (services, networks,
    volumes) and nested mappings under each service (environment, build,
    deploy, healthcheck, depends_on) at arbitrary depth.  Complex YAML
    features (anchors, merge keys, multi-line block scalars) are best-effort.
    """
    state = _ComposeParserState()

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip())

        if _start_compose_top_level_section(state, stripped, indent):
            continue

        if state.current_top == "services":
            _parse_compose_service_line(state, stripped, indent)
            continue

        if state.current_top == "networks":
            _collect_compose_section_name(state.networks, stripped, indent)
            continue

        if state.current_top == "volumes":
            _collect_compose_section_name(state.named_volumes, stripped, indent)
            continue

    return {
        "type": "compose",
        "services": state.services,
        "networks": state.networks,
        "volumes": state.named_volumes,
    }


def _looks_like_compose(text: str) -> bool:
    """Return True if the file content appears to be a docker-compose file.

    Checks for a ``services:`` top-level key at indent 0 AND at least one
    service containing a compose-specific key (``image``, ``build``,
    ``ports``, ``depends_on``, ``container_name``, ``environment``,
    ``volumes``, ``command``, ``healthcheck``).  This avoids false positives
    from non-compose YAML files that happen to have a ``services:`` key.
    """
    _COMPOSE_SERVICE_KEYS = {
        "image:",
        "build:",
        "ports:",
        "depends_on:",
        "container_name:",
        "environment:",
        "volumes:",
        "command:",
        "healthcheck:",
        "restart:",
        "networks:",
        "deploy:",
        "profiles:",
    }
    in_services = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith("services:") or line.startswith("services :"):
            in_services = True
            continue
        # Another top-level key ends the services block
        if in_services and not line[0].isspace():
            in_services = False
        if in_services:
            for ck in _COMPOSE_SERVICE_KEYS:
                if ck in stripped:
                    return True
    return False


def get_docker_inventory(
    src_dir: str, *, source_snapshot: SourceSnapshot | None = None
) -> dict:
    """Discover and parse Dockerfiles and Compose files in the source tree.

    Uses two strategies:
    1. **Name-based**: glob patterns from config (Dockerfile*, *.dockerfile,
       docker-compose*.yml, compose*.yml) — searched recursively.
    2. **Content-based**: any ``.yml`` / ``.yaml`` file containing a
       ``services:`` top-level key is treated as a Compose file.  This
       catches non-standard names like ``infra.yml`` or ``core.yml`` that
       are common in split-compose layouts.

    Respects .gitignore rules to skip ignored files.

    Returns a dict of relative-path -> parsed data.  Keys always use
    forward slashes regardless of the host OS.
    """
    source_snapshot = source_snapshot or build_source_snapshot(src_dir)
    inventory: dict[str, dict] = {}

    for source_file in source_snapshot.dockerfile_candidates:
        rel = source_file.rel_path
        if rel not in inventory:
            inventory[rel] = _parse_dockerfile(
                source_file.abs_path.read_text(errors="replace")
            )

    for source_file in source_snapshot.compose_candidates:
        rel = source_file.rel_path
        if rel not in inventory:
            inventory[rel] = _parse_compose(
                source_file.abs_path.read_text(errors="replace")
            )

    for source_file in source_snapshot.yaml_candidates:
        rel = source_file.rel_path
        if rel in inventory:
            continue
        text = source_file.abs_path.read_text(errors="replace")
        if _looks_like_compose(text):
            inventory[rel] = _parse_compose(text)

    return inventory
