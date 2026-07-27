from __future__ import annotations

import json
import re
import sys
import time
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

from ..config import validate_path, validate_source_root
from ..extractors.common import normalize_include_tests
from ..services import wiki_media
from ..services.data_flow import analyze_data_flow
from ..services.dependencies import analyze_dependencies
from ..services.entrypoints import (
    build_flow,
    get_entry_points,
    javascript_flow_limitations,
    read_console_scripts,
)
from ..services.extraction_jobs import (
    ExtractionJobPlan,
    ExtractionJobRequest,
    extraction_job_request_from_args,
    print_extraction_job_plan,
)
from ..services.infrastructure_inventory import (
    get_yaml_infrastructure_inventory,
    infrastructure_page_name,
)
from ..services.infrastructure_sync import (
    INFRASTRUCTURE_GENERATION_INPUT_KEY,
    INFRASTRUCTURE_SYNC_SCHEMA_VERSION,
    build_infrastructure_page_map,
)
from ..services.inventory_cache import (
    InventoryCacheOptions,
    InventoryCacheStats,
    format_cache_stats,
)
from ..services.io import read_md
from ..services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from ..services.knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadView,
    build_knowledge_read_view,
)
from ..services.knowledge_loader import (
    KnowledgeLoadIssue,
    KnowledgeLoadResult,
    KnowledgeMismatchPolicy,
    KnowledgeStateLoadError,
    load_knowledge_state,
)
from ..services.knowledge_model import (
    ComputedFreshness,
    EvidenceState,
    KnowledgeLoadState,
    ObservationScope,
)
from ..services.knowledge_evidence import hash_json
from ..services.knowledge_governance import (
    GOVERNANCE_EXTENSION_KEY,
    GOVERNANCE_FILENAME,
    evaluate_review_event,
    load_governance,
)
from ..services.knowledge_observability import (
    KnowledgeAggregateSummary,
    KnowledgePhaseDurations,
    summarize_knowledge_view,
)
from ..services.knowledge_orchestration import (
    RUNTIME_GENERATION_OPTION_DEFAULTS,
    RuntimeLiveEvaluationInputs,
    build_runtime_live_evaluation,
    runtime_generation_options,
)
from ..services.plugins import PluginError, iter_components, load_entry_point
from ..services.source_snapshot import (
    SourceSnapshot,
    build_source_snapshot,
    format_unsupported_source_summary,
    unsupported_source_label,
    unsupported_source_summary,
)
from ..services.sync_manifest import MANIFEST_FILENAME, SyncManifest
from ..services.verification_contracts import (
    VERIFICATION_RECEIPT_FILENAME,
    VerificationResult,
    build_artifact_verification_context,
    evaluate_verification_receipt,
    load_verification_receipt,
)
from ..services.team import build_team_issues
from ..services.wiki_surface import PageKind, is_safe_page_id, iter_page_kinds
from ..services.wiki_surface_index import SURFACE_INDEX_FILENAME
from .bootstrap_cmd import (
    build_entity_occurrence_page_map,
    build_module_page_map,
)
from .extract_cmd import (
    InventoryResult,
    get_call_graph,
    get_docker_inventory,
    get_inventory_result,
    resolve_call_edges,
)

MERMAID_CLICK_RE = re.compile(r'^\s*click\s+\S+\s+"([^"]+)"', re.MULTILINE)
MERMAID_NODE_RE = re.compile(r'^\s*[A-Za-z][A-Za-z0-9_]*\s*\["')
MERMAID_FENCE = "```mermaid"
FENCE_END = "```"
GENERATED_DIAGRAM_NODE_LIMIT = 40
GENERATED_DIAGRAM_LINE_LIMIT = 80
GENERATED_DIAGRAM_CHAR_LIMIT = 6000
GENERATED_DIAGRAM_SECTIONS = {
    "Relationships": (
        "<!-- Auto-generated relationship summary. Do not edit by hand. -->"
    ),
    "Local dependency map": (
        "<!-- Auto-generated local dependency summary. Do not edit by hand. -->"
    ),
}

_PROFILE_PHASES = [
    "inventory",
    "docker_inventory",
    "page_index",
    "unsupported_sources",
    "links",
    "generated_diagrams",
    "orphans",
    "entities",
    "modules",
    "workflows",
    "flows",
    "data_flow",
    "javascript_flow",
    "dependencies",
    "infrastructure",
    "knowledge_load",
    "knowledge_freshness",
    "knowledge_checks",
    "strict",
    "plugins",
    "team",
]


class _LintProfiler:
    def __init__(self) -> None:
        self._started = time.perf_counter()
        self._durations = {name: 0.0 for name in _PROFILE_PHASES}

    @contextmanager
    def phase(self, name: str) -> Iterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            self._durations[name] = self._durations.get(name, 0.0) + (
                time.perf_counter() - started
            )

    def to_dict(self) -> dict:
        return {
            "total_ms": int(round((time.perf_counter() - self._started) * 1000)),
            "phases": [
                {
                    "name": name,
                    "duration_ms": int(round(self._durations.get(name, 0.0) * 1000)),
                }
                for name in _PROFILE_PHASES
            ],
        }


@contextmanager
def _profile_phase(profiler: _LintProfiler | None, name: str) -> Iterator[None]:
    if profiler is None:
        yield
        return
    with profiler.phase(name):
        yield


@dataclass
class LintIssue:
    category: str
    message: str
    severity: str = "error"
    path: str | None = None
    target: str | None = None


@dataclass(frozen=True)
class KnowledgeLintSummary(KnowledgeAggregateSummary):
    """Aggregate strict-lint knowledge status without exposing evidence."""

    concepts_total: int
    concepts_by_kind: dict[str, int]
    evidence_by_state: dict[str, int]
    freshness_by_state: dict[str, int]

    def aggregate_payload(self) -> dict[str, object]:
        """Return only the shared low-cardinality metrics contract."""

        return KnowledgeAggregateSummary(
            availability=self.availability,
            reason=self.reason,
            concepts_evaluated=self.concepts_evaluated,
            freshness_counts=self.freshness_counts,
            evidence_issue_counts=self.evidence_issue_counts,
            degraded_reason=self.degraded_reason,
            phase_durations_ms=self.phase_durations_ms,
            freshness_evaluated=self.freshness_evaluated,
        ).to_payload()

    def report_payload(self) -> dict[str, object]:
        """Return aggregate observability plus the existing lint-only counts."""

        payload = super().to_payload()
        payload.update(
            {
                "concepts_total": self.concepts_total,
                "concepts_by_kind": dict(self.concepts_by_kind),
                "evidence_by_state": dict(self.evidence_by_state),
                "freshness_by_state": dict(self.freshness_by_state),
            }
        )
        return payload


@dataclass
class LintReport:
    wiki_dir: str
    src_dir: str
    strict: bool = False
    issues: list[LintIssue] = field(default_factory=list)
    diagnostics: list[LintIssue] = field(default_factory=list)
    cache_stats: InventoryCacheStats | None = None
    extraction_job_plan: ExtractionJobPlan = field(default_factory=ExtractionJobPlan)
    knowledge_summary: KnowledgeLintSummary | None = None

    @property
    def job_plan(self) -> ExtractionJobPlan:
        return self.extraction_job_plan

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def passed(self) -> bool:
        return self.issue_count == 0

    def by_category(self) -> dict[str, list[LintIssue]]:
        grouped: dict[str, list[LintIssue]] = {}
        for issue in self.issues:
            grouped.setdefault(issue.category, []).append(issue)
        return grouped

    def count(self, category: str) -> int:
        return len(self.by_category().get(category, []))


@dataclass(frozen=True)
class _WikiPageIndex:
    pages: list[Path]
    links_by_page: dict[Path, list[str]]
    content_by_page: dict[Path, str]


@dataclass(frozen=True)
class _LintInputs:
    deep_inventory: dict
    docker_inventory: dict
    yaml_infrastructure_inventory: dict
    page_index: _WikiPageIndex
    unsupported_sources: dict[str, dict[str, object]]
    source_snapshot: SourceSnapshot
    inventory_result: InventoryResult
    include_tests: frozenset[str]


@dataclass(frozen=True)
class _KnowledgeLintState:
    enabled: bool = False
    load_result: KnowledgeLoadResult | None = None
    view: KnowledgeReadView | None = None
    load_issues: tuple[KnowledgeLoadIssue, ...] = ()
    freshness_error_field: str | None = None
    freshness_error_message: str | None = None


def _local_link_path(link: str) -> str | None:
    """Return the file portion of a local markdown link, or None if ignored."""
    return wiki_media.local_link_path(link)


def _is_legacy_page(path: Path, wiki_dir: Path) -> bool:
    """Return True for archived migration pages that lint should ignore."""
    try:
        return path.relative_to(wiki_dir).parts[:1] == ("legacy",)
    except ValueError:
        try:
            return path.resolve().relative_to(wiki_dir.resolve()).parts[:1] == (
                "legacy",
            )
        except ValueError:
            return False


def _collect_documented_entities(wiki_dir: Path) -> set[str]:
    """Return the set of entity names that have wiki pages."""
    entities_dir = wiki_dir / "entities"
    if not entities_dir.exists():
        return set()
    return {p.stem for p in entities_dir.glob("*.md")}


def _collect_code_classes(inventory_or_src_dir) -> set[str]:
    """Return the set of entity page names found by AST scanning.

    Uses collision-aware naming so that duplicate class names across
    different modules are qualified (e.g. ``parser_Parser``).
    """
    inventory = (
        inventory_or_src_dir
        if isinstance(inventory_or_src_dir, dict)
        else get_inventory_result(inventory_or_src_dir).inventory
    )
    entity_map = build_entity_occurrence_page_map(inventory)
    return set(entity_map.values())


def _collect_documented_modules(wiki_dir: Path) -> set[str]:
    """Return the set of module names that have wiki pages."""
    modules_dir = wiki_dir / "modules"
    if not modules_dir.exists():
        return set()
    return {p.stem for p in modules_dir.glob("*.md")}


def _collect_code_modules(inventory_or_src_dir) -> set[str]:
    """Return the set of module page names with tracked inventory.

    Uses collision-aware naming so that duplicate file stems across
    different directories are qualified (e.g. ``pkg_a_cli``).
    """
    inventory = (
        inventory_or_src_dir
        if isinstance(inventory_or_src_dir, dict)
        else get_inventory_result(inventory_or_src_dir).inventory
    )
    mod_map = build_module_page_map(inventory)
    return set(mod_map.values())


def _collect_documented_workflows(wiki_dir: Path) -> set[str]:
    """Return the set of workflow names that have wiki pages."""
    workflows_dir = wiki_dir / "workflows"
    if not workflows_dir.exists():
        return set()
    return {p.stem for p in workflows_dir.glob("*.md")}


def _collect_documented_flows(wiki_dir: Path) -> set[str]:
    """Return the set of user-flow page stems (entry-point ids)."""
    flows_dir = wiki_dir / "flows"
    if not flows_dir.exists():
        return set()
    return {p.stem for p in flows_dir.glob("*.md")}


def _collect_documented_infrastructure(wiki_dir: Path) -> set[str]:
    """Return the set of infrastructure page names that have wiki pages."""
    infra_dir = wiki_dir / "infrastructure"
    if not infra_dir.exists():
        return set()
    return {p.stem for p in infra_dir.glob("*.md")}


def _collect_docker_files(docker_inventory_or_src_dir) -> set[str]:
    """Return the set of Docker/Compose file page-names found in source."""
    docker_inv = (
        docker_inventory_or_src_dir
        if isinstance(docker_inventory_or_src_dir, dict)
        else get_docker_inventory(docker_inventory_or_src_dir)
    )
    return {infrastructure_page_name(f) for f in docker_inv}


def _collect_infrastructure_files(
    docker_inventory: dict, yaml_infrastructure_inventory: dict | None = None
) -> set[str]:
    """Return page names for all supported infrastructure files in source."""
    combined = dict(docker_inventory)
    for source_path, info in (yaml_infrastructure_inventory or {}).items():
        combined.setdefault(source_path, info)
    return {
        Path(page_path).stem
        for page_path in build_infrastructure_page_map(combined).values()
    }


def _persisted_infrastructure_tombstone_pages(wiki_dir: Path) -> set[str]:
    try:
        manifest = SyncManifest.load(wiki_dir)
    except (FileNotFoundError, TypeError, ValueError):
        return set()
    state = manifest.generation_inputs.get("infrastructure")
    if not isinstance(state, Mapping):
        return set()
    raw_tombstones = state.get("tombstones")
    if not isinstance(raw_tombstones, Mapping):
        return set()
    pages: set[str] = set()
    for record in raw_tombstones.values():
        if not isinstance(record, Mapping) or record.get("reason") != "source-removed":
            continue
        page_path = record.get("page_path")
        if isinstance(page_path, str):
            pages.add(Path(page_path).stem)
    return pages


def _add(
    report: LintReport,
    category: str,
    message: str,
    *,
    path: str | None = None,
    target: str | None = None,
) -> None:
    report.issues.append(
        LintIssue(category=category, message=message, path=path, target=target)
    )


def _diagnose(
    report: LintReport,
    category: str,
    message: str,
    *,
    path: str | None = None,
    target: str | None = None,
    severity: str = "warning",
) -> None:
    report.diagnostics.append(
        LintIssue(
            category=category,
            message=message,
            severity=severity,
            path=path,
            target=target,
        )
    )


def _coerce_plugin_issue(raw: object, component_ref: str) -> LintIssue:
    if isinstance(raw, LintIssue):
        return raw
    if isinstance(raw, dict):
        category = str(raw.get("category") or f"plugin:{component_ref}")
        message = str(raw.get("message") or "Plugin lint rule reported an issue.")
        severity = str(raw.get("severity") or "error")
        path = raw.get("path")
        target = raw.get("target")
        return LintIssue(
            category=category,
            message=message,
            severity=severity,
            path=str(path) if path is not None else None,
            target=str(target) if target is not None else None,
        )
    return LintIssue(
        category=f"plugin:{component_ref}",
        message=f"Plugin lint rule returned unsupported issue type: {type(raw).__name__}",
    )


def _run_plugin_lint_rules(
    report: LintReport,
    wiki_dir: Path,
    src_dir: str,
    inventory: dict,
    pages: list[Path],
) -> None:
    for component in iter_components("lint_rule"):
        component_ref = component["ref"]
        try:
            rule = load_entry_point(component["entry_point"])
            issues = rule(wiki_dir, src_dir, inventory, pages)
        except (PluginError, Exception) as exc:
            _add(
                report,
                "plugin_lint_rule",
                f"Plugin lint rule {component_ref} failed: {exc}",
                target=component_ref,
            )
            continue

        if issues is None:
            continue
        if not isinstance(issues, list):
            issues = [issues]
        for issue in issues:
            report.issues.append(_coerce_plugin_issue(issue, component_ref))


def _inventory_code_classes(inventory: dict) -> set[str]:
    entity_map = build_entity_occurrence_page_map(inventory)
    return set(entity_map.values())


def _inventory_code_modules(inventory: dict) -> set[str]:
    mod_map = build_module_page_map(inventory)
    return set(mod_map.values())


def _check_required_structure(report: LintReport, wiki_dir: Path) -> None:
    required_files = ["index.md", "log.md"]
    required_dirs = ["entities", "modules", "workflows", "infrastructure"]
    for filename in required_files:
        path = wiki_dir / filename
        if not path.exists():
            _add(
                report,
                "wiki_structure",
                f"Missing required wiki file: {filename}",
                path=filename,
            )
    for dirname in required_dirs:
        path = wiki_dir / dirname
        if not path.is_dir():
            _add(
                report,
                "wiki_structure",
                f"Missing required wiki directory: {dirname}/",
                path=dirname,
            )


def _check_sync_manifest(
    report: LintReport,
    wiki_dir: Path,
    src_dir: str,
    inventory: dict | None = None,
    *,
    source_snapshot: SourceSnapshot | None = None,
    proven_nonsemantic_paths: frozenset[str] = frozenset(),
) -> None:
    from .sync_cmd import _compute_diff

    try:
        manifest = SyncManifest.load(wiki_dir)
    except FileNotFoundError:
        _add(
            report,
            "sync_manifest",
            f"Missing sync manifest: {MANIFEST_FILENAME}. Run `llm-wiki bootstrap` or `llm-wiki sync`.",
            path=MANIFEST_FILENAME,
        )
        return
    except Exception as exc:
        _add(
            report,
            "sync_manifest",
            f"Invalid sync manifest {MANIFEST_FILENAME}: {exc}",
            path=MANIFEST_FILENAME,
        )
        return

    try:
        if inventory is None:
            inventory_result = get_inventory_result(src_dir, deep=True)
            if inventory_result.failed:
                messages = "; ".join(
                    f"{status.language}: {status.message}"
                    for status in inventory_result.failed
                )
                raise RuntimeError(messages)
            inventory = inventory_result.inventory
            source_snapshot = inventory_result.source_snapshot
        source_content_hashes = (
            source_snapshot.hashes_for(inventory)
            if source_snapshot is not None
            else None
        )
        diff = _compute_diff(
            manifest,
            inventory,
            src_dir,
            source_content_hashes=source_content_hashes,
        )
    except Exception as exc:
        _add(
            report,
            "sync_manifest",
            f"Could not verify sync manifest freshness: {exc}",
            path=MANIFEST_FILENAME,
        )
        return

    unproven_metadata = sorted(
        set(diff.metadata_only_files) - set(proven_nonsemantic_paths)
    )
    has_hard_changes = bool(
        diff.new_files
        or diff.changed_files
        or unproven_metadata
        or diff.removed_files
        or diff.moved_entities
        or diff.renamed_entity_pages
        or diff.renamed_module_pages
    )
    if has_hard_changes:
        parts = [
            f"{len(diff.new_files)} new",
            f"{len(diff.changed_files)} changed",
            f"{len(unproven_metadata)} metadata-only",
            f"{len(diff.removed_files)} removed",
            f"{len(diff.moved_entities)} moved",
            f"{len(diff.renamed_entity_pages)} renamed entity pages",
            f"{len(diff.renamed_module_pages)} renamed module pages",
        ]
        _add(
            report,
            "sync_manifest",
            "Sync manifest is stale against current inventory: "
            + ", ".join(parts)
            + ".",
            path=MANIFEST_FILENAME,
        )


def _collect_lint_inputs(
    report: LintReport,
    wiki_path: Path,
    src_dir: str,
    profiler: _LintProfiler | None,
    cache_options: InventoryCacheOptions | None,
    parallel_jobs: int,
    helper_cache_dir: str | None,
    include_tests: Iterable[str] | None,
    job_request: ExtractionJobRequest | None,
    plan_reporter: Callable[[ExtractionJobPlan], None] | None,
    include_plugins: bool,
) -> _LintInputs | None:
    normalized_include_tests = normalize_include_tests(include_tests)
    with _profile_phase(profiler, "inventory"):
        source_snapshot = build_source_snapshot(
            src_dir,
            include_tests=normalized_include_tests,
        )
        inventory_result = get_inventory_result(
            src_dir,
            deep=True,
            source_snapshot=source_snapshot,
            cache_options=cache_options,
            parallel_jobs=parallel_jobs,
            helper_cache_dir=helper_cache_dir,
            include_tests=normalized_include_tests,
            job_request=job_request,
            plan_reporter=plan_reporter,
            include_plugins=include_plugins,
        )
        report.extraction_job_plan = inventory_result.extraction_job_plan
        if cache_options is not None and cache_options.stats_enabled:
            report.cache_stats = inventory_result.cache_stats
        if inventory_result.failed:
            _add_extractor_failures(report, inventory_result)
            return None
        source_snapshot = inventory_result.source_snapshot or source_snapshot
        deep_inventory = inventory_result.inventory
        unsupported_sources = unsupported_source_summary(
            source_snapshot, supported_languages=inventory_result.statuses
        )

    with _profile_phase(profiler, "docker_inventory"):
        docker_inventory = get_docker_inventory(
            src_dir, source_snapshot=source_snapshot
        )
        yaml_infrastructure_inventory = get_yaml_infrastructure_inventory(
            src_dir, source_snapshot=source_snapshot
        )

    with _profile_phase(profiler, "page_index"):
        page_index = _build_page_index(wiki_path)

    return _LintInputs(
        deep_inventory=deep_inventory,
        docker_inventory=docker_inventory,
        yaml_infrastructure_inventory=yaml_infrastructure_inventory,
        page_index=page_index,
        unsupported_sources=unsupported_sources,
        source_snapshot=source_snapshot,
        inventory_result=inventory_result,
        include_tests=normalized_include_tests,
    )


def _check_unsupported_source_diagnostics(
    report: LintReport, unsupported_sources: dict[str, dict[str, object]]
) -> None:
    message = format_unsupported_source_summary(unsupported_sources)
    if not message:
        return
    for language, data in sorted(unsupported_sources.items()):
        label = unsupported_source_label(language)
        raw_paths = data.get("paths", [])
        paths = (
            [str(path) for path in raw_paths if path]
            if isinstance(raw_paths, list)
            else []
        )
        if not paths:
            _diagnose(
                report,
                "unsupported_sources",
                message,
                target=label,
                severity="info",
            )
            continue
        for path in paths:
            _diagnose(
                report,
                "unsupported_sources",
                f"{message}; {label}: {path}",
                path=path,
                target=label,
                severity="info",
            )


def _build_page_index(wiki_path: Path) -> _WikiPageIndex:
    pages = [
        page for page in wiki_path.rglob("*.md") if not _is_legacy_page(page, wiki_path)
    ]
    page_content = {page: read_md(page) for page in pages}
    links_by_page = {
        page: [
            link.raw_target for link in wiki_media.iter_markdown_link_targets(content)
        ]
        for page, content in page_content.items()
    }
    return _WikiPageIndex(pages, links_by_page, page_content)


def _check_broken_links(
    report: LintReport,
    wiki_path: Path,
    page_index: _WikiPageIndex,
) -> None:
    for page in page_index.pages:
        for link in page_index.links_by_page.get(page, []):
            local_path = _local_link_path(link)
            if local_path is None:
                continue
            if wiki_media.media_type_for_path(local_path) is not None:
                continue
            target = (page.parent / local_path).resolve()
            if not target.exists():
                rel = page.relative_to(wiki_path).as_posix()
                _add(
                    report,
                    "broken_links",
                    f"Broken link in {rel} -> {link}",
                    path=rel,
                    target=link,
                )


def _check_media_references(
    report: LintReport,
    wiki_path: Path,
    page_index: _WikiPageIndex,
    *,
    media_size_warn_bytes: int,
) -> None:
    seen_targets: set[tuple[str, str, str]] = set()
    content_by_rel = _content_by_relative_path(page_index, wiki_path)
    references_by_page = wiki_media.collect_media_references_by_page(
        wiki_path, content_by_rel
    )
    outside_assets_by_page: dict[str, set[str]] = {}
    for page in page_index.pages:
        rel = page.relative_to(wiki_path).as_posix()
        for reference in references_by_page.get(rel, []):
            target = (page.parent / reference.target).resolve()
            key = (rel, reference.target, reference.source)
            if key in seen_targets:
                continue
            seen_targets.add(key)
            if wiki_media.is_symlink_escape(wiki_path, reference):
                _diagnose(
                    report,
                    "media_symlink_escape",
                    (
                        f"Media link in {rel} resolves outside the wiki through "
                        f"a symlink: {reference.target}"
                    ),
                    path=rel,
                    target=reference.target,
                )
                continue
            if not target.exists():
                _add(
                    report,
                    "media_link_broken",
                    f"Broken media link in {rel} -> {reference.target}",
                    path=rel,
                    target=reference.target,
                )
                continue
            asset_rel = wiki_media.asset_relative_path(wiki_path, reference)
            if asset_rel is not None and not wiki_media.is_assets_path(asset_rel):
                outside_assets_by_page.setdefault(rel, set()).add(asset_rel)
            if reference.requires_alt and not (reference.alt_text or "").strip():
                _diagnose(
                    report,
                    "media_missing_alt_text",
                    f"Media image in {rel} is missing alt text: {reference.target}",
                    path=rel,
                    target=reference.target,
                )
            try:
                size = target.stat().st_size
            except OSError:
                continue
            if size > media_size_warn_bytes:
                _diagnose(
                    report,
                    "media_oversize",
                    (
                        f"Media asset in {rel} exceeds {media_size_warn_bytes} "
                        f"bytes: {reference.target} ({size} bytes)"
                    ),
                    path=rel,
                    target=reference.target,
                )

    for rel, targets in sorted(outside_assets_by_page.items()):
        sorted_targets = sorted(targets, key=lambda value: (value.casefold(), value))
        _diagnose(
            report,
            "media_outside_assets",
            (f"Media referenced outside assets/ in {rel}: {', '.join(sorted_targets)}"),
            path=rel,
            target=", ".join(sorted_targets),
        )

    asset_index = wiki_media.build_asset_index(
        wiki_path, references_by_page=references_by_page
    )
    for asset in asset_index.unreferenced:
        if wiki_media.media_type_for_path(asset) is not None:
            expected_page = asset_index.expected_pages.get(asset)
            message = f"Asset is not referenced by any wiki page: {asset}"
            if expected_page:
                message += f" (expected owner page: {expected_page})"
            _diagnose(
                report,
                "media_orphan",
                message,
                path=asset,
                target=expected_page,
            )
        elif wiki_media.is_unrecognized_asset_warning_path(asset):
            _diagnose(
                report,
                "asset_unrecognized_type",
                f"Asset has an unrecognized media type: {asset}",
                path=asset,
            )


def _content_by_relative_path(
    page_index: _WikiPageIndex,
    wiki_path: Path,
) -> dict[str, str]:
    return {
        page.relative_to(wiki_path).as_posix(): content
        for page, content in page_index.content_by_page.items()
    }


def _section_body(markdown: str, heading: str) -> str | None:
    lines = markdown.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = idx + 1
            break
    if start is None:
        return None

    end = len(lines)
    for idx in range(start, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    return "\n".join(lines[start:end]).strip()


def _iter_mermaid_blocks(section_body: str) -> Iterator[list[str]]:
    lines = section_body.splitlines()
    idx = 0
    while idx < len(lines):
        if lines[idx].strip() != MERMAID_FENCE:
            idx += 1
            continue
        idx += 1
        block: list[str] = []
        while idx < len(lines) and lines[idx].strip() != FENCE_END:
            block.append(lines[idx])
            idx += 1
        yield block
        if idx < len(lines):
            idx += 1


def _generated_diagram_sections(markdown: str) -> Iterator[tuple[str, str]]:
    for heading, marker in GENERATED_DIAGRAM_SECTIONS.items():
        body = _section_body(markdown, heading)
        if body and marker in body:
            yield heading, body


def _check_generated_diagram_links(
    report: LintReport,
    page: Path,
    rel: str,
    heading: str,
    block: list[str],
) -> None:
    diagram = "\n".join(block)
    for link in MERMAID_CLICK_RE.findall(diagram):
        local_path = _local_link_path(link)
        if local_path is None:
            continue
        target = (page.parent / local_path).resolve()
        if not target.exists():
            _add(
                report,
                "broken_links",
                f"Broken generated diagram link in {rel} ## {heading} -> {link}",
                path=rel,
                target=link,
            )


def _diagnose_generated_diagram_bloat(
    report: LintReport,
    rel: str,
    heading: str,
    block: list[str],
) -> None:
    measurements = [
        (
            "node declarations",
            sum(1 for line in block if MERMAID_NODE_RE.match(line)),
            GENERATED_DIAGRAM_NODE_LIMIT,
        ),
        ("body lines", len(block), GENERATED_DIAGRAM_LINE_LIMIT),
        ("characters", len("\n".join(block)), GENERATED_DIAGRAM_CHAR_LIMIT),
    ]
    for label, value, cap in measurements:
        if value <= cap:
            continue
        _diagnose(
            report,
            "generated_diagram_bloat",
            (
                f"Generated diagram bloat in {rel} ## {heading}: {label} "
                f"{value} exceeds cap {cap}. rerun `llm-wiki sync` and reduce "
                "relationship/dependency fan-out if this persists."
            ),
            path=rel,
            target=heading,
        )


def _check_generated_diagrams(
    report: LintReport,
    wiki_path: Path,
    page_index: _WikiPageIndex,
) -> None:
    for page in page_index.pages:
        markdown = page_index.content_by_page.get(page, "")
        rel = page.relative_to(wiki_path).as_posix()
        for heading, body in _generated_diagram_sections(markdown):
            for block in _iter_mermaid_blocks(body):
                _check_generated_diagram_links(report, page, rel, heading, block)
                _diagnose_generated_diagram_bloat(report, rel, heading, block)


def _check_orphan_pages(
    report: LintReport,
    wiki_path: Path,
    page_index: _WikiPageIndex,
) -> None:
    index_path = wiki_path / "index.md"
    referenced_files: set[Path] = set()
    if index_path.exists():
        index_links = page_index.links_by_page.get(index_path, [])

        for link in index_links:
            local_path = _local_link_path(link)
            if local_path is not None:
                target = (index_path.parent / local_path).resolve()
                referenced_files.add(target)

        for page in page_index.pages:
            if page.name in ["index.md", "log.md"]:
                continue
            if page.resolve() not in referenced_files:
                rel = page.relative_to(wiki_path).as_posix()
                _add(
                    report,
                    "orphan_pages",
                    f"Orphan page (not in index.md): {rel}",
                    path=rel,
                )


def _check_entity_coverage(
    report: LintReport, wiki_path: Path, deep_inventory: dict
) -> None:
    documented_entities = _collect_documented_entities(wiki_path)
    code_classes = _inventory_code_classes(deep_inventory)

    undocumented = code_classes - documented_entities
    stale = documented_entities - code_classes

    if undocumented:
        for name in sorted(undocumented):
            _add(
                report,
                "undocumented_classes",
                f"Undocumented class (in code, not in wiki): {name}",
                target=name,
            )

    if stale:
        for name in sorted(stale):
            _add(
                report,
                "stale_entities",
                f"Stale entity (in wiki, not in code): {name}",
                target=name,
            )


def _check_module_coverage(
    report: LintReport, wiki_path: Path, deep_inventory: dict
) -> None:
    documented_modules = _collect_documented_modules(wiki_path)
    code_modules = _inventory_code_modules(deep_inventory)

    undoc_mods = code_modules - documented_modules
    stale_mods = documented_modules - code_modules

    if undoc_mods:
        for name in sorted(undoc_mods):
            _add(
                report,
                "undocumented_modules",
                f"Undocumented module (in code, not in wiki): {name}",
                target=name,
            )

    if stale_mods:
        for name in sorted(stale_mods):
            _add(
                report,
                "stale_modules",
                f"Stale module (in wiki, not in code): {name}",
                target=name,
            )


def _check_workflow_coverage(
    report: LintReport,
    wiki_path: Path,
    deep_inventory: dict,
    page_index: _WikiPageIndex,
) -> None:
    documented_workflows = _collect_documented_workflows(wiki_path)

    workflows_dir = wiki_path / "workflows"
    if workflows_dir.exists():
        for wf_page in workflows_dir.glob("*.md"):
            for link in page_index.links_by_page.get(wf_page, []):
                local_path = _local_link_path(link)
                if local_path is None:
                    continue
                target = (wf_page.parent / local_path).resolve()
                if not target.exists():
                    _diagnose(
                        report,
                        "broken_workflow_links",
                        f"Broken link in workflow {wf_page.stem} -> {link}",
                        path=wf_page.relative_to(wiki_path).as_posix(),
                        target=link,
                    )

    detected_workflows = set(get_call_graph(deep_inventory).keys())
    missing_wf = detected_workflows - documented_workflows
    if missing_wf:
        for name in sorted(missing_wf):
            _add(
                report,
                "missing_workflows",
                f"Missing workflow (detected in code, no wiki page): {name}",
                target=name,
            )


def _check_flow_coverage(
    report: LintReport,
    wiki_path: Path,
    deep_inventory: dict,
    src_dir: str,
    *,
    include_plugins: bool = True,
) -> None:
    """Flag user-flow pages whose entry point no longer exists in the code.

    Only stale pages are reported (missing flows are not, since flow generation
    is opt-out via ``--skip-flows``). Broken links and orphan pages in ``flows/``
    are already covered by the global link and orphan checks.
    """
    documented_flows = _collect_documented_flows(wiki_path)
    if not documented_flows:
        return
    detected_flows = {
        ep["id"]
        for ep in get_entry_points(
            deep_inventory,
            console_scripts=read_console_scripts(src_dir),
            root=src_dir,
            fallback_root=Path.cwd(),
            include_plugins=include_plugins,
        )
    }
    for name in sorted(documented_flows - detected_flows):
        _add(
            report,
            "stale_flows",
            f"Stale user-flow page (entry point removed): {name}",
            target=name,
        )


def _check_data_flow_diagnostics(
    report: LintReport,
    wiki_path: Path,
    deep_inventory: dict,
    src_dir: str,
    *,
    include_plugins: bool = True,
) -> None:
    documented_flows = _collect_documented_flows(wiki_path)
    if not documented_flows:
        return

    edges = resolve_call_edges(deep_inventory)
    for entry_point in get_entry_points(
        deep_inventory,
        console_scripts=read_console_scripts(src_dir),
        root=src_dir,
        fallback_root=Path.cwd(),
        include_plugins=include_plugins,
    ):
        if entry_point["id"] not in documented_flows:
            continue
        data_flow = analyze_data_flow(
            deep_inventory, build_flow(entry_point, edges), edges
        )
        for gap in data_flow["gaps"]:
            line = gap.get("line")
            location = f" line {line}" if line else ""
            _diagnose(
                report,
                "data_flow_gaps",
                (
                    f"Data-flow gap in {entry_point['id']}: {gap['kind']} "
                    f"{gap['step']} -> {gap['target']}{location}"
                ),
                target=entry_point["id"],
            )


def _check_javascript_flow_diagnostics(
    report: LintReport,
    deep_inventory: dict,
    src_dir: str,
    *,
    include_plugins: bool = True,
) -> None:
    entry_points = get_entry_points(
        deep_inventory,
        console_scripts=read_console_scripts(src_dir),
        root=src_dir,
        fallback_root=Path.cwd(),
        include_plugins=include_plugins,
    )
    for limitation in javascript_flow_limitations(deep_inventory, entry_points):
        _diagnose(
            report,
            "javascript_flow_unsupported",
            limitation["message"],
            path=limitation["file"],
            target=limitation["file"],
        )


def _check_dependency_coverage(
    report: LintReport,
    wiki_path: Path,
    deep_inventory: dict,
    src_dir: str,
    source_snapshot: SourceSnapshot | None = None,
) -> None:
    """Re-run dependency analysis for the architecture pages and warn on drift.

    Only runs when ``dependencies.md`` / ``load-order.md`` exist (projects that
    opted out via ``bootstrap --skip-dependencies`` are left untouched). Import
    cycles and undeclared / unused external dependencies surface as non-failing
    **diagnostics** so they never break ``ci-check`` on their own; a page that
    exists but whose analysis found no modules is flagged **stale** as a hard
    issue. Reuses the already-built deep inventory, so no extra extraction pass
    runs (DL-010).
    """
    pages = [
        p
        for p in (wiki_path / "dependencies.md", wiki_path / "load-order.md")
        if p.exists()
    ]
    if not pages:
        return

    analysis = analyze_dependencies(
        deep_inventory, src_dir, source_snapshot=source_snapshot
    )
    if not analysis["graph"]["nodes"]:
        for page in pages:
            _add(
                report,
                "stale_dependencies",
                f"Stale architecture page (no modules detected in source): {page.stem}",
                path=page.name,
                target=page.stem,
            )
        return

    for cycle in analysis["cycles"]:
        _diagnose(
            report,
            "dependency_cycles",
            "Import cycle: " + " ⇄ ".join(cycle),
        )
    for language, data in sorted(analysis["reconciliation"]["languages"].items()):
        undeclared_details = {
            item.get("package"): item for item in data.get("undeclared_details", [])
        }
        for package in data["undeclared"]:
            detail = undeclared_details.get(package)
            suffix = ""
            if detail:
                files = detail.get("files") or []
                locations = ", ".join(files) if files else "unknown file"
                scope = _format_dependency_scope(detail.get("scope"))
                suffix = f" in {locations} (manifest scope: {scope})"
            _diagnose(
                report,
                "undeclared_dependencies",
                f"Undeclared {language} dependency "
                f"(imported, not declared): {package}{suffix}",
                target=package,
            )
        unused_details = {
            item.get("package"): item for item in data.get("unused_details", [])
        }
        for package in data["unused"]:
            detail = unused_details.get(package)
            suffix = ""
            if detail:
                scope = _format_dependency_scope(detail.get("scope"))
                suffix = f" (manifest scope: {scope})"
            _diagnose(
                report,
                "unused_dependencies",
                f"Unused {language} dependency "
                f"(declared, not imported): {package}{suffix}",
                target=package,
            )
        for module, files in sorted((data.get("path_aliases") or {}).items()):
            locations = ", ".join(files)
            _diagnose(
                report,
                "unresolved_path_aliases",
                "Unresolved TypeScript path alias import "
                f"(matched tsconfig paths, no local file found): {module}"
                f" in {locations}",
                target=module,
            )


def _format_dependency_scope(scope: object) -> str:
    if scope is None:
        return "<none>"
    scope_text = str(scope)
    return scope_text if scope_text else "."


def _check_infrastructure_coverage(
    report: LintReport,
    wiki_path: Path,
    docker_inventory: dict,
    yaml_infrastructure_inventory: dict | None = None,
) -> None:
    documented_infra = _collect_documented_infrastructure(wiki_path)
    source_infra = _collect_infrastructure_files(
        docker_inventory, yaml_infrastructure_inventory
    )

    undoc_infra = source_infra - documented_infra
    tombstone_pages = _persisted_infrastructure_tombstone_pages(wiki_path)
    stale_infra = documented_infra - source_infra - tombstone_pages

    if undoc_infra:
        for name in sorted(undoc_infra):
            _add(
                report,
                "undocumented_infrastructure",
                f"Undocumented infrastructure file (in source, not in wiki): {name}",
                target=name,
            )

    if stale_infra:
        for name in sorted(stale_infra):
            _add(
                report,
                "stale_infrastructure",
                f"Stale infrastructure page (in wiki, source file removed): {name}",
                target=name,
            )


def _check_team_issues(
    report: LintReport,
    wiki_path: Path,
    src_dir: str,
    inputs: _LintInputs,
) -> None:
    for issue in build_team_issues(
        wiki_path,
        src_dir,
        inputs.deep_inventory,
        inputs.page_index.pages,
        docker_inventory=inputs.docker_inventory,
    ):
        report.issues.append(_coerce_plugin_issue(issue, "team"))


def _canonical_markdown_content(
    page_index: _WikiPageIndex,
    wiki_path: Path,
) -> dict[str, str]:
    """Reuse the page-index bytes for only the versioned canonical surface."""

    content_by_path = _content_by_relative_path(page_index, wiki_path)
    root_paths = {
        entry.path_pattern for entry in iter_page_kinds() if not entry.requires_page_id
    }
    directories = {
        entry.directory
        for entry in iter_page_kinds()
        if entry.requires_page_id and entry.directory is not None
    }
    canonical: dict[str, str] = {}
    for relative_path, content in content_by_path.items():
        if relative_path in root_paths:
            canonical[relative_path] = content
            continue
        parts = relative_path.split("/")
        if (
            len(parts) == 2
            and parts[0] in directories
            and parts[1].endswith(".md")
            and is_safe_page_id(parts[1][:-3])
        ):
            canonical[relative_path] = content
    return canonical


def _knowledge_lint_enabled(wiki_path: Path) -> bool:
    """Recognize generated or manifest-declared knowledge without taxing legacy."""

    for filename in (
        SURFACE_INDEX_FILENAME,
        KNOWLEDGE_INDEX_FILENAME,
        GOVERNANCE_FILENAME,
        VERIFICATION_RECEIPT_FILENAME,
    ):
        artifact = wiki_path / filename
        if artifact.exists() or artifact.is_symlink():
            return True
    try:
        manifest = SyncManifest.load(wiki_path)
    except (FileNotFoundError, OSError, UnicodeError, ValueError):
        return False
    return manifest.artifact_hashes is not None


def _load_knowledge_lint_state(
    wiki_path: Path,
    inputs: _LintInputs,
) -> _KnowledgeLintState:
    if not _knowledge_lint_enabled(wiki_path):
        return _KnowledgeLintState()
    try:
        load_result = load_knowledge_state(
            wiki_path,
            policy=KnowledgeMismatchPolicy.DEGRADED,
            markdown_pages=_canonical_markdown_content(
                inputs.page_index,
                wiki_path,
            ),
        )
    except KnowledgeStateLoadError as exc:
        return _KnowledgeLintState(enabled=True, load_issues=exc.issues)
    except (OSError, TypeError, UnicodeError, ValueError) as exc:
        return _KnowledgeLintState(
            enabled=True,
            load_issues=(
                KnowledgeLoadIssue(
                    code="knowledge-load-failed",
                    artifact_path=KNOWLEDGE_INDEX_FILENAME,
                    message=str(exc),
                ),
            ),
        )
    return _KnowledgeLintState(enabled=True, load_result=load_result)


def _reliably_missing_source_paths(
    load_result: KnowledgeLoadResult,
    source_snapshot: SourceSnapshot,
) -> frozenset[str]:
    knowledge = load_result.knowledge
    if knowledge is None:
        return frozenset()
    captured = source_snapshot.captured_content_hashes
    uncaptured = {
        basis.source_path
        for concept in knowledge.concepts
        if (basis := concept.facets.structure.basis) is not None
        and basis.source_path is not None
        and basis.source_path not in captured
    }
    missing: set[str] = set()
    for source_path in sorted(uncaptured):
        candidate = source_snapshot.root / source_path
        try:
            candidate.lstat()
        except FileNotFoundError:
            missing.add(source_path)
        except OSError:
            # Unreadable, excluded, or otherwise indeterminate paths are not
            # reliable source-missing evidence.
            continue
    return frozenset(missing)


def _evaluate_knowledge_lint_state(
    state: _KnowledgeLintState,
    inputs: _LintInputs,
) -> _KnowledgeLintState:
    load_result = state.load_result
    if not state.enabled or load_result is None:
        return state
    if load_result.status is not KnowledgeLoadState.VALID:
        return _KnowledgeLintState(
            enabled=True,
            load_result=load_result,
            view=build_knowledge_read_view(load_result),
        )

    assert load_result.knowledge is not None
    assert load_result.manifest_basis is not None
    try:
        generation_options = runtime_generation_options(
            surfaces=load_result.manifest_basis.surfaces,
            generation_inputs=load_result.manifest_basis.generation_inputs,
            include_tests=inputs.include_tests,
            preserve_semantic=True,
        )
        live_evaluation = build_runtime_live_evaluation(
            RuntimeLiveEvaluationInputs(
                knowledge=load_result.knowledge,
                manifest=load_result.manifest_basis,
                inventory=inputs.deep_inventory,
                source_snapshot=inputs.source_snapshot,
                generation_options=generation_options,
                generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS,
                generation_option_allowlist=tuple(
                    RUNTIME_GENERATION_OPTION_DEFAULTS
                ),
                infrastructure_inventory={
                    **inputs.docker_inventory,
                    **{
                        path: value
                        for path, value in (
                            inputs.yaml_infrastructure_inventory.items()
                        )
                        if path not in inputs.docker_inventory
                    },
                },
                missing_source_paths=_reliably_missing_source_paths(
                    load_result,
                    inputs.source_snapshot,
                ),
                inventory_complete=True,
                extractor_registry=inputs.inventory_result.extractor_registry,
                plugin_extractor_components=(inputs.inventory_result.plugin_components),
                plugin_components=(inputs.inventory_result.producer_plugin_components),
            )
        )
        view = build_knowledge_read_view(
            load_result,
            live_evaluation=live_evaluation,
        )
    except (OSError, TypeError, UnicodeError, ValueError) as exc:
        field_name = str(getattr(exc, "field", "live_evaluation"))
        message = str(getattr(exc, "message", exc))
        view = build_knowledge_read_view(load_result, snapshot_only=True)
        return _KnowledgeLintState(
            enabled=True,
            load_result=load_result,
            view=view,
            freshness_error_field=field_name,
            freshness_error_message=message,
        )
    return _KnowledgeLintState(
        enabled=True,
        load_result=load_result,
        view=view,
    )


def _projection_issue_category(issue: KnowledgeLoadIssue) -> str:
    if (
        issue.field is not None
        and (
            "review_events" in issue.field
            or (
                GOVERNANCE_EXTENSION_KEY in issue.field
                and "reviews" in issue.field
            )
        )
    ):
        return "knowledge_review"
    if issue.code.startswith("governance-"):
        return "knowledge_governance"
    if issue.code.endswith("-version-unsupported") or issue.code in {
        "knowledge-invalid",
        "manifest-invalid",
        "surface-invalid",
    }:
        return "knowledge_schema"
    if issue.code in {
        "markdown-snapshot-invalid",
        "markdown-snapshot-mismatch",
        "page-parity-mismatch",
    }:
        return "knowledge_snapshot"
    return "knowledge_projection"


def _enum_count_payload(values: Mapping[object, int]) -> dict[str, int]:
    normalized = {
        key.value if isinstance(key, Enum) else str(key): value
        for key, value in values.items()
    }
    return dict(sorted(normalized.items()))


def _set_knowledge_summary(
    report: LintReport,
    view: KnowledgeReadView,
    *,
    durations: KnowledgePhaseDurations,
) -> None:
    if view.availability is KnowledgeAvailability.ABSENT:
        return

    counts = view.counts
    aggregate = summarize_knowledge_view(view, durations=durations)
    report.knowledge_summary = KnowledgeLintSummary(
        **aggregate.to_payload(),
        concepts_total=0 if counts is None else counts.concepts_total,
        concepts_by_kind={} if counts is None else dict(counts.concepts_by_kind),
        evidence_by_state=(
            {} if counts is None else _enum_count_payload(counts.evidence_by_state)
        ),
        freshness_by_state=(
            {}
            if aggregate.freshness_counts is None
            else dict(aggregate.freshness_counts)
        ),
    )


def _promised_structural_scope(concept) -> ObservationScope | None:
    return {
        PageKind.MODULES: ObservationScope.MODULE,
        PageKind.ENTITIES: ObservationScope.ENTITY,
        PageKind.INFRASTRUCTURE: ObservationScope.INFRASTRUCTURE,
    }.get(concept.document.page_kind)


def _promised_evidence_reason(
    concept,
    expected_scope: ObservationScope,
) -> str | None:
    structure = concept.facets.structure
    if structure.evidence is not EvidenceState.PRESENT:
        return f"promised-evidence-{structure.evidence.value}"
    basis = structure.basis
    if basis is None:
        return "promised-evidence-basis-missing"
    if basis.scope is not expected_scope:
        return "promised-evidence-scope-mismatch"
    if (
        basis.source_path is None
        or basis.extractor_ref is None
        or basis.source_content_hash is None
        or basis.concept_observation_hash is None
    ):
        return "promised-evidence-basis-invalid"
    return None


def _check_knowledge_concepts(
    report: LintReport,
    view: KnowledgeReadView,
) -> None:
    knowledge = view.knowledge
    manifest = view.manifest_basis
    if knowledge is None or manifest is None:
        return
    for concept in sorted(knowledge.concepts, key=lambda item: item.locator):
        if (
            concept.document.page_kind is PageKind.INFRASTRUCTURE
            and not _manifest_promises_infrastructure_evidence(manifest)
        ):
            # Pre-NKC-108 infrastructure snapshots remain readable and do not
            # acquire a retrospective live-evidence promise.
            continue
        expected_scope = _promised_structural_scope(concept)
        if expected_scope is None:
            continue
        evidence_reason = _promised_evidence_reason(concept, expected_scope)
        if evidence_reason is not None:
            _add(
                report,
                "knowledge_evidence",
                (
                    f"Promised structural evidence for {concept.locator!r} is "
                    f"not valid [reason={evidence_reason}]."
                ),
                path=concept.document.canonical_path,
                target=concept.locator,
            )
            continue
        if view.freshness is None:
            continue
        freshness = view.freshness.by_locator.get(concept.locator)
        if freshness is None:
            _add(
                report,
                "knowledge_freshness",
                (
                    f"Knowledge freshness is unavailable for {concept.locator!r} "
                    "[reason=freshness-result-missing]."
                ),
                path=concept.document.canonical_path,
                target=concept.locator,
            )
            continue
        message = (
            f"Knowledge freshness for {concept.locator!r} is "
            f"{freshness.state.value} [reason={freshness.reason_code}]: "
            f"{freshness.description}."
        )
        if freshness.state is ComputedFreshness.NONSEMANTIC_SOURCE_CHANGE:
            _diagnose(
                report,
                "knowledge_freshness",
                message,
                path=concept.document.canonical_path,
                target=concept.locator,
            )
        elif freshness.state in {
            ComputedFreshness.UNKNOWN,
            ComputedFreshness.SOURCE_CHANGED,
            ComputedFreshness.SOURCE_MISSING,
            ComputedFreshness.BASIS_INCOMPATIBLE,
        }:
            _add(
                report,
                "knowledge_freshness",
                message,
                path=concept.document.canonical_path,
                target=concept.locator,
            )


def _manifest_promises_infrastructure_evidence(manifest: SyncManifest) -> bool:
    value = manifest.generation_inputs.get(INFRASTRUCTURE_GENERATION_INPUT_KEY)
    return (
        isinstance(value, Mapping)
        and value.get("schema_version") == INFRASTRUCTURE_SYNC_SCHEMA_VERSION
    )


def _check_knowledge_reviews(
    report: LintReport,
    view: KnowledgeReadView,
) -> None:
    """Surface computed review expiry without treating it as machine status."""

    if view.knowledge is None:
        return
    try:
        loaded = load_governance(Path(report.wiki_dir))
    except FileNotFoundError:
        loaded = None
    except (OSError, TypeError, UnicodeError, ValueError):
        _add(
            report,
            "knowledge_governance",
            (
                "Governance ledger became invalid after the loaded projection "
                "[reason=governance-invalid]."
            ),
            path=GOVERNANCE_FILENAME,
            target="governance",
        )
        return
    if loaded is not None:
        artifact_hashes = (
            None
            if view.manifest_basis is None
            else view.manifest_basis.artifact_hashes
        )
        committed_hash = (
            None
            if artifact_hashes is None
            else artifact_hashes.governance_hash
        )
        if committed_hash != loaded.content_hash:
            _add(
                report,
                "knowledge_governance",
                (
                    "Governance ledger changed after the loaded projection "
                    "[reason=governance-live-hash-mismatch]."
                ),
                path=GOVERNANCE_FILENAME,
                target="artifact_hashes.governance_hash",
            )
            return
        concepts = {
            concept.locator: concept for concept in view.knowledge.concepts
        }
        for event in sorted(
            loaded.ledger.review_events.values(),
            key=lambda item: (item.authored_at, item.event_id),
        ):
            validity = evaluate_review_event(
                event,
                loaded.ledger,
                view.knowledge,
            )
            if validity.valid:
                continue
            allocation = loaded.ledger.concepts[event.concept_uid]
            concept = concepts.get(allocation.locator)
            _add(
                report,
                "knowledge_review",
                (
                    f"Human review for {allocation.locator!r} is expired "
                    f"[reason={','.join(validity.reasons)}]."
                ),
                path=(
                    None
                    if concept is None
                    else concept.document.canonical_path
                ),
                target=event.event_id,
            )
        return

    # A ready locator-only projection has no review authority.  Keeping this
    # projection fallback supports isolated callers that deliberately supply
    # an already validated governed read view without its backing directory.
    for concept in sorted(view.knowledge.concepts, key=lambda item: item.locator):
        governance = concept.extensions.get(GOVERNANCE_EXTENSION_KEY)
        if not isinstance(governance, Mapping):
            continue
        bounded = governance.get("reviews")
        items = bounded.get("items") if isinstance(bounded, Mapping) else None
        if not isinstance(items, list):
            continue
        for review in items:
            if not isinstance(review, Mapping) or review.get("state") != "expired":
                continue
            reasons = review.get("reasons")
            reason_codes = (
                [str(reason) for reason in reasons]
                if isinstance(reasons, list) and reasons
                else ["review-invalid"]
            )
            event_id = review.get("event_id")
            _add(
                report,
                "knowledge_review",
                (
                    f"Human review for {concept.locator!r} is expired "
                    f"[reason={','.join(reason_codes)}]."
                ),
                path=concept.document.canonical_path,
                target=(
                    event_id
                    if isinstance(event_id, str)
                    else concept.locator
                ),
            )


def _receipt_context(
    view: KnowledgeReadView,
    scope_uid: str,
):
    """Resolve a receipt scope to current anchors without running a checker."""

    knowledge = view.knowledge
    manifest = view.manifest_basis
    if knowledge is None or manifest is None or manifest.artifact_hashes is None:
        return None
    hashes = manifest.artifact_hashes

    def build(scope_locator: str | None):
        return build_artifact_verification_context(
            knowledge,
            knowledge_hash=hashes.knowledge_index_hash,
            surface_index_hash=hashes.surface_index_hash,
            evaluated_envelope_hash=hashes.evaluated_envelope_hash,
            governance_hash=hashes.governance_hash,
            scope_locator=scope_locator,
        )

    bundle = build(None)
    if bundle.scope_uid == scope_uid:
        return bundle
    for concept in knowledge.concepts:
        governance = concept.extensions.get(GOVERNANCE_EXTENSION_KEY)
        projected_uid = (
            governance.get("uid")
            if isinstance(governance, Mapping)
            else None
        )
        current_uid = (
            projected_uid
            if isinstance(projected_uid, str)
            else "locator:"
            + hash_json(concept.locator).removeprefix("sha256:")
        )
        if current_uid == scope_uid:
            return build(concept.locator)
    # Evaluate against bundle scope to produce an explicit scope-changed
    # reason rather than trusting an orphaned receipt.
    return bundle


def _check_verification_receipt(
    report: LintReport,
    view: KnowledgeReadView | None,
) -> None:
    """Validate a disposable receipt; loading never executes its checkers."""

    wiki_root = Path(report.wiki_dir)
    try:
        receipt = load_verification_receipt(wiki_root)
    except (OSError, TypeError, UnicodeError, ValueError):
        _add(
            report,
            "knowledge_verification",
            (
                "Machine verification receipt is malformed or unreadable "
                "[reason=verification-receipt-invalid]."
            ),
            path=VERIFICATION_RECEIPT_FILENAME,
            target="receipt",
        )
        return
    if receipt is None:
        return
    if view is None:
        context = None
    else:
        try:
            context = _receipt_context(view, receipt.scope_uid)
        except (TypeError, ValueError):
            context = None
    if context is None:
        _add(
            report,
            "knowledge_verification",
            (
                "Machine verification receipt has no valid current artifact "
                "basis [reason=verification-basis-unavailable]."
            ),
            path=VERIFICATION_RECEIPT_FILENAME,
            target=receipt.scope_uid,
        )
    else:
        evaluation = evaluate_verification_receipt(receipt, context)
        if not evaluation.valid:
            reasons = ",".join(reason.value for reason in evaluation.reasons)
            _add(
                report,
                "knowledge_verification",
                (
                    "Machine verification receipt is stale "
                    f"[reason={reasons}]."
                ),
                path=VERIFICATION_RECEIPT_FILENAME,
                target=receipt.scope_uid,
            )
    if receipt.result is VerificationResult.FAILED:
        _add(
            report,
            "knowledge_verification",
            (
                "Machine verification recorded failed checks "
                "[reason=verification-check-failed]."
            ),
            path=VERIFICATION_RECEIPT_FILENAME,
            target=receipt.scope_uid,
        )


def _check_knowledge_lint(
    report: LintReport,
    state: _KnowledgeLintState,
) -> None:
    if not state.enabled:
        return
    if state.load_issues:
        findings = state.load_issues
    elif state.view is None or state.view.availability is KnowledgeAvailability.ABSENT:
        findings = ()
    else:
        findings = state.view.projection_findings
    for issue in sorted(
        findings,
        key=lambda item: (
            _projection_issue_category(item),
            item.artifact_path,
            item.field or "",
            item.code,
        ),
    ):
        _add(
            report,
            _projection_issue_category(issue),
            (
                "Knowledge projection validation failed "
                f"[reason={issue.code}]: {issue.message}."
            ),
            path=issue.artifact_path,
            target=issue.field or issue.code,
        )
    if state.freshness_error_message is not None:
        _add(
            report,
            "knowledge_freshness",
            (
                "Live knowledge evaluation could not be constructed "
                f"[reason=live-evaluation-invalid]: "
                f"{state.freshness_error_message}."
            ),
            path=KNOWLEDGE_INDEX_FILENAME,
            target=state.freshness_error_field or "live-evaluation-invalid",
        )
    _check_verification_receipt(report, state.view)
    if state.view is None or not state.view.ready:
        return
    _check_knowledge_concepts(report, state.view)
    _check_knowledge_reviews(report, state.view)


@contextmanager
def _measure_knowledge_phase(
    durations: dict[str, int],
    name: str,
) -> Iterator[None]:
    started = time.perf_counter()
    try:
        yield
    finally:
        durations[name] = max(
            0,
            round((time.perf_counter() - started) * 1000),
        )


def _proven_nonsemantic_source_paths(
    view: KnowledgeReadView | None,
) -> frozenset[str]:
    if (
        view is None
        or not view.ready
        or view.knowledge is None
        or view.manifest_basis is None
        or view.freshness is None
    ):
        return frozenset()
    states_by_path: dict[str, list[ComputedFreshness]] = {}
    for concept in view.knowledge.concepts:
        expected_scope = _promised_structural_scope(concept)
        if (
            expected_scope is None
            or _promised_evidence_reason(concept, expected_scope) is not None
        ):
            continue
        mapping = view.manifest_basis.page_source_mappings.get(
            concept.document.canonical_path
        )
        if mapping is None or mapping.scope != expected_scope.value:
            continue
        freshness = view.freshness.by_locator.get(concept.locator)
        if freshness is not None:
            states_by_path.setdefault(mapping.source_path, []).append(freshness.state)
    return frozenset(
        source_path
        for source_path, states in states_by_path.items()
        if states
        and all(
            state is ComputedFreshness.NONSEMANTIC_SOURCE_CHANGE for state in states
        )
    )


def _run_report_checks(
    report: LintReport,
    wiki_path: Path,
    src_dir: str,
    strict: bool,
    profiler: _LintProfiler | None,
    inputs: _LintInputs,
    media_size_warn_bytes: int,
    include_plugins: bool,
) -> None:
    with _profile_phase(profiler, "unsupported_sources"):
        _check_unsupported_source_diagnostics(report, inputs.unsupported_sources)
    with _profile_phase(profiler, "links"):
        _check_broken_links(report, wiki_path, inputs.page_index)
        _check_media_references(
            report,
            wiki_path,
            inputs.page_index,
            media_size_warn_bytes=media_size_warn_bytes,
        )
    with _profile_phase(profiler, "generated_diagrams"):
        _check_generated_diagrams(report, wiki_path, inputs.page_index)
    with _profile_phase(profiler, "orphans"):
        _check_orphan_pages(report, wiki_path, inputs.page_index)
    with _profile_phase(profiler, "entities"):
        _check_entity_coverage(report, wiki_path, inputs.deep_inventory)
    with _profile_phase(profiler, "modules"):
        _check_module_coverage(report, wiki_path, inputs.deep_inventory)
    with _profile_phase(profiler, "workflows"):
        _check_workflow_coverage(
            report, wiki_path, inputs.deep_inventory, inputs.page_index
        )
    with _profile_phase(profiler, "flows"):
        _check_flow_coverage(
            report,
            wiki_path,
            inputs.deep_inventory,
            src_dir,
            include_plugins=include_plugins,
        )
    with _profile_phase(profiler, "data_flow"):
        _check_data_flow_diagnostics(
            report,
            wiki_path,
            inputs.deep_inventory,
            src_dir,
            include_plugins=include_plugins,
        )
    with _profile_phase(profiler, "javascript_flow"):
        _check_javascript_flow_diagnostics(
            report,
            inputs.deep_inventory,
            src_dir,
            include_plugins=include_plugins,
        )
    with _profile_phase(profiler, "dependencies"):
        _check_dependency_coverage(
            report,
            wiki_path,
            inputs.deep_inventory,
            src_dir,
            source_snapshot=inputs.source_snapshot,
        )
    with _profile_phase(profiler, "infrastructure"):
        _check_infrastructure_coverage(
            report,
            wiki_path,
            inputs.docker_inventory,
            inputs.yaml_infrastructure_inventory,
        )
    knowledge_state = _KnowledgeLintState()
    if strict:
        knowledge_durations: dict[str, int] = {}
        with (
            _profile_phase(profiler, "knowledge_load"),
            _measure_knowledge_phase(knowledge_durations, "load"),
        ):
            knowledge_state = _load_knowledge_lint_state(wiki_path, inputs)
        with (
            _profile_phase(profiler, "knowledge_freshness"),
            _measure_knowledge_phase(knowledge_durations, "evaluate"),
        ):
            knowledge_state = _evaluate_knowledge_lint_state(
                knowledge_state,
                inputs,
            )
        with (
            _profile_phase(profiler, "knowledge_checks"),
            _measure_knowledge_phase(knowledge_durations, "check"),
        ):
            _check_knowledge_lint(report, knowledge_state)
        if knowledge_state.view is not None:
            _set_knowledge_summary(
                report,
                knowledge_state.view,
                durations=KnowledgePhaseDurations(
                    load_ms=knowledge_durations["load"],
                    evaluate_ms=knowledge_durations["evaluate"],
                    check_ms=knowledge_durations["check"],
                ),
            )
    with _profile_phase(profiler, "strict"):
        if strict:
            _check_required_structure(report, wiki_path)
            _check_sync_manifest(
                report,
                wiki_path,
                src_dir,
                inputs.deep_inventory,
                source_snapshot=inputs.source_snapshot,
                proven_nonsemantic_paths=_proven_nonsemantic_source_paths(
                    knowledge_state.view
                ),
            )
    with _profile_phase(profiler, "plugins"):
        if include_plugins:
            _run_plugin_lint_rules(
                report,
                wiki_path,
                src_dir,
                inputs.deep_inventory,
                inputs.page_index.pages,
            )
    with _profile_phase(profiler, "team"):
        _check_team_issues(report, wiki_path, src_dir, inputs)


def build_report(
    wiki_dir: str | Path,
    src_dir: str = ".",
    *,
    strict: bool = False,
    profiler: _LintProfiler | None = None,
    cache_options: InventoryCacheOptions | None = None,
    parallel_jobs: int = 1,
    helper_cache_dir: str | None = None,
    include_tests: Iterable[str] | None = None,
    media_size_warn_bytes: int = wiki_media.DEFAULT_MEDIA_SIZE_WARN_BYTES,
    job_request: ExtractionJobRequest | None = None,
    plan_reporter: Callable[[ExtractionJobPlan], None] | None = None,
    include_plugins: bool = True,
) -> LintReport:
    """Build a structured lint report without rendering or exiting."""
    wiki_path = Path(wiki_dir)
    report = LintReport(wiki_dir=str(wiki_path), src_dir=src_dir, strict=strict)
    if not wiki_path.exists():
        _add(
            report,
            "wiki_missing",
            f"Directory {wiki_path} does not exist.",
            path=str(wiki_path),
        )
        return report
    inputs = _collect_lint_inputs(
        report,
        wiki_path,
        src_dir,
        profiler,
        cache_options,
        parallel_jobs,
        helper_cache_dir,
        include_tests,
        job_request,
        plan_reporter,
        include_plugins,
    )
    if inputs is None:
        return report
    _run_report_checks(
        report,
        wiki_path,
        src_dir,
        strict,
        profiler,
        inputs,
        media_size_warn_bytes,
        include_plugins,
    )
    return report


def report_to_dict(report: LintReport, *, include_execution: bool = False) -> dict:
    payload = {
        "wiki_dir": report.wiki_dir,
        "src_dir": report.src_dir,
        "strict": report.strict,
        "ok": report.passed,
        "issue_count": report.issue_count,
        "issues": [asdict(issue) for issue in report.issues],
        "diagnostics": [asdict(diagnostic) for diagnostic in report.diagnostics],
    }
    if report.knowledge_summary is not None:
        payload["knowledge_summary"] = report.knowledge_summary.report_payload()
    if include_execution:
        payload["execution"] = {"extractor_jobs": report.extraction_job_plan.to_dict()}
    return payload


def _profile_report_to_dict(
    report: LintReport, profiler: _LintProfiler, *, include_cache: bool = False
) -> dict:
    payload = report_to_dict(report, include_execution=True)
    payload["diagnostics"] = [asdict(diagnostic) for diagnostic in report.diagnostics]
    payload["profile"] = profiler.to_dict()
    if include_cache and report.cache_stats is not None:
        payload["cache"] = report.cache_stats.to_dict()
    return payload


def _add_extractor_failures(report: LintReport, inventory_result) -> None:
    for status in inventory_result.failed:
        detail = f": {status.message}" if status.message else ""
        _add(
            report,
            "extractor_failure",
            f"{status.language} extraction failed{detail}",
            target=status.language,
        )


def render_text(report: LintReport) -> str:
    grouped = report.by_category()
    diagnostic_groups: dict[str, list[LintIssue]] = {}
    for diagnostic in report.diagnostics:
        diagnostic_groups.setdefault(diagnostic.category, []).append(diagnostic)
    lines: list[str] = [f"Linting Wiki at: {report.wiki_dir}"]

    if grouped.get("wiki_missing"):
        for issue in grouped["wiki_missing"]:
            lines.append(f"Error: {issue.message}")
        lines.append(f"❌ Lint found {report.issue_count} issue(s).")
        return "\n".join(lines) + "\n"

    def emit_group(
        category: str,
        empty: str,
        found: str,
        prefix: str = "  ⚠️  ",
        *,
        only_if_present: bool = False,
    ) -> None:
        issues = grouped.get(category, []) + diagnostic_groups.get(category, [])
        if issues:
            for issue in issues:
                lines.append(f"{prefix}{issue.message}")
            lines.append(f"  {found.format(count=len(issues))}")
            lines.append("")
        elif not only_if_present:
            lines.append(f"  ✅ {empty}")
            lines.append("")

    def emit_knowledge_group(category: str, found: str) -> None:
        issues = grouped.get(category, [])
        diagnostics = diagnostic_groups.get(category, [])
        if not issues and not diagnostics:
            return
        for issue in issues:
            lines.append(f"  ❌ {issue.message}")
        for diagnostic in diagnostics:
            marker = "INFO" if diagnostic.severity == "info" else "⚠️ "
            lines.append(f"  {marker} {diagnostic.message}")
        lines.append(f"  {found.format(count=len(issues) + len(diagnostics))}")
        lines.append("")

    if grouped.get("extractor_failure"):
        emit_group(
            "extractor_failure",
            "Source extraction completed.",
            "Found {count} source extraction failure(s).",
            prefix="  ❌ ",
        )
    emit_group(
        "broken_links",
        "No broken links.",
        "Found {count} broken link(s).",
        prefix="  ❌ ",
    )
    emit_group(
        "media_link_broken",
        "No broken media links.",
        "Found {count} broken media link(s).",
        prefix="  ❌ ",
    )
    emit_group(
        "media_missing_alt_text",
        "No media alt-text warnings.",
        "Found {count} media alt-text warning(s).",
        only_if_present=True,
    )
    emit_group(
        "media_oversize",
        "No oversized media assets.",
        "Found {count} oversized media asset warning(s).",
        only_if_present=True,
    )
    emit_group(
        "media_orphan",
        "No unreferenced media assets.",
        "Found {count} unreferenced media asset warning(s).",
        only_if_present=True,
    )
    emit_group(
        "media_outside_assets",
        "No media outside assets/.",
        "Found {count} media outside assets/ warning(s).",
        only_if_present=True,
    )
    emit_group(
        "asset_unrecognized_type",
        "No unrecognized asset file types.",
        "Found {count} unrecognized asset file type warning(s).",
        only_if_present=True,
    )
    emit_group(
        "media_symlink_escape",
        "No symlinked media escapes.",
        "Found {count} symlinked media escape warning(s).",
        only_if_present=True,
    )
    emit_group("orphan_pages", "No orphan pages.", "Found {count} orphan page(s).")
    emit_group(
        "undocumented_classes",
        "All classes documented.",
        "Found {count} undocumented class(es).",
    )
    emit_group(
        "stale_entities",
        "No stale entity pages.",
        "Found {count} stale entity page(s).",
    )
    emit_group(
        "undocumented_modules",
        "All modules documented.",
        "Found {count} undocumented module(s).",
    )
    emit_group(
        "stale_modules", "No stale module pages.", "Found {count} stale module page(s)."
    )
    emit_group(
        "broken_workflow_links",
        "No broken workflow links.",
        "Found {count} broken workflow link(s).",
    )
    emit_group(
        "missing_workflows",
        "All detected workflows documented.",
        "Found {count} missing workflow(s).",
    )
    emit_group(
        "undocumented_infrastructure",
        "All infrastructure files documented.",
        "Found {count} undocumented infrastructure file(s).",
    )
    emit_group(
        "stale_infrastructure",
        "No stale infrastructure pages.",
        "Found {count} stale infrastructure page(s).",
    )

    # Architecture-page checks are only meaningful when the pages exist, so they
    # stay quiet (no all-clear line) otherwise. Cycles / undeclared / unused are
    # warnings; stale architecture pages are hard issues.
    emit_group(
        "stale_dependencies",
        "No stale architecture pages.",
        "Found {count} stale architecture page(s).",
        prefix="  ❌ ",
        only_if_present=True,
    )
    emit_group(
        "dependency_cycles",
        "No import cycles.",
        "Found {count} import cycle(s).",
        only_if_present=True,
    )
    emit_group(
        "undeclared_dependencies",
        "No undeclared dependencies.",
        "Found {count} undeclared dependency(ies).",
        only_if_present=True,
    )
    emit_group(
        "unused_dependencies",
        "No unused dependencies.",
        "Found {count} unused dependency(ies).",
        only_if_present=True,
    )
    emit_group(
        "generated_diagram_bloat",
        "No generated diagram bloat.",
        "Found {count} generated diagram warning(s).",
        only_if_present=True,
    )
    emit_group(
        "unsupported_sources",
        "No unsupported source files.",
        "Found {count} unsupported source diagnostic(s).",
        only_if_present=True,
    )
    emit_group(
        "javascript_flow_unsupported",
        "No unsupported JavaScript flow surfaces.",
        "Found {count} JavaScript flow diagnostic(s).",
        only_if_present=True,
    )

    if report.strict:
        emit_knowledge_group(
            "knowledge_schema",
            "Found {count} knowledge schema issue(s).",
        )
        emit_knowledge_group(
            "knowledge_projection",
            "Found {count} knowledge projection issue(s).",
        )
        emit_knowledge_group(
            "knowledge_governance",
            "Found {count} knowledge governance issue(s).",
        )
        emit_knowledge_group(
            "knowledge_review",
            "Found {count} human review issue(s).",
        )
        emit_knowledge_group(
            "knowledge_verification",
            "Found {count} machine verification issue(s).",
        )
        emit_knowledge_group(
            "knowledge_snapshot",
            "Found {count} knowledge snapshot issue(s).",
        )
        emit_knowledge_group(
            "knowledge_evidence",
            "Found {count} knowledge evidence issue(s).",
        )
        emit_knowledge_group(
            "knowledge_freshness",
            "Found {count} knowledge freshness finding(s).",
        )
        emit_group(
            "wiki_structure",
            "Required wiki structure present.",
            "Found {count} wiki structure issue(s).",
        )
        emit_group(
            "sync_manifest",
            "Sync manifest is fresh.",
            "Found {count} sync manifest issue(s).",
        )

    emit_group(
        "team_config",
        "Team config valid or not configured.",
        "Found {count} team config issue(s).",
    )
    emit_group(
        "team_plugin_requirement",
        "Team plugin requirements satisfied.",
        "Found {count} team plugin requirement issue(s).",
    )
    emit_group(
        "team_conventions",
        "Team conventions satisfied.",
        "Found {count} team convention issue(s).",
    )
    emit_group(
        "team_canonical_naming",
        "Team canonical naming satisfied.",
        "Found {count} team canonical naming issue(s).",
    )

    # ── Summary ───────────────────────────────────────────────────────
    if report.passed:
        lines.append("✅ Lint passed: wiki is fully consistent.")
    else:
        lines.append(f"❌ Lint found {report.issue_count} issue(s).")
    if report.cache_stats is not None:
        lines.extend(format_cache_stats(report.cache_stats))
    return "\n".join(lines) + "\n"


def render_markdown(report: LintReport) -> str:
    status = "passed" if report.passed else "failed"
    lines = [
        "# LLM Wiki Validation Report",
        "",
        f"- Wiki: `{report.wiki_dir}`",
        f"- Source: `{report.src_dir}`",
        f"- Mode: `{'strict' if report.strict else 'normal'}`",
        f"- Result: **{status}**",
        f"- Issues: {report.issue_count}",
        f"- Diagnostics: {len(report.diagnostics)}",
        "",
    ]
    if not report.issues and not report.diagnostics:
        lines.append("No issues found.")
        return "\n".join(lines) + "\n"

    if report.issues:
        lines.append("## Issues")
        lines.append("")
        for issue in report.issues:
            location = f" (`{issue.path}`)" if issue.path else ""
            lines.append(f"- **{issue.category}**{location}: {issue.message}")
        lines.append("")
    else:
        lines.append("No issues found.")
        lines.append("")

    if report.diagnostics:
        lines.append("## Diagnostics")
        lines.append("")
        for diagnostic in report.diagnostics:
            location = f" (`{diagnostic.path}`)" if diagnostic.path else ""
            severity = diagnostic.severity or "warning"
            lines.append(
                f"- **{diagnostic.category}**{location} [{severity}]: "
                f"{diagnostic.message}"
            )
    return "\n".join(lines) + "\n"


def run(args):
    wiki_dir = Path(args.wiki_dir)
    src_dir = getattr(args, "src_dir", ".")
    strict = bool(getattr(args, "strict", False))
    profile = bool(getattr(args, "profile", False))
    cache_stats = bool(getattr(args, "cache_stats", False))
    allow_external_src = bool(getattr(args, "allow_external_src", False))
    validate_path(str(wiki_dir), "--wiki-dir")
    src_root = validate_source_root(
        src_dir, "--src-dir", allow_external=allow_external_src
    )
    if allow_external_src:
        src_dir = str(src_root)

    profiler = _LintProfiler() if profile else None
    cache_options = InventoryCacheOptions(
        enabled=not bool(getattr(args, "no_cache", False)),
        rebuild=bool(getattr(args, "rebuild_cache", False)),
        cache_dir=getattr(args, "cache_dir", None),
        stats_enabled=cache_stats,
    )
    job_request = extraction_job_request_from_args(args)
    report = build_report(
        wiki_dir,
        src_dir,
        strict=strict,
        profiler=profiler,
        cache_options=cache_options,
        parallel_jobs=getattr(args, "jobs", 1),
        helper_cache_dir=getattr(args, "helper_cache_dir", None),
        include_tests=getattr(args, "include_tests", None),
        media_size_warn_bytes=(
            getattr(args, "media_size_warn_bytes", None)
            or wiki_media.DEFAULT_MEDIA_SIZE_WARN_BYTES
        ),
        job_request=job_request,
        plan_reporter=print_extraction_job_plan,
    )
    if report.count("extractor_failure") and not profile:
        for issue in report.by_category().get("extractor_failure", []):
            print(f"Error: {issue.message}", file=sys.stderr)
        sys.exit(1)
    if profile and profiler is not None:
        print(
            json.dumps(
                _profile_report_to_dict(report, profiler, include_cache=cache_stats),
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(render_text(report), end="")

    if strict:
        try:
            from ..services.metrics import record_validation_event

            record_validation_event(
                command="lint",
                passed=report.passed,
                issue_count=report.issue_count,
                strict=True,
                duration_ms=None,
                wiki_dir=str(wiki_dir),
                src_dir=src_dir,
                knowledge_summary=(
                    None
                    if report.knowledge_summary is None
                    else report.knowledge_summary.aggregate_payload()
                ),
            )
        except Exception:  # noqa: BLE001,S110 - metrics are best-effort
            pass

    if not report.passed:
        sys.exit(1)
