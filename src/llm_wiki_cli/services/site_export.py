"""Pure static-site mirror export support for LLM Wiki.

The canonical wiki remains ``docs/llm_wiki``. This service builds a derived
Markdown mirror for static-site tooling without invoking external builders.
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union
from urllib.parse import unquote

from . import wiki_surface
from .io import read_md, write_md


SUPPORTED_SITE_FORMATS = frozenset({"plain", "mkdocs", "docusaurus"})
MARKDOWN_LINK_RE = re.compile(r"(!)?\[([^\]]+)\]\(([^)]+)\)")


class SiteExportError(ValueError):
    """Raised for invalid static-site export requests."""


@dataclass(frozen=True)
class SiteExportOperation:
    action: str
    source: str
    path: str
    message: str = ""


@dataclass
class SiteExportReport:
    ok: bool = True
    dry_run: bool = False
    wiki_dir: str = ""
    out_dir: str = ""
    format: str = "plain"
    front_matter: bool = False
    page_count: int = 0
    operations: list[SiteExportOperation] = field(default_factory=list)
    issues: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dry_run": self.dry_run,
            "wiki_dir": self.wiki_dir,
            "out_dir": self.out_dir,
            "format": self.format,
            "front_matter": self.front_matter,
            "page_count": self.page_count,
            "operations": [operation.__dict__ for operation in self.operations],
            "issues": self.issues,
        }


def export_site_mirror(
    *,
    wiki_dir: Union[str, Path],
    out_dir: Union[str, Path],
    format: str = "plain",
    front_matter: bool = False,
    dry_run: bool = False,
    allow_overwrite_source: bool = False,
) -> SiteExportReport:
    """Export a static-site-friendly Markdown mirror of the canonical wiki."""
    _validate_format(format)
    wiki = Path(wiki_dir).expanduser()
    out = Path(out_dir).expanduser()
    _validate_existing_dir(wiki, "wiki_dir")
    _validate_output_base(wiki, out, allow_overwrite_source=allow_overwrite_source)

    pages = wiki_surface.collect_wiki_pages(wiki)
    export_rel_by_source = {page.path.resolve(): page.relative_path for page in pages}
    report = SiteExportReport(
        dry_run=dry_run,
        wiki_dir=str(wiki),
        out_dir=str(out),
        format=format,
        front_matter=front_matter,
        page_count=len(pages),
    )

    for page in pages:
        target = _safe_join(out, page.relative_path)
        content = _build_export_page(
            page,
            read_md(page.path),
            export_rel_by_source,
            front_matter=front_matter,
        )

        if dry_run:
            report.operations.append(
                SiteExportOperation("would_write", str(page.path), str(target))
            )
            continue

        if target.exists() and read_md(target) == content:
            report.operations.append(
                SiteExportOperation("unchanged", str(page.path), str(target))
            )
            continue

        write_md(target, content)
        report.operations.append(
            SiteExportOperation("write", str(page.path), str(target))
        )

    return report


def _build_export_page(
    page: wiki_surface.WikiSurfacePage,
    content: str,
    export_rel_by_source: dict[Path, str],
    *,
    front_matter: bool,
) -> str:
    transformed = _rewrite_markdown_links(content, page, export_rel_by_source)
    if not front_matter:
        return transformed
    return "\n".join([_build_front_matter(page, transformed), "", transformed])


def _build_front_matter(page: wiki_surface.WikiSurfacePage, content: str) -> str:
    lines = [
        "---",
        f"title: {_yaml_quote(_markdown_title(content, page.page_id))}",
        "llm_wiki:",
        f"  kind: {_yaml_quote(page.kind.value)}",
        f"  id: {_yaml_quote(page.page_id)}",
        f"  role: {_yaml_quote(page.role.value)}",
        f"  canonical_path: {_yaml_quote(page.relative_path)}",
        f"  mcp_uri: {_yaml_quote(page.mcp_uri)}",
        "---",
    ]
    return "\n".join(lines)


def _rewrite_markdown_links(
    content: str,
    page: wiki_surface.WikiSurfacePage,
    export_rel_by_source: dict[Path, str],
) -> str:
    lines: list[str] = []
    in_fence = False
    for line in content.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            lines.append(line)
            continue
        if in_fence:
            lines.append(line)
            continue
        lines.append(
            MARKDOWN_LINK_RE.sub(
                lambda match: _rewrite_markdown_link(
                    match,
                    page,
                    export_rel_by_source,
                ),
                line,
            )
        )
    return "".join(lines)


def _rewrite_markdown_link(
    match: re.Match[str],
    page: wiki_surface.WikiSurfacePage,
    export_rel_by_source: dict[Path, str],
) -> str:
    if match.group(1):
        return match.group(0)

    label = match.group(2)
    target = match.group(3).strip()
    rewritten = _relative_export_link(page, target, export_rel_by_source)
    if rewritten is None:
        return match.group(0)
    return f"[{label}]({rewritten})"


def _relative_export_link(
    page: wiki_surface.WikiSurfacePage,
    target: str,
    export_rel_by_source: dict[Path, str],
) -> Optional[str]:
    if _is_external_link(target) or target.startswith("#"):
        return None

    raw_base, separator, anchor = target.partition("#")
    base = raw_base.strip()
    if not base or base.startswith("/"):
        return None
    if base.startswith("<") and base.endswith(">"):
        base = base[1:-1].strip()
    if not base:
        return None

    normalized = unquote(base).replace("\\", "/")
    source_target = (page.path.parent / normalized).resolve()
    target_export_rel = export_rel_by_source.get(source_target)
    if target_export_rel is None:
        return None

    current_parent = posixpath.dirname(page.relative_path) or "."
    rewritten = posixpath.relpath(target_export_rel, start=current_parent)
    if separator:
        rewritten = f"{rewritten}#{anchor}"
    return rewritten


def _markdown_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def _yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _validate_format(format: str) -> None:
    if format not in SUPPORTED_SITE_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_SITE_FORMATS))
        raise SiteExportError(
            f"Unsupported site export format: {format}. Supported formats: {supported}"
        )


def _validate_output_base(
    wiki: Path,
    out: Path,
    *,
    allow_overwrite_source: bool,
) -> None:
    if allow_overwrite_source:
        return
    wiki_resolved = wiki.resolve()
    out_resolved = out.resolve()
    if _paths_overlap(wiki_resolved, out_resolved):
        raise SiteExportError(
            f"Output directory overlaps the source wiki: {out_resolved}"
        )


def _paths_overlap(left: Path, right: Path) -> bool:
    try:
        left.relative_to(right)
        return True
    except ValueError:
        pass
    try:
        right.relative_to(left)
        return True
    except ValueError:
        return False


def _safe_join(root: Path, relative: str) -> Path:
    root_resolved = root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError as exc:
        raise SiteExportError(f"Path escapes output directory: {path}") from exc
    return path


def _validate_existing_dir(path: Path, label: str) -> None:
    if not path.exists() or not path.is_dir():
        raise SiteExportError(f"{label} does not exist or is not a directory: {path}")


def _is_external_link(target: str) -> bool:
    lowered = target.lower()
    return (
        "://" in lowered or lowered.startswith("mailto:") or lowered.startswith("tel:")
    )
