"""Obsidian mirror export support for LLM Wiki.

The canonical wiki remains ``docs/llm_wiki``.  This module builds an
Obsidian-friendly mirror with frontmatter, wikilinks, related links, and
sidecar human notes without modifying the canonical wiki.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..commands.bootstrap_cmd import (
    build_entity_occurrence_page_map,
    build_module_page_map,
)
from ..commands.extract_cmd import get_inventory
from . import wiki_surface
from .io import read_md, write_md


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
    wiki_surface.PageKind.DEPENDENCIES: "dependencies",
    wiki_surface.PageKind.LOAD_ORDER: "load-order",
}

MARKDOWN_LINK_RE = re.compile(r"(!)?\[([^\]]+)\]\(([^)]+)\)")
WIKILINK_RE = re.compile(r"!?\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
LOCATION_RE = re.compile(r"\*\*Location:\*\*\s*`([^`]+?)(?::(\d+))?`")
PATH_RE = re.compile(r"\*\*Path:\*\*\s*`([^`]+)`")


class ObsidianError(ValueError):
    """Raised for invalid Obsidian export/check requests."""


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dry_run": self.dry_run,
            "wiki_dir": self.wiki_dir,
            "vault_dir": self.vault_dir,
            "mirror_root": self.mirror_root,
            "page_count": self.page_count,
            "operations": [op.__dict__ for op in self.operations],
            "issues": self.issues,
        }


def export_obsidian_vault(
    *,
    src_dir: str = ".",
    wiki_dir: str | Path = "docs/llm_wiki",
    vault_dir: str | Path,
    notes_dir: str | Path = DEFAULT_NOTES_DIR,
    dry_run: bool = False,
) -> ObsidianReport:
    """Export an Obsidian-friendly mirror and sidecar notes."""
    wiki = Path(wiki_dir)
    vault = Path(vault_dir).expanduser()
    notes = _resolve_notes_dir(vault, notes_dir)
    _validate_existing_dir(wiki, "wiki_dir")
    _ensure_safe_base(vault)
    _ensure_safe_base(notes)

    page_content: dict[str, str] = {}
    pages = collect_wiki_pages(wiki, content_cache=page_content)
    canonical_map = {page.canonical_rel: page for page in pages}
    outgoing = _collect_outgoing_links(pages, canonical_map, wiki, page_content)
    related = _build_related_links(pages, outgoing)
    _merge_inventory_relationships(related, pages, src_dir)

    report = ObsidianReport(
        dry_run=dry_run,
        wiki_dir=str(wiki),
        vault_dir=str(vault),
        page_count=len(pages),
    )

    for page in pages:
        mirror_path = _safe_join(vault, page.mirror_rel)
        note_path = _sidecar_note_path(notes, page)
        note_target = _vault_link_for_path(note_path, vault)

        content = build_mirror_page(
            page,
            page_content[page.canonical_rel],
            outgoing=outgoing.get(page.canonical_rel, set()),
            related=related.get(page.canonical_rel, set()),
            canonical_map=canonical_map,
            wiki_dir=wiki,
            note_target=note_target,
        )

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

        if not note_path.exists():
            note_path.parent.mkdir(parents=True, exist_ok=True)
            write_md(note_path, _sidecar_note_stub(page))
            report.operations.append(ObsidianOperation("create_note", str(note_path)))
        else:
            report.operations.append(ObsidianOperation("keep_note", str(note_path)))

    return report


def check_obsidian_vault(
    *,
    wiki_dir: str | Path = "docs/llm_wiki",
    vault_dir: str | Path,
) -> ObsidianReport:
    """Check whether the Obsidian mirror is present and internally linked."""
    wiki = Path(wiki_dir)
    vault = Path(vault_dir).expanduser()
    _validate_existing_dir(wiki, "wiki_dir")
    _ensure_safe_base(vault)

    pages = collect_wiki_pages(wiki)
    report = ObsidianReport(
        wiki_dir=str(wiki),
        vault_dir=str(vault),
        page_count=len(pages),
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
            target_path = _safe_join(vault, target + ".md")
            if not target_path.exists():
                report.issues.append(
                    {
                        "category": "broken_wikilink",
                        "path": str(mirror_path),
                        "target": target,
                        "message": f"Broken Obsidian wikilink: {target}",
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

    dest = _safe_join(vault, Path(".obsidian") / "plugins" / PLUGIN_ID)
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
    note_target: str,
) -> str:
    transformed = convert_markdown_links(
        _escape_source_wikilinks(content), page, canonical_map, wiki_dir
    )
    parts = [
        build_frontmatter(page),
        "",
        transformed.strip(),
        "",
        "## Related",
        "",
        _render_related_links(sorted(outgoing | related), canonical_map),
        "",
        "## Human Notes",
        "",
        f"![[{note_target}]]",
        "",
    ]
    return "\n".join(parts).replace("\r\n", "\n")


def _escape_source_wikilinks(content: str) -> str:
    """Treat existing double-bracket text as source prose, not vault links."""
    return content.replace("[[", r"\[\[").replace("]]", r"\]\]")


def build_frontmatter(page: WikiPage) -> str:
    aliases = _aliases_for(page)
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
    if page.source_path:
        lines.append(f"  source_path: {_yaml_quote(page.source_path)}")
    if page.source_line is not None:
        lines.append(f"  source_line: {page.source_line}")
    lines.append("---")
    return "\n".join(lines)


def convert_markdown_links(
    content: str,
    page: WikiPage,
    canonical_map: dict[str, WikiPage],
    wiki_dir: Path,
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
            f"[[{_vault_link_target(linked)}{anchor}|{_escape_wikilink_alias(text)}]]"
        )

    return MARKDOWN_LINK_RE.sub(repl, content)


def render_report_text(report: ObsidianReport, *, action: str) -> str:
    lines = [f"Obsidian {action}", f"Vault: {report.vault_dir}"]
    if report.wiki_dir:
        lines.append(f"Wiki: {report.wiki_dir}")
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
    related: dict[str, set[str]], pages: list[WikiPage], src_dir: str
) -> None:
    try:
        inventory = get_inventory(src_dir, deep=True)
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


def _render_related_links(
    related_rels: list[str], canonical_map: dict[str, WikiPage]
) -> str:
    lines = []
    for rel in related_rels:
        page = canonical_map.get(rel)
        if page is None:
            continue
        lines.append(f"- [[{_vault_link_target(page)}|{page.title}]]")
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


def _aliases_for(page: WikiPage) -> list[str]:
    values = [
        page.title,
        page.page_id,
        f"{page.kind}/{page.page_id}",
        page.canonical_rel,
        page.canonical_rel.removesuffix(".md"),
    ]
    if page.source_path:
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
    return value.replace("|", "\\|").strip()


def _vault_link_target(page: WikiPage) -> str:
    return Path(page.mirror_rel).with_suffix("").as_posix()


def _vault_link_for_path(path: Path, vault_dir: Path) -> str:
    try:
        return (
            path.resolve().relative_to(vault_dir.resolve()).with_suffix("").as_posix()
        )
    except ValueError:
        # Obsidian cannot transclude outside the vault; fall back to a readable
        # path so the page still communicates where the note lives.
        return path.with_suffix("").as_posix()


def _resolve_notes_dir(vault_dir: Path, notes_dir: str | Path) -> Path:
    notes = Path(notes_dir).expanduser()
    if notes.is_absolute():
        return notes
    return vault_dir / notes


def _sidecar_note_path(notes_dir: Path, page: WikiPage) -> Path:
    safe_id = _safe_filename(page.page_id)
    return _safe_join(notes_dir, Path(page.kind) / f"{safe_id}.md")


def _sidecar_note_stub(page: WikiPage) -> str:
    return f"# {page.title} Notes\n\n"


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "note"


def _safe_join(root: Path, relative: str | Path) -> Path:
    root_resolved = root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError as exc:
        raise ObsidianError(f"Path escapes base directory: {path}") from exc
    return path


def _ensure_safe_base(path: Path) -> None:
    if path.name in {"", ".", ".."}:
        raise ObsidianError(f"Invalid directory path: {path}")


def _validate_existing_dir(path: Path, label: str) -> None:
    if not path.exists() or not path.is_dir():
        raise ObsidianError(f"{label} does not exist or is not a directory: {path}")


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
