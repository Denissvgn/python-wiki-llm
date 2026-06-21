"""Pure static-site mirror export support for LLM Wiki.

The canonical wiki remains ``docs/llm_wiki``. This service builds a derived
Markdown mirror for static-site tooling without invoking external builders.
"""

from __future__ import annotations

import json
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
    source_paths = _load_surface_index_sources(wiki)
    effective_front_matter = front_matter or format in {"mkdocs", "docusaurus"}
    report = SiteExportReport(
        dry_run=dry_run,
        wiki_dir=str(wiki),
        out_dir=str(out),
        format=format,
        front_matter=effective_front_matter,
        page_count=len(pages),
    )

    for sidebar_position, page in enumerate(pages, start=1):
        target = _safe_join(out, page.relative_path)
        content = _build_export_page(
            page,
            read_md(page.path),
            export_rel_by_source,
            site_format=format,
            front_matter=effective_front_matter,
            sidebar_position=sidebar_position,
            source_path=source_paths.get(page.relative_path),
        )

        _record_write_operation(
            report,
            source=str(page.path),
            target=target,
            content=content,
        )

    if format == "mkdocs":
        _record_write_operation(
            report,
            source=str(wiki),
            target=_safe_join(out, "mkdocs.yml"),
            content=_build_mkdocs_config(pages),
        )

    if format == "docusaurus":
        _record_write_operation(
            report,
            source=str(wiki),
            target=_safe_join(out, "sidebars.json"),
            content=_build_docusaurus_sidebar(pages),
        )

    return report


def check_site_mirror(
    *,
    wiki_dir: Union[str, Path],
    out_dir: Union[str, Path],
) -> SiteExportReport:
    """Validate that an exported static-site mirror is present and linked."""
    wiki = Path(wiki_dir).expanduser()
    out = Path(out_dir).expanduser()
    _validate_existing_dir(wiki, "wiki_dir")
    pages = wiki_surface.collect_wiki_pages(wiki)
    report = SiteExportReport(
        wiki_dir=str(wiki),
        out_dir=str(out),
        page_count=len(pages),
    )

    if not out.exists() or not out.is_dir():
        report.issues.append(
            {
                "category": "missing_output_dir",
                "path": str(out),
                "message": f"Output directory does not exist: {out}",
            }
        )
        report.ok = False
        return report

    for page in pages:
        target = _safe_join(out, page.relative_path)
        if not target.is_file():
            report.issues.append(
                {
                    "category": "missing_mirror_page",
                    "path": str(target),
                    "message": f"Missing mirrored page for {page.relative_path}",
                }
            )
            continue
        report.issues.extend(_check_mirror_markdown_links(target, read_md(target), out))

    report.ok = not report.issues
    return report


def render_report_text(report: SiteExportReport, *, action: str) -> str:
    lines = [f"Static site {action}", f"Output: {report.out_dir}"]
    if report.wiki_dir:
        lines.append(f"Wiki: {report.wiki_dir}")
    lines.append(f"Format: {report.format}")
    lines.append(f"Pages: {report.page_count}")
    if report.dry_run:
        lines.append("Dry run: no files were changed.")
    if report.operations:
        lines.append("")
        lines.append("Operations:")
        for operation in report.operations:
            suffix = f" - {operation.message}" if operation.message else ""
            lines.append(f"- {operation.action}: {operation.path}{suffix}")
    if report.issues:
        lines.append("")
        lines.append("Issues:")
        for issue in report.issues:
            target = f" -> {issue.get('target')}" if issue.get("target") else ""
            lines.append(
                f"- {issue['category']}: {issue['path']}{target} - {issue['message']}"
            )
    elif action == "check":
        lines.append("No static-site mirror issues found.")
    return "\n".join(lines) + "\n"


def render_report_json(report: SiteExportReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def _build_export_page(
    page: wiki_surface.WikiSurfacePage,
    content: str,
    export_rel_by_source: dict[Path, str],
    *,
    site_format: str,
    front_matter: bool,
    sidebar_position: int,
    source_path: Optional[str],
) -> str:
    transformed = _rewrite_markdown_links(content, page, export_rel_by_source)
    title_source = transformed
    if site_format == "docusaurus":
        transformed = _escape_docusaurus_mdx_text(transformed)
    if not front_matter:
        return transformed
    return "\n".join(
        [
            _build_front_matter(
                page,
                title_source,
                site_format=site_format,
                sidebar_position=sidebar_position,
                source_path=source_path,
            ),
            "",
            transformed,
        ]
    )


def _build_front_matter(
    page: wiki_surface.WikiSurfacePage,
    content: str,
    *,
    site_format: str,
    sidebar_position: int,
    source_path: Optional[str],
) -> str:
    title = _markdown_title(content, page.page_id)
    lines = ["---"]
    if site_format == "docusaurus":
        lines.extend(
            [
                f"id: {_yaml_quote(_docusaurus_doc_id(page))}",
                f"title: {_yaml_quote(title)}",
                f"sidebar_label: {_yaml_quote(title)}",
                f"sidebar_position: {sidebar_position}",
            ]
        )
    else:
        lines.append(f"title: {_yaml_quote(title)}")
    lines.extend(
        [
            "llm_wiki:",
            f"  kind: {_yaml_quote(page.kind.value)}",
            f"  id: {_yaml_quote(page.page_id)}",
            f"  role: {_yaml_quote(page.role.value)}",
            f"  canonical_path: {_yaml_quote(page.relative_path)}",
            f"  mcp_uri: {_yaml_quote(page.mcp_uri)}",
        ]
    )
    if source_path:
        lines.append(f"  source_path: {_yaml_quote(source_path)}")
    lines.append("---")
    return "\n".join(lines)


def _record_write_operation(
    report: SiteExportReport,
    *,
    source: str,
    target: Path,
    content: str,
) -> None:
    if report.dry_run:
        report.operations.append(
            SiteExportOperation("would_write", source, str(target))
        )
        return

    if target.exists() and read_md(target) == content:
        report.operations.append(SiteExportOperation("unchanged", source, str(target)))
        return

    write_md(target, content)
    report.operations.append(SiteExportOperation("write", source, str(target)))


def _build_mkdocs_config(pages: list[wiki_surface.WikiSurfacePage]) -> str:
    lines = [
        "# Generated by llm-wiki site export.",
        "# Mermaid code fences are preserved as Markdown. Configure a MkDocs",
        "# Mermaid plugin in your site environment to render diagrams.",
        'site_name: "LLM Wiki"',
        'docs_dir: "."',
        'site_dir: "_site"',
        "nav:",
    ]
    for page in pages:
        title = _markdown_title(read_md(page.path), page.page_id)
        lines.append(f"  - {_yaml_quote(title)}: {_yaml_quote(page.relative_path)}")
    lines.append("")
    return "\n".join(lines)


def _build_docusaurus_sidebar(pages: list[wiki_surface.WikiSurfacePage]) -> str:
    sidebar_items: list[Any] = []
    categories_by_kind: dict[str, dict[str, Any]] = {}
    for page in pages:
        doc_id = _docusaurus_doc_id(page)
        if "/" not in page.relative_path:
            sidebar_items.append(doc_id)
            continue

        category = categories_by_kind.get(page.kind.value)
        if category is None:
            category = {
                "type": "category",
                "label": page.label,
                "items": [],
            }
            categories_by_kind[page.kind.value] = category
            sidebar_items.append(category)
        category["items"].append(doc_id)
    return json.dumps({"llmWikiSidebar": sidebar_items}, indent=2) + "\n"


def _load_surface_index_sources(wiki: Path) -> dict[str, str]:
    path = wiki / ".llm-wiki-surface.json"
    if not path.is_file():
        return {}
    try:
        payload = json.loads(read_md(path))
    except (OSError, json.JSONDecodeError):
        return {}

    sources: dict[str, str] = {}
    pages = payload.get("pages")
    if not isinstance(pages, list):
        return sources
    for entry in pages:
        if not isinstance(entry, dict):
            continue
        canonical_path = entry.get("canonical_path")
        source_path = entry.get("source_path")
        if isinstance(canonical_path, str) and isinstance(source_path, str):
            if canonical_path and source_path:
                sources[canonical_path] = source_path
    return sources


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


def _check_mirror_markdown_links(
    page_path: Path,
    content: str,
    out_dir: Path,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    out_resolved = out_dir.resolve()
    for target in _iter_markdown_link_targets(content):
        base = _local_markdown_link_base(target)
        if base is None:
            continue
        normalized = unquote(base).replace("\\", "/")
        candidate = (page_path.parent / normalized).resolve()
        try:
            candidate.relative_to(out_resolved)
        except ValueError:
            issues.append(
                {
                    "category": "unsafe_markdown_link",
                    "path": str(page_path),
                    "target": target,
                    "message": f"Markdown link escapes output directory: {target}",
                }
            )
            continue
        if not candidate.is_file():
            issues.append(
                {
                    "category": "broken_markdown_link",
                    "path": str(page_path),
                    "target": target,
                    "message": f"Broken local Markdown link: {target}",
                }
            )
    return issues


def _iter_markdown_link_targets(content: str) -> list[str]:
    targets: list[str] = []
    in_fence = False
    for line in content.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in MARKDOWN_LINK_RE.finditer(line):
            if match.group(1):
                continue
            targets.append(match.group(3).strip())
    return targets


def _local_markdown_link_base(target: str) -> Optional[str]:
    if _is_external_link(target) or target.startswith("#"):
        return None
    raw_base = target.split("#", 1)[0].strip()
    if not raw_base:
        return None
    if raw_base.startswith("<") and raw_base.endswith(">"):
        raw_base = raw_base[1:-1].strip()
    if not raw_base.lower().endswith(".md"):
        return None
    return raw_base


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


def _docusaurus_doc_id(page: wiki_surface.WikiSurfacePage) -> str:
    if page.relative_path.endswith(".md"):
        return page.relative_path[:-3]
    return page.relative_path


def _escape_docusaurus_mdx_text(content: str) -> str:
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
        lines.append(_escape_docusaurus_mdx_line(line))
    return "".join(lines)


def _escape_docusaurus_mdx_line(line: str) -> str:
    parts = line.split("`")
    escaped: list[str] = []
    for index, part in enumerate(parts):
        if index % 2:
            escaped.append(part)
        else:
            escaped.append(_escape_docusaurus_mdx_segment(part))
    return "`".join(escaped)


def _escape_docusaurus_mdx_segment(segment: str) -> str:
    escaped: list[str] = []
    for index, char in enumerate(segment):
        if char in "{}<" and (index == 0 or segment[index - 1] != "\\"):
            escaped.append("\\" + char)
        else:
            escaped.append(char)
    return "".join(escaped)


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
