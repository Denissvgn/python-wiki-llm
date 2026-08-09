"""Obsidian mirror export support for LLM Wiki.

The canonical wiki remains ``docs/llm_wiki``.  This module builds an
Obsidian-friendly mirror with frontmatter, wikilinks, related links, and
sidecar human notes without modifying the canonical wiki.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

from .bootstrap_runtime import (
    build_entity_occurrence_page_map,
    build_module_page_map,
)
from .filesystem_guard import fresh_no_follow_stat
from .extraction_service import InventoryRequest, get_inventory, get_inventory_result
from . import wiki_surface
from .io import first_unsafe_path_component, read_md, write_md
from .knowledge_projection import (
    KnowledgeProjection,
    KnowledgeProjectionError,
    projection_concept_summary,
    projection_json_value,
    validate_projection_summaries,
)
from .documentation_queries import DocumentationQueryError
from .documentation_query_builder import validate_live_query_source_selection
from .source_selection import (
    SourceSelectionError,
    resolve_source_selection,
)
from .source_snapshot import (
    SourceSnapshot,
    build_source_snapshot,
    capture_source_selection_inputs,
)
from .validation import (
    path_is_within as shared_path_is_within,
    paths_overlap as shared_paths_overlap,
    require_existing_directory,
    require_portable_relative_path,
    require_safe_base_path,
    resolve_portable_workspace_path,
)


MIRROR_ROOT = "LLM Wiki"
DEFAULT_NOTES_DIR = ".llm-wiki/obsidian-notes"
PLUGIN_ID = "llm-wiki"
DEFAULT_PLUGIN_SOURCE = Path("integrations") / "obsidian" / PLUGIN_ID

_OBSIDIAN_KIND_BY_PAGE_KIND = {
    wiki_surface.PageKind.INDEX: "index",
    wiki_surface.PageKind.LOG: "log",
    wiki_surface.PageKind.ENTITIES: "entity",
    wiki_surface.PageKind.MODULES: "module",
    wiki_surface.PageKind.WORKFLOWS: "workflow",
    wiki_surface.PageKind.GUIDES: "guide",
    wiki_surface.PageKind.FLOWS: "flow",
    wiki_surface.PageKind.INFRASTRUCTURE: "infrastructure",
    wiki_surface.PageKind.API_CONTRACTS: "api-contracts",
    wiki_surface.PageKind.DEPENDENCIES: "dependencies",
    wiki_surface.PageKind.LOAD_ORDER: "load-order",
}

MARKDOWN_LINK_RE = re.compile(r"(!)?\[([^\]]+)\]\(([^)]+)\)")
WIKILINK_RE = re.compile(r"!?\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
LOCATION_RE = re.compile(r"\*\*Location:\*\*\s*`([^`]+?)(?::(\d+))?`")
PATH_RE = re.compile(r"\*\*Path:\*\*\s*`([^`]+)`")
LLM_WIKI_FRONTMATTER_RE = re.compile(r"(?m)^llm_wiki:[ \t]*(?:#.*)?$")
PROJECTED_FRONTMATTER_KEY_RE = re.compile(
    r"(?m)^[ \t]+(?:knowledge_|source_knowledge_)[A-Za-z0-9_-]*[ \t]*:"
    r"|^[ \t]+source_path[ \t]*:"
)
PROJECTED_KNOWLEDGE_FRONTMATTER_KEY_RE = re.compile(
    r"(?m)^[ \t]+(?:knowledge_|source_knowledge_)[A-Za-z0-9_-]*[ \t]*:"
)
LLM_WIKI_FRESHNESS_RE = re.compile(
    r"(?m)^llm_wiki:[ \t]*(?:#.*)?"
    r"(?:\r?\n[ \t]+[^\r\n]*)*"
    r"\r?\n[ \t]+freshness[ \t]*:"
)
TOP_LEVEL_PROJECTED_FRONTMATTER_KEY_RE = re.compile(
    r"(?m)^(?:knowledge_|source_knowledge_)[A-Za-z0-9_-]*[ \t]*:"
    r"|^source_path[ \t]*:"
)
TOP_LEVEL_PROJECTED_KNOWLEDGE_FRONTMATTER_KEY_RE = re.compile(
    r"(?m)^(?:knowledge_|source_knowledge_)[A-Za-z0-9_-]*[ \t]*:"
)
FRONTMATTER_END_BYTES_RE = re.compile(rb"\r?\n---(?:\r?\n|\Z)")
MAX_OBSIDIAN_MIRROR_SCAN_ENTRIES = 10_000
MAX_OBSIDIAN_MIRROR_SCAN_DEPTH = 32
MAX_OBSIDIAN_PROJECTED_FRONTMATTER_BYTES = 256 * 1024


class ObsidianError(ValueError):
    """Raised for invalid Obsidian export/check requests."""


def validate_obsidian_export_source_selection(
    *,
    src_dir: str | Path,
    wiki_dir: str | Path,
    source_selection: str | Path | None,
) -> SourceSnapshot:
    """Freeze and validate the live profile before any persisted wiki read."""

    try:
        selection_policy = resolve_source_selection(src_dir, source_selection)
        selection_inputs = capture_source_selection_inputs(
            src_dir,
            source_selection=source_selection,
            selection_policy=selection_policy,
        )
        validate_live_query_source_selection(
            source_root=Path(src_dir),
            wiki_root=Path(wiki_dir),
            live_identity=(
                selection_policy.identity if selection_policy is not None else None
            ),
            live_selection_inputs=selection_inputs,
            operation="Obsidian export",
        )
        snapshot = build_source_snapshot(
            src_dir,
            source_selection=source_selection,
            selection_policy=selection_policy,
            expected_selection_inputs=selection_inputs,
        )
        validate_live_query_source_selection(
            source_root=snapshot.root,
            wiki_root=Path(wiki_dir),
            live_identity=snapshot.source_selection_identity,
            live_selection_inputs=snapshot.source_selection_inputs,
            operation="Obsidian export",
        )
    except (DocumentationQueryError, SourceSelectionError) as exc:
        raise ObsidianError(f"source selection failed: {exc}") from exc
    return snapshot


@dataclass(frozen=True)
class WikiPage:
    kind: str
    page_id: str
    title: str
    canonical_path: Path
    canonical_rel: str
    mirror_rel: str
    source_path: str | None = None
    source_line: int | None = None


@dataclass
class ObsidianOperation:
    action: str
    path: str
    message: str = ""


@dataclass
class ObsidianReport:
    ok: bool = True
    dry_run: bool = False
    wiki_dir: str = ""
    vault_dir: str = ""
    mirror_root: str = MIRROR_ROOT
    page_count: int = 0
    operations: list[ObsidianOperation] = field(default_factory=list)
    issues: list[dict[str, str]] = field(default_factory=list)
    freshness: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "ok": self.ok,
            "dry_run": self.dry_run,
            "wiki_dir": self.wiki_dir,
            "vault_dir": self.vault_dir,
            "mirror_root": self.mirror_root,
            "page_count": self.page_count,
            "operations": [op.__dict__ for op in self.operations],
            "issues": self.issues,
        }
        if self.freshness is not None:
            payload["freshness"] = self.freshness
        return payload


def export_obsidian_vault(
    *,
    src_dir: str = ".",
    wiki_dir: str | Path = "docs/llm_wiki",
    vault_dir: str | Path,
    notes_dir: str | Path = DEFAULT_NOTES_DIR,
    dry_run: bool = False,
    source_selection: str | Path | None = None,
    knowledge_metadata: str | None = None,
    knowledge_projection: KnowledgeProjection | None = None,
) -> ObsidianReport:
    """Export an Obsidian-friendly mirror and sidecar notes."""
    wiki = Path(wiki_dir)
    vault = Path(vault_dir).expanduser()
    notes = _resolve_notes_dir(vault, notes_dir)
    _validate_existing_dir(wiki, "wiki_dir")
    _ensure_safe_base(vault)
    _ensure_safe_base(notes)
    _validate_no_authority_overlap(wiki, vault, "vault_dir")
    _validate_no_authority_overlap(wiki, notes, "notes_dir")

    source_snapshot = validate_obsidian_export_source_selection(
        src_dir=src_dir,
        wiki_dir=wiki,
        source_selection=source_selection,
    )
    source_selection = source_snapshot.source_selection_path

    page_content: dict[str, str] = {}
    pages = collect_wiki_pages(wiki, content_cache=page_content)
    canonical_map = {page.canonical_rel: page for page in pages}
    outgoing = _collect_outgoing_links(pages, canonical_map, wiki, page_content)
    related = _build_related_links(pages, outgoing)
    projection = _select_knowledge_projection(
        pages,
        knowledge_metadata=knowledge_metadata,
        knowledge_projection=knowledge_projection,
    )
    if projection is None:
        _merge_inventory_relationships(
            related,
            pages,
            src_dir,
            source_selection=source_selection,
            source_snapshot=source_snapshot,
        )
    else:
        _merge_source_coordinate_relationships(related, pages)
        _preflight_no_alias_paths(
            [
                *[vault / page.mirror_rel for page in pages],
                *[
                    _sidecar_note_path(notes, page)
                    for page in pages
                ],
            ]
        )
    planned_paths = [
        (
            page,
            _safe_join(vault, page.mirror_rel),
            _sidecar_note_path(notes, page),
        )
        for page in pages
    ]
    if projection is not None:
        unexpected = _unexpected_projected_mirror_pages(
            vault,
            expected_relative_paths=[
                _mirror_scan_relative_path(page) for page in pages
            ],
            excluded_roots=[notes],
        )
        if unexpected:
            rendered = ", ".join(
                _vault_relative_path(path, vault) for path in unexpected
            )
            raise ObsidianError(
                "Unexpected projected Obsidian mirror page(s) are not in the "
                f"current knowledge projection: {rendered}"
            )

    if projection is not None:
        _preflight_planned_parent_directories(
            [mirror_path for _, mirror_path, _ in planned_paths],
            label="Obsidian mirror",
        )
        _preflight_planned_parent_directories(
            [note_path for _, _, note_path in planned_paths],
            label="Obsidian sidecar",
        )
    rendered_pages: list[tuple[WikiPage, Path, Path, str]] = []
    for page, mirror_path, note_path in planned_paths:
        note_target = _vault_link_for_path(
            note_path,
            vault,
            omit_external=projection is not None,
        )
        rendered_pages.append(
            (
                page,
                mirror_path,
                note_path,
                build_mirror_page(
                    page,
                    page_content[page.canonical_rel],
                    outgoing=outgoing.get(page.canonical_rel, set()),
                    related=related.get(page.canonical_rel, set()),
                    canonical_map=canonical_map,
                    wiki_dir=wiki,
                    note_target=note_target,
                    knowledge_projection=projection,
                ),
            )
        )

    report = ObsidianReport(
        dry_run=dry_run,
        wiki_dir=str(wiki),
        vault_dir=str(vault),
        page_count=len(pages),
        freshness=projection.freshness if projection is not None else None,
    )

    for page, mirror_path, note_path, content in rendered_pages:
        if dry_run:
            report.operations.append(ObsidianOperation("would_write", str(mirror_path)))
            if not note_path.exists():
                report.operations.append(
                    ObsidianOperation("would_create_note", str(note_path))
                )
            continue

        mirror_path.parent.mkdir(parents=True, exist_ok=True)
        write_md(mirror_path, content)
        report.operations.append(ObsidianOperation("write", str(mirror_path)))

        if _create_note_exclusive(note_path, _sidecar_note_stub(page)):
            report.operations.append(ObsidianOperation("create_note", str(note_path)))
        else:
            report.operations.append(ObsidianOperation("keep_note", str(note_path)))

    return report


def check_obsidian_vault(
    *,
    wiki_dir: str | Path = "docs/llm_wiki",
    vault_dir: str | Path,
    knowledge_metadata: str | None = None,
    knowledge_projection: KnowledgeProjection | None = None,
) -> ObsidianReport:
    """Check whether the Obsidian mirror is present and internally linked."""
    wiki = Path(wiki_dir)
    vault = Path(vault_dir).expanduser()
    _validate_existing_dir(wiki, "wiki_dir")
    _ensure_safe_base(vault)
    _validate_no_authority_overlap(wiki, vault, "vault_dir")

    pages = collect_wiki_pages(wiki)
    canonical_map = {page.canonical_rel: page for page in pages}
    projection = _select_knowledge_projection(
        pages,
        knowledge_metadata=knowledge_metadata,
        knowledge_projection=knowledge_projection,
    )
    report = ObsidianReport(
        wiki_dir=str(wiki),
        vault_dir=str(vault),
        page_count=len(pages),
        freshness=projection.freshness if projection is not None else None,
    )
    try:
        unexpected_pages = _unexpected_projected_mirror_pages(
            vault,
            expected_relative_paths=(
                [
                    _mirror_scan_relative_path(page) for page in pages
                ]
                if projection is not None
                else []
            ),
            knowledge_metadata_only=projection is None,
        )
    except ObsidianError as exc:
        report.issues.append(
            {
                "category": "unsafe_projected_mirror_scan",
                "path": str(vault / MIRROR_ROOT),
                "message": str(exc),
            }
        )
        report.ok = False
        return report
    for unexpected in unexpected_pages:
        if projection is None:
            report.issues.append(
                {
                    "category": "unexpected_knowledge_metadata",
                    "path": str(unexpected),
                    "message": (
                        "Projected knowledge frontmatter is present, but "
                        "knowledge metadata mode was not selected"
                    ),
                }
            )
        else:
            report.issues.append(
                {
                    "category": "unexpected_projected_mirror_page",
                    "path": str(unexpected),
                    "message": (
                        "Projected knowledge frontmatter is present on a "
                        "Markdown page outside the current mirror page set"
                    ),
                }
            )

    for page in pages:
        mirror_path = _safe_join(vault, page.mirror_rel)
        if not mirror_path.exists():
            report.issues.append(
                {
                    "category": "missing_mirror_page",
                    "path": str(mirror_path),
                    "message": f"Missing mirrored page for {page.canonical_rel}",
                }
            )
            continue
        for target in _wikilink_targets(read_md(mirror_path)):
            if _is_absolute_link_target(target):
                # Legacy exports may point at a caller-selected sidecar outside
                # the vault. The checker never follows that external path.
                if projection is not None:
                    report.issues.append(
                        {
                            "category": "unsafe_wikilink",
                            "path": str(mirror_path),
                            "target": target,
                            "message": (
                                "Absolute Obsidian wikilink targets are not "
                                f"allowed in enriched mirrors: {target}"
                            ),
                        }
                    )
                continue
            try:
                target_path = _safe_join(vault, target + ".md")
            except ObsidianError as exc:
                report.issues.append(
                    {
                        "category": "unsafe_wikilink",
                        "path": str(mirror_path),
                        "target": target,
                        "message": str(exc),
                    }
                )
                continue
            if not target_path.exists():
                report.issues.append(
                    {
                        "category": "broken_wikilink",
                        "path": str(mirror_path),
                        "target": target,
                        "message": f"Broken Obsidian wikilink: {target}",
                    }
                )
        if projection is not None:
            mirror_content = read_md(mirror_path)
            expected_frontmatter = build_frontmatter(
                page,
                knowledge_projection=projection,
            )
            if _frontmatter_block(mirror_content) != expected_frontmatter:
                report.issues.append(
                    {
                        "category": "knowledge_metadata_mismatch",
                        "path": str(mirror_path),
                        "message": (
                            "Projected knowledge frontmatter does not match "
                            f"{projection.source_knowledge_hash}"
                        ),
                    }
                )
            expected_relationships = _render_typed_relationships(
                projection,
                page,
                canonical_map,
            )
            if (
                _typed_relationships_block(mirror_content)
                != expected_relationships
            ):
                report.issues.append(
                    {
                        "category": "knowledge_relationship_mismatch",
                        "path": str(mirror_path),
                        "message": (
                            "Rendered typed relationships do not match the "
                            "validated knowledge projection"
                        ),
                    }
                )

    report.ok = not report.issues
    return report


def install_obsidian_plugin(
    *,
    vault_dir: str | Path,
    plugin_dir: str | Path = DEFAULT_PLUGIN_SOURCE,
) -> ObsidianReport:
    """Copy the bundled companion plugin into a vault's plugin directory."""
    vault = Path(vault_dir).expanduser()
    source = _resolve_plugin_source(plugin_dir)
    if not source.exists() or not source.is_dir():
        raise ObsidianError(f"Obsidian plugin source directory not found: {source}")
    _ensure_safe_base(vault)

    plugin_relative = (
        PurePosixPath(".obsidian") / "plugins" / PLUGIN_ID
    ).as_posix()
    dest = _safe_join(vault, plugin_relative)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest, dirs_exist_ok=True, ignore=_plugin_copy_ignore)

    report = ObsidianReport(wiki_dir="", vault_dir=str(vault), page_count=0)
    report.operations.append(ObsidianOperation("install_plugin", str(dest)))
    return report


def collect_wiki_pages(
    wiki_dir: str | Path,
    *,
    content_cache: dict[str, str] | None = None,
) -> list[WikiPage]:
    """Collect active canonical wiki pages in deterministic order."""
    wiki = Path(wiki_dir)
    pages: list[WikiPage] = []

    for surface_page in wiki_surface.collect_wiki_pages(wiki):
        content = read_md(surface_page.path)
        canonical_rel = surface_page.relative_path
        if content_cache is not None:
            content_cache[canonical_rel] = content
        source_path, source_line = _source_location(content)
        pages.append(
            WikiPage(
                kind=_obsidian_kind(surface_page.kind),
                page_id=surface_page.page_id,
                title=_markdown_title(content, surface_page.page_id),
                canonical_path=surface_page.path,
                canonical_rel=canonical_rel,
                mirror_rel=_mirror_rel(surface_page),
                source_path=source_path,
                source_line=source_line,
            )
        )

    return pages


def _obsidian_kind(kind: wiki_surface.PageKind) -> str:
    return _OBSIDIAN_KIND_BY_PAGE_KIND[kind]


def _mirror_rel(surface_page: wiki_surface.WikiSurfacePage) -> str:
    if surface_page.obsidian_mirror_dir:
        return (
            Path(MIRROR_ROOT)
            / surface_page.obsidian_mirror_dir
            / f"{surface_page.page_id}.md"
        ).as_posix()
    return (Path(MIRROR_ROOT) / f"{surface_page.label}.md").as_posix()


def build_mirror_page(
    page: WikiPage,
    content: str,
    *,
    outgoing: set[str],
    related: set[str],
    canonical_map: dict[str, WikiPage],
    wiki_dir: Path,
    note_target: str | None,
    knowledge_projection: KnowledgeProjection | None = None,
) -> str:
    transformed = convert_markdown_links(
        _escape_source_wikilinks(content),
        page,
        canonical_map,
        wiki_dir,
        escape_aliases=knowledge_projection is not None,
    )
    parts = [
        build_frontmatter(page, knowledge_projection=knowledge_projection),
        "",
        transformed.strip(),
        "",
        "## Related",
        "",
        _render_related_links(
            sorted(outgoing | related),
            canonical_map,
            escape_aliases=knowledge_projection is not None,
        ),
    ]
    if knowledge_projection is not None:
        parts.extend(
            [
                "",
                "## Typed Relationships",
                "",
                _render_typed_relationships(
                    knowledge_projection,
                    page,
                    canonical_map,
                ),
            ]
        )
    parts.extend(
        [
            "",
            "## Human Notes",
            "",
            (
                f"![[{note_target}]]"
                if note_target is not None
                else "_Human note is stored outside this vault._"
            ),
            "",
        ]
    )
    return "\n".join(parts).replace("\r\n", "\n")


def _escape_source_wikilinks(content: str) -> str:
    """Treat existing double-bracket text as source prose, not vault links."""
    return content.replace("[[", r"\[\[").replace("]]", r"\]\]")


def build_frontmatter(
    page: WikiPage,
    *,
    knowledge_projection: KnowledgeProjection | None = None,
) -> str:
    include_source_metadata = knowledge_projection is None
    aliases = _aliases_for(
        page,
        include_source_path=include_source_metadata,
    )
    tag = f"llm-wiki/{page.kind}"
    lines = [
        "---",
        "aliases:",
        *[f"  - {_yaml_quote(alias)}" for alias in aliases],
        "tags:",
        f"  - {_yaml_quote(tag)}",
        "llm_wiki:",
        f"  kind: {_yaml_quote(page.kind)}",
        f"  id: {_yaml_quote(page.page_id)}",
        f"  canonical_path: {_yaml_quote(page.canonical_rel)}",
    ]
    if include_source_metadata and page.source_path:
        lines.append(f"  source_path: {_yaml_quote(page.source_path)}")
    if include_source_metadata and page.source_line is not None:
        lines.append(f"  source_line: {page.source_line}")
    if knowledge_projection is not None:
        summary = _knowledge_frontmatter_summary(knowledge_projection, page)
        lines.extend(
            f"  {name}: {_yaml_quote(value)}"
            for name, value in sorted(summary.items())
        )
    lines.append("---")
    return "\n".join(lines)


def convert_markdown_links(
    content: str,
    page: WikiPage,
    canonical_map: dict[str, WikiPage],
    wiki_dir: Path,
    *,
    escape_aliases: bool = False,
) -> str:
    """Convert internal Markdown links to Obsidian wikilinks."""

    def repl(match: re.Match[str]) -> str:
        if match.group(1):
            return match.group(0)
        text = match.group(2)
        target = match.group(3)
        linked = _resolve_markdown_target(page, target, canonical_map, wiki_dir)
        if linked is None:
            return match.group(0)
        anchor = ""
        if "#" in target:
            anchor = "#" + target.split("#", 1)[1]
        return (
            f"[[{_vault_link_target(linked)}{anchor}|"
            f"{_wikilink_alias(text, escape=escape_aliases)}]]"
        )

    return MARKDOWN_LINK_RE.sub(repl, content)


def render_report_text(report: ObsidianReport, *, action: str) -> str:
    lines = [f"Obsidian {action}", f"Vault: {report.vault_dir}"]
    if report.wiki_dir:
        lines.append(f"Wiki: {report.wiki_dir}")
    if report.freshness is not None:
        lines.append(f"Freshness: {report.freshness}")
    lines.append(f"Pages: {report.page_count}")
    if report.dry_run:
        lines.append("Dry run: no files were changed.")
    if report.operations:
        lines.append("")
        lines.append("Operations:")
        for op in report.operations:
            suffix = f" - {op.message}" if op.message else ""
            lines.append(f"- {op.action}: {op.path}{suffix}")
    if report.issues:
        lines.append("")
        lines.append("Issues:")
        for issue in report.issues:
            target = f" -> {issue.get('target')}" if issue.get("target") else ""
            lines.append(
                f"- {issue['category']}: {issue['path']}{target} - {issue['message']}"
            )
    elif action == "check":
        lines.append("No Obsidian mirror issues found.")
    return "\n".join(lines) + "\n"


def render_report_json(report: ObsidianReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def _collect_outgoing_links(
    pages: list[WikiPage],
    canonical_map: dict[str, WikiPage],
    wiki_dir: Path,
    page_content: dict[str, str],
) -> dict[str, set[str]]:
    outgoing: dict[str, set[str]] = {}
    for page in pages:
        links: set[str] = set()
        for match in MARKDOWN_LINK_RE.finditer(page_content[page.canonical_rel]):
            if match.group(1):
                continue
            target = _resolve_markdown_target(
                page, match.group(3), canonical_map, wiki_dir
            )
            if target is not None:
                links.add(target.canonical_rel)
        outgoing[page.canonical_rel] = links
    return outgoing


def _build_related_links(
    pages: list[WikiPage],
    outgoing: dict[str, set[str]],
) -> dict[str, set[str]]:
    related = {page.canonical_rel: set() for page in pages}
    for source, targets in outgoing.items():
        related[source].update(targets)
        for target in targets:
            related.setdefault(target, set()).add(source)
    return related


def _merge_inventory_relationships(
    related: dict[str, set[str]],
    pages: list[WikiPage],
    src_dir: str,
    *,
    source_selection: str | Path | None = None,
    source_snapshot: SourceSnapshot | None = None,
) -> None:
    """Restore the legacy source-inventory relationship projection.

    Disabled exports keep the original fail-open behavior, including the
    source scan and its handling of missing or unreadable source roots.
    """

    try:
        if source_snapshot is not None:
            inventory = get_inventory_result(
                InventoryRequest(
                    src_dir=src_dir,
                    deep=True,
                    source_selection=source_selection,
                    source_snapshot=source_snapshot,
                )
            ).inventory
        elif source_selection is None:
            inventory = get_inventory(src_dir, deep=True)
        else:
            inventory = get_inventory(
                src_dir,
                deep=True,
                source_selection=source_selection,
            )
    except SourceSelectionError as exc:
        raise ObsidianError(f"source selection failed: {exc}") from exc
    except Exception:
        return

    canonical_by_kind_id = {
        (page.kind, page.page_id): page.canonical_rel for page in pages
    }
    module_map = build_module_page_map(inventory)
    entity_map = build_entity_occurrence_page_map(inventory, module_map)

    for filepath, module_id in module_map.items():
        module_rel = canonical_by_kind_id.get(("module", module_id))
        if not module_rel:
            continue
        seen_names: dict[str, int] = {}
        for cls in inventory.get(filepath, {}).get("classes", []):
            name = cls.get("name")
            if not name:
                continue
            name_text = str(name)
            seen_names[name_text] = seen_names.get(name_text, 0) + 1
            entity_id = entity_map.get((name_text, filepath, seen_names[name_text]))
            entity_rel = (
                canonical_by_kind_id.get(("entity", entity_id)) if entity_id else None
            )
            if entity_rel:
                related.setdefault(module_rel, set()).add(entity_rel)
                related.setdefault(entity_rel, set()).add(module_rel)


def _merge_source_coordinate_relationships(
    related: dict[str, set[str]],
    pages: Sequence[WikiPage],
) -> None:
    """Preserve legacy module/entity related links without scanning source.

    Canonical generated pages already carry the exact repository-relative
    source coordinate that the removed inventory pass used.  Matching those
    committed coordinates preserves the historical mirror for pages whose
    Markdown body omitted an explicit cross-link, while keeping export
    read-only over the wiki snapshot.
    """

    modules_by_source: dict[str, list[str]] = {}
    entities_by_source: dict[str, list[str]] = {}
    for page in pages:
        if not page.source_path:
            continue
        if page.kind == "module":
            modules_by_source.setdefault(page.source_path, []).append(
                page.canonical_rel
            )
        elif page.kind == "entity":
            entities_by_source.setdefault(page.source_path, []).append(
                page.canonical_rel
            )
    for source_path in sorted(set(modules_by_source) & set(entities_by_source)):
        for module_rel in sorted(modules_by_source[source_path]):
            for entity_rel in sorted(entities_by_source[source_path]):
                related.setdefault(module_rel, set()).add(entity_rel)
                related.setdefault(entity_rel, set()).add(module_rel)


def _select_knowledge_projection(
    pages: Sequence[WikiPage],
    *,
    knowledge_metadata: str | None,
    knowledge_projection: KnowledgeProjection | None,
) -> KnowledgeProjection | None:
    if knowledge_metadata is None:
        if knowledge_projection is not None:
            raise ObsidianError(
                "knowledge_projection requires knowledge_metadata='summary'"
            )
        return None
    if knowledge_metadata != "summary":
        raise ObsidianError("knowledge_metadata must be 'summary' when enabled")
    if not isinstance(knowledge_projection, KnowledgeProjection):
        raise ObsidianError(
            "knowledge_metadata='summary' requires a validated knowledge projection"
        )

    try:
        validate_projection_summaries(
            knowledge_projection,
            [page.canonical_rel for page in pages],
        )
    except KnowledgeProjectionError as exc:
        raise ObsidianError(f"knowledge projection {exc}") from exc
    return knowledge_projection


def _knowledge_frontmatter_summary(
    projection: KnowledgeProjection,
    page: WikiPage,
) -> dict[str, str]:
    try:
        summary = projection_concept_summary(
            projection,
            page.canonical_rel,
        )
    except KnowledgeProjectionError as exc:
        raise ObsidianError(str(exc)) from exc
    return summary


def _render_typed_relationships(
    projection: KnowledgeProjection,
    page: WikiPage,
    canonical_map: Mapping[str, WikiPage],
) -> str:
    concept = projection.concept_for_path(page.canonical_rel)
    if concept is None:
        raise ObsidianError(
            f"knowledge projection has no concept for {page.canonical_rel!r}"
        )
    relationships = concept.get("relationships")
    relation_map = relationships if isinstance(relationships, Mapping) else {}
    if relation_map.get("availability") != "ready":
        return "_Typed relationship graph is unavailable._"
    summary = (
        "_Relationships: returned "
        f"{_projection_count(relation_map.get('returned'))} of "
        f"{_projection_count(relation_map.get('total'))}; limit "
        f"{_projection_count(relation_map.get('limit'))}; truncated "
        + ("true" if bool(relation_map.get("truncated", False)) else "false")
        + "._"
    )
    raw_items = relation_map.get("items")
    items = (
        [item for item in raw_items if isinstance(item, Mapping)]
        if isinstance(raw_items, Sequence)
        and not isinstance(raw_items, (str, bytes))
        else []
    )
    if not items:
        return summary + "\n\n_No typed relationships found._"

    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for item in items:
        direction = str(item.get("direction", "unknown"))
        kind = str(item.get("kind", "unknown"))
        groups.setdefault((direction, kind), []).append(item)

    direction_order = {"incoming": 0, "outgoing": 1, "both": 2}
    lines: list[str] = [summary]
    for direction, kind in sorted(
        groups,
        key=lambda value: (
            direction_order.get(value[0], 3),
            value[0],
            value[1],
        ),
    ):
        lines.append("")
        lines.append(
            f"### {_markdown_text(direction.title())}: "
            f"{_markdown_code(kind)}"
        )
        lines.append("")
        relations = sorted(groups[(direction, kind)], key=_relation_sort_key)
        for relation in relations:
            target = relation.get("target")
            target_map = target if isinstance(target, Mapping) else {}
            lines.append(
                "- "
                + _render_projected_target(
                    target_map,
                    canonical_map,
                    resolution=str(relation.get("resolution", "unknown")),
                )
                + " — "
                + _render_relation_details(relation)
            )
    return "\n".join(lines)


def _relation_sort_key(relation: Mapping[str, Any]) -> tuple[str, ...]:
    target = relation.get("target")
    target_map = target if isinstance(target, Mapping) else {}
    return (
        str(target_map.get("canonical_path", "")),
        str(target_map.get("namespaced_uid", "")),
        str(target_map.get("title", "")),
        str(target_map.get("label", "")),
        str(relation.get("resolution", "")),
        json.dumps(
            projection_json_value(relation),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
    )


def _render_projected_target(
    target: Mapping[str, Any],
    canonical_map: Mapping[str, WikiPage],
    *,
    resolution: str,
) -> str:
    canonical_path = target.get("canonical_path")
    if (
        resolution == "resolved"
        and target.get("present") is True
        and isinstance(canonical_path, str)
    ):
        related = canonical_map.get(canonical_path)
        if related is not None:
            title = str(target.get("title") or related.title)
            return (
                f"[[{_vault_link_target(related)}|"
                f"{_escape_wikilink_alias(title)}]]"
            )
    label = target.get("title") or target.get("label") or "Unknown target"
    return _markdown_text(str(label))


def _render_relation_details(relation: Mapping[str, Any]) -> str:
    resolution = _markdown_code(str(relation.get("resolution", "unknown")))
    evidence = relation.get("evidence")
    evidence_map = evidence if isinstance(evidence, Mapping) else {}
    coverage = relation.get("coverage")
    coverage_map = coverage if isinstance(coverage, Mapping) else {}
    evidence_parts = [
        f"state {_markdown_code(str(evidence_map.get('state', 'unknown')))}",
        f"observed {_projection_count(evidence_map.get('observed'))}",
        f"emitted {_projection_count(evidence_map.get('emitted'))}",
        f"omitted {_projection_count(evidence_map.get('omitted'))}",
    ]
    if "unique" in evidence_map:
        evidence_parts.insert(
            2,
            f"unique {_projection_count(evidence_map.get('unique'))}",
        )
    coverage_parts = [
        f"observed {_projection_count(coverage_map.get('observed'))}",
        f"emitted {_projection_count(coverage_map.get('emitted'))}",
        f"omitted {_projection_count(coverage_map.get('omitted'))}",
        "truncated "
        + ("true" if bool(coverage_map.get("truncated", False)) else "false"),
    ]
    if "limit" in coverage_map:
        coverage_parts.insert(
            3,
            f"limit {_projection_count(coverage_map.get('limit'))}",
        )
    return (
        f"resolution {resolution}; evidence "
        + ", ".join(evidence_parts)
        + "; coverage "
        + ", ".join(coverage_parts)
    )


def _projection_count(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _markdown_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("[", r"\[").replace("]", r"\]")


def _markdown_code(value: str) -> str:
    return "`" + value.replace("`", r"\`") + "`"


def _frontmatter_block(content: str) -> str | None:
    lines = content.replace("\r\n", "\n").splitlines()
    if not lines or lines[0] != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index] == "---":
            return "\n".join(lines[: index + 1])
    return None


def _unexpected_projected_mirror_pages(
    vault_dir: Path,
    *,
    expected_relative_paths: Sequence[str],
    excluded_roots: Sequence[Path] = (),
    knowledge_metadata_only: bool = False,
) -> list[Path]:
    """Find stale generated-looking pages through a bounded no-follow scan."""

    mirror_root = vault_dir.resolve() / MIRROR_ROOT
    try:
        root_metadata = mirror_root.lstat()
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise ObsidianError(
            "Cannot safely inspect the existing Obsidian mirror root"
        ) from exc
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(
        root_metadata.st_mode
    ):
        raise ObsidianError(
            "Cannot safely scan the existing Obsidian mirror: "
            "mirror root must be a regular directory"
        )

    expected = {
        _validate_mirror_scan_relative_path(path)
        for path in expected_relative_paths
    }
    expected_directories = {
        parent.as_posix()
        for path in expected
        for parent in Path(path).parents
        if parent.parts
    }
    excluded = _excluded_mirror_scan_roots(
        vault_dir,
        excluded_roots=excluded_roots,
    )
    root_resolved = mirror_root.resolve(strict=True)
    stack: list[tuple[Path, int]] = [(mirror_root, 0)]
    visited_entries = 0
    unexpected: list[Path] = []
    while stack:
        directory, depth = stack.pop()
        try:
            directory_metadata = directory.lstat()
            resolved_directory = directory.resolve(strict=True)
        except OSError as exc:
            raise ObsidianError(
                "Cannot safely inspect an existing Obsidian mirror directory"
            ) from exc
        if (
            stat.S_ISLNK(directory_metadata.st_mode)
            or not stat.S_ISDIR(directory_metadata.st_mode)
            or not _path_is_within(resolved_directory, root_resolved)
        ):
            raise ObsidianError(
                "Cannot safely scan the existing Obsidian mirror: "
                "directory path escapes through a symlink"
            )
        entries: list[tuple[str, Path, os.stat_result]] = []
        try:
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    visited_entries += 1
                    if visited_entries > MAX_OBSIDIAN_MIRROR_SCAN_ENTRIES:
                        raise ObsidianError(
                            "Cannot safely scan the existing Obsidian mirror: "
                            "entry limit exceeded"
                        )
                    path = Path(entry.path)
                    relative = path.relative_to(mirror_root).as_posix()
                    if _mirror_scan_path_is_excluded(relative, excluded):
                        continue
                    try:
                        metadata = fresh_no_follow_stat(path)
                    except OSError as exc:
                        raise ObsidianError(
                            "Cannot safely inspect an existing Obsidian "
                            "mirror entry"
                        ) from exc
                    entries.append((entry.name, path, metadata))
        except ObsidianError:
            raise
        except OSError as exc:
            raise ObsidianError(
                "Cannot safely enumerate an existing Obsidian mirror directory"
            ) from exc

        for _, path, metadata in sorted(entries, key=lambda value: value[0]):
            relative = path.relative_to(mirror_root).as_posix()
            if stat.S_ISLNK(metadata.st_mode):
                raise ObsidianError(
                    "Cannot safely scan the existing Obsidian mirror: "
                    f"symlink entry {relative!r}"
                )
            if (
                relative in expected_directories
                and not stat.S_ISDIR(metadata.st_mode)
            ):
                raise ObsidianError(
                    "Cannot safely scan the existing Obsidian mirror: "
                    f"expected directory {relative!r} is not a regular directory"
                )
            if relative in expected and not stat.S_ISREG(metadata.st_mode):
                raise ObsidianError(
                    "Cannot safely scan the existing Obsidian mirror: "
                    f"expected page {relative!r} is not a regular file"
                )
            if stat.S_ISDIR(metadata.st_mode):
                if depth >= MAX_OBSIDIAN_MIRROR_SCAN_DEPTH:
                    raise ObsidianError(
                        "Cannot safely scan the existing Obsidian mirror: "
                        "directory depth limit exceeded"
                    )
                stack.append((path, depth + 1))
                continue
            if stat.S_ISREG(metadata.st_mode) and metadata.st_nlink != 1:
                raise ObsidianError(
                    "Cannot safely scan the existing Obsidian mirror: "
                    f"hard-linked file {relative!r} is not isolated"
                )
            if path.suffix.casefold() != ".md" or relative in expected:
                continue
            if not stat.S_ISREG(metadata.st_mode):
                raise ObsidianError(
                    "Cannot safely scan the existing Obsidian mirror: "
                    f"Markdown candidate {relative!r} is not a regular file"
                )
            frontmatter = _read_bounded_projected_frontmatter(
                path,
                expected_metadata=metadata,
            )
            has_projected_metadata = (
                _has_projected_knowledge_metadata_frontmatter(frontmatter)
                if knowledge_metadata_only
                else _has_projected_knowledge_frontmatter(frontmatter)
            )
            if has_projected_metadata:
                unexpected.append(path)
    return unexpected


def _read_bounded_projected_frontmatter(
    path: Path,
    *,
    expected_metadata: os.stat_result,
) -> str:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or not _same_file_identity(opened, expected_metadata)
        ):
            raise ObsidianError(
                "Cannot safely scan the existing Obsidian mirror: "
                "Markdown identity changed during inspection"
            )

        prefix = _read_descriptor_bytes(descriptor, 5)
        if not (
            prefix.startswith(b"---\n")
            or prefix.startswith(b"---\r\n")
        ):
            frontmatter_bytes = b""
        else:
            remaining = (
                MAX_OBSIDIAN_PROJECTED_FRONTMATTER_BYTES + 1 - len(prefix)
            )
            payload = prefix + _read_descriptor_bytes(descriptor, remaining)
            closing = FRONTMATTER_END_BYTES_RE.search(
                payload,
                max(0, len(prefix) - 2),
            )
            if closing is not None:
                frontmatter_bytes = payload[: closing.end()]
            elif len(payload) > MAX_OBSIDIAN_PROJECTED_FRONTMATTER_BYTES:
                raise ObsidianError(
                    "Cannot safely scan the existing Obsidian mirror: "
                    "unexpected Markdown frontmatter exceeds the size limit"
                )
            else:
                frontmatter_bytes = payload
        after = os.fstat(descriptor)
        if not _same_file_identity(after, opened):
            raise ObsidianError(
                "Cannot safely scan the existing Obsidian mirror: "
                "Markdown changed during inspection"
            )
        try:
            return frontmatter_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ObsidianError(
                "Cannot safely scan the existing Obsidian mirror: "
                "unexpected Markdown frontmatter is not valid UTF-8"
            ) from exc
    except ObsidianError:
        raise
    except OSError as exc:
        raise ObsidianError(
            "Cannot safely read existing Obsidian mirror Markdown"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_descriptor_bytes(descriptor: int, limit: int) -> bytes:
    chunks: list[bytes] = []
    remaining = max(0, limit)
    while remaining:
        chunk = os.read(descriptor, min(64 * 1024, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _same_file_identity(
    left: os.stat_result,
    right: os.stat_result,
) -> bool:
    return (
        left.st_dev == right.st_dev
        and left.st_ino == right.st_ino
        and left.st_size == right.st_size
        and left.st_mtime_ns == right.st_mtime_ns
        and left.st_nlink == right.st_nlink == 1
    )


def _validate_mirror_scan_relative_path(value: str) -> str:
    error = ObsidianError(f"Unsafe expected Obsidian mirror path: {value!r}")
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


def _mirror_scan_relative_path(page: WikiPage) -> str:
    try:
        relative = Path(page.mirror_rel).relative_to(MIRROR_ROOT)
    except ValueError as exc:
        raise ObsidianError(
            f"Obsidian mirror path is outside {MIRROR_ROOT!r}"
        ) from exc
    return _validate_mirror_scan_relative_path(relative.as_posix())


def _excluded_mirror_scan_roots(
    vault_dir: Path,
    *,
    excluded_roots: Sequence[Path],
) -> frozenset[str]:
    mirror_root = Path(os.path.abspath(vault_dir / MIRROR_ROOT))
    excluded: set[str] = set()
    for root in excluded_roots:
        absolute = Path(os.path.abspath(root))
        try:
            relative = absolute.relative_to(mirror_root)
        except ValueError:
            continue
        if not relative.parts:
            continue
        excluded.add(relative.as_posix())
    return frozenset(excluded)


def _mirror_scan_path_is_excluded(
    relative_path: str,
    excluded_roots: frozenset[str],
) -> bool:
    return any(
        relative_path == root or relative_path.startswith(root + "/")
        for root in excluded_roots
    )


def _has_projected_knowledge_frontmatter(content: str) -> bool:
    frontmatter = _frontmatter_block(content)
    if frontmatter is None and content.startswith("---"):
        # Malformed/truncated frontmatter with generated keys still fails
        # closed instead of being treated as an unrelated human note.
        frontmatter = content
    return bool(
        frontmatter
        and (
            TOP_LEVEL_PROJECTED_FRONTMATTER_KEY_RE.search(frontmatter)
            or (
                LLM_WIKI_FRONTMATTER_RE.search(frontmatter)
                and PROJECTED_FRONTMATTER_KEY_RE.search(frontmatter)
            )
            or LLM_WIKI_FRESHNESS_RE.search(frontmatter)
        )
    )


def _has_projected_knowledge_metadata_frontmatter(content: str) -> bool:
    """Detect knowledge-only fields while preserving legacy source metadata."""

    frontmatter = _frontmatter_block(content)
    if frontmatter is None and content.startswith("---"):
        frontmatter = content
    return bool(
        frontmatter
        and (
            TOP_LEVEL_PROJECTED_KNOWLEDGE_FRONTMATTER_KEY_RE.search(frontmatter)
            or (
                LLM_WIKI_FRONTMATTER_RE.search(frontmatter)
                and PROJECTED_KNOWLEDGE_FRONTMATTER_KEY_RE.search(frontmatter)
            )
            or LLM_WIKI_FRESHNESS_RE.search(frontmatter)
        )
    )


def _typed_relationships_block(content: str) -> str | None:
    marker = "\n## Typed Relationships\n\n"
    start = content.find(marker)
    if start < 0:
        return None
    block_start = start + len(marker)
    end = content.find("\n## Human Notes\n", block_start)
    if end < 0:
        return None
    return content[block_start:end].strip()


def _render_related_links(
    related_rels: list[str],
    canonical_map: dict[str, WikiPage],
    *,
    escape_aliases: bool = False,
) -> str:
    lines = []
    for rel in related_rels:
        page = canonical_map.get(rel)
        if page is None:
            continue
        alias = (
            _escape_wikilink_alias(page.title)
            if escape_aliases
            else page.title
        )
        lines.append(
            f"- [[{_vault_link_target(page)}|"
            f"{alias}]]"
        )
    if not lines:
        return "_No related wiki pages found._"
    return "\n".join(lines)


def _resolve_markdown_target(
    page: WikiPage,
    target: str,
    canonical_map: dict[str, WikiPage],
    wiki_dir: Path,
) -> WikiPage | None:
    if _is_external_link(target) or target.startswith("#"):
        return None
    target_path = target.split("#", 1)[0].strip()
    if not target_path or target_path.startswith("<"):
        return None
    source_parent = (wiki_dir / page.canonical_rel).parent
    resolved = (source_parent / target_path).resolve()
    try:
        rel = resolved.relative_to(wiki_dir.resolve()).as_posix()
    except ValueError:
        return None
    return canonical_map.get(rel)


def _wikilink_targets(content: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in WIKILINK_RE.finditer(content)
        if match.group(1).strip()
    }


def _is_external_link(target: str) -> bool:
    lowered = target.lower()
    return (
        "://" in lowered or lowered.startswith("mailto:") or lowered.startswith("tel:")
    )


def _source_location(content: str) -> tuple[str | None, int | None]:
    match = LOCATION_RE.search(content)
    if match:
        line = int(match.group(2)) if match.group(2) else None
        return match.group(1), line
    match = PATH_RE.search(content)
    if match:
        return match.group(1), None
    return None, None


def _markdown_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def _aliases_for(
    page: WikiPage,
    *,
    include_source_path: bool = True,
) -> list[str]:
    values = [
        page.title,
        page.page_id,
        f"{page.kind}/{page.page_id}",
        page.canonical_rel,
        page.canonical_rel.removesuffix(".md"),
    ]
    if include_source_path and page.source_path:
        values.append(page.source_path)
    aliases: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            aliases.append(value)
            seen.add(value)
    return aliases


def _yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _escape_wikilink_alias(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("[", r"\[")
        .replace("]", r"\]")
        .replace("|", r"\|")
        .strip()
    )


def _legacy_wikilink_alias(value: str) -> str:
    """Match the pre-projection alias rendering byte-for-byte."""

    return value.replace("|", "\\|").strip()


def _wikilink_alias(value: str, *, escape: bool) -> str:
    if escape:
        return _escape_wikilink_alias(value)
    return _legacy_wikilink_alias(value)


def _vault_link_target(page: WikiPage) -> str:
    return Path(page.mirror_rel).with_suffix("").as_posix()


def _vault_link_for_path(
    path: Path,
    vault_dir: Path,
    *,
    omit_external: bool = False,
) -> str | None:
    try:
        return (
            path.resolve().relative_to(vault_dir.resolve()).with_suffix("").as_posix()
        )
    except ValueError:
        if omit_external:
            return None
        # Obsidian cannot transclude outside the vault; fall back to a readable
        # path so the page still communicates where the note lives.
        return path.with_suffix("").as_posix()


def _resolve_notes_dir(vault_dir: Path, notes_dir: str | Path) -> Path:
    notes = Path(notes_dir).expanduser()
    if notes.is_absolute():
        return notes
    return vault_dir / notes


def _sidecar_note_path(notes_dir: Path, page: WikiPage) -> Path:
    return _safe_join(notes_dir, _sidecar_note_relative_path(page))


def _sidecar_note_relative_path(page: WikiPage) -> str:
    safe_id = _safe_filename(page.page_id)
    return (PurePosixPath(page.kind) / f"{safe_id}.md").as_posix()


def _sidecar_note_stub(page: WikiPage) -> str:
    return f"# {page.title} Notes\n\n"


def _create_note_exclusive(path: Path, content: str) -> bool:
    """Create one sidecar without overwriting a concurrent human write."""

    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    fd, temporary = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(normalized)
        try:
            os.link(temporary, path)
        except FileExistsError:
            return False
        return True
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "note"


def _preflight_no_alias_paths(paths: Sequence[Path]) -> None:
    for path in paths:
        unsafe = first_unsafe_path_component(path)
        if unsafe is not None:
            raise ObsidianError(
                "Cannot safely publish enriched Obsidian output through "
                f"an unsafe existing path component: {unsafe}"
            )


def _preflight_planned_parent_directories(
    paths: Sequence[Path],
    *,
    label: str,
) -> None:
    for path in paths:
        parent = path.parent
        while True:
            try:
                metadata = parent.lstat()
            except FileNotFoundError:
                if parent == parent.parent:
                    raise ObsidianError(
                        f"Cannot safely prepare {label} parent directory"
                    )
                parent = parent.parent
                continue
            except OSError as exc:
                raise ObsidianError(
                    f"Cannot safely inspect {label} parent directory"
                ) from exc
            if not stat.S_ISDIR(metadata.st_mode):
                raise ObsidianError(
                    f"Cannot safely prepare {label}: parent path "
                    f"{parent} is not a directory"
                )
            break


def _safe_join(root: Path, relative: str | Path) -> Path:
    return resolve_portable_workspace_path(
        root,
        relative,
        path_error=ObsidianError(f"Unsafe portable path: {relative}"),
        escape_error=ObsidianError(
            f"Path escapes base directory: {(root / relative).resolve()}"
        ),
    )


def _ensure_safe_base(path: Path) -> None:
    require_safe_base_path(
        path,
        error=ObsidianError(f"Invalid directory path: {path}"),
    )


def _validate_no_authority_overlap(
    wiki_dir: Path,
    derived_dir: Path,
    label: str,
) -> None:
    wiki = wiki_dir.resolve()
    derived = derived_dir.resolve()
    if _paths_overlap(wiki, derived):
        raise ObsidianError(
            f"{label} overlaps the canonical wiki"
        )


def _paths_overlap(left: Path, right: Path) -> bool:
    return shared_paths_overlap(left, right)


def _path_is_within(path: Path, root: Path) -> bool:
    return shared_path_is_within(path, root)


def _vault_relative_path(path: Path, vault_dir: Path) -> str:
    try:
        return path.resolve().relative_to(vault_dir.resolve()).as_posix()
    except ValueError:
        return path.name


def _is_absolute_link_target(value: str) -> bool:
    return (
        Path(value).is_absolute()
        or re.match(r"^[A-Za-z]:[/\\]", value) is not None
    )


def _validate_existing_dir(path: Path, label: str) -> None:
    require_existing_directory(
        path,
        error=ObsidianError(
            f"{label} does not exist or is not a directory: {path}"
        ),
    )


def _plugin_copy_ignore(_dir: str, names: list[str]) -> set[str]:
    ignored = {"node_modules", ".git", ".obsidian", ".DS_Store"}
    return {name for name in names if name in ignored}


def _resolve_plugin_source(plugin_dir: str | Path) -> Path:
    source = Path(plugin_dir).expanduser()
    if source.exists() or source.is_absolute():
        return source
    repo_source = Path(__file__).resolve().parents[3] / source
    if repo_source.exists():
        return repo_source
    return source
