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
from typing import Any, Iterable, Optional, Union
from urllib.parse import unquote

from . import wiki_surface
from .io import read_md, write_md


SUPPORTED_SITE_FORMATS = frozenset({"plain", "mkdocs", "docusaurus"})
MARKDOWN_LINK_RE = re.compile(r"(!)?\[([^\]]+)\]\(([^)]+)\)")
FRONT_MATTER_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")


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
    source_count: int = 0
    operations: list[SiteExportOperation] = field(default_factory=list)
    issues: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dry_run": self.dry_run,
            "wiki_dir": self.wiki_dir,
            "out_dir": self.out_dir,
            "format": self.format,
            "front_matter": self.front_matter,
            "page_count": self.page_count,
            "source_count": self.source_count,
            "operations": [operation.__dict__ for operation in self.operations],
            "issues": self.issues,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class FrontMatterParseResult:
    exists: bool
    metadata: dict[str, Any] = field(default_factory=dict)
    issue: Optional[dict[str, str]] = None


@dataclass(frozen=True)
class HubWikiSource:
    source_id: str
    wiki_dir: Path


def export_site_mirror(
    *,
    wiki_dir: Union[str, Path],
    out_dir: Union[str, Path],
    format: str = "plain",
    front_matter: bool = False,
    dry_run: bool = False,
    allow_overwrite_source: bool = False,
    docusaurus_id_prefix: str = "",
) -> SiteExportReport:
    """Export a static-site-friendly Markdown mirror of the canonical wiki."""
    _validate_format(format)
    wiki = Path(wiki_dir).expanduser()
    out = Path(out_dir).expanduser()
    _validate_existing_dir(wiki, "wiki_dir")
    _validate_output_base(wiki, out, allow_overwrite_source=allow_overwrite_source)

    pages = wiki_surface.collect_wiki_pages(wiki)
    page_contents = {page.relative_path: read_md(page.path) for page in pages}
    display_titles = _build_display_titles(pages, page_contents)
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
            page_contents[page.relative_path],
            export_rel_by_source,
            display_title=display_titles[page.relative_path],
            site_format=format,
            front_matter=effective_front_matter,
            sidebar_position=sidebar_position,
            source_path=source_paths.get(page.relative_path),
            docusaurus_id_prefix=docusaurus_id_prefix,
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
            content=_build_mkdocs_config(pages, display_titles),
        )

    if format == "docusaurus":
        _record_write_operation(
            report,
            source=str(wiki),
            target=_safe_join(out, "sidebars.json"),
            content=_build_docusaurus_sidebar(
                pages, docusaurus_id_prefix=docusaurus_id_prefix
            ),
        )

    return report


def export_site_hub(
    *,
    out_dir: Union[str, Path],
    wiki_root: Union[str, Path, None] = None,
    wikis: Iterable[Union[str, Path]] | None = None,
    format: str = "plain",
    front_matter: bool = False,
    dry_run: bool = False,
    allow_overwrite_source: bool = False,
) -> SiteExportReport:
    """Export multiple source wikis into a namespaced static-site hub."""
    _validate_format(format)
    out = Path(out_dir).expanduser()
    sources = _resolve_hub_sources(wiki_root=wiki_root, wikis=wikis)
    effective_front_matter = front_matter or format in {"mkdocs", "docusaurus"}
    report = SiteExportReport(
        dry_run=dry_run,
        wiki_dir=str(Path(wiki_root).expanduser()) if wiki_root is not None else "",
        out_dir=str(out),
        format=format,
        front_matter=effective_front_matter,
        source_count=len(sources),
    )

    hub_rows: list[tuple[str, int]] = []
    for source in sources:
        target = _safe_join(out, source.source_id)
        child = export_site_mirror(
            wiki_dir=source.wiki_dir,
            out_dir=target,
            format=format,
            front_matter=front_matter,
            dry_run=dry_run,
            allow_overwrite_source=allow_overwrite_source,
            docusaurus_id_prefix=(source.source_id if format == "docusaurus" else ""),
        )
        report.operations.extend(child.operations)
        report.issues.extend(child.issues)
        report.warnings.extend(child.warnings)
        report.page_count += child.page_count
        hub_rows.append((source.source_id, child.page_count))

    _record_write_operation(
        report,
        source=report.wiki_dir or "hub",
        target=_safe_join(out, "index.md"),
        content=_build_hub_index(hub_rows),
    )
    report.page_count += 1

    if format == "mkdocs":
        _record_write_operation(
            report,
            source=report.wiki_dir or "hub",
            target=_safe_join(out, "mkdocs.yml"),
            content=_build_mkdocs_hub_config(sources),
        )
    if format == "docusaurus":
        _record_write_operation(
            report,
            source=report.wiki_dir or "hub",
            target=_safe_join(out, "sidebars.json"),
            content=_build_docusaurus_hub_sidebar(sources),
        )

    report.ok = not report.issues
    return report


def check_site_mirror(
    *,
    wiki_dir: Union[str, Path],
    out_dir: Union[str, Path],
    docusaurus_id_prefix: str = "",
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

    out_resolved = out.resolve()
    pages_without_front_matter: list[tuple[wiki_surface.WikiSurfacePage, Path]] = []
    front_matter_ids: dict[str, Path] = {}
    found_front_matter = False

    for page in pages:
        try:
            target = _safe_join(out, page.relative_path)
        except SiteExportError as exc:
            report.issues.append(
                {
                    "category": "unsafe_output_path",
                    "path": str(out),
                    "target": page.relative_path,
                    "message": str(exc),
                }
            )
            continue
        if not _is_relative_to(target.resolve(), out_resolved):
            report.issues.append(
                {
                    "category": "unsafe_output_path",
                    "path": str(target),
                    "target": page.relative_path,
                    "message": (
                        "Mirrored page path escapes output directory: "
                        f"{page.relative_path}"
                    ),
                }
            )
            continue
        if not target.is_file():
            report.issues.append(
                {
                    "category": "missing_mirror_page",
                    "path": str(target),
                    "message": f"Missing mirrored page for {page.relative_path}",
                }
            )
            continue
        content = read_md(target)
        report.issues.extend(_check_mirror_markdown_links(target, content, out))
        front_matter = _parse_front_matter(target, content)
        if front_matter.issue is not None:
            report.issues.append(front_matter.issue)
            continue
        if not front_matter.exists:
            pages_without_front_matter.append((page, target))
            continue

        found_front_matter = True
        report.issues.extend(
            _check_front_matter_metadata(
                page,
                target,
                front_matter.metadata,
                docusaurus_id_prefix=docusaurus_id_prefix,
            )
        )
        doc_id = front_matter.metadata.get("id")
        if isinstance(doc_id, str):
            if doc_id in front_matter_ids:
                report.issues.append(
                    {
                        "category": "duplicate_front_matter_id",
                        "path": str(target),
                        "target": str(front_matter_ids[doc_id]),
                        "message": f"Duplicate front matter id: {doc_id}",
                    }
                )
            else:
                front_matter_ids[doc_id] = target

    report.front_matter = found_front_matter
    if found_front_matter:
        for page, target in pages_without_front_matter:
            report.warnings.append(
                {
                    "category": "missing_front_matter",
                    "path": str(target),
                    "target": page.relative_path,
                    "message": (
                        "Expected front matter in mixed static-site mirror page: "
                        f"{page.relative_path}"
                    ),
                }
            )

    report.ok = not report.issues
    return report


def check_site_hub(
    *,
    out_dir: Union[str, Path],
    wiki_root: Union[str, Path, None] = None,
    wikis: Iterable[Union[str, Path]] | None = None,
) -> SiteExportReport:
    """Validate a namespaced multi-wiki static-site hub."""
    out = Path(out_dir).expanduser()
    sources = _resolve_hub_sources(wiki_root=wiki_root, wikis=wikis)
    report = SiteExportReport(
        wiki_dir=str(Path(wiki_root).expanduser()) if wiki_root is not None else "",
        out_dir=str(out),
        source_count=len(sources),
        page_count=1,
    )

    if not (out / "index.md").is_file():
        report.issues.append(
            {
                "category": "missing_hub_index",
                "path": str(out / "index.md"),
                "message": "Missing generated hub index page.",
            }
        )

    for source in sources:
        child = check_site_mirror(
            wiki_dir=source.wiki_dir,
            out_dir=out / source.source_id,
            docusaurus_id_prefix=source.source_id,
        )
        report.page_count += child.page_count
        report.issues.extend(child.issues)
        report.warnings.extend(child.warnings)

    report.issues.extend(_check_hub_front_matter_id_collisions(out, sources))
    report.ok = not report.issues
    return report


def render_report_text(report: SiteExportReport, *, action: str) -> str:
    lines = [f"Static site {action}", f"Output: {report.out_dir}"]
    if report.wiki_dir:
        lines.append(f"Wiki: {report.wiki_dir}")
    lines.append(f"Format: {report.format}")
    if report.source_count:
        lines.append(f"Sources: {report.source_count}")
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
    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in report.warnings:
            target = f" -> {warning.get('target')}" if warning.get("target") else ""
            lines.append(
                "- "
                f"{warning['category']}: "
                f"{warning['path']}{target} - {warning['message']}"
            )
    elif action == "check" and not report.issues:
        lines.append("No static-site mirror issues found.")
    return "\n".join(lines) + "\n"


def render_report_json(report: SiteExportReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def _build_export_page(
    page: wiki_surface.WikiSurfacePage,
    content: str,
    export_rel_by_source: dict[Path, str],
    *,
    display_title: str,
    site_format: str,
    front_matter: bool,
    sidebar_position: int,
    source_path: Optional[str],
    docusaurus_id_prefix: str = "",
) -> str:
    transformed = _rewrite_markdown_links(content, page, export_rel_by_source)
    if site_format == "docusaurus":
        transformed = _escape_docusaurus_mdx_text(transformed)
    if not front_matter:
        return transformed
    return "\n".join(
        [
            _build_front_matter(
                page,
                display_title,
                site_format=site_format,
                sidebar_position=sidebar_position,
                source_path=source_path,
                docusaurus_id_prefix=docusaurus_id_prefix,
            ),
            "",
            transformed,
        ]
    )


def _build_front_matter(
    page: wiki_surface.WikiSurfacePage,
    title: str,
    *,
    site_format: str,
    sidebar_position: int,
    source_path: Optional[str],
    docusaurus_id_prefix: str = "",
) -> str:
    lines = ["---"]
    if site_format == "docusaurus":
        lines.extend(
            [
                f"id: {_yaml_quote(_docusaurus_doc_id(page, prefix=docusaurus_id_prefix))}",
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


def _build_mkdocs_config(
    pages: list[wiki_surface.WikiSurfacePage],
    display_titles: dict[str, str],
) -> str:
    lines = [
        "# Generated by llm-wiki site export.",
        "# Mermaid code fences are preserved as Markdown. Configure a MkDocs",
        "# Mermaid plugin in your site environment to render diagrams.",
        'site_name: "LLM Wiki"',
        'docs_dir: "."',
        'site_dir: "../_site"',
        "nav:",
    ]
    for page in pages:
        title = display_titles[page.relative_path]
        lines.append(f"  - {_yaml_quote(title)}: {_yaml_quote(page.relative_path)}")
    lines.append("")
    return "\n".join(lines)


def _build_hub_index(rows: list[tuple[str, int]]) -> str:
    lines = [
        "# LLM Wiki Hub",
        "",
        "| Source | Pages | Index |",
        "|---|---:|---|",
    ]
    for source_id, page_count in sorted(rows):
        lines.append(f"| {source_id} | {page_count} | [index]({source_id}/index.md) |")
    lines.append("")
    return "\n".join(lines)


def _hub_source_page_data(
    source: HubWikiSource,
) -> tuple[list[wiki_surface.WikiSurfacePage], dict[str, str]]:
    pages = wiki_surface.collect_wiki_pages(source.wiki_dir)
    page_contents = {page.relative_path: read_md(page.path) for page in pages}
    return pages, _build_display_titles(pages, page_contents)


def _build_mkdocs_hub_config(sources: list[HubWikiSource]) -> str:
    lines = [
        "# Generated by llm-wiki site export.",
        "# Mermaid code fences are preserved as Markdown. Configure a MkDocs",
        "# Mermaid plugin in your site environment to render diagrams.",
        'site_name: "LLM Wiki Hub"',
        'docs_dir: "."',
        'site_dir: "../_site"',
        "nav:",
    ]
    for source in sources:
        pages, display_titles = _hub_source_page_data(source)
        lines.append(f"  - {_yaml_quote(source.source_id)}:")
        for page in pages:
            title = display_titles[page.relative_path]
            path = f"{source.source_id}/{page.relative_path}"
            lines.append(f"    - {_yaml_quote(title)}: {_yaml_quote(path)}")
    lines.append("")
    return "\n".join(lines)


def _build_docusaurus_hub_sidebar(sources: list[HubWikiSource]) -> str:
    sidebar_items: list[Any] = []
    for source in sources:
        pages, _display_titles = _hub_source_page_data(source)
        sidebar_items.append(
            {
                "type": "category",
                "label": source.source_id,
                "items": _docusaurus_sidebar_items(
                    pages,
                    docusaurus_id_prefix=source.source_id,
                ),
            }
        )
    return json.dumps({"llmWikiSidebar": sidebar_items}, indent=2) + "\n"


def _build_docusaurus_sidebar(
    pages: list[wiki_surface.WikiSurfacePage],
    *,
    docusaurus_id_prefix: str = "",
) -> str:
    return (
        json.dumps(
            {
                "llmWikiSidebar": _docusaurus_sidebar_items(
                    pages, docusaurus_id_prefix=docusaurus_id_prefix
                )
            },
            indent=2,
        )
        + "\n"
    )


def _docusaurus_sidebar_items(
    pages: list[wiki_surface.WikiSurfacePage],
    *,
    docusaurus_id_prefix: str = "",
) -> list[Any]:
    sidebar_items: list[Any] = []
    categories_by_kind: dict[str, dict[str, Any]] = {}
    for page in pages:
        doc_id = _docusaurus_doc_id(page, prefix=docusaurus_id_prefix)
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
    return sidebar_items


def _resolve_hub_sources(
    *,
    wiki_root: Union[str, Path, None],
    wikis: Iterable[Union[str, Path]] | None,
) -> list[HubWikiSource]:
    sources: list[HubWikiSource] = []
    if wiki_root is not None:
        root = Path(wiki_root).expanduser()
        _validate_existing_dir(root, "wiki_root")
        for child in sorted(root.iterdir(), key=lambda path: path.name):
            if child.is_dir() and (child / "index.md").is_file():
                sources.append(HubWikiSource(child.name, child))

    for wiki in wikis or []:
        path = Path(wiki).expanduser()
        _validate_existing_dir(path, "wiki")
        sources.append(HubWikiSource(path.name, path))

    if not sources:
        raise SiteExportError("No source wikis found for hub export.")

    seen: dict[str, Path] = {}
    for source in sources:
        if source.source_id in seen:
            raise SiteExportError(f"Duplicate hub source id: {source.source_id}")
        seen[source.source_id] = source.wiki_dir
    return sources


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


def _parse_front_matter(page_path: Path, content: str) -> FrontMatterParseResult:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return FrontMatterParseResult(exists=False)

    closing_index: Optional[int] = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        return FrontMatterParseResult(
            exists=True,
            issue=_malformed_front_matter_issue(
                page_path, "Front matter is missing a closing delimiter."
            ),
        )

    metadata: dict[str, Any] = {}
    current_section: Optional[str] = None
    for raw_line in lines[1:closing_index]:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent == 0:
            parsed = _parse_front_matter_key_value(raw_line)
            if parsed is None:
                return FrontMatterParseResult(
                    exists=True,
                    issue=_malformed_front_matter_issue(
                        page_path, f"Cannot parse front matter line: {raw_line}"
                    ),
                )
            key, value = parsed
            if value == "":
                metadata[key] = {}
                current_section = key
                continue
            scalar = _parse_front_matter_scalar(value)
            if scalar is None:
                return FrontMatterParseResult(
                    exists=True,
                    issue=_malformed_front_matter_issue(
                        page_path, f"Cannot parse front matter value: {value}"
                    ),
                )
            metadata[key] = scalar
            current_section = None
            continue

        if indent == 2:
            parsed = _parse_front_matter_key_value(raw_line.strip())
            section = metadata.get(current_section or "")
            if parsed is None or not isinstance(section, dict):
                return FrontMatterParseResult(
                    exists=True,
                    issue=_malformed_front_matter_issue(
                        page_path, f"Cannot parse nested front matter line: {raw_line}"
                    ),
                )
            key, value = parsed
            scalar = _parse_front_matter_scalar(value)
            if scalar is None:
                return FrontMatterParseResult(
                    exists=True,
                    issue=_malformed_front_matter_issue(
                        page_path, f"Cannot parse front matter value: {value}"
                    ),
                )
            section[key] = scalar
            continue

        return FrontMatterParseResult(
            exists=True,
            issue=_malformed_front_matter_issue(
                page_path, f"Unsupported front matter indentation: {raw_line}"
            ),
        )

    return FrontMatterParseResult(exists=True, metadata=metadata)


def _parse_front_matter_key_value(line: str) -> Optional[tuple[str, str]]:
    if ":" not in line:
        return None
    key, value = line.split(":", 1)
    key = key.strip()
    if not key or not FRONT_MATTER_KEY_RE.fullmatch(key):
        return None
    return key, value.strip()


def _parse_front_matter_scalar(value: str) -> Optional[str]:
    if not value:
        return ""
    if not value.startswith('"'):
        return value
    if len(value) < 2 or not value.endswith('"'):
        return None
    return _yaml_unquote(value[1:-1])


def _yaml_unquote(value: str) -> Optional[str]:
    chars: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char != "\\":
            chars.append(char)
            index += 1
            continue
        index += 1
        if index >= len(value):
            return None
        escaped = value[index]
        if escaped == "n":
            chars.append("\n")
        elif escaped in {'"', "\\"}:
            chars.append(escaped)
        else:
            return None
        index += 1
    return "".join(chars)


def _check_front_matter_metadata(
    page: wiki_surface.WikiSurfacePage,
    page_path: Path,
    metadata: dict[str, Any],
    *,
    docusaurus_id_prefix: str = "",
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    llm_wiki = metadata.get("llm_wiki")
    if llm_wiki is None:
        issues.append(_missing_front_matter_key_issue(page_path, "llm_wiki"))
        return issues
    if not isinstance(llm_wiki, dict):
        issues.append(
            _malformed_front_matter_issue(
                page_path, "Front matter llm_wiki value must be a mapping."
            )
        )
        return issues

    expected_llm_wiki = {
        "kind": page.kind.value,
        "id": page.page_id,
        "role": page.role.value,
        "canonical_path": page.relative_path,
        "mcp_uri": page.mcp_uri,
    }
    for key, expected in expected_llm_wiki.items():
        actual = llm_wiki.get(key)
        target = f"llm_wiki.{key}"
        if actual is None:
            issues.append(_missing_front_matter_key_issue(page_path, target))
            continue
        if actual != expected:
            issues.append(
                _front_matter_mismatch_issue(
                    page_path,
                    target,
                    expected=expected,
                    actual=str(actual),
                )
            )

    doc_id = metadata.get("id")
    expected_doc_id = _docusaurus_doc_id(page, prefix=docusaurus_id_prefix)
    if isinstance(doc_id, str) and doc_id != expected_doc_id:
        issues.append(
            _front_matter_mismatch_issue(
                page_path,
                "id",
                expected=expected_doc_id,
                actual=doc_id,
            )
        )
    return issues


def _check_hub_front_matter_id_collisions(
    out: Path,
    sources: list[HubWikiSource],
) -> list[dict[str, str]]:
    seen: dict[str, Path] = {}
    issues: list[dict[str, str]] = []
    for source in sources:
        root = out / source.source_id
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.md")):
            try:
                content = read_md(path)
            except OSError:
                continue
            front_matter = _parse_front_matter(path, content)
            doc_id = front_matter.metadata.get("id") if front_matter.exists else None
            if not isinstance(doc_id, str):
                continue
            if doc_id in seen:
                issues.append(
                    {
                        "category": "duplicate_hub_front_matter_id",
                        "path": str(path),
                        "target": str(seen[doc_id]),
                        "message": f"Duplicate hub front matter id: {doc_id}",
                    }
                )
            else:
                seen[doc_id] = path
    return issues


def _malformed_front_matter_issue(page_path: Path, message: str) -> dict[str, str]:
    return {
        "category": "malformed_front_matter",
        "path": str(page_path),
        "message": message,
    }


def _missing_front_matter_key_issue(page_path: Path, target: str) -> dict[str, str]:
    return {
        "category": "front_matter_missing_key",
        "path": str(page_path),
        "target": target,
        "message": f"Front matter is missing required key: {target}",
    }


def _front_matter_mismatch_issue(
    page_path: Path,
    target: str,
    *,
    expected: str,
    actual: str,
) -> dict[str, str]:
    return {
        "category": "front_matter_mismatch",
        "path": str(page_path),
        "target": target,
        "message": (f"Front matter {target} is {actual!r}, expected {expected!r}."),
    }


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


def _build_display_titles(
    pages: list[wiki_surface.WikiSurfacePage],
    page_contents: dict[str, str],
) -> dict[str, str]:
    base_titles = {
        page.relative_path: _markdown_title(
            page_contents[page.relative_path], page.page_id
        )
        for page in pages
    }
    pages_by_title: dict[str, list[wiki_surface.WikiSurfacePage]] = {}
    for page in pages:
        title = base_titles[page.relative_path]
        pages_by_title.setdefault(title, []).append(page)

    display_titles: dict[str, str] = {}
    used_titles: set[str] = set()
    for page in pages:
        title = base_titles[page.relative_path]
        if len(pages_by_title[title]) == 1:
            display_title = title
        else:
            display_title = _disambiguated_display_title(page, title)
            if display_title in used_titles:
                display_title = f"{page.page_id} / {title}"
            if display_title in used_titles:
                stable_path = page.relative_path.removesuffix(".md").replace("/", " / ")
                display_title = f"{stable_path} / {title}"
        display_titles[page.relative_path] = display_title
        used_titles.add(display_title)
    return display_titles


def _disambiguated_display_title(
    page: wiki_surface.WikiSurfacePage,
    title: str,
) -> str:
    context = _page_id_context(page.page_id, title)
    return f"{context} / {title}"


def _page_id_context(page_id: str, title: str) -> str:
    page_id_parts = [part for part in page_id.split("_") if part]
    title_part_candidates = _title_part_candidates(title)
    for title_parts in title_part_candidates:
        if len(page_id_parts) <= len(title_parts):
            continue
        if _parts_match(page_id_parts[-len(title_parts) :], title_parts):
            return " / ".join(page_id_parts[: -len(title_parts)])
    return page_id.replace("_", " / ")


def _title_part_candidates(title: str) -> list[list[str]]:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", title) if part]
    candidates = [parts]
    if parts and parts[-1].casefold() == "module":
        candidates.append(parts[:-1])
    return [candidate for candidate in candidates if candidate]


def _parts_match(left: list[str], right: list[str]) -> bool:
    return [part.casefold() for part in left] == [part.casefold() for part in right]


def _docusaurus_doc_id(page: wiki_surface.WikiSurfacePage, *, prefix: str = "") -> str:
    doc_id = (
        page.relative_path[:-3]
        if page.relative_path.endswith(".md")
        else page.relative_path
    )
    return f"{prefix}/{doc_id}" if prefix else doc_id


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


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
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
