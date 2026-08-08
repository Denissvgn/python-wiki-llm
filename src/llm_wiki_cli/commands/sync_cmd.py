"""Incremental wiki sync — update only pages whose source has changed.

Workflow:
    1. Classify the wiki lifecycle, loading a managed manifest, safely seeding a
       legacy wiki with ``index.md``, or routing pristine/partial targets to
       bootstrap/migration before source extraction.
    2. Hash every source file in the current AST inventory.
    3. Compute a diff: new / changed / unchanged / removed files, moved classes.
    4. Apply changes surgically: regenerate pages for new/changed files, add a
       deprecation warning to pages whose source was removed, skip everything else.
    5. Rebuild index.md and append a log entry if anything changed.
    6. Save the updated manifest.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional

from ..config import validate_path, validate_source_root
from ..services.api_contracts import (
    ApiContractError,
    attach_routes_to_entry_points,
    build_api_contracts,
    load_openapi_document,
    render_api_contracts_markdown,
)
from ..services.data_flow import (
    analyze_data_flow,
    analyze_data_flow_detailed,
    build_data_flow_context,
)
from ..services.dependencies import (
    analyze_dependencies,
    build_dependency_observations,
    build_external_dependency_observations,
)
from ..services.entrypoints import (
    build_flow,
    build_flow_detailed,
    entry_points_from_detailed_observations,
    get_detailed_entry_points,
    read_console_scripts,
)
from ..services.extraction_jobs import (
    ExtractionJobPlan,
    ExtractionJobRequest,
    extraction_job_request_from_args,
    print_extraction_job_plan,
)
from ..services.inventory_cache import (
    InventoryCacheOptions,
    InventoryCacheStats,
    format_cache_stats,
)
from ..services.infrastructure_inventory import (
    get_yaml_infrastructure_inventory,
    infrastructure_display_label,
)
from ..services.infrastructure_sync import (
    InfrastructureSyncError,
    InfrastructureSyncPlan,
    build_infrastructure_sync_plan,
    with_infrastructure_generation_input,
)
from ..services.io import read_md, write_md
from ..services.knowledge_artifacts import (
    ArtifactWriteState,
    KnowledgeCommitResult,
)
from ..services.knowledge_envelope import RepositoryEvidence
from ..services.knowledge_evidence import hash_file
from ..services.knowledge_evidence import (
    is_valid_sha256,
)
from ..services.knowledge_evidence import semantic_hash_for_file
from ..services.knowledge_governance import (
    GOVERNANCE_FILENAME,
    GovernanceError,
    load_governance,
)
from ..services.knowledge_orchestration import (
    RUNTIME_GENERATION_OPTION_DEFAULTS,
    RuntimeKnowledgeInputs,
    collect_runtime_repository_evidence,
    committed_governance_bundle_id,
    finalize_runtime_knowledge,
    runtime_generation_options,
)
from ..services.markdown_sections import (
    format_table_row as _service_format_table_row,
    is_placeholder_description as _service_is_placeholder_description,
    is_table_separator as _service_is_table_separator,
    normalize_markdown as _service_normalize_markdown,
    preserve_index_custom_sections as _service_preserve_index_custom_sections,
    preserve_level_two_section_exact as _service_preserve_level_two_section_exact,
    preserve_table_description_cells as _service_preserve_table_description_cells,
    replace_section_body as _service_replace_section_body,
    section_body as _service_section_body,
    section_bounds as _service_section_bounds,
    semantic_table_key as _service_semantic_table_key,
    should_preserve_semantic_value as _service_should_preserve_semantic_value,
    split_table_row as _service_split_table_row,
    table_description_cells as _service_table_description_cells,
    trim_blank_lines as _service_trim_blank_lines,
)
from ..services.module_maps import build_module_dependency_maps
from ..services.paths import is_test_source_path
from ..services.source_snapshot import (
    SourceSnapshot,
    build_source_snapshot,
    format_unsupported_source_summary,
    unsupported_source_summary,
)
from ..services.sync_manifest import (
    EVIDENCE_NOT_RECORDED,
    MANIFEST_FILENAME,
    MANIFEST_REPAIR_UNAVAILABLE,
    MANIFEST_STATE_UNAVAILABLE,
    MANIFEST_VERSION,  # noqa: F401 - compatibility re-export
    SyncManifest,
    retained_concept_page_paths,
)
from ..services.sync_analysis import SyncDiff, compute_sync_diff as _compute_diff
from ..services.wiki_lifecycle import (
    WikiLifecycleState,
    bootstrap_guidance,
    classify_wiki_lifecycle,
    migration_guidance,
)
from ..services.section_ownership import (
    SemanticMergeResult,
    merge_entity_semantics as _service_merge_entity_semantics,
    merge_module_semantics as _service_merge_module_semantics,
    merge_semantic_markdown as _service_merge_semantic_markdown,
    replace_generated_section as _service_replace_generated_section,
)
from ..services.wiki_surface import (
    PageKind,
    WikiSurfaceError,
    canonical_path,
    collect_wiki_pages,
    mcp_uri,
)
from ..services.wiki_surface_index import evaluate_surface_index
from ..services.bootstrap_runtime import (
    _build_entity_relationship_summary_map,
    _build_relationships,
    _generate_dependencies_md,
    _generate_entity_md,
    _generate_flow_md,
    _generate_index_md,
    _generate_load_order_md,
    _generate_module_md,
    _generate_infrastructure_md,
    _generated_diagram_style,
    _module_name_from_path,
    _page_name_for_module,
    build_entity_occurrence_page_map,
    build_entity_page_map,
    build_module_page_map,
)
from ..services.extraction_service import (
    InventoryResult,
    get_call_graph,
    get_inventory_result,
    get_docker_inventory,
    print_inventory_failures,
    resolve_call_observations,
    resolve_call_edges,
)

# Historical private aliases are imported by downstream integrations.
_hash_file = hash_file
_semantic_hash_for_file = semantic_hash_for_file

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_SYNC_AFFECTED_FILES = 50
MAX_SYNC_AFFECTED_RATIO = 0.30
MIN_SOURCES_FOR_RATIO_GUARD = 10
MAX_INFRASTRUCTURE_AFFECTED_FILES = MAX_SYNC_AFFECTED_FILES
MAX_INFRASTRUCTURE_AFFECTED_RATIO = MAX_SYNC_AFFECTED_RATIO
MIN_INFRASTRUCTURE_SOURCES_FOR_RATIO_GUARD = MIN_SOURCES_FOR_RATIO_GUARD
INITIALIZABLE_SURFACES = ("flows", "dependencies", "api-contracts")
_SURFACE_POLICY_KEYS = {
    "flows": "flows",
    "dependencies": "dependencies",
    "api-contracts": "api_contracts",
}
MAX_SURFACE_CREATED_PAGES = MAX_SYNC_AFFECTED_FILES
MAX_SURFACE_CREATED_RATIO = MAX_SYNC_AFFECTED_RATIO
MIN_PAGES_FOR_SURFACE_RATIO_GUARD = MIN_SOURCES_FOR_RATIO_GUARD
_FLOW_CATEGORY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_DEPRECATION_HEADER = (
    "> ⚠️ **Stale:** Source no longer found in codebase. "
    "Run `llm-wiki lint` to audit.\n\n"
)


def _cache_options_from_args(args) -> InventoryCacheOptions:
    cache_stats = bool(getattr(args, "cache_stats", False))
    return InventoryCacheOptions(
        enabled=not bool(getattr(args, "no_cache", False)),
        rebuild=bool(getattr(args, "rebuild_cache", False)),
        cache_dir=getattr(args, "cache_dir", None),
        stats_enabled=cache_stats,
    )


def _print_cache_stats(stats: InventoryCacheStats | None, *, enabled: bool) -> None:
    if not enabled or stats is None:
        return
    for line in format_cache_stats(stats):
        print(line)


def _is_valid_manifest_hash(value: object) -> bool:
    return is_valid_sha256(value)


def _invalid_manifest_hash_paths(manifest: "SyncManifest") -> list[str]:
    return [
        filepath
        for filepath, info in manifest.sources.items()
        if not _is_valid_manifest_hash(info.get("hash"))
    ]


def _build_manifest_from_inventory(
    inventory: dict,
    src_dir: str,
    *,
    entity_page_cache: dict[tuple[str, str], str] | None = None,
    entity_occurrence_page_cache: dict[tuple[str, str, int], str] | None = None,
    module_page_map: dict[str, str] | None = None,
    surfaces: Mapping[str, Mapping] | None = None,
    generation_inputs: Mapping[str, object] | None = None,
    previous_manifest: SyncManifest | None = None,
    retained_page_paths: Iterable[str] | None = None,
    unknown_evidence_reason: str = EVIDENCE_NOT_RECORDED,
    source_content_hashes: Mapping[str, str] | None = None,
) -> "SyncManifest":
    if entity_page_cache is None:
        _, _, entity_page_cache = _collision_maps(inventory, src_dir)
    if module_page_map is None:
        module_page_map = build_module_page_map(inventory)
    if entity_occurrence_page_cache is None:
        entity_occurrence_page_cache = build_entity_occurrence_page_map(
            inventory, module_page_map
        )
    return SyncManifest.build_from_inventory(
        inventory,
        src_dir,
        entity_page_cache,
        module_page_map,
        entity_occurrence_page_cache=entity_occurrence_page_cache,
        surfaces=surfaces,
        generation_inputs=generation_inputs,
        previous_manifest=previous_manifest,
        retained_page_paths=retained_page_paths,
        unknown_evidence_reason=unknown_evidence_reason,
        source_content_hashes=source_content_hashes,
    )


def _normalize_md(text: str) -> str:
    return _service_normalize_markdown(text)


def _write_md_if_changed(path: Path, text: str) -> str:
    """Write markdown only when content changes.

    Returns ``created``, ``updated``, or ``unchanged``.
    """
    normalized = _normalize_md(text)
    if path.exists():
        existing = _normalize_md(read_md(path))
        if existing == normalized:
            return "unchanged"
        write_md(path, normalized)
        return "updated"
    write_md(path, normalized)
    return "created"


def _section_bounds(lines: list[str], heading: str) -> tuple[int, int, int] | None:
    """Return ``(heading_index, body_start, body_end)`` for a level-2 heading."""
    return _service_section_bounds(lines, heading)


def _trim_blank_lines(lines: list[str]) -> list[str]:
    return _service_trim_blank_lines(lines)


def _section_body(markdown: str, heading: str) -> str | None:
    return _service_section_body(markdown, heading)


def _replace_section_body(markdown: str, heading: str, body: str) -> str:
    return _service_replace_section_body(markdown, heading, body)


def _preserve_level_two_section_exact(
    existing: str, generated: str, heading: str
) -> str:
    """Splice a human-owned level-two section without normalizing its body."""
    return _service_preserve_level_two_section_exact(existing, generated, heading)


def _is_placeholder_description(value: str | None) -> bool:
    return _service_is_placeholder_description(value)


def _should_preserve_semantic_value(
    existing: str | None,
    generated: str | None,
    old_generated: str | None,
) -> bool:
    return _service_should_preserve_semantic_value(
        existing,
        generated,
        old_generated,
    )


def _split_table_row(line: str) -> list[str]:
    return _service_split_table_row(line)


def _format_table_row(cells: list[str]) -> str:
    return _service_format_table_row(cells)


def _is_table_separator(cells: list[str]) -> bool:
    return _service_is_table_separator(cells)


def _semantic_table_key(cell: str) -> str:
    return _service_semantic_table_key(cell)


def _table_description_cells(markdown: str, heading: str) -> dict[str, str]:
    return _service_table_description_cells(markdown, heading)


def _preserve_table_description_cells(
    markdown: str,
    heading: str,
    descriptions: dict[str, str],
    old_descriptions: dict[str, str] | None = None,
) -> tuple[str, int]:
    return _service_preserve_table_description_cells(
        markdown,
        heading,
        descriptions,
        old_descriptions,
    )


def _merge_semantic_markdown(
    existing: str,
    generated: str,
    table_headings: tuple[str, ...],
    *,
    old_description: str | None = None,
    old_table_descriptions: dict[str, dict[str, str]] | None = None,
) -> SemanticMergeResult:
    """Preserve human-written semantic fields in regenerated wiki markdown."""
    return _service_merge_semantic_markdown(
        existing,
        generated,
        table_headings,
        old_description=old_description,
        old_table_descriptions=old_table_descriptions,
    )


def _merge_entity_semantics(
    existing: str,
    generated: str,
    old_semantics: dict | None = None,
) -> SemanticMergeResult:
    return _service_merge_entity_semantics(existing, generated, old_semantics)


def _merge_module_semantics(
    existing: str,
    generated: str,
    old_semantics: dict | None = None,
) -> SemanticMergeResult:
    return _service_merge_module_semantics(existing, generated, old_semantics)


# ``SyncManifest`` and its manifest constants are imported above and intentionally
# remain module attributes for one compatibility cycle.


# ── Diff ──────────────────────────────────────────────────────────────────────


def _governance_moves_for_sync(
    diff: SyncDiff,
    manifest: SyncManifest,
    *,
    entity_page_cache: Mapping[tuple[str, str], str],
) -> dict[str, str]:
    """Return only unambiguous old-to-current concept locator moves.

    Diff detection is the source of authority for automatic carry-forward.
    Multiple candidates for one prior route are intentionally omitted: a
    collision expansion is not enough evidence to decide which new concept
    should inherit the old UID and must be handled by ``knowledge move``.
    """

    candidates: dict[str, set[str]] = {}

    def add(kind: PageKind, old_page: str, new_page: str) -> None:
        if old_page == new_page:
            return
        try:
            old_locator = mcp_uri(kind, old_page)
            new_locator = mcp_uri(kind, new_page)
        except WikiSurfaceError:
            return
        candidates.setdefault(old_locator, set()).add(new_locator)

    for (_entity_name, _filepath), (old_page, new_page) in sorted(
        diff.renamed_entity_pages.items()
    ):
        add(PageKind.ENTITIES, old_page, new_page)

    for _filepath, (old_page, new_page) in sorted(
        diff.renamed_module_pages.items()
    ):
        add(PageKind.MODULES, old_page, new_page)

    for entity_name, (old_filepath, new_filepath) in sorted(
        diff.moved_entities.items()
    ):
        old_source = manifest.sources.get(old_filepath)
        if not isinstance(old_source, Mapping):
            continue
        old_entity_pages = old_source.get("entity_pages")
        old_page = (
            str(old_entity_pages[entity_name])
            if isinstance(old_entity_pages, Mapping)
            and entity_name in old_entity_pages
            else entity_name
        )
        new_page = entity_page_cache.get((entity_name, new_filepath))
        if new_page is not None:
            add(PageKind.ENTITIES, old_page, new_page)

    one_target_per_source = {
        old_locator: next(iter(targets))
        for old_locator, targets in sorted(candidates.items())
        if len(targets) == 1
    }
    source_count_by_target = Counter(one_target_per_source.values())
    return {
        old_locator: target_locator
        for old_locator, target_locator in one_target_per_source.items()
        if source_count_by_target[target_locator] == 1
    }


def _affected_source_files(diff: SyncDiff) -> set[str]:
    affected = (
        set(diff.new_files)
        | set(diff.changed_files)
        | set(diff.metadata_only_files)
        | set(diff.removed_files)
    )
    for old_path, new_path in diff.moved_entities.values():
        affected.add(old_path)
        affected.add(new_path)
    for _, filepath in diff.renamed_entity_pages:
        affected.add(filepath)
    affected.update(diff.renamed_module_pages)
    return affected


def _large_diff_message(diff: SyncDiff, manifest: SyncManifest) -> str | None:
    affected_count = len(_affected_source_files(diff))
    manifest_count = len(manifest.sources)
    if affected_count > MAX_SYNC_AFFECTED_FILES:
        return (
            f"sync would affect {affected_count} source file(s), "
            f"which exceeds the safety limit of {MAX_SYNC_AFFECTED_FILES}."
        )
    if manifest_count >= MIN_SOURCES_FOR_RATIO_GUARD:
        affected_ratio = affected_count / manifest_count
        if affected_ratio > MAX_SYNC_AFFECTED_RATIO:
            percent = int(affected_ratio * 100)
            limit_percent = int(MAX_SYNC_AFFECTED_RATIO * 100)
            return (
                f"sync would affect {affected_count} of {manifest_count} manifest source file(s) "
                f"({percent}%), which exceeds the {limit_percent}% safety limit."
            )
    return None


def _large_infrastructure_message(plan: InfrastructureSyncPlan) -> str | None:
    affected_count = plan.affected_count
    prior_count = len(plan.prior_sources)
    if affected_count > MAX_INFRASTRUCTURE_AFFECTED_FILES:
        return (
            "sync would affect "
            f"{affected_count} infrastructure source(s), which exceeds the safety "
            f"limit of {MAX_INFRASTRUCTURE_AFFECTED_FILES}."
        )
    if prior_count >= MIN_INFRASTRUCTURE_SOURCES_FOR_RATIO_GUARD:
        affected_ratio = affected_count / prior_count
        if affected_ratio > MAX_INFRASTRUCTURE_AFFECTED_RATIO:
            percent = int(affected_ratio * 100)
            limit_percent = int(MAX_INFRASTRUCTURE_AFFECTED_RATIO * 100)
            return (
                "sync would affect "
                f"{affected_count} of {prior_count} infrastructure source(s) "
                f"({percent}%), which exceeds the {limit_percent}% safety limit."
            )
    return None


# ── Apply ─────────────────────────────────────────────────────────────────────


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    metadata_only: int = 0
    skipped: int = 0
    deprecated: int = 0
    preserved_semantic: int = 0


def _collision_maps(
    inventory: dict, src_dir: str
) -> tuple[set[str], set[str], dict[tuple[str, str], str]]:
    """Return (colliding_stems, colliding_cls, entity_page_name_cache).

    Uses :func:`build_entity_page_map` for collision-aware entity names.
    The first two sets are retained for API compatibility but are no
    longer consumed directly.
    """
    entity_page_cache = build_entity_page_map(inventory)
    return set(), set(), entity_page_cache


@dataclass(frozen=True)
class _ApplyDiffContext:
    wiki_dir: Path
    src_dir: str
    inventory: dict
    manifest: SyncManifest
    entity_page_cache: dict[tuple[str, str], str]
    entity_occurrence_page_cache: dict[tuple[str, str, int], str]
    module_page_map: dict[str, str]
    relationships: dict
    generated_sections: "_GeneratedSectionContext"
    metadata_only_files: set[str]
    current_entity_pages: set[str]
    current_module_pages: set[str]
    preserve_semantic: bool


@dataclass(frozen=True)
class _GeneratedSectionContext:
    entity_relationship_summaries: Mapping[tuple[str, str], Mapping]
    module_dependency_maps: dict[str, dict] | None = None
    dependency_analysis: dict | None = None


def _empty_generated_section_context() -> "_GeneratedSectionContext":
    return _GeneratedSectionContext(entity_relationship_summaries={})


def _has_existing_module_dependency_sections(wiki_dir: Path) -> bool:
    modules_dir = wiki_dir / "modules"
    if not modules_dir.exists():
        return False
    for path in sorted(modules_dir.glob("*.md")):
        if _section_body(read_md(path), "Local dependency map") is not None:
            return True
    return False


def _build_generated_section_context(
    options: "_SyncRunOptions",
    inventory: dict,
    *,
    call_edges: list[dict] | None = None,
    dependency_analysis: dict | None = None,
) -> "_GeneratedSectionContext":
    call_edges = call_edges if call_edges is not None else resolve_call_edges(inventory)
    entity_relationship_summaries = _build_entity_relationship_summary_map(
        inventory,
        call_edges,
    )
    module_dependency_maps = None
    if _has_existing_module_dependency_sections(options.wiki_dir):
        dependency_analysis = dependency_analysis or analyze_dependencies(
            inventory, options.src_dir
        )
        module_dependency_maps = build_module_dependency_maps(dependency_analysis)
    else:
        dependency_analysis = None
    return _GeneratedSectionContext(
        entity_relationship_summaries=entity_relationship_summaries,
        module_dependency_maps=module_dependency_maps,
        dependency_analysis=dependency_analysis,
    )


def _target_entities_for_diff(diff: SyncDiff, inventory: dict) -> set[tuple[str, str]]:
    target_entities = {
        (cls["name"], filepath)
        for filepath in diff.new_files + diff.changed_files + diff.metadata_only_files
        if filepath in inventory
        for cls in inventory[filepath].get("classes", [])
    }
    for cls_name, (_, new_path) in diff.moved_entities.items():
        if new_path in inventory:
            target_entities.add((cls_name, new_path))
    target_entities.update(diff.renamed_entity_pages)
    for filepath in diff.renamed_module_pages:
        if filepath in inventory:
            for cls in inventory[filepath].get("classes", []):
                target_entities.add((cls["name"], filepath))
    return target_entities


def _relationships_for_targets(
    inventory: dict,
    module_page_map: dict[str, str],
    target_entities: set[tuple[str, str]],
) -> dict:
    if not target_entities:
        return {}
    print(
        f"Building relationships for {len(target_entities)} affected entity target(s)...",
        flush=True,
    )
    relationships = _build_relationships(
        inventory,
        module_page_map,
        target_entities=target_entities,
    )
    print(
        f"Built affected relationships: {sum(len(v) for v in relationships.values())}.",
        flush=True,
    )
    return relationships


def _refresh_files_for_diff(diff: SyncDiff) -> list[str]:
    return list(
        dict.fromkeys(
            diff.new_files
            + diff.changed_files
            + diff.metadata_only_files
            + [filepath for _, filepath in diff.renamed_entity_pages]
            + list(diff.renamed_module_pages)
        )
    )


def _file_entity_page_map(
    filepath: str,
    file_data: dict,
    entity_page_cache: dict[tuple[str, str], str],
    entity_occurrence_page_cache: dict[tuple[str, str, int], str] | None = None,
) -> dict[str, str]:
    page_map: dict[str, str] = {}
    seen_names: dict[str, int] = {}
    for cls in file_data.get("classes", []):
        name = cls["name"]
        seen_names[name] = seen_names.get(name, 0) + 1
        page_name = entity_page_cache[(name, filepath)]
        if entity_occurrence_page_cache is not None:
            page_name = entity_occurrence_page_cache.get(
                (name, filepath, seen_names[name]),
                page_name,
            )
        page_map.setdefault(name, page_name)
    return page_map


def _move_renamed_entity_page(
    wiki_dir: Path,
    rename: tuple[str, str] | None,
    current_entity_pages: set[str],
) -> None:
    if not rename:
        return
    old_page_name, new_page_name = rename
    old_entity_path = wiki_dir / "entities" / f"{old_page_name}.md"
    new_entity_path = wiki_dir / "entities" / f"{new_page_name}.md"
    if old_entity_path == new_entity_path or not old_entity_path.exists():
        return
    if not new_entity_path.exists():
        old_entity_path.replace(new_entity_path)
        print(f"  RENAME entity: {old_page_name} -> {new_page_name}")
    elif old_page_name not in current_entity_pages:
        old_entity_path.unlink()
        print(f"  REMOVE stale entity page: {old_page_name}")


def _move_renamed_module_page(
    wiki_dir: Path,
    rename: tuple[str, str] | None,
    current_module_pages: set[str],
) -> None:
    if not rename:
        return
    old_page_name, new_page_name = rename
    old_module_path = wiki_dir / "modules" / f"{old_page_name}.md"
    new_module_path = wiki_dir / "modules" / f"{new_page_name}.md"
    if old_module_path == new_module_path or not old_module_path.exists():
        return
    if not new_module_path.exists():
        old_module_path.replace(new_module_path)
        print(f"  RENAME module: {old_page_name} -> {new_page_name}")
    elif old_page_name not in current_module_pages:
        old_module_path.unlink()
        print(f"  REMOVE stale module page: {old_page_name}")


def _record_page_write(
    result: SyncResult,
    page_kind: str,
    page_name: str,
    write_state: str,
    *,
    metadata_only: bool,
) -> None:
    if write_state == "created":
        result.created += 1
        print(f"  CREATE {page_kind}: {page_name}")
    elif write_state == "updated":
        if metadata_only:
            result.metadata_only += 1
            print(f"  METADATA {page_kind}: {page_name}")
        else:
            result.updated += 1
            print(f"  UPDATE {page_kind}: {page_name}")
    else:
        result.skipped += 1
        print(f"  SKIP {page_kind} (unchanged): {page_name}")


def _merge_entity_page(
    ctx: _ApplyDiffContext,
    entity_path: Path,
    generated: str,
    old_generated_semantics: dict,
    cls_name: str,
    result: SyncResult,
) -> SemanticMergeResult:
    merge_result = SemanticMergeResult(generated)
    if ctx.preserve_semantic and entity_path.exists():
        old_entity_semantics = (
            old_generated_semantics.get("entities", {}).get(cls_name)
            if isinstance(old_generated_semantics, dict)
            else None
        )
        merge_result = _merge_entity_semantics(
            read_md(entity_path),
            generated,
            old_entity_semantics,
        )
        result.preserved_semantic += merge_result.preserved
    return merge_result


def _merge_module_page(
    ctx: _ApplyDiffContext,
    module_path: Path,
    generated: str,
    old_generated_semantics: dict,
    result: SyncResult,
) -> SemanticMergeResult:
    merge_result = SemanticMergeResult(generated)
    if ctx.preserve_semantic and module_path.exists():
        old_module_semantics = (
            old_generated_semantics.get("module")
            if isinstance(old_generated_semantics, dict)
            else None
        )
        merge_result = _merge_module_semantics(
            read_md(module_path),
            generated,
            old_module_semantics,
        )
        result.preserved_semantic += merge_result.preserved
    return merge_result


def _apply_entity_page(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
    filepath: str,
    cls: dict,
    mod_page_name: str,
    old_generated_semantics: dict,
    entity_page_name: str,
) -> None:
    entity_path = ctx.wiki_dir / "entities" / f"{entity_page_name}.md"
    rename = diff.renamed_entity_pages.get((cls["name"], filepath))
    _move_renamed_entity_page(ctx.wiki_dir, rename, ctx.current_entity_pages)

    relationship_summary = ctx.generated_sections.entity_relationship_summaries.get(
        (cls["name"], filepath),
        {},
    )
    generated = _generate_entity_md(
        cls,
        filepath,
        ctx.relationships,
        mod_page_name,
        relationship_summary=relationship_summary,
        module_page_map=ctx.module_page_map,
        diagram_style=_generated_diagram_style(
            "relationships",
            root=ctx.src_dir,
            fallback_root=Path.cwd(),
            entity=relationship_summary.get("name"),
            file=relationship_summary.get("file"),
        ),
    )
    merge_result = _merge_entity_page(
        ctx,
        entity_path,
        generated,
        old_generated_semantics,
        cls["name"],
        result,
    )
    write_state = _write_md_if_changed(entity_path, merge_result.text)
    _record_page_write(
        result,
        "entity",
        entity_page_name,
        write_state,
        metadata_only=filepath in ctx.metadata_only_files,
    )


def _apply_module_page(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
    filepath: str,
    file_data: dict,
    mod_page_name: str,
    old_generated_semantics: dict,
    file_entity_page_map: dict[str, str],
) -> None:
    module_path = ctx.wiki_dir / "modules" / f"{mod_page_name}.md"
    _move_renamed_module_page(
        ctx.wiki_dir,
        diff.renamed_module_pages.get(filepath),
        ctx.current_module_pages,
    )

    module_dependency_map = None
    if ctx.generated_sections.module_dependency_maps is not None:
        module_dependency_map = (
            ctx.generated_sections.module_dependency_maps.get(filepath) or {}
        )
    generated = _generate_module_md(
        filepath,
        file_data,
        file_entity_page_map,
        module_dependency_map=module_dependency_map,
        module_page_map=ctx.module_page_map,
        entity_occurrence_page_map=ctx.entity_occurrence_page_cache,
        diagram_style=_generated_diagram_style(
            "module_dependency",
            root=ctx.src_dir,
            fallback_root=Path.cwd(),
            file=filepath,
        )
        if module_dependency_map is not None
        else None,
    )
    merge_result = _merge_module_page(
        ctx, module_path, generated, old_generated_semantics, result
    )
    write_state = _write_md_if_changed(module_path, merge_result.text)
    _record_page_write(
        result,
        "module",
        mod_page_name,
        write_state,
        metadata_only=filepath in ctx.metadata_only_files,
    )


def _apply_refreshed_file_pages(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
    refresh_files: list[str],
) -> None:
    for filepath in refresh_files:
        file_data = ctx.inventory[filepath]
        mod_page_name = ctx.module_page_map.get(
            filepath, _page_name_for_module(filepath)
        )
        old_generated_semantics = ctx.manifest.sources.get(filepath, {}).get(
            "generated_semantics", {}
        )
        file_entity_page_map = _file_entity_page_map(
            filepath,
            file_data,
            ctx.entity_page_cache,
            ctx.entity_occurrence_page_cache,
        )

        seen_names: dict[str, int] = {}
        for cls in file_data.get("classes", []):
            name = cls["name"]
            seen_names[name] = seen_names.get(name, 0) + 1
            entity_page_name = ctx.entity_occurrence_page_cache.get(
                (name, filepath, seen_names[name]),
                file_entity_page_map[name],
            )
            _apply_entity_page(
                ctx,
                diff,
                result,
                filepath,
                cls,
                mod_page_name,
                old_generated_semantics,
                entity_page_name,
            )
        _apply_module_page(
            ctx,
            diff,
            result,
            filepath,
            file_data,
            mod_page_name,
            old_generated_semantics,
            file_entity_page_map,
        )


def _record_unchanged_file_skips(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
    refresh_files: list[str],
) -> None:
    refresh_file_set = set(refresh_files)
    unchanged_files = [
        filepath
        for filepath in diff.unchanged_files
        if filepath not in refresh_file_set
    ]
    unchanged_pages = sum(
        1 + len(ctx.inventory[filepath].get("classes", []))
        for filepath in unchanged_files
        if filepath in ctx.inventory
    )
    result.skipped += unchanged_pages
    if unchanged_files:
        print(
            f"  SKIP unchanged source files: {len(unchanged_files)} "
            f"file(s), {unchanged_pages} generated page(s)"
        )


def _deprecate_existing_page(
    path: Path,
    result: SyncResult,
    page_kind: str,
    page_name: str,
) -> None:
    if not path.exists():
        return
    text = read_md(path)
    if _DEPRECATION_HEADER in text:
        return
    write_state = _write_md_if_changed(path, _DEPRECATION_HEADER + text)
    if write_state != "unchanged":
        result.deprecated += 1
        print(f"  DEPRECATE {page_kind}: {page_name}")


def _deprecate_removed_entities(
    wiki_dir: Path,
    filepath: str,
    old_info: dict,
    result: SyncResult,
    *,
    retained_page_names: frozenset[str] = frozenset(),
) -> None:
    for cls_name in old_info.get("entities", []):
        entity_page_name = _removed_entity_page_name(
            wiki_dir, cls_name, filepath, old_info
        )
        if entity_page_name and entity_page_name not in retained_page_names:
            entity_path = wiki_dir / "entities" / f"{entity_page_name}.md"
            _deprecate_existing_page(entity_path, result, "entity", entity_page_name)


def _deprecate_removed_module(
    wiki_dir: Path,
    filepath: str,
    old_info: dict,
    result: SyncResult,
) -> None:
    old_mod_page = old_info.get("module_page", _module_name_from_path(filepath))
    mod_page_path = wiki_dir / "modules" / f"{old_mod_page}.md"
    _deprecate_existing_page(mod_page_path, result, "module", mod_page_path.stem)


def _deprecate_removed_files(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
) -> None:
    for filepath in diff.removed_files:
        old_info = ctx.manifest.sources.get(filepath)
        if old_info is None:
            old_info = _removed_source_info_from_mappings(ctx.manifest, filepath)
        retained_entity_pages = _moved_entity_retained_page_names(
            ctx,
            diff,
            filepath,
            old_info,
        )
        _deprecate_removed_entities(
            ctx.wiki_dir,
            filepath,
            old_info,
            result,
            retained_page_names=retained_entity_pages,
        )
        _deprecate_removed_module(ctx.wiki_dir, filepath, old_info, result)


def _moved_entity_retained_page_names(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    old_source_path: str,
    old_info: Mapping[str, object],
) -> frozenset[str]:
    """Return moved entity pages whose current path rule keeps the locator."""

    retained: set[str] = set()
    for entity_name, (old_path, new_path) in diff.moved_entities.items():
        if old_path != old_source_path:
            continue
        old_page_name = _removed_entity_page_name(
            ctx.wiki_dir,
            entity_name,
            old_source_path,
            dict(old_info),
        )
        if old_page_name is None:
            continue
        current_pages = {
            page_name
            for (name, source_path, _occurrence), page_name in (
                ctx.entity_occurrence_page_cache.items()
            )
            if name == entity_name and source_path == new_path
        }
        if old_page_name in current_pages:
            retained.add(old_page_name)
    return frozenset(retained)


def _removed_source_info_from_mappings(
    manifest: SyncManifest,
    source_path: str,
) -> dict:
    """Recover page coordinates for a repair-pending removed source."""

    module_page = _module_name_from_path(source_path)
    entities: list[str] = []
    entity_pages: dict[str, str] = {}
    occurrences: list[dict[str, object]] = []
    for page_path, mapping in manifest.page_source_mappings.items():
        if mapping.source_path != source_path:
            continue
        page_name = Path(page_path).stem
        if mapping.scope == "module":
            module_page = page_name
            continue
        assert mapping.entity_name is not None
        assert mapping.occurrence is not None
        entities.append(mapping.entity_name)
        entity_pages.setdefault(mapping.entity_name, page_name)
        occurrences.append(
            {
                "name": mapping.entity_name,
                "page": page_name,
                "occurrence": mapping.occurrence,
            }
        )
    return {
        "entities": entities,
        "entity_pages": entity_pages,
        "entity_page_occurrences": occurrences,
        "module_page": module_page,
    }


def _replace_generated_section(existing: str, generated: str, heading: str) -> str:
    return _service_replace_generated_section(existing, generated, heading)


def _record_generated_section_write(
    result: SyncResult,
    diff: SyncDiff,
    filepath: str,
    page_kind: str,
    section_label: str,
    page_name: str,
) -> None:
    result.updated += 1
    if filepath in diff.unchanged_files and result.skipped > 0:
        result.skipped -= 1
    print(f"  UPDATE {page_kind} {section_label}: {page_name}")


def _refresh_entity_relationship_sections(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
) -> None:
    for filepath, file_data in ctx.inventory.items():
        mod_page_name = ctx.module_page_map.get(
            filepath, _page_name_for_module(filepath)
        )
        seen_names: dict[str, int] = {}
        for cls in file_data.get("classes", []):
            name = cls["name"]
            seen_names[name] = seen_names.get(name, 0) + 1
            page_name = ctx.entity_occurrence_page_cache.get(
                (name, filepath, seen_names[name]),
                ctx.entity_page_cache[(name, filepath)],
            )
            entity_path = ctx.wiki_dir / "entities" / f"{page_name}.md"
            if not entity_path.exists():
                continue
            relationship_summary = (
                ctx.generated_sections.entity_relationship_summaries.get(
                    (cls["name"], filepath),
                    {},
                )
            )
            generated = _generate_entity_md(
                cls,
                filepath,
                ctx.relationships,
                mod_page_name,
                relationship_summary=relationship_summary,
                module_page_map=ctx.module_page_map,
                diagram_style=_generated_diagram_style(
                    "relationships",
                    root=ctx.src_dir,
                    fallback_root=Path.cwd(),
                    entity=relationship_summary.get("name"),
                    file=relationship_summary.get("file"),
                ),
            )
            refreshed = _replace_generated_section(
                read_md(entity_path),
                generated,
                "Relationships",
            )
            if _write_md_if_changed(entity_path, refreshed) == "updated":
                _record_generated_section_write(
                    result,
                    diff,
                    filepath,
                    "entity",
                    "relationships",
                    page_name,
                )


def _refresh_module_dependency_sections(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
) -> None:
    module_dependency_maps = ctx.generated_sections.module_dependency_maps
    if module_dependency_maps is None:
        return
    for filepath, file_data in ctx.inventory.items():
        mod_page_name = ctx.module_page_map.get(
            filepath, _page_name_for_module(filepath)
        )
        module_path = ctx.wiki_dir / "modules" / f"{mod_page_name}.md"
        if not module_path.exists():
            continue
        generated = _generate_module_md(
            filepath,
            file_data,
            _file_entity_page_map(
                filepath,
                file_data,
                ctx.entity_page_cache,
                ctx.entity_occurrence_page_cache,
            ),
            module_dependency_map=module_dependency_maps.get(filepath) or {},
            module_page_map=ctx.module_page_map,
            entity_occurrence_page_map=ctx.entity_occurrence_page_cache,
            diagram_style=_generated_diagram_style(
                "module_dependency",
                root=ctx.src_dir,
                fallback_root=Path.cwd(),
                file=filepath,
            ),
        )
        refreshed = _replace_generated_section(
            read_md(module_path),
            generated,
            "Local dependency map",
        )
        if _write_md_if_changed(module_path, refreshed) == "updated":
            _record_generated_section_write(
                result,
                diff,
                filepath,
                "module",
                "local dependency map",
                mod_page_name,
            )


def _refresh_generated_sections(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
) -> None:
    _refresh_entity_relationship_sections(ctx, diff, result)
    _refresh_module_dependency_sections(ctx, diff, result)


def _apply_diff_page_maps(
    inventory: dict,
    src_dir: str,
    entity_page_cache: dict[tuple[str, str], str] | None,
    entity_occurrence_page_cache: dict[tuple[str, str, int], str] | None,
    module_page_map: dict[str, str] | None,
) -> tuple[
    dict[tuple[str, str], str],
    dict[tuple[str, str, int], str],
    dict[str, str],
]:
    if entity_page_cache is None:
        _, _, entity_page_cache = _collision_maps(inventory, src_dir)
    if module_page_map is None:
        module_page_map = build_module_page_map(inventory)
    if entity_occurrence_page_cache is None:
        entity_occurrence_page_cache = build_entity_occurrence_page_map(
            inventory, module_page_map
        )
    return entity_page_cache, entity_occurrence_page_cache, module_page_map


def _build_apply_diff_context(
    *,
    wiki_dir: Path,
    src_dir: str,
    inventory: dict,
    manifest: SyncManifest,
    entity_page_cache: dict[tuple[str, str], str],
    entity_occurrence_page_cache: dict[tuple[str, str, int], str],
    module_page_map: dict[str, str],
    relationships: dict,
    generated_sections: _GeneratedSectionContext | None,
    diff: SyncDiff,
    preserve_semantic: bool,
) -> _ApplyDiffContext:
    return _ApplyDiffContext(
        wiki_dir=wiki_dir,
        src_dir=src_dir,
        inventory=inventory,
        manifest=manifest,
        entity_page_cache=entity_page_cache,
        entity_occurrence_page_cache=entity_occurrence_page_cache,
        module_page_map=module_page_map,
        relationships=relationships,
        generated_sections=generated_sections or _empty_generated_section_context(),
        metadata_only_files=set(diff.metadata_only_files),
        current_entity_pages=set(entity_occurrence_page_cache.values()),
        current_module_pages=set(module_page_map.values()),
        preserve_semantic=preserve_semantic,
    )


def _apply_diff(
    diff: SyncDiff,
    wiki_dir: Path,
    inventory: dict,
    src_dir: str,
    manifest: SyncManifest,
    *,
    entity_page_cache: dict[tuple[str, str], str] | None = None,
    entity_occurrence_page_cache: dict[tuple[str, str, int], str] | None = None,
    module_page_map: dict[str, str] | None = None,
    generated_sections: _GeneratedSectionContext | None = None,
    preserve_semantic: bool = True,
) -> SyncResult:
    """Regenerate pages for new/changed files, deprecate pages for removed files."""
    entity_page_cache, entity_occurrence_page_cache, module_page_map = (
        _apply_diff_page_maps(
            inventory,
            src_dir,
            entity_page_cache,
            entity_occurrence_page_cache,
            module_page_map,
        )
    )

    target_entities = _target_entities_for_diff(diff, inventory)
    relationships = _relationships_for_targets(
        inventory, module_page_map, target_entities
    )
    refresh_files = _refresh_files_for_diff(diff)
    result = SyncResult()
    ctx = _build_apply_diff_context(
        wiki_dir=wiki_dir,
        src_dir=src_dir,
        inventory=inventory,
        manifest=manifest,
        entity_page_cache=entity_page_cache,
        entity_occurrence_page_cache=entity_occurrence_page_cache,
        module_page_map=module_page_map,
        relationships=relationships,
        generated_sections=generated_sections,
        diff=diff,
        preserve_semantic=preserve_semantic,
    )

    print("Applying wiki page changes...", flush=True)
    _apply_refreshed_file_pages(ctx, diff, result, refresh_files)
    _record_unchanged_file_skips(ctx, diff, result, refresh_files)
    _refresh_generated_sections(ctx, diff, result)
    _deprecate_removed_files(ctx, diff, result)

    print("Applied wiki page changes.", flush=True)
    return result


def _removed_entity_page_name(
    wiki_dir: Path,
    cls_name: str,
    filepath: str,
    old_info: dict,
) -> Optional[str]:
    """Resolve the existing entity page for a class whose source file was removed."""
    entity_pages = old_info.get("entity_pages", {})
    candidates: list[str] = []
    if isinstance(entity_pages, dict) and entity_pages.get(cls_name):
        candidates.append(str(entity_pages[cls_name]))

    old_mod_page = old_info.get("module_page", _module_name_from_path(filepath))
    if old_mod_page:
        candidates.append(f"{old_mod_page}_{cls_name}")
    candidates.append(cls_name)

    seen: set[str] = set()
    for page_name in candidates:
        if page_name in seen:
            continue
        seen.add(page_name)
        if (wiki_dir / "entities" / f"{page_name}.md").exists():
            return page_name

    matches = sorted((wiki_dir / "entities").glob(f"*_{cls_name}.md"))
    return matches[0].stem if matches else None


# ── run ───────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _SyncRunOptions:
    src_dir: str
    wiki_dir: Path
    allow_external_src: bool
    cache_options: InventoryCacheOptions
    cache_stats_enabled: bool
    parallel_jobs: int
    job_request: ExtractionJobRequest
    plan_reporter: Callable[[ExtractionJobPlan], None] | None
    helper_cache_dir: str | None
    include_tests: Iterable[str] | None
    force: bool
    preserve_semantic: bool
    initialize_surfaces: frozenset[str]
    flow_categories: frozenset[str] | None
    exclude_tests: bool
    dry_run: bool
    openapi_file: str | None
    clear_openapi_file: bool


@dataclass(frozen=True)
class _SyncPageMaps:
    module_page_map: dict[str, str]
    entity_page_cache: dict[tuple[str, str], str]
    entity_occurrence_page_cache: dict[tuple[str, str, int], str]


@dataclass(frozen=True)
class _ExtractedSyncInventory:
    result: InventoryResult
    source_snapshot: SourceSnapshot


@dataclass(frozen=True)
class _SyncEntryPointAnalysis:
    entries: list[dict]
    observations: dict


@dataclass(frozen=True)
class _RuntimeGraphObservations:
    resolved_call_edges: list[dict]
    call_observations: dict
    dependency_observations: dict
    entrypoint_observations: dict
    surface_flow_entries: list[dict]
    flows: list[dict]
    rendering_flows: list[dict]
    data_flows: list[dict]
    rendering_data_flows: list[dict]
    external_dependencies: list[dict]
    dependency_analysis: dict | None
    analyzer_limitations: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class _SurfaceInitializationPlan:
    surfaces: dict[str, dict]
    policy_changed: bool
    flow_entries: tuple[dict, ...]
    new_flow_entries: tuple[dict, ...]
    excluded_flow_tests: int
    dependency_inventory: dict
    dependency_analysis: dict | None
    dependency_target_pages: tuple[str, ...]
    new_dependency_pages: tuple[str, ...]
    requested_surfaces: frozenset[str]
    excluded_dependency_tests: int = 0
    api_contracts: dict | None = None
    api_contract_target: bool = False
    new_api_contract_page: bool = False
    generation_inputs: dict[str, object] = field(default_factory=dict)
    generation_inputs_changed: bool = False

    @property
    def created_pages(self) -> int:
        return (
            len(self.new_flow_entries)
            + len(self.new_dependency_pages)
            + int(self.new_api_contract_page)
        )

    @property
    def has_work(self) -> bool:
        return (
            self.policy_changed
            or self.generation_inputs_changed
            or self.created_pages > 0
        )


@dataclass(frozen=True)
class _PreparedSyncRun:
    manifest: "SyncManifest"
    seed_manifest: bool
    repair_only: bool
    inventory_result: InventoryResult
    source_snapshot: SourceSnapshot
    inventory: dict
    page_maps: _SyncPageMaps
    diff: "SyncDiff"
    surface_plan: _SurfaceInitializationPlan
    repository_evidence: RepositoryEvidence
    graph_observations: _RuntimeGraphObservations
    infrastructure_plan: InfrastructureSyncPlan


def _updated_surface_policies(
    options: _SyncRunOptions, manifest: "SyncManifest"
) -> tuple[dict[str, dict], bool]:
    surfaces = deepcopy(manifest.surfaces)
    if "flows" in options.initialize_surfaces:
        surfaces["flows"] = {
            "enabled": True,
            "categories": (
                sorted(options.flow_categories) if options.flow_categories else None
            ),
            "exclude_tests": options.exclude_tests,
        }
    if "dependencies" in options.initialize_surfaces:
        surfaces["dependencies"] = {
            "enabled": True,
            "exclude_tests": options.exclude_tests,
        }
    if "api-contracts" in options.initialize_surfaces or options.openapi_file:
        surfaces["api_contracts"] = {"enabled": True}
    return surfaces, surfaces != manifest.surfaces


def _surface_policy(surfaces: Mapping[str, Mapping], key: str) -> Mapping | None:
    value = surfaces.get(key)
    return value if isinstance(value, Mapping) else None


def _filtered_surface_inventory(inventory: dict, *, exclude_tests: bool) -> dict:
    if not exclude_tests:
        return inventory
    return {
        filepath: file_data
        for filepath, file_data in inventory.items()
        if not is_test_source_path(filepath)
    }


def _flow_plan(
    options: _SyncRunOptions,
    surfaces: Mapping[str, Mapping],
    entry_points: list[dict],
    *,
    allow_legacy_creation: bool,
) -> tuple[tuple[dict, ...], tuple[dict, ...], int]:
    flows_dir = options.wiki_dir / PageKind.FLOWS.value
    existing_ids = (
        {path.stem for path in flows_dir.glob("*.md") if path.is_file()}
        if flows_dir.exists()
        else set()
    )
    policy = _surface_policy(surfaces, "flows")
    if policy is None:
        enabled = bool(existing_ids) and allow_legacy_creation
        categories = None
        exclude_tests = False
    else:
        enabled = bool(policy.get("enabled", False))
        raw_categories = policy.get("categories")
        categories = (
            {str(category) for category in raw_categories}
            if isinstance(raw_categories, list)
            else None
        )
        exclude_tests = bool(policy.get("exclude_tests", False))

    category_entries = [
        entry
        for entry in entry_points
        if categories is None or entry.get("category") in categories
    ]
    excluded_tests = sum(
        1
        for entry in category_entries
        if exclude_tests and is_test_source_path(entry.get("file"))
    )
    allowed_new = {
        str(entry.get("id"))
        for entry in category_entries
        if enabled
        and entry.get("id")
        and not (exclude_tests and is_test_source_path(entry.get("file")))
    }
    target_ids = existing_ids | allowed_new
    target_entries = tuple(
        entry for entry in entry_points if str(entry.get("id")) in target_ids
    )
    new_entries = tuple(
        entry for entry in target_entries if str(entry.get("id")) not in existing_ids
    )
    return target_entries, new_entries, excluded_tests


def _dependency_plan(
    options: _SyncRunOptions,
    surfaces: Mapping[str, Mapping],
    inventory: dict,
    *,
    source_snapshot: SourceSnapshot | None = None,
) -> tuple[dict, dict | None, tuple[str, ...], tuple[str, ...], int]:
    existing = tuple(
        stem
        for stem, _label in _ARCHITECTURE_PAGES
        if (options.wiki_dir / f"{stem}.md").exists()
    )
    policy = _surface_policy(surfaces, "dependencies")
    if policy is None:
        target_pages = existing
        exclude_tests = False
    elif policy.get("enabled", False):
        target_pages = tuple(stem for stem, _label in _ARCHITECTURE_PAGES)
        exclude_tests = bool(policy.get("exclude_tests", False))
    else:
        target_pages = existing
        exclude_tests = False

    dependency_inventory = _filtered_surface_inventory(
        inventory, exclude_tests=exclude_tests
    )
    excluded_tests = len(inventory) - len(dependency_inventory)
    analysis = (
        analyze_dependencies(
            dependency_inventory,
            options.src_dir,
            source_snapshot=source_snapshot,
        )
        if target_pages
        else None
    )
    has_nodes = bool(analysis and analysis["graph"]["nodes"])
    new_pages = tuple(
        stem
        for stem in target_pages
        if has_nodes and not (options.wiki_dir / f"{stem}.md").exists()
    )
    active_targets = tuple(dict.fromkeys((*existing, *new_pages)))
    return dependency_inventory, analysis, active_targets, new_pages, excluded_tests


def _build_surface_initialization_plan(
    options: _SyncRunOptions,
    manifest: "SyncManifest",
    inventory: dict,
    entry_points: list[dict],
    *,
    source_changed: bool,
    api_contracts: dict | None,
    generation_inputs: Mapping[str, object],
    source_snapshot: SourceSnapshot | None = None,
) -> _SurfaceInitializationPlan:
    surfaces, policy_changed = _updated_surface_policies(options, manifest)
    include_all_enabled = not options.initialize_surfaces
    if include_all_enabled or "flows" in options.initialize_surfaces:
        flow_entries, new_flow_entries, excluded_flow_tests = _flow_plan(
            options,
            surfaces,
            entry_points,
            allow_legacy_creation=source_changed,
        )
    else:
        flow_entries, new_flow_entries, excluded_flow_tests = (), (), 0
    if include_all_enabled or "dependencies" in options.initialize_surfaces:
        (
            dependency_inventory,
            dependency_analysis,
            target_pages,
            new_pages,
            excluded_dependency_tests,
        ) = _dependency_plan(
            options,
            surfaces,
            inventory,
            source_snapshot=source_snapshot,
        )
    else:
        dependency_inventory = inventory
        dependency_analysis = None
        target_pages = ()
        new_pages = ()
        excluded_dependency_tests = 0
    api_selected = (
        include_all_enabled
        or "api-contracts" in options.initialize_surfaces
        or bool(options.openapi_file)
        or options.clear_openapi_file
        or dict(generation_inputs) != manifest.generation_inputs
    )
    api_policy = _surface_policy(surfaces, "api_contracts")
    api_contract_path = options.wiki_dir / f"{PageKind.API_CONTRACTS.value}.md"
    api_contract_target = api_selected and bool(
        api_contract_path.exists()
        or (api_policy and api_policy.get("enabled", False))
        or generation_inputs.get("openapi")
        or options.openapi_file
        or "api-contracts" in options.initialize_surfaces
    )
    new_api_contract_page = api_contract_target and not api_contract_path.exists()
    return _SurfaceInitializationPlan(
        surfaces=surfaces,
        policy_changed=policy_changed,
        flow_entries=flow_entries,
        new_flow_entries=new_flow_entries,
        excluded_flow_tests=excluded_flow_tests,
        dependency_inventory=dependency_inventory,
        dependency_analysis=dependency_analysis,
        dependency_target_pages=target_pages,
        new_dependency_pages=new_pages,
        excluded_dependency_tests=excluded_dependency_tests,
        api_contracts=api_contracts if api_contract_target else None,
        api_contract_target=api_contract_target,
        new_api_contract_page=new_api_contract_page,
        generation_inputs=deepcopy(dict(generation_inputs)),
        generation_inputs_changed=(
            dict(generation_inputs) != manifest.generation_inputs
        ),
        requested_surfaces=options.initialize_surfaces,
    )


def _large_surface_message(
    plan: _SurfaceInitializationPlan, wiki_dir: Path
) -> str | None:
    created = plan.created_pages
    if created > MAX_SURFACE_CREATED_PAGES:
        return (
            f"surface initialization would create {created} page(s), which exceeds "
            f"the safety limit of {MAX_SURFACE_CREATED_PAGES}."
        )
    current_pages = len(collect_wiki_pages(wiki_dir))
    if current_pages >= MIN_PAGES_FOR_SURFACE_RATIO_GUARD:
        ratio = created / current_pages
        if ratio > MAX_SURFACE_CREATED_RATIO:
            percent = int(ratio * 100)
            limit = int(MAX_SURFACE_CREATED_RATIO * 100)
            return (
                f"surface initialization would create {created} page(s) against "
                f"{current_pages} current wiki page(s) ({percent}%), which exceeds "
                f"the {limit}% safety limit."
            )
    return None


def _exit_if_large_unforced_surface_plan(
    options: _SyncRunOptions, plan: _SurfaceInitializationPlan
) -> None:
    message = _large_surface_message(plan, options.wiki_dir)
    if not message or options.force or options.dry_run:
        return
    print(f"Error: {message}", file=sys.stderr)
    print(
        "Preview with `llm-wiki sync --dry-run`, then re-run with --force "
        "if the initialization is intentional.",
        file=sys.stderr,
    )
    sys.exit(1)


def _print_dry_run_plan(
    options: _SyncRunOptions,
    diff: "SyncDiff",
    plan: _SurfaceInitializationPlan,
    infrastructure_plan: InfrastructureSyncPlan,
    manifest: SyncManifest,
    *,
    seed_manifest: bool,
    repair_only: bool,
) -> None:
    print("\nSync dry-run plan:")
    source_label = (
        "deferred source files" if options.initialize_surfaces else "source files"
    )
    print(
        f"  {source_label}: "
        f"{len(diff.new_files)} new, {len(diff.changed_files)} changed, "
        f"{len(diff.metadata_only_files)} metadata-only, "
        f"{len(diff.removed_files)} removed"
    )
    infrastructure_label = (
        "deferred infrastructure sources"
        if options.initialize_surfaces
        else "infrastructure sources"
    )
    print(
        f"  {infrastructure_label}: "
        f"{len(infrastructure_plan.new_sources)} new, "
        f"{len(infrastructure_plan.changed_sources)} changed, "
        f"{len(infrastructure_plan.moved_sources)} moved, "
        f"{len(infrastructure_plan.removed_sources)} removed, "
        f"{len(infrastructure_plan.unsupported_yaml)} unsupported YAML"
    )
    categories = Counter(
        str(entry.get("category") or "unknown") for entry in plan.new_flow_entries
    )
    category_text = (
        ", ".join(
            f"{category}: {count}" for category, count in sorted(categories.items())
        )
        or "none"
    )
    print(
        f"  flows: {len(plan.new_flow_entries)} create "
        f"({category_text}); {plan.excluded_flow_tests} test candidate(s) excluded"
    )
    print(
        f"  dependency architecture: {len(plan.new_dependency_pages)} create "
        f"({', '.join(plan.new_dependency_pages) or 'none'}); "
        f"{plan.excluded_dependency_tests} test source(s) excluded"
    )
    api_source = (
        str(plan.api_contracts.get("source"))
        if isinstance(plan.api_contracts, Mapping)
        else "disabled"
    )
    print(
        "  api contracts: "
        f"{int(plan.new_api_contract_page)} create; authority: {api_source}"
    )
    if plan.generation_inputs_changed:
        openapi = plan.generation_inputs.get("openapi")
        if isinstance(openapi, Mapping):
            print(f"  OpenAPI input: {openapi.get('path')} ({openapi.get('sha256')})")
        else:
            print("  OpenAPI input: cleared; static authority will be used")
    policy_names = [
        surface
        for surface, key in _SURFACE_POLICY_KEYS.items()
        if plan.surfaces.get(key) != {}
        and key in plan.surfaces
        and surface in plan.requested_surfaces
    ]
    print(f"  policy updates: {', '.join(policy_names) or 'none'}")
    if seed_manifest:
        print("  manifest: seed from the current source inventory")
    ancillary = [
        "index.md",
        "log.md",
        ".llm-wiki-surface.json",
        ".llm-wiki-knowledge.json",
        MANIFEST_FILENAME,
    ]
    print(f"  ancillary files considered: {', '.join(ancillary)}")
    source_requires_force = (
        not options.initialize_surfaces
        and not seed_manifest
        and not repair_only
        and (
            _large_diff_message(diff, manifest) is not None
            or _large_infrastructure_message(infrastructure_plan) is not None
        )
    )
    surface_requires_force = (
        not seed_manifest
        and not repair_only
        and _large_surface_message(plan, options.wiki_dir) is not None
    )
    requires_force = source_requires_force or surface_requires_force
    print(f"  requires --force: {'yes' if requires_force else 'no'}")
    print("DRY-RUN: no files modified.")


def _surface_args(value: object) -> frozenset[str]:
    if value in (None, ""):
        return frozenset()
    raw_items = list(value) if isinstance(value, (list, tuple, set)) else [value]
    surfaces: set[str] = set()
    for raw in raw_items:
        nested = list(raw) if isinstance(raw, (list, tuple, set)) else [raw]
        for item in nested:
            surfaces.update(
                part.strip().lower() for part in str(item).split(",") if part.strip()
            )
    invalid = sorted(surfaces - set(INITIALIZABLE_SURFACES))
    if invalid:
        allowed = ", ".join(INITIALIZABLE_SURFACES)
        print(
            f"Error: unknown initialization surface {invalid[0]!r}; "
            f"choose from: {allowed}.",
            file=sys.stderr,
        )
        sys.exit(2)
    return frozenset(surfaces)


def _flow_category_args(value: object) -> frozenset[str] | None:
    if value in (None, ""):
        return None
    raw_items = list(value) if isinstance(value, (list, tuple, set)) else [value]
    categories = frozenset(str(item).strip() for item in raw_items if str(item).strip())
    invalid = sorted(
        category for category in categories if not _FLOW_CATEGORY_RE.fullmatch(category)
    )
    if invalid:
        print(f"Error: unsafe flow category {invalid[0]!r}.", file=sys.stderr)
        sys.exit(2)
    return categories or None


def _manifest_openapi_path(manifest: "SyncManifest") -> str | None:
    """Return the persisted OpenAPI path, rejecting malformed v4 state."""
    if "openapi" not in manifest.generation_inputs:
        return None
    value = manifest.generation_inputs.get("openapi")
    if not isinstance(value, Mapping):
        raise ApiContractError("Persisted generation_inputs.openapi must be an object.")
    path = value.get("path")
    if not isinstance(path, str) or not path.strip():
        raise ApiContractError(
            "Persisted generation_inputs.openapi.path must be a non-empty string."
        )
    return path


def _resolve_openapi_generation_input(
    options: _SyncRunOptions,
    manifest: "SyncManifest",
) -> tuple[str | None, dict[str, object]]:
    """Validate OpenAPI state before inventory/cache writes and update metadata."""
    generation_inputs = deepcopy(manifest.generation_inputs)
    if options.clear_openapi_file:
        generation_inputs.pop("openapi", None)
        return None, generation_inputs

    selected = options.openapi_file or _manifest_openapi_path(manifest)
    if not selected:
        return None, generation_inputs
    loaded = load_openapi_document(selected, source_root=options.src_dir)
    generation_inputs["openapi"] = {
        key: loaded[key] for key in ("path", "sha256", "format")
    }
    return str(loaded["path"]), generation_inputs


def _linked_api_contracts(
    contracts: Mapping[str, object], entry_points: Iterable[Mapping[str, object]]
) -> dict:
    """Attach stable flow ids to operations with statically linked handlers."""
    linked = deepcopy(dict(contracts))
    flow_ids: dict[tuple[str, str], str] = {}
    for entry in entry_points:
        if entry.get("category") != "http" or not entry.get("id"):
            continue
        symbol = str(entry.get("symbol") or "").rsplit(".", 1)[-1]
        flow_ids[(str(entry.get("file") or ""), symbol)] = str(entry["id"])
    operations = linked.get("operations")
    if not isinstance(operations, list):
        operations = []
    for operation in operations:
        if not isinstance(operation, dict):
            continue
        handler = operation.get("handler")
        if not isinstance(handler, Mapping):
            continue
        symbol = str(handler.get("symbol") or "").rsplit(".", 1)[-1]
        flow_id = flow_ids.get((str(handler.get("file") or ""), symbol))
        if flow_id:
            operation["flow_id"] = flow_id
    return linked


def _sync_run_options_from_args(args) -> _SyncRunOptions:
    src_dir: str = getattr(args, "src_dir", ".")
    wiki_dir = Path(getattr(args, "wiki_dir", "docs/llm_wiki"))
    dry_run = bool(getattr(args, "dry_run", False))
    cache_options = _cache_options_from_args(args)
    if dry_run:
        cache_options = InventoryCacheOptions(enabled=False)
    cache_stats_enabled = bool(getattr(args, "cache_stats", False))
    parallel_jobs = getattr(args, "jobs", 1)
    job_request = extraction_job_request_from_args(args)
    helper_cache_dir = getattr(args, "helper_cache_dir", None)
    include_tests = getattr(args, "include_tests", None)
    force = bool(getattr(args, "force", False))
    preserve_semantic = not bool(getattr(args, "no_preserve_semantic", False))
    initialize_surfaces = _surface_args(getattr(args, "initialize_surfaces", None))
    flow_categories = _flow_category_args(getattr(args, "flow_category", None))
    exclude_tests = bool(getattr(args, "exclude_tests", False))
    openapi_file = getattr(args, "openapi_file", None)
    clear_openapi_file = bool(getattr(args, "clear_openapi_file", False))
    if openapi_file and clear_openapi_file:
        print(
            "Error: --openapi-file and --clear-openapi-file are mutually exclusive.",
            file=sys.stderr,
        )
        sys.exit(2)
    if flow_categories and "flows" not in initialize_surfaces:
        print(
            "Error: --flow-category requires --initialize-surfaces flows.",
            file=sys.stderr,
        )
        sys.exit(2)
    if exclude_tests and not initialize_surfaces:
        print(
            "Error: --exclude-tests requires --initialize-surfaces.",
            file=sys.stderr,
        )
        sys.exit(2)
    allow_external_src = bool(getattr(args, "allow_external_src", False))
    src_root = validate_source_root(
        src_dir, "--src-dir", allow_external=allow_external_src
    )
    if allow_external_src:
        src_dir = str(src_root)
    validate_path(str(wiki_dir), "--wiki-dir")

    return _SyncRunOptions(
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        allow_external_src=allow_external_src,
        cache_options=cache_options,
        cache_stats_enabled=cache_stats_enabled,
        parallel_jobs=parallel_jobs,
        job_request=job_request,
        plan_reporter=print_extraction_job_plan,
        helper_cache_dir=helper_cache_dir,
        include_tests=include_tests,
        force=force,
        preserve_semantic=preserve_semantic,
        initialize_surfaces=initialize_surfaces,
        flow_categories=flow_categories,
        exclude_tests=exclude_tests,
        dry_run=dry_run,
        openapi_file=str(openapi_file) if openapi_file else None,
        clear_openapi_file=clear_openapi_file,
    )


def _load_or_seed_manifest(
    options: _SyncRunOptions,
) -> tuple[Optional["SyncManifest"], bool]:
    state = classify_wiki_lifecycle(options.wiki_dir)
    if state is WikiLifecycleState.MANAGED:
        return SyncManifest.load(options.wiki_dir), False
    if state is WikiLifecycleState.SYNC_SEEDABLE:
        return None, True
    guidance = (
        bootstrap_guidance(src_dir=options.src_dir, wiki_dir=options.wiki_dir)
        if state is WikiLifecycleState.FIRST_USE
        else migration_guidance(src_dir=options.src_dir, wiki_dir=options.wiki_dir)
    )
    print(
        f"Error: no sync manifest found at {options.wiki_dir / MANIFEST_FILENAME}.\n"
        f"{guidance}",
        file=sys.stderr,
    )
    sys.exit(1)


def _extract_current_inventory(options: _SyncRunOptions) -> _ExtractedSyncInventory:
    print("Extracting current source inventory...")
    source_snapshot = build_source_snapshot(
        options.src_dir,
        include_tests=options.include_tests,
    )
    inventory_result = get_inventory_result(
        options.src_dir,
        deep=True,
        source_snapshot=source_snapshot,
        cache_options=options.cache_options,
        parallel_jobs=options.parallel_jobs,
        job_request=options.job_request,
        plan_reporter=options.plan_reporter,
        helper_cache_dir=options.helper_cache_dir,
        include_tests=options.include_tests,
        capture_data_effect_observations=True,
        capture_import_observations=True,
    )
    if inventory_result.failed:
        print_inventory_failures(inventory_result)
        sys.exit(1)
    source_snapshot = inventory_result.source_snapshot or source_snapshot
    unsupported_message = format_unsupported_source_summary(
        unsupported_source_summary(
            source_snapshot, supported_languages=inventory_result.statuses
        )
    )
    if unsupported_message:
        print(unsupported_message)
    print(
        f"Extracted current source inventory: {len(inventory_result.inventory)} file(s)."
    )
    return _ExtractedSyncInventory(
        result=inventory_result,
        source_snapshot=source_snapshot,
    )


def _prepare_sync_page_maps(inventory: dict) -> _SyncPageMaps:
    print("Preparing sync page maps...", flush=True)
    module_page_map = build_module_page_map(inventory)
    entity_occurrence_page_cache = build_entity_occurrence_page_map(
        inventory, module_page_map
    )
    page_maps = _SyncPageMaps(
        module_page_map=module_page_map,
        entity_page_cache=build_entity_page_map(inventory),
        entity_occurrence_page_cache=entity_occurrence_page_cache,
    )
    print("Prepared sync page maps.", flush=True)
    return page_maps


def _compute_sync_diff(
    manifest: "SyncManifest",
    inventory: dict,
    options: _SyncRunOptions,
    page_maps: _SyncPageMaps,
    source_content_hashes: Mapping[str, str],
) -> "SyncDiff":
    diff = _compute_diff(
        manifest,
        inventory,
        options.src_dir,
        entity_page_cache=page_maps.entity_page_cache,
        module_page_map=page_maps.module_page_map,
        source_content_hashes=source_content_hashes,
    )
    _mark_pending_repair_sources_changed(manifest, inventory, diff)
    return diff


def _mark_pending_repair_sources_changed(
    manifest: SyncManifest,
    inventory: Mapping[str, Mapping],
    diff: "SyncDiff",
) -> None:
    """Force one trusted regeneration after a provenance-only repair."""

    pending_live = {
        mapping.source_path
        for page_path, baseline in manifest.evidence_baselines.items()
        if (
            not baseline.is_known
            and baseline.unknown_reason == MANIFEST_REPAIR_UNAVAILABLE
            and (mapping := manifest.page_source_mappings.get(page_path)) is not None
            and mapping.source_path in inventory
        )
    }
    unchanged = set(diff.unchanged_files)
    promote = unchanged & pending_live
    if promote:
        diff.unchanged_files = [
            source_path
            for source_path in diff.unchanged_files
            if source_path not in promote
        ]
        diff.changed_files.extend(sorted(promote))

    pending_removed = {
        mapping.source_path
        for page_path, tombstone in manifest.tombstones.items()
        if (
            tombstone.unknown_reason == MANIFEST_REPAIR_UNAVAILABLE
            and (mapping := manifest.page_source_mappings.get(page_path)) is not None
            and mapping.source_path not in inventory
        )
    }
    existing_removed = set(diff.removed_files)
    diff.removed_files.extend(sorted(pending_removed - existing_removed))


def _exit_if_large_unforced_diff(
    options: _SyncRunOptions,
    diff: "SyncDiff",
    manifest: "SyncManifest",
    inventory_result: InventoryResult,
    infrastructure_plan: InfrastructureSyncPlan,
) -> None:
    large_diff_message = _large_diff_message(diff, manifest) or (
        _large_infrastructure_message(infrastructure_plan)
    )
    if not large_diff_message or options.force:
        return

    print(f"Error: {large_diff_message}", file=sys.stderr)
    print(
        "This sync is broad enough to risk unintended wiki churn. "
        "Re-run with `llm-wiki sync --force` if this update is intentional.",
        file=sys.stderr,
    )
    _print_cache_stats(
        inventory_result.cache_stats, enabled=options.cache_stats_enabled
    )
    sys.exit(1)


def _apply_sync_changes(
    options: _SyncRunOptions,
    manifest: "SyncManifest",
    inventory: dict,
    diff: "SyncDiff",
    page_maps: _SyncPageMaps,
    surface_plan: _SurfaceInitializationPlan,
    graph_observations: _RuntimeGraphObservations,
    infrastructure_plan: InfrastructureSyncPlan,
    source_snapshot: SourceSnapshot,
) -> "SyncResult":
    generated_sections = _build_generated_section_context(
        options,
        inventory,
        call_edges=graph_observations.resolved_call_edges,
        dependency_analysis=graph_observations.dependency_analysis,
    )
    result = _apply_diff(
        diff,
        options.wiki_dir,
        inventory,
        options.src_dir,
        manifest,
        entity_page_cache=page_maps.entity_page_cache,
        entity_occurrence_page_cache=page_maps.entity_occurrence_page_cache,
        module_page_map=page_maps.module_page_map,
        generated_sections=generated_sections,
        preserve_semantic=options.preserve_semantic,
    )
    _apply_infrastructure_plan(
        options,
        infrastructure_plan,
        result,
        page_maps=page_maps,
        source_snapshot=source_snapshot,
    )

    _apply_surface_page_changes(
        options,
        inventory,
        page_maps,
        surface_plan,
        graph_observations=graph_observations,
    )

    _rebuild_index(
        options.wiki_dir,
        inventory,
        options.src_dir,
        entity_page_cache=page_maps.entity_page_cache,
        entity_occurrence_page_cache=page_maps.entity_occurrence_page_cache,
        module_page_map=page_maps.module_page_map,
        preserve_semantic=options.preserve_semantic,
        workflow_entries=_sync_workflow_index_entries(
            options.wiki_dir,
            inventory,
        ),
        flow_entries=_sync_flow_index_entries(
            options.wiki_dir,
            graph_observations,
        ),
        infra_entries=_sync_infrastructure_index_entries(
            options.wiki_dir,
            infrastructure_plan,
        ),
    )

    _append_log(
        options.wiki_dir,
        options.src_dir,
        diff,
        result,
        surface_plan=surface_plan,
        infrastructure_plan=infrastructure_plan,
    )
    return result


def _apply_surface_page_changes(
    options: _SyncRunOptions,
    inventory: dict,
    page_maps: _SyncPageMaps,
    surface_plan: _SurfaceInitializationPlan,
    *,
    graph_observations: _RuntimeGraphObservations | None = None,
) -> None:
    initializing = bool(options.initialize_surfaces)
    generation_options = runtime_generation_options(
        surfaces=surface_plan.surfaces,
        generation_inputs=surface_plan.generation_inputs,
        include_tests=options.include_tests,
        preserve_semantic=options.preserve_semantic,
    )
    _regenerate_flow_pages(
        options,
        inventory,
        page_maps.module_page_map,
        entry_points=_selected_sync_flow_entries(options, surface_plan),
        allow_create=_surface_policy(surface_plan.surfaces, "flows") is not None,
        api_contracts=surface_plan.api_contracts,
        data_flow_enabled=bool(generation_options["data_flow_enabled"]),
        call_edges=(
            graph_observations.resolved_call_edges
            if graph_observations is not None
            else None
        ),
        evaluated_flows=(
            graph_observations.rendering_flows
            if graph_observations is not None
            else None
        ),
        evaluated_data_flows=(
            graph_observations.rendering_data_flows
            if graph_observations is not None
            else None
        ),
    )
    _regenerate_dependency_pages(
        options,
        surface_plan.dependency_inventory,
        page_maps.module_page_map,
        dependency_analysis=surface_plan.dependency_analysis,
        target_pages=(
            surface_plan.new_dependency_pages
            if initializing
            else surface_plan.dependency_target_pages
        ),
        detail=str(generation_options["dependency_graph_detail"]),
    )
    _regenerate_api_contracts_page(options, page_maps, surface_plan)


def _detect_sync_entry_points(
    inventory: dict, src_dir: str
) -> _SyncEntryPointAnalysis:
    console_scripts = read_console_scripts(src_dir)
    observations = get_detailed_entry_points(
        inventory,
        console_scripts=console_scripts,
        root=src_dir,
        fallback_root=Path.cwd(),
        include_warnings=True,
    )
    for warning in observations.pop("warnings", []):
        print(f"Warning: {warning}", flush=True)
    return _SyncEntryPointAnalysis(
        entries=entry_points_from_detailed_observations(
            observations,
            include_provenance=True,
        ),
        observations=observations,
    )


def _selected_sync_flow_entries(
    options: _SyncRunOptions,
    surface_plan: _SurfaceInitializationPlan,
) -> list[dict]:
    initializing = bool(options.initialize_surfaces)
    selected = (
        surface_plan.new_flow_entries if initializing else surface_plan.flow_entries
    )
    return [dict(entry) for entry in selected]


def _canonical_sync_surface_flow_targets(
    options: _SyncRunOptions,
    entry_points: list[dict],
    surface_plan: _SurfaceInitializationPlan,
) -> list[dict]:
    """Select detected metadata for extant and about-to-be-created flow pages."""

    flows_dir = options.wiki_dir / PageKind.FLOWS.value
    target_ids = (
        {path.stem for path in flows_dir.glob("*.md") if path.is_file()}
        if flows_dir.exists()
        else set()
    )
    target_ids.update(
        str(entry["id"])
        for entry in (*surface_plan.flow_entries, *surface_plan.new_flow_entries)
        if entry.get("id")
    )
    return [
        dict(entry)
        for entry in entry_points
        if str(entry.get("id")) in target_ids
    ]


def _canonical_surface_flow_entries(
    inventory: Mapping[str, Mapping],
    entry_points: list[dict],
    rendering_flows: list[dict],
    rendering_data_flows: list[dict],
) -> list[dict]:
    """Project sync observations into bootstrap's canonical flow metadata."""

    if rendering_data_flows and len(rendering_data_flows) != len(entry_points):
        raise ValueError(
            "rendered data-flow observations must align with flow entry points"
        )
    entries: list[dict] = []
    for index, (entry_point, flow) in enumerate(
        zip(entry_points, rendering_flows, strict=True)
    ):
        data_flow = (
            rendering_data_flows[index]
            if index < len(rendering_data_flows)
            else None
        )
        source_path = entry_point.get("file")
        source_info = (
            inventory.get(source_path, {}) if isinstance(source_path, str) else {}
        )
        flow_entry = {
            "id": entry_point["id"],
            "category": entry_point["category"],
            "entry": entry_point["symbol"],
            "file": source_path,
            "label": entry_point.get("label"),
            "detector": entry_point.get("detector", "unknown"),
            "language": source_info.get("language") or "unknown",
            "evidence": {
                "flow": {
                    "step_count": len(flow.get("steps", [])),
                    "truncated": bool(flow.get("truncated")),
                    "modules_touched": list(flow.get("modules_touched", [])),
                },
                "data_flow": (
                    {
                        "generated": True,
                        "step_count": len(data_flow.get("steps", [])),
                        "transfer_count": len(data_flow.get("transfers", [])),
                        "truncated": bool(data_flow.get("truncated")),
                        "boundary_effects": list(
                            data_flow.get("boundaries", [])
                        ),
                        "gaps": list(data_flow.get("gaps", [])),
                    }
                    if data_flow is not None
                    else None
                ),
            },
        }
        if entry_point.get("routes"):
            flow_entry["routes"] = entry_point["routes"]
        entries.append(flow_entry)
    return entries


def _build_sync_graph_observations(
    options: _SyncRunOptions,
    inventory: dict,
    source_snapshot: SourceSnapshot,
    entry_points: list[dict],
    entrypoint_observations: dict,
    surface_plan: _SurfaceInitializationPlan,
    dependency_analysis: dict | None,
    *,
    data_effect_observations: Mapping | None = None,
    import_observations: Mapping | None = None,
) -> _RuntimeGraphObservations:
    call_edges = [dict(edge) for edge in resolve_call_edges(inventory)]
    call_observations = resolve_call_observations(inventory)
    flow_entries = _selected_sync_flow_entries(options, surface_plan)
    surface_flow_entry_points = _canonical_sync_surface_flow_targets(
        options,
        entry_points,
        surface_plan,
    )
    rendering_flows = [build_flow(entry, call_edges) for entry in flow_entries]
    flows = [build_flow_detailed(entry, call_edges) for entry in flow_entries]
    generation_options = runtime_generation_options(
        surfaces=surface_plan.surfaces,
        generation_inputs=surface_plan.generation_inputs,
        include_tests=options.include_tests,
        preserve_semantic=options.preserve_semantic,
    )
    data_flow_enabled = bool(generation_options["data_flow_enabled"])
    context = (
        build_data_flow_context(
            inventory,
            call_edges,
            data_effect_observations=data_effect_observations,
        )
        if data_flow_enabled and surface_flow_entry_points
        else None
    )
    data_flows: list[dict] = []
    rendering_data_flows: list[dict] = []
    if data_flow_enabled:
        for rendering_flow, flow in zip(rendering_flows, flows, strict=True):
            # The versioned graph projection uses unknown locations instead of
            # legacy line-zero placeholders. Retain the old analyzer result
            # separately so regenerated Markdown remains byte-compatible.
            rendering_data_flows.append(
                analyze_data_flow(
                    inventory,
                    rendering_flow,
                    call_edges,
                    context=context,
                )
            )
            data_flows.append(
                analyze_data_flow_detailed(
                    inventory,
                    flow,
                    call_edges,
                    context=context,
                )
            )
    surface_rendering_flows = rendering_flows
    surface_rendering_data_flows = rendering_data_flows
    if surface_flow_entry_points != flow_entries:
        surface_rendering_flows = [
            build_flow(entry, call_edges) for entry in surface_flow_entry_points
        ]
        surface_rendering_data_flows = (
            [
                analyze_data_flow(
                    inventory,
                    rendering_flow,
                    call_edges,
                    context=context,
                )
                for rendering_flow in surface_rendering_flows
            ]
            if data_flow_enabled
            else []
        )
    limitations: dict[str, tuple[str, ...]] = {}
    if not data_flow_enabled:
        limitations["data-flows"] = ("data-flow-analysis-disabled",)
    if dependency_analysis is None:
        limitations["external-dependencies"] = (
            "dependency-analysis-not-evaluated",
        )
    elif surface_plan.excluded_dependency_tests:
        limitations["external-dependencies"] = (
            "dependency-analysis-excludes-test-sources",
        )
    return _RuntimeGraphObservations(
        resolved_call_edges=call_edges,
        call_observations=call_observations,
        dependency_observations=build_dependency_observations(
            inventory,
            options.src_dir,
            source_snapshot=source_snapshot,
            import_observations=import_observations,
        ),
        entrypoint_observations=entrypoint_observations,
        surface_flow_entries=_canonical_surface_flow_entries(
            inventory,
            surface_flow_entry_points,
            surface_rendering_flows,
            surface_rendering_data_flows,
        ),
        flows=flows,
        rendering_flows=rendering_flows,
        data_flows=data_flows,
        rendering_data_flows=rendering_data_flows,
        external_dependencies=(
            build_external_dependency_observations(dependency_analysis)
            if dependency_analysis is not None
            else []
        ),
        dependency_analysis=dependency_analysis,
        analyzer_limitations=limitations,
    )


def _print_sync_summary(
    result: "SyncResult",
    diff: "SyncDiff",
    infrastructure_plan: InfrastructureSyncPlan | None = None,
) -> None:
    print(
        f"\nSync complete: {result.created} created, {result.updated} updated, "
        f"{result.metadata_only} metadata-only, {result.skipped} skipped, "
        f"{result.deprecated} deprecated."
    )
    if result.preserved_semantic:
        print(f"Preserved semantic fields: {result.preserved_semantic}")
    if diff.moved_entities:
        names = ", ".join(diff.moved_entities.keys())
        print(f"Moved entities detected (pages updated in-place): {names}")
    if infrastructure_plan is not None:
        print(
            "Infrastructure observations: "
            f"{len(infrastructure_plan.new_sources)} added, "
            f"{len(infrastructure_plan.changed_sources)} changed, "
            f"{len(infrastructure_plan.moved_sources)} moved, "
            f"{len(infrastructure_plan.removed_sources)} removed, "
            f"{len(infrastructure_plan.unsupported_yaml)} unsupported YAML."
        )


def _print_surface_summary(plan: _SurfaceInitializationPlan) -> None:
    if not plan.has_work:
        return
    print(
        "Surface initialization: "
        f"{len(plan.new_flow_entries)} flow page(s), "
        f"{len(plan.new_dependency_pages)} dependency page(s), "
        f"{int(plan.new_api_contract_page)} API-contract page(s), "
        f"policy {'updated' if plan.policy_changed else 'unchanged'}."
    )


def _discover_infrastructure_plan(
    source_snapshot: SourceSnapshot,
    generation_inputs: Mapping[str, object],
) -> InfrastructureSyncPlan:
    docker_inventory = get_docker_inventory(
        str(source_snapshot.root),
        source_snapshot=source_snapshot,
    )
    yaml_inventory = get_yaml_infrastructure_inventory(
        source_snapshot.root,
        source_snapshot=source_snapshot,
    )
    infrastructure_inventory = dict(docker_inventory)
    for source_path, info in yaml_inventory.items():
        infrastructure_inventory.setdefault(source_path, info)
    plan = build_infrastructure_sync_plan(
        source_snapshot,
        infrastructure_inventory,
        generation_inputs=generation_inputs,
    )
    print(
        "Infrastructure discovery roots: "
        f"{', '.join(plan.discovery_roots)} "
        f"({len(plan.current_sources)} supported source(s), "
        f"{len(plan.unsupported_yaml)} unsupported YAML candidate(s))."
    )
    if plan.unsupported_yaml:
        print(
            "Unsupported infrastructure YAML: "
            + ", ".join(str(item["path"]) for item in plan.unsupported_yaml)
        )
    return plan


def _with_planned_infrastructure_state(
    plan: _SurfaceInitializationPlan,
    infrastructure_plan: InfrastructureSyncPlan,
) -> _SurfaceInitializationPlan:
    if not infrastructure_plan.state_changed:
        return plan
    generation_inputs = with_infrastructure_generation_input(
        plan.generation_inputs,
        infrastructure_plan,
    )
    return replace(
        plan,
        generation_inputs=generation_inputs,
        generation_inputs_changed=(
            plan.generation_inputs_changed
            or generation_inputs != plan.generation_inputs
        ),
    )


def _prepare_sync_run(options: _SyncRunOptions) -> _PreparedSyncRun | None:
    manifest, seed_manifest = _load_or_seed_manifest(options)
    if manifest is None and not seed_manifest:
        return None

    baseline_manifest = manifest or SyncManifest()
    _preflight_sync_governance(options.wiki_dir, baseline_manifest)
    selected_openapi, generation_inputs = _resolve_openapi_generation_input(
        options, baseline_manifest
    )
    print(f"Syncing wiki from source: {options.src_dir}")
    print(f"Wiki directory: {options.wiki_dir}")
    extracted = _extract_current_inventory(options)
    inventory_result = extracted.result
    source_snapshot = extracted.source_snapshot
    inventory = inventory_result.inventory
    source_content_hashes = source_snapshot.hashes_for(inventory)
    repair_only = manifest is not None and bool(_invalid_manifest_hash_paths(manifest))
    maps = _prepare_sync_page_maps(inventory)
    if manifest is None:
        manifest = _build_manifest_from_inventory(
            inventory,
            options.src_dir,
            entity_page_cache=maps.entity_page_cache,
            entity_occurrence_page_cache=maps.entity_occurrence_page_cache,
            module_page_map=maps.module_page_map,
            retained_page_paths=retained_concept_page_paths(options.wiki_dir),
            unknown_evidence_reason=MANIFEST_STATE_UNAVAILABLE,
            source_content_hashes=source_content_hashes,
        )
    contracts = build_api_contracts(
        inventory,
        openapi_file=selected_openapi,
        source_root=options.src_dir,
    )
    entrypoint_analysis = _detect_sync_entry_points(inventory, options.src_dir)
    entries = attach_routes_to_entry_points(entrypoint_analysis.entries, contracts)
    contracts = _linked_api_contracts(contracts, entries)
    diff = _compute_sync_diff(
        manifest,
        inventory,
        options,
        maps,
        source_content_hashes,
    )
    surface_plan = _build_surface_initialization_plan(
        options,
        manifest,
        inventory,
        entries,
        source_changed=diff.has_changes,
        api_contracts=contracts,
        generation_inputs=generation_inputs,
        source_snapshot=source_snapshot,
    )
    infrastructure_plan = _discover_infrastructure_plan(
        source_snapshot,
        manifest.generation_inputs,
    )
    infrastructure_plan = _qualify_infrastructure_page_drift(
        options,
        infrastructure_plan,
        page_maps=maps,
        source_snapshot=source_snapshot,
    )
    if not seed_manifest and not repair_only and not options.initialize_surfaces:
        surface_plan = _with_planned_infrastructure_state(
            surface_plan,
            infrastructure_plan,
        )
    graph_observations = _build_sync_graph_observations(
        options,
        inventory,
        source_snapshot,
        entries,
        entrypoint_analysis.observations,
        surface_plan,
        surface_plan.dependency_analysis,
        data_effect_observations=inventory_result.data_effect_observations,
        import_observations=inventory_result.import_observations,
    )
    repository_evidence = collect_runtime_repository_evidence(
        options.src_dir,
        options.wiki_dir,
    )
    return _PreparedSyncRun(
        manifest=manifest,
        seed_manifest=seed_manifest,
        repair_only=repair_only,
        inventory_result=inventory_result,
        source_snapshot=source_snapshot,
        inventory=inventory,
        page_maps=maps,
        diff=diff,
        surface_plan=surface_plan,
        repository_evidence=repository_evidence,
        graph_observations=graph_observations,
        infrastructure_plan=infrastructure_plan,
    )


def _preflight_sync_governance(
    wiki_dir: Path,
    manifest: SyncManifest,
) -> None:
    """Reject corrupt or missing committed governance before page mutation."""

    try:
        load_governance(
            wiki_dir,
            expected_bundle_id=committed_governance_bundle_id(
                wiki_dir,
                manifest,
            ),
        )
    except FileNotFoundError:
        marker = manifest.artifact_hashes
        if getattr(marker, "governance_hash", None) is not None:
            raise GovernanceError(
                GOVERNANCE_FILENAME,
                "is missing but the sync manifest commits governed artifacts; "
                "restore the ledger from version control before syncing",
                code="governance-missing",
            )


def _infrastructure_page_path(wiki_dir: Path, record: Mapping[str, object]) -> Path:
    relative = str(record.get("page_path") or "")
    parts = Path(relative).parts
    if (
        len(parts) != 2
        or parts[0] != "infrastructure"
        or not parts[1].endswith(".md")
        or parts[1] in {".md", "..md"}
    ):
        raise ValueError(f"invalid persisted infrastructure page path: {relative!r}")
    return wiki_dir / relative


def _merge_infrastructure_notes(existing: str | None, generated: str) -> str:
    if existing is None or _section_body(existing, "Notes") is None:
        return generated
    return _preserve_level_two_section_exact(existing, generated, "Notes")


def _record_infrastructure_write(
    result: SyncResult,
    state: str,
    *,
    label: str,
) -> None:
    if state == "created":
        result.created += 1
        print(f"  CREATE infrastructure: {label}")
    elif state == "updated":
        result.updated += 1
        print(f"  UPDATE infrastructure: {label}")
    else:
        result.skipped += 1
        print(f"  SKIP infrastructure (unchanged): {label}")


def _write_current_infrastructure_page(
    options: _SyncRunOptions,
    plan: InfrastructureSyncPlan,
    result: SyncResult,
    source_path: str,
    *,
    module_page_map: Mapping[str, str],
    unsupported_sources: Mapping[str, Mapping[str, object]],
    semantic_source: Path | None = None,
) -> Path:
    record = plan.current_sources[source_path]
    path = _infrastructure_page_path(options.wiki_dir, record)
    existing_path = (
        (path if path.is_file() else semantic_source)
        if options.preserve_semantic
        else None
    )
    existing = read_md(existing_path) if existing_path and existing_path.is_file() else None
    generated = _generate_infrastructure_md(
        source_path,
        plan.inventory[source_path],
        module_page_map,
        {
            source: dict(details)
            for source, details in unsupported_sources.items()
        },
    )
    merged = _merge_infrastructure_notes(existing, generated)
    state = _write_md_if_changed(path, merged)
    _record_infrastructure_write(result, state, label=source_path)
    return path


def _infrastructure_tombstone_markdown(
    source_path: str,
    record: Mapping[str, object],
) -> str:
    adapter = str(record.get("adapter") or "unknown")
    return (
        f"# Removed infrastructure: {source_path}\n\n"
        "> ⚠️ **Stale observation:** The mapped infrastructure source is no longer "
        "present in the current discovery snapshot.\n\n"
        f"**Path:** `{source_path}`\n"
        f"**Type:** `{adapter}`\n"
        "**Observation State:** `source-removed`\n\n"
        "## Notes\n\n"
        "_Add retained operational context here; this page is not current source "
        "evidence._\n"
    )


def _qualify_infrastructure_page_drift(
    options: _SyncRunOptions,
    plan: InfrastructureSyncPlan,
    *,
    page_maps: _SyncPageMaps,
    source_snapshot: SourceSnapshot,
) -> InfrastructureSyncPlan:
    """Promote page drift without treating the semantic Notes body as generated."""

    changed = set(plan.changed_sources)
    unsupported_sources = unsupported_source_summary(source_snapshot)
    for source_path in plan.unchanged_sources:
        record = plan.current_sources[source_path]
        path = _infrastructure_page_path(options.wiki_dir, record)
        existing = read_md(path) if path.is_file() else None
        generated = _generate_infrastructure_md(
            source_path,
            plan.inventory[source_path],
            page_maps.module_page_map,
            unsupported_sources,
        )
        expected = _merge_infrastructure_notes(
            existing if options.preserve_semantic else None,
            generated,
        )
        if existing is None or _normalize_md(existing) != _normalize_md(expected):
            changed.add(source_path)

    repair_tombstones: list[str] = []
    cleanup_moved_pages: list[str] = []
    raw_tombstones = plan.next_state.get("tombstones")
    tombstones = raw_tombstones if isinstance(raw_tombstones, Mapping) else {}
    for source_path, raw_record in sorted(tombstones.items()):
        if not isinstance(source_path, str) or not isinstance(raw_record, Mapping):
            continue
        if source_path in plan.removed_sources or source_path in plan.moved_sources:
            continue
        path = _infrastructure_page_path(options.wiki_dir, raw_record)
        reason = raw_record.get("reason")
        if reason == "source-moved":
            if path.is_file():
                cleanup_moved_pages.append(source_path)
            continue
        if reason != "source-removed":
            continue
        existing = read_md(path) if path.is_file() else None
        expected = _merge_infrastructure_notes(
            existing if options.preserve_semantic else None,
            _infrastructure_tombstone_markdown(source_path, raw_record),
        )
        if existing is None or _normalize_md(existing) != _normalize_md(expected):
            repair_tombstones.append(source_path)

    unchanged = tuple(
        source_path
        for source_path in plan.unchanged_sources
        if source_path not in changed
    )
    return replace(
        plan,
        changed_sources=tuple(sorted(changed)),
        unchanged_sources=unchanged,
        repair_tombstones=tuple(repair_tombstones),
        cleanup_moved_pages=tuple(cleanup_moved_pages),
    )


def _apply_infrastructure_plan(
    options: _SyncRunOptions,
    plan: InfrastructureSyncPlan,
    result: SyncResult,
    *,
    page_maps: _SyncPageMaps,
    source_snapshot: SourceSnapshot,
) -> None:
    unsupported_sources = unsupported_source_summary(source_snapshot)
    for old_path, new_path in plan.moved_sources.items():
        old_page = _infrastructure_page_path(options.wiki_dir, plan.prior_sources[old_path])
        new_page = _write_current_infrastructure_page(
            options,
            plan,
            result,
            new_path,
            module_page_map=page_maps.module_page_map,
            unsupported_sources=unsupported_sources,
            semantic_source=old_page,
        )
        if old_page != new_page and old_page.is_file():
            old_page.unlink()
            print(f"  MOVE infrastructure: {old_path} -> {new_path}")
    for source_path in (*plan.new_sources, *plan.changed_sources):
        prior_record = plan.prior_sources.get(source_path)
        old_page = (
            _infrastructure_page_path(options.wiki_dir, prior_record)
            if prior_record is not None
            else None
        )
        new_page = _write_current_infrastructure_page(
            options,
            plan,
            result,
            source_path,
            module_page_map=page_maps.module_page_map,
            unsupported_sources=unsupported_sources,
            semantic_source=old_page,
        )
        if old_page is not None and old_page != new_page and old_page.is_file():
            old_page.unlink()
            print(f"  RENAME infrastructure page mapping: {source_path}")
    for source_path in plan.removed_sources:
        record = plan.prior_sources[source_path]
        path = _infrastructure_page_path(options.wiki_dir, record)
        existing = read_md(path) if path.is_file() else None
        tombstone = _merge_infrastructure_notes(
            existing if options.preserve_semantic else None,
            _infrastructure_tombstone_markdown(source_path, record),
        )
        state = _write_md_if_changed(path, tombstone)
        _record_infrastructure_write(result, state, label=f"{source_path} (removed)")
        result.deprecated += 1
    raw_tombstones = plan.next_state.get("tombstones")
    tombstones = raw_tombstones if isinstance(raw_tombstones, Mapping) else {}
    for source_path in plan.repair_tombstones:
        record = tombstones[source_path]
        path = _infrastructure_page_path(options.wiki_dir, record)
        existing = read_md(path) if path.is_file() else None
        tombstone = _merge_infrastructure_notes(
            existing if options.preserve_semantic else None,
            _infrastructure_tombstone_markdown(source_path, record),
        )
        state = _write_md_if_changed(path, tombstone)
        _record_infrastructure_write(result, state, label=f"{source_path} (removed)")
    for source_path in plan.cleanup_moved_pages:
        record = tombstones[source_path]
        path = _infrastructure_page_path(options.wiki_dir, record)
        if path.is_file():
            path.unlink()
            print(f"  REMOVE moved infrastructure page: {source_path}")


def _apply_prepared_sync(
    options: _SyncRunOptions, prepared: _PreparedSyncRun
) -> SyncResult:
    if prepared.repair_only or (
        prepared.seed_manifest and not options.initialize_surfaces
    ):
        return SyncResult()
    if prepared.diff.has_changes and not options.initialize_surfaces:
        return _apply_sync_changes(
            options,
            prepared.manifest,
            prepared.inventory,
            prepared.diff,
            prepared.page_maps,
            prepared.surface_plan,
            prepared.graph_observations,
            prepared.infrastructure_plan,
            prepared.source_snapshot,
        )
    result = SyncResult()
    if not options.initialize_surfaces:
        _apply_infrastructure_plan(
            options,
            prepared.infrastructure_plan,
            result,
            page_maps=prepared.page_maps,
            source_snapshot=prepared.source_snapshot,
        )
    _apply_surface_page_changes(
        options,
        prepared.inventory,
        prepared.page_maps,
        prepared.surface_plan,
        graph_observations=prepared.graph_observations,
    )
    if options.initialize_surfaces:
        _rebuild_surface_only_index(
            options.wiki_dir,
            prepared.manifest,
            preserve_semantic=options.preserve_semantic,
            workflow_entries=_sync_workflow_index_entries(
                options.wiki_dir,
                prepared.inventory,
            ),
            flow_entries=_sync_flow_index_entries(
                options.wiki_dir,
                prepared.graph_observations,
            ),
            infra_entries=_sync_infrastructure_index_entries(
                options.wiki_dir,
                prepared.infrastructure_plan,
            ),
        )
    else:
        _rebuild_index(
            options.wiki_dir,
            prepared.inventory,
            options.src_dir,
            entity_page_cache=prepared.page_maps.entity_page_cache,
            entity_occurrence_page_cache=(
                prepared.page_maps.entity_occurrence_page_cache
            ),
            module_page_map=prepared.page_maps.module_page_map,
            preserve_semantic=options.preserve_semantic,
            workflow_entries=_sync_workflow_index_entries(
                options.wiki_dir,
                prepared.inventory,
            ),
            flow_entries=_sync_flow_index_entries(
                options.wiki_dir,
                prepared.graph_observations,
            ),
            infra_entries=_sync_infrastructure_index_entries(
                options.wiki_dir,
                prepared.infrastructure_plan,
            ),
        )
    if (
        prepared.diff.has_changes
        or prepared.surface_plan.has_work
        or prepared.infrastructure_plan.has_changes
    ):
        _append_log(
            options.wiki_dir,
            options.src_dir,
            prepared.diff,
            result,
            surface_plan=prepared.surface_plan,
            infrastructure_plan=prepared.infrastructure_plan,
        )
    return result


def _finalize_prepared_sync(
    options: _SyncRunOptions,
    prepared: _PreparedSyncRun,
    result: SyncResult,
    *,
    target_wiki_dir: Path | None = None,
    dry_run: bool = False,
) -> KnowledgeCommitResult:
    target = target_wiki_dir or options.wiki_dir
    page_source_overrides = None
    if options.initialize_surfaces and not prepared.repair_only:
        page_source_overrides = {
            page_path: mapping.source_path
            for page_path, mapping in prepared.manifest.page_source_mappings.items()
        }
    surface = evaluate_surface_index(
        options.wiki_dir,
        prepared.inventory,
        src_dir=options.src_dir,
        entity_page_cache=prepared.page_maps.entity_page_cache,
        entity_occurrence_page_cache=(prepared.page_maps.entity_occurrence_page_cache),
        module_page_map=prepared.page_maps.module_page_map,
        entry_points=prepared.graph_observations.surface_flow_entries,
        page_source_overrides=page_source_overrides,
    )
    next_manifest = None
    if options.initialize_surfaces and not prepared.repair_only:
        next_manifest = prepared.manifest.with_generation_state(
            surfaces=prepared.surface_plan.surfaces,
            generation_inputs=prepared.surface_plan.generation_inputs,
        )
    artifact_result = finalize_runtime_knowledge(
        RuntimeKnowledgeInputs(
            target_wiki_dir=target,
            inventory=prepared.inventory,
            surface=surface,
            source_snapshot=prepared.source_snapshot,
            module_page_map=prepared.page_maps.module_page_map,
            entity_occurrence_page_map=(
                prepared.page_maps.entity_occurrence_page_cache
            ),
            repository_evidence=prepared.repository_evidence,
            inventory_complete=True,
            previous_manifest=prepared.manifest,
            next_manifest=next_manifest,
            manifest_surfaces=prepared.surface_plan.surfaces,
            manifest_generation_inputs=prepared.surface_plan.generation_inputs,
            unknown_evidence_reason=(
                MANIFEST_REPAIR_UNAVAILABLE
                if prepared.repair_only
                else MANIFEST_STATE_UNAVAILABLE
                if prepared.seed_manifest
                else EVIDENCE_NOT_RECORDED
            ),
            force_unknown_evidence=(prepared.seed_manifest or prepared.repair_only),
            extractor_registry=prepared.inventory_result.extractor_registry,
            plugin_extractor_components=(prepared.inventory_result.plugin_components),
            plugin_components=(prepared.inventory_result.producer_plugin_components),
            plugin_lock_path=prepared.inventory_result.plugin_lock_path,
            plugin_lock_hash=prepared.inventory_result.plugin_lock_hash,
            generation_options=runtime_generation_options(
                surfaces=prepared.surface_plan.surfaces,
                generation_inputs=prepared.surface_plan.generation_inputs,
                include_tests=options.include_tests,
                preserve_semantic=options.preserve_semantic,
            ),
            generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS,
            generation_option_allowlist=tuple(RUNTIME_GENERATION_OPTION_DEFAULTS),
            call_edges=prepared.graph_observations.call_observations,
            dependency_observations=(
                prepared.graph_observations.dependency_observations
            ),
            entrypoint_observations=(
                prepared.graph_observations.entrypoint_observations
            ),
            flows=prepared.graph_observations.flows,
            data_flows=prepared.graph_observations.data_flows,
            external_dependencies=(
                prepared.graph_observations.external_dependencies
            ),
            graph_analyzer_limitations=(
                prepared.graph_observations.analyzer_limitations
            ),
            governance_moves=_governance_moves_for_sync(
                prepared.diff,
                prepared.manifest,
                entity_page_cache=prepared.page_maps.entity_page_cache,
            )
            if (target / GOVERNANCE_FILENAME).is_file()
            else {},
        ),
        dry_run=dry_run,
    )
    _print_sync_artifact_actions(artifact_result)
    if dry_run:
        return artifact_result

    if prepared.repair_only:
        invalid_hashes = len(_invalid_manifest_hash_paths(prepared.manifest))
        print(
            "Sync manifest repaired: "
            f"{invalid_hashes} source entr"
            f"{'y has' if invalid_hashes == 1 else 'ies have'} invalid or missing hashes."
        )
        print(
            "Wiki pages were not modified. Run `llm-wiki sync` again to apply "
            "source changes."
        )
    elif prepared.seed_manifest:
        print(
            "No sync manifest found — seeding from current source state.\n"
            "Existing wiki pages were not modified.\n"
            "Future `llm-wiki sync` runs will update incrementally."
        )
        print(f"Manifest written to {target / MANIFEST_FILENAME}")
        if artifact_result.committed_manifest.tombstones:
            print(
                "Retained stale pages with unknown provenance: "
                f"{len(artifact_result.committed_manifest.tombstones)}."
            )
        if options.initialize_surfaces:
            _print_surface_summary(prepared.surface_plan)
    elif options.initialize_surfaces:
        _print_surface_summary(prepared.surface_plan)
        deferred = len(_affected_source_files(prepared.diff))
        if deferred:
            print(f"Deferred source changes: {deferred} file(s).")
        elif not prepared.surface_plan.has_work:
            print("Requested optional surfaces are up to date.")
    else:
        if (
            prepared.diff.has_changes
            or prepared.surface_plan.has_work
            or prepared.infrastructure_plan.has_changes
        ):
            _print_sync_summary(
                result,
                prepared.diff,
                prepared.infrastructure_plan,
            )
        else:
            print("Wiki is up to date.")
    _print_cache_stats(
        prepared.inventory_result.cache_stats,
        enabled=options.cache_stats_enabled,
    )
    return artifact_result


def _print_sync_artifact_actions(result: KnowledgeCommitResult) -> None:
    prefix = "DRY-RUN: " if result.dry_run else ""
    labels = (
        ("Surface index", result.surface_index),
        ("Knowledge index", result.knowledge_index),
        ("Manifest", result.manifest),
    )
    for label, artifact in labels:
        if artifact.state is ArtifactWriteState.UNCHANGED:
            action = "unchanged"
        else:
            action = artifact.state.value
        print(f"{prefix}{label}: {action} ({artifact.relative_path})", flush=True)


def _run_sync_dry_run(
    options: _SyncRunOptions,
    prepared: _PreparedSyncRun,
) -> None:
    unsafe_symlink = _unsafe_dry_run_symlink(options.wiki_dir)
    if unsafe_symlink is not None:
        print(
            "Error: sync dry-run cannot safely stage a wiki containing an "
            f"external or broken symbolic link: {unsafe_symlink}.",
            file=sys.stderr,
        )
        sys.exit(2)
    _print_dry_run_plan(
        options,
        prepared.diff,
        prepared.surface_plan,
        prepared.infrastructure_plan,
        prepared.manifest,
        seed_manifest=prepared.seed_manifest,
        repair_only=prepared.repair_only,
    )
    with tempfile.TemporaryDirectory(prefix="llm-wiki-sync-preview-") as temp_dir:
        staged_wiki = Path(temp_dir) / "wiki"
        if options.wiki_dir.exists():
            shutil.copytree(
                options.wiki_dir,
                staged_wiki,
                symlinks=True,
            )
        else:
            staged_wiki.mkdir(parents=True)
        staged_options = replace(
            options,
            wiki_dir=staged_wiki,
            dry_run=False,
        )
        result = _apply_prepared_sync(staged_options, prepared)
        _finalize_prepared_sync(
            staged_options,
            prepared,
            result,
            target_wiki_dir=options.wiki_dir,
            dry_run=True,
        )
    _print_cache_stats(
        prepared.inventory_result.cache_stats,
        enabled=options.cache_stats_enabled,
    )


def _unsafe_dry_run_symlink(wiki_dir: Path) -> str | None:
    """Return the first symlink that would escape an isolated preview tree."""

    if not wiki_dir.exists():
        return None
    resolved_root = wiki_dir.resolve()
    for directory, directory_names, filenames in os.walk(
        wiki_dir,
        followlinks=False,
    ):
        directory_names.sort()
        filenames.sort()
        parent = Path(directory)
        for name in (*directory_names, *filenames):
            candidate = parent / name
            if not candidate.is_symlink():
                continue
            relative_path = candidate.relative_to(wiki_dir).as_posix()
            try:
                raw_target = Path(os.readlink(candidate))
                if raw_target.is_absolute():
                    return relative_path
                resolved_target = candidate.resolve(strict=True)
                if not resolved_target.is_relative_to(resolved_root):
                    return relative_path
            except (OSError, RuntimeError):
                return relative_path
    return None


def run(args) -> None:
    options = _sync_run_options_from_args(args)
    try:
        prepared = _prepare_sync_run(options)
    except (ApiContractError, GovernanceError, InfrastructureSyncError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)
    if prepared is None:
        return

    if options.dry_run:
        _run_sync_dry_run(options, prepared)
        return
    if (
        not options.initialize_surfaces
        and not prepared.seed_manifest
        and not prepared.repair_only
    ):
        _exit_if_large_unforced_diff(
            options,
            prepared.diff,
            prepared.manifest,
            prepared.inventory_result,
            prepared.infrastructure_plan,
        )
    if not prepared.seed_manifest and not prepared.repair_only:
        _exit_if_large_unforced_surface_plan(options, prepared.surface_plan)
    result = _apply_prepared_sync(options, prepared)
    _finalize_prepared_sync(options, prepared, result)


# ── Index + log helpers ───────────────────────────────────────────────────────


def _preserve_index_custom_sections(old_md: str, new_md: str) -> str:
    return _service_preserve_index_custom_sections(old_md, new_md)


def _overlay_live_index_metadata(
    existing: list[dict],
    live: Iterable[Mapping],
    *,
    key: str,
) -> list[dict]:
    """Retain existing page coverage while preferring canonical live metadata."""

    live_by_id = {
        str(entry[key]): dict(entry) for entry in live if entry.get(key) is not None
    }
    return [live_by_id.get(str(entry[key]), entry) for entry in existing]


def _sync_workflow_index_entries(wiki_dir: Path, inventory: dict) -> list[dict]:
    live_entries = [
        {"name": name, "entry": workflow["entry"]}
        for name, workflow in get_call_graph(inventory).items()
    ]
    return _overlay_live_index_metadata(
        _list_existing_pages(wiki_dir / PageKind.WORKFLOWS.value, "entry"),
        live_entries,
        key="name",
    )


def _sync_flow_index_entries(
    wiki_dir: Path,
    graph_observations: _RuntimeGraphObservations,
) -> list[dict]:
    return _overlay_live_index_metadata(
        _list_existing_flow_pages(wiki_dir / PageKind.FLOWS.value),
        graph_observations.surface_flow_entries,
        key="id",
    )


def _sync_infrastructure_index_entries(
    wiki_dir: Path,
    plan: InfrastructureSyncPlan,
) -> list[dict]:
    live_entries = []
    for source_path, info in sorted(plan.inventory.items()):
        record = plan.current_sources[source_path]
        page_name = Path(str(record["page_path"])).stem
        live_entries.append(
            {
                "name": page_name,
                "type": info["type"],
                "label": infrastructure_display_label(source_path, info),
            }
        )
    return _overlay_live_index_metadata(
        _list_existing_pages(
            wiki_dir / PageKind.INFRASTRUCTURE.value,
            "type",
        ),
        live_entries,
        key="name",
    )


def _rebuild_index(
    wiki_dir: Path,
    inventory: dict,
    src_dir: str,
    *,
    entity_page_cache: dict[tuple[str, str], str] | None = None,
    entity_occurrence_page_cache: dict[tuple[str, str, int], str] | None = None,
    module_page_map: dict[str, str] | None = None,
    preserve_semantic: bool = True,
    workflow_entries: list[dict] | None = None,
    flow_entries: list[dict] | None = None,
    infra_entries: list[dict] | None = None,
) -> None:
    """Regenerate index.md from the live inventory."""
    if entity_page_cache is None:
        _, _, entity_page_cache = _collision_maps(inventory, src_dir)
    mod_page_map = module_page_map or build_module_page_map(inventory)
    if entity_occurrence_page_cache is None:
        entity_occurrence_page_cache = build_entity_occurrence_page_map(
            inventory, mod_page_map
        )

    all_entity_names: list[str] = []
    seen: set[str] = set()
    module_entries: list[dict] = []

    for filepath, file_data in inventory.items():
        mod_page_name = mod_page_map.get(filepath, _page_name_for_module(filepath))
        module_entries.append(
            {
                "name": mod_page_name,
                "path": filepath,
                "docstring": file_data.get("module_docstring", ""),
            }
        )
        seen_names: dict[str, int] = {}
        for cls in file_data.get("classes", []):
            name = cls["name"]
            seen_names[name] = seen_names.get(name, 0) + 1
            page_name = entity_occurrence_page_cache.get(
                (name, filepath, seen_names[name]),
                entity_page_cache[(name, filepath)],
            )
            if page_name not in seen:
                all_entity_names.append(page_name)
                seen.add(page_name)

    # Collect any existing semantic/user-facing entries from disk.
    if workflow_entries is None:
        workflow_entries = _list_existing_pages(
            wiki_dir / PageKind.WORKFLOWS.value,
            "entry",
        )
    guide_entries = _list_existing_pages(wiki_dir / "guides", "topic")
    if flow_entries is None:
        flow_entries = _list_existing_flow_pages(
            wiki_dir / PageKind.FLOWS.value
        )
    if infra_entries is None:
        infra_entries = _list_existing_pages(
            wiki_dir / PageKind.INFRASTRUCTURE.value,
            "type",
        )
    architecture_entries = _list_existing_architecture_pages(wiki_dir)

    index_path = wiki_dir / "index.md"
    new_index = _generate_index_md(
        all_entity_names,
        module_entries,
        workflow_entries=workflow_entries or None,
        guide_entries=guide_entries or None,
        infra_entries=infra_entries or None,
        flow_entries=flow_entries or None,
        architecture_entries=architecture_entries or None,
        api_contracts_present=(wiki_dir / "api-contracts.md").is_file(),
    )
    if preserve_semantic and index_path.exists():
        new_index = _preserve_index_custom_sections(read_md(index_path), new_index)
    write_state = _write_md_if_changed(
        index_path,
        new_index,
    )
    if write_state == "unchanged":
        print("  SKIP index.md (unchanged)")
    else:
        print("  WRITE index.md")


def _rebuild_surface_only_index(
    wiki_dir: Path,
    manifest: SyncManifest,
    *,
    preserve_semantic: bool = True,
    workflow_entries: list[dict] | None = None,
    flow_entries: list[dict] | None = None,
    infra_entries: list[dict] | None = None,
) -> None:
    """Re-index only pages already present during source-deferred backfill."""
    entity_names = [
        path.stem
        for path in sorted((wiki_dir / PageKind.ENTITIES.value).glob("*.md"))
        if path.is_file()
    ]
    source_by_module_page = {}
    description_by_module_page = {}
    for filepath, info in manifest.sources.items():
        page = str(info.get("module_page") or _module_name_from_path(filepath))
        source_by_module_page[page] = filepath
        semantics = info.get("generated_semantics")
        module_semantics = (
            semantics.get("module") if isinstance(semantics, Mapping) else None
        )
        if isinstance(module_semantics, Mapping):
            description_by_module_page[page] = str(
                module_semantics.get("description") or ""
            )
    module_entries = [
        {
            "name": path.stem,
            "path": source_by_module_page.get(path.stem, ""),
            "docstring": description_by_module_page.get(path.stem, ""),
        }
        for path in sorted((wiki_dir / PageKind.MODULES.value).glob("*.md"))
        if path.is_file()
    ]
    index_path = wiki_dir / canonical_path(PageKind.INDEX)
    if workflow_entries is None:
        workflow_entries = _list_existing_pages(
            wiki_dir / PageKind.WORKFLOWS.value,
            "entry",
        )
    if flow_entries is None:
        flow_entries = _list_existing_flow_pages(
            wiki_dir / PageKind.FLOWS.value
        )
    if infra_entries is None:
        infra_entries = _list_existing_pages(
            wiki_dir / PageKind.INFRASTRUCTURE.value,
            "type",
        )
    new_index = _generate_index_md(
        entity_names,
        module_entries,
        workflow_entries=workflow_entries or None,
        guide_entries=_list_existing_pages(wiki_dir / PageKind.GUIDES.value, "topic")
        or None,
        infra_entries=infra_entries or None,
        flow_entries=flow_entries or None,
        architecture_entries=_list_existing_architecture_pages(wiki_dir) or None,
        api_contracts_present=(
            wiki_dir / canonical_path(PageKind.API_CONTRACTS)
        ).is_file(),
        log_present=(wiki_dir / canonical_path(PageKind.LOG)).is_file(),
    )
    if preserve_semantic and index_path.exists():
        new_index = _preserve_index_custom_sections(read_md(index_path), new_index)
    state = _write_md_if_changed(index_path, new_index)
    if state == "unchanged":
        print("  SKIP index.md (unchanged)")
    else:
        print("  WRITE index.md")


def _list_existing_pages(directory: Path, extra_key: str) -> list[dict]:
    """Return a list of ``{"name": stem}`` dicts for every .md file in *directory*."""
    if not directory.exists():
        return []
    return [
        {"name": p.stem, "label": _markdown_title(p), extra_key: ""}
        for p in sorted(directory.glob("*.md"))
    ]


def _markdown_title(path: Path) -> str:
    try:
        for line in read_md(path).splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
    except OSError:
        return ""
    return ""


# Top-level architecture pages (stem → index label), regenerated and re-linked
# on sync so they neither go stale nor get orphaned (DL-502).
_ARCHITECTURE_PAGES: tuple[tuple[str, str], ...] = (
    (PageKind.DEPENDENCIES.value, "Dependencies"),
    (PageKind.LOAD_ORDER.value, "Load order"),
)


def _list_existing_architecture_pages(wiki_dir: Path) -> list[dict]:
    """Return ``{"name", "page"}`` entries for architecture pages present on disk."""
    return [
        {"name": label, "page": stem}
        for stem, label in _ARCHITECTURE_PAGES
        if (wiki_dir / f"{stem}.md").exists()
    ]


def _list_existing_flow_pages(directory: Path) -> list[dict]:
    """Return ``{"id", "category"}`` dicts for existing flow pages.

    ``category`` is derived from the entry-point id prefix so the index can be
    regrouped without re-running entry-point detection.
    """
    if not directory.exists():
        return []
    return [
        {"id": p.stem, "category": p.stem.split("-", 1)[0]}
        for p in sorted(directory.glob("*.md"))
    ]


def _preserve_flow_behavior(old_md: str, new_md: str) -> str:
    """Carry a human-edited ``## Behavior`` section into regenerated flow md."""
    return _preserve_level_two_section_exact(old_md, new_md, "Behavior")


def _api_operations_for_flow(
    contracts: Mapping[str, object] | None, entry_point: Mapping[str, object]
) -> list[dict]:
    if not contracts:
        return []
    file = str(entry_point.get("file") or "")
    symbol = str(entry_point.get("symbol") or "").rsplit(".", 1)[-1]
    matches = []
    operations = contracts.get("operations")
    if not isinstance(operations, list):
        return []
    for operation in operations:
        if not isinstance(operation, Mapping):
            continue
        handler = operation.get("handler")
        if not isinstance(handler, Mapping):
            continue
        handler_symbol = str(handler.get("symbol") or "").rsplit(".", 1)[-1]
        if str(handler.get("file") or "") == file and handler_symbol == symbol:
            matches.append(dict(operation))
    return matches


def _regenerate_flow_pages(
    options: _SyncRunOptions,
    inventory: dict,
    module_page_map: dict[str, str],
    *,
    entry_points: list[dict] | None = None,
    allow_create: bool = False,
    api_contracts: Mapping[str, object] | None = None,
    data_flow_enabled: bool = True,
    call_edges: list[dict] | None = None,
    evaluated_flows: list[dict] | None = None,
    evaluated_data_flows: list[dict] | None = None,
) -> int:
    """Regenerate flow pages from the current inventory, preserving Behavior.

    Legacy projects run only when a flow page already exists; explicit surface
    policy can opt into creating selected missing pages. Detection and Mermaid
    diagrams are recomputed from the full inventory, content-equal pages are not
    rewritten, and human-edited ``## Behavior`` is preserved by default.
    """
    flows_dir = options.wiki_dir / "flows"
    has_existing_pages = flows_dir.exists() and any(flows_dir.glob("*.md"))
    if not has_existing_pages and not allow_create:
        return 0

    if entry_points is None:
        entry_points = _detect_sync_entry_points(inventory, options.src_dir).entries
    edges = (
        call_edges
        if call_edges is not None
        else resolve_call_edges(inventory)
        if entry_points
        else []
    )
    data_flow_context = (
        build_data_flow_context(inventory, edges)
        if data_flow_enabled and entry_points and evaluated_data_flows is None
        else None
    )
    flow_by_id = {
        str(entry.get("id")): flow
        for flow in evaluated_flows or []
        if isinstance(flow, Mapping)
        and isinstance((entry := flow.get("entry")), Mapping)
        and entry.get("id")
    }
    data_flow_by_id = {
        str(entry.get("id")): data_flow
        for data_flow in evaluated_data_flows or []
        if isinstance(data_flow, Mapping)
        and isinstance((entry := data_flow.get("entry")), Mapping)
        and entry.get("id")
    }
    regenerated = 0
    for entry_point in entry_points:
        flow = flow_by_id.get(str(entry_point.get("id"))) or build_flow(
            entry_point, edges
        )
        data_flow = (
            data_flow_by_id.get(str(entry_point.get("id")))
            or analyze_data_flow(inventory, flow, edges, context=data_flow_context)
            if data_flow_enabled
            else None
        )
        new_md = _generate_flow_md(
            flow,
            module_page_map,
            data_flow=data_flow,
            diagram_style=(
                _generated_diagram_style(
                    "data_flow",
                    root=options.src_dir,
                    fallback_root=Path.cwd(),
                    flow_id=entry_point.get("id"),
                    category=entry_point.get("category"),
                )
                if data_flow is not None
                else None
            ),
            api_contract_operations=_api_operations_for_flow(
                api_contracts, entry_point
            ),
        )
        flow_path = flows_dir / f"{entry_point['id']}.md"
        if options.preserve_semantic and flow_path.exists():
            new_md = _preserve_flow_behavior(read_md(flow_path), new_md)
        state = _write_md_if_changed(flow_path, new_md)
        if state != "unchanged":
            print(f"  {state.upper()} flow: {entry_point['id']}")
            regenerated += 1
    if regenerated:
        print(f"Regenerated {regenerated} flow page(s).")
    return regenerated


def _regenerate_api_contracts_page(
    options: _SyncRunOptions,
    page_maps: _SyncPageMaps,
    plan: _SurfaceInitializationPlan,
) -> int:
    """Regenerate the canonical mixed API surface while preserving Notes."""
    if not plan.api_contract_target or plan.api_contracts is None:
        return 0
    if (
        options.initialize_surfaces
        and not plan.new_api_contract_page
        and not plan.generation_inputs_changed
    ):
        return 0
    path = options.wiki_dir / f"{PageKind.API_CONTRACTS.value}.md"
    new_md = render_api_contracts_markdown(
        plan.api_contracts,
        module_page_map=page_maps.module_page_map,
        entity_page_map=page_maps.entity_page_cache,
    )
    if options.preserve_semantic and path.exists():
        new_md = _preserve_notes(read_md(path), new_md)
    state = _write_md_if_changed(path, new_md)
    if state == "unchanged":
        return 0
    print(f"  {state.upper()} {path.name}")
    return 1


def _preserve_notes(old_md: str, new_md: str) -> str:
    """Carry a human-edited ``## Notes`` section into regenerated architecture md."""
    return _preserve_level_two_section_exact(old_md, new_md, "Notes")


def _regenerate_dependency_pages(
    options: _SyncRunOptions,
    inventory: dict,
    module_page_map: dict[str, str],
    *,
    dependency_analysis: dict | None = None,
    target_pages: Iterable[str] | None = None,
    detail: str = "auto",
) -> int:
    """Regenerate dependencies.md / load-order.md, preserving ``## Notes``.

    Legacy projects regenerate only root pages already present. Explicit
    surface policy may select missing architecture pages for creation. The
    graph, cycles, reconciliation, and load order are computed once; unchanged
    Markdown is not rewritten and human-authored ``## Notes`` is preserved.
    """
    deps_path = options.wiki_dir / "dependencies.md"
    load_path = options.wiki_dir / "load-order.md"
    selected_pages = (
        set(target_pages)
        if target_pages is not None
        else {
            stem
            for stem, _label in _ARCHITECTURE_PAGES
            if (options.wiki_dir / f"{stem}.md").exists()
        }
    )
    if not selected_pages:
        return 0

    analysis = dependency_analysis or analyze_dependencies(inventory, options.src_dir)
    pages = (
        (
            deps_path,
            _generate_dependencies_md(
                analysis,
                module_page_map,
                detail=detail,
                diagram_style=_generated_diagram_style(
                    "dependencies",
                    root=options.src_dir,
                    fallback_root=Path.cwd(),
                    detail=detail,
                ),
            ),
        ),
        (load_path, _generate_load_order_md(analysis, module_page_map)),
    )
    regenerated = 0
    for path, new_md in pages:
        if path.stem not in selected_pages:
            continue
        if options.preserve_semantic and path.exists():
            new_md = _preserve_notes(read_md(path), new_md)
        state = _write_md_if_changed(path, new_md)
        if state != "unchanged":
            print(f"  {state.upper()} {path.name}")
            regenerated += 1
    if regenerated:
        print(f"Regenerated {regenerated} architecture page(s).")
    return regenerated


def _append_log(
    wiki_dir: Path,
    src_dir: str,
    diff: SyncDiff,
    result: SyncResult,
    *,
    surface_plan: _SurfaceInitializationPlan | None = None,
    infrastructure_plan: InfrastructureSyncPlan | None = None,
) -> None:
    log_path = wiki_dir / "log.md"
    today = date.today().isoformat()
    moved_str = (
        ", ".join(
            f"`{cls}` ({old} → {new})"
            for cls, (old, new) in diff.moved_entities.items()
        )
        if diff.moved_entities
        else "none"
    )
    surface_lines = ""
    if surface_plan is not None and surface_plan.has_work:
        categories = Counter(
            str(entry.get("category") or "unknown")
            for entry in surface_plan.new_flow_entries
        )
        category_text = (
            ", ".join(
                f"{category}={count}" for category, count in sorted(categories.items())
            )
            or "none"
        )
        surface_lines = (
            f"- Flow pages initialized: {len(surface_plan.new_flow_entries)} "
            f"({category_text})\n"
            "- Dependency pages initialized: "
            f"{len(surface_plan.new_dependency_pages)}\n"
            "- Surface policy updated: "
            f"{'yes' if surface_plan.policy_changed else 'no'}\n"
        )
        if surface_plan.requested_surfaces:
            surface_lines += (
                f"- Source files deferred: {len(_affected_source_files(diff))}\n"
            )
    operation = (
        "surface initialization"
        if surface_plan is not None and surface_plan.requested_surfaces
        else "incremental sync"
    )
    infrastructure_lines = ""
    if infrastructure_plan is not None and infrastructure_plan.has_changes:
        infrastructure_lines = (
            f"- Infrastructure added: {len(infrastructure_plan.new_sources)}\n"
            f"- Infrastructure changed: {len(infrastructure_plan.changed_sources)}\n"
            f"- Infrastructure moved: {len(infrastructure_plan.moved_sources)}\n"
            f"- Infrastructure removed: {len(infrastructure_plan.removed_sources)}\n"
            "- Unsupported infrastructure YAML: "
            f"{len(infrastructure_plan.unsupported_yaml)}\n"
        )
    entry = (
        f"\n## {today}\n\n"
        f"### feat: {operation}\n"
        f"- Source: `{src_dir}`\n"
        f"- Pages created: {result.created}\n"
        f"- Pages updated: {result.updated}\n"
        f"- Pages metadata-only: {result.metadata_only}\n"
        f"- Pages skipped (unchanged): {result.skipped}\n"
        f"- Pages deprecated: {result.deprecated}\n"
        f"- Semantic fields preserved: {result.preserved_semantic}\n"
        f"- Moved entities: {moved_str}\n"
        f"{surface_lines}"
        f"{infrastructure_lines}"
    )
    if log_path.exists():
        existing_log = read_md(log_path)
        write_md(log_path, existing_log + entry)
    else:
        write_md(
            log_path, "# Architectural Log\n\nAppend-only chronological log.\n" + entry
        )
    print("  APPEND log.md")
