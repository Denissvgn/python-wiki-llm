"""Pure static-site mirror export support for LLM Wiki.

The canonical wiki remains ``docs/llm_wiki``. This service builds a derived
Markdown mirror for static-site tooling without invoking external builders.
"""

from __future__ import annotations

import json
import os
import posixpath
import re
import shutil
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional, Union
from urllib.parse import unquote

from . import wiki_surface
from .io import read_md, write_md
from .knowledge_projection import (
    UNKNOWN_VALUE as UNKNOWN_KNOWLEDGE_VALUE,
    KnowledgeProjection,
    KnowledgeProjectionError,
    validate_projection_summaries,
)
from .site_html_check import SUPPORTED_LINK_MODES, check_built_site_links
from .wiki_media import (
    build_asset_index,
    collect_media_references,
    iter_markdown_link_targets as iter_wiki_markdown_link_targets,
    media_type_for_path,
    strip_fenced_code_blocks,
)


SUPPORTED_SITE_FORMATS = frozenset({"plain", "mkdocs", "docusaurus"})
SUPPORTED_SITE_PROFILES = frozenset({"reference", "user"})
SUPPORTED_KNOWLEDGE_METADATA = frozenset({"summary"})
MAX_ENRICHED_OUTPUT_SCAN_ENTRIES = 10_000
MAX_ENRICHED_OUTPUT_SCAN_DEPTH = 32
MAX_ENRICHED_MARKDOWN_BYTES = 2 * 1024 * 1024
MARKDOWN_LINK_RE = re.compile(r"(!)?\[([^\]]+)\]\(([^)]+)\)")
_RAW_MEDIA_HTML_RE = re.compile(
    r"^\s*(?:<(?:img|video|source)(?=[\s/>])|</video\s*>)",
    re.IGNORECASE,
)
FRONT_MATTER_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")
GENERATED_REFERENCE_PATH = "generated-reference.md"
MKDOCS_FILE_FRIENDLY_OVERRIDE_DIR = ".llm-wiki-mkdocs-overrides"
MKDOCS_FILE_FRIENDLY_MAIN_TEMPLATE = """\
{% extends "base.html" %}

{% block site_name %}
{%- set home = namespace(prefix="") -%}
{%- if page and page.url -%}
  {%- for _ in range(page.url.count("/")) -%}
    {%- set home.prefix = home.prefix ~ "../" -%}
  {%- endfor -%}
{%- endif -%}
<a class="navbar-brand" href="{{ home.prefix }}index.html">{{ config.site_name }}</a>
{%- endblock %}
"""
MKDOCS_FILE_FRIENDLY_404_TEMPLATE = """\
{% extends "base.html" %}

{% block site_name %}
<a class="navbar-brand" href="index.html">{{ config.site_name }}</a>
{%- endblock %}

{% block content %}

    <div class="row-fluid">
      <div id="main-content" class="span12">
        <h1 id="404-page-not-found" style="text-align: center">404</h1>
        <p style="text-align: center"><strong>{% trans %}Page not found{% endtrans %}</strong></p>
      </div>
    </div>

{% endblock %}
"""
_PLACEHOLDER_PHRASES = (
    "Replace this placeholder",
    "_Auto-generated from",
    "data not statically known",
    "/**",
)


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
    built_site_dir: str = ""
    format: str = "plain"
    profile: str = "reference"
    site_name: str = ""
    distribution_mode: str = "http"
    link_mode: str = ""
    front_matter: bool = False
    page_count: int = 0
    source_count: int = 0
    asset_count: int = 0
    operations: list[SiteExportOperation] = field(default_factory=list)
    asset_operations: list[SiteExportOperation] = field(default_factory=list)
    issues: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dry_run": self.dry_run,
            "wiki_dir": self.wiki_dir,
            "out_dir": self.out_dir,
            "built_site_dir": self.built_site_dir,
            "format": self.format,
            "profile": self.profile,
            "site_name": self.site_name,
            "distribution_mode": self.distribution_mode,
            "link_mode": self.link_mode,
            "front_matter": self.front_matter,
            "page_count": self.page_count,
            "source_count": self.source_count,
            "asset_count": self.asset_count,
            "operations": [operation.__dict__ for operation in self.operations],
            "asset_operations": [
                operation.__dict__ for operation in self.asset_operations
            ],
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
    file_friendly: bool = False,
    profile: str = "reference",
    site_name: Optional[str] = None,
    knowledge_metadata: str | None = None,
    knowledge_projection: KnowledgeProjection | None = None,
) -> SiteExportReport:
    """Export a static-site-friendly Markdown mirror of the canonical wiki."""
    _validate_format(format)
    _validate_file_friendly(format, file_friendly=file_friendly)
    _validate_profile(profile)
    _validate_export_site_name(profile, site_name)
    wiki = Path(wiki_dir).expanduser()
    out = Path(out_dir).expanduser()
    _validate_existing_dir(wiki, "wiki_dir")
    _validate_output_base(
        wiki,
        out,
        allow_overwrite_source=(
            allow_overwrite_source and knowledge_metadata is None
        ),
    )

    pages = wiki_surface.collect_wiki_pages(wiki)
    knowledge_summaries = _preflight_knowledge_projection(
        pages,
        knowledge_metadata=knowledge_metadata,
        knowledge_projection=knowledge_projection,
    )
    if knowledge_summaries is not None:
        _preflight_existing_unexpected_knowledge_pages(
            out,
            expected_paths=_expected_mirror_markdown_paths(
                pages,
                profile=profile,
            ),
        )
    page_contents = {page.relative_path: read_md(page.path) for page in pages}
    display_titles = _build_display_titles(pages, page_contents)
    export_rel_by_source = {page.path.resolve(): page.relative_path for page in pages}
    # Enriched metadata has one authority: the validated projection. In
    # particular, public output never consults the raw surface index for source
    # coordinates.
    source_paths = (
        {}
        if knowledge_summaries is not None
        else _load_surface_index_sources(wiki)
    )
    effective_front_matter = (
        front_matter
        or format in {"mkdocs", "docusaurus"}
        or knowledge_summaries is not None
    )
    effective_site_name = site_name or "LLM Wiki"
    report = SiteExportReport(
        dry_run=dry_run,
        wiki_dir=str(wiki),
        out_dir=str(out),
        format=format,
        profile=profile,
        site_name=effective_site_name,
        distribution_mode=_distribution_mode(file_friendly),
        front_matter=effective_front_matter,
        page_count=len(pages) + (1 if profile == "user" else 0),
    )

    if profile == "user":
        _record_write_operation(
            report,
            source=str(wiki / "index.md"),
            target=_safe_join(out, "index.md"),
            content=_build_user_index_page(
                pages,
                page_contents,
                display_titles,
                site_name=effective_site_name,
                site_format=format,
                front_matter=effective_front_matter,
            ),
        )

    for sidebar_position, page in enumerate(pages, start=1):
        if profile == "user" and page.relative_path == "index.md":
            target = _safe_join(out, GENERATED_REFERENCE_PATH)
            content = _build_generated_reference_page(
                page,
                page_contents[page.relative_path],
                export_rel_by_source,
                site_format=format,
                display_title=display_titles[page.relative_path],
                front_matter=knowledge_summaries is not None,
                sidebar_position=sidebar_position,
                knowledge_summary=(
                    knowledge_summaries.get(page.relative_path)
                    if knowledge_summaries is not None
                    else None
                ),
            )
        else:
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
                knowledge_summary=(
                    knowledge_summaries.get(page.relative_path)
                    if knowledge_summaries is not None
                    else None
                ),
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
            content=(
                _build_mkdocs_user_config(
                    pages,
                    page_contents,
                    display_titles,
                    source_paths,
                    site_name=effective_site_name,
                    file_friendly=file_friendly,
                )
                if profile == "user"
                else _build_mkdocs_config(
                    pages,
                    display_titles,
                    file_friendly=file_friendly,
                )
            ),
        )
        _record_mkdocs_file_friendly_override(
            report, source=str(wiki), out=out, file_friendly=file_friendly
        )

    if format == "docusaurus":
        _record_write_operation(
            report,
            source=str(wiki),
            target=_safe_join(out, "sidebars.json"),
            content=(
                _build_docusaurus_user_sidebar(
                    pages,
                    page_contents,
                    display_titles,
                    source_paths,
                    docusaurus_id_prefix=docusaurus_id_prefix,
                )
                if profile == "user"
                else _build_docusaurus_sidebar(
                    pages, docusaurus_id_prefix=docusaurus_id_prefix
                )
            ),
        )

    _record_asset_operations(report, wiki=wiki, out=out, page_contents=page_contents)
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
    file_friendly: bool = False,
    profile: str = "reference",
    site_name: Optional[str] = None,
    knowledge_metadata: str | None = None,
    knowledge_projections: Mapping[str, KnowledgeProjection] | None = None,
) -> SiteExportReport:
    """Export multiple source wikis into a namespaced static-site hub."""
    _validate_format(format)
    _validate_file_friendly(format, file_friendly=file_friendly)
    _validate_profile(profile)
    if profile != "reference":
        raise SiteExportError("Hub export only supports --profile reference.")
    out = Path(out_dir).expanduser()
    sources = _resolve_hub_sources(wiki_root=wiki_root, wikis=wikis)
    _preflight_hub_knowledge_projections(
        sources,
        knowledge_metadata=knowledge_metadata,
        knowledge_projections=knowledge_projections,
    )
    _preflight_hub_root_output_collisions(
        sources,
        out=out,
        format=format,
        file_friendly=file_friendly,
    )
    # Resolve and cross-validate every output tree against every source before
    # the first child can write. Checking only the corresponding child/source
    # pair is insufficient: one child's destination can contain a different
    # source wiki and overwrite its canonical pages.
    planned_output_roots = [
        out,
        *(_safe_join(out, source.source_id) for source in sources),
    ]
    for planned_output in planned_output_roots:
        for source in sources:
            _validate_output_base(
                source.wiki_dir,
                planned_output,
                allow_overwrite_source=(
                    allow_overwrite_source and knowledge_metadata is None
                ),
            )
    if knowledge_metadata is not None:
        _preflight_existing_unexpected_knowledge_pages(
            out,
            expected_paths=_expected_hub_markdown_paths(sources),
        )
    effective_front_matter = (
        front_matter
        or format in {"mkdocs", "docusaurus"}
        or knowledge_metadata is not None
    )
    report = SiteExportReport(
        dry_run=dry_run,
        wiki_dir=str(Path(wiki_root).expanduser()) if wiki_root is not None else "",
        out_dir=str(out),
        format=format,
        profile=profile,
        site_name=site_name or "LLM Wiki Hub",
        distribution_mode=_distribution_mode(file_friendly),
        front_matter=effective_front_matter,
        source_count=len(sources),
    )

    hub_rows: list[tuple[str, int]] = []
    for source in sources:
        target = _safe_join(out, source.source_id)
        docusaurus_prefix = _hub_front_matter_id_prefix(
            source,
            knowledge_metadata=knowledge_metadata,
            knowledge_projections=knowledge_projections,
        )
        child = export_site_mirror(
            wiki_dir=source.wiki_dir,
            out_dir=target,
            format=format,
            front_matter=front_matter,
            dry_run=dry_run,
            allow_overwrite_source=allow_overwrite_source,
            docusaurus_id_prefix=(
                docusaurus_prefix if format == "docusaurus" else ""
            ),
            file_friendly=file_friendly,
            knowledge_metadata=knowledge_metadata,
            knowledge_projection=(
                knowledge_projections.get(source.source_id)
                if knowledge_projections is not None
                else None
            ),
        )
        report.operations.extend(child.operations)
        report.asset_operations.extend(child.asset_operations)
        report.issues.extend(child.issues)
        report.warnings.extend(child.warnings)
        report.page_count += child.page_count
        report.asset_count += child.asset_count
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
            content=_build_mkdocs_hub_config(sources, file_friendly=file_friendly),
        )
        _record_mkdocs_file_friendly_override(
            report,
            source=report.wiki_dir or "hub",
            out=out,
            file_friendly=file_friendly,
        )
    if format == "docusaurus":
        _record_write_operation(
            report,
            source=report.wiki_dir or "hub",
            target=_safe_join(out, "sidebars.json"),
            content=_build_docusaurus_hub_sidebar(
                sources,
                docusaurus_id_prefixes={
                    source.source_id: _hub_front_matter_id_prefix(
                        source,
                        knowledge_metadata=knowledge_metadata,
                        knowledge_projections=knowledge_projections,
                    )
                    for source in sources
                },
            ),
        )

    report.ok = not report.issues
    return report


def check_site_mirror(
    *,
    wiki_dir: Union[str, Path],
    out_dir: Union[str, Path],
    docusaurus_id_prefix: str = "",
    built_site_dir: Union[str, Path, None] = None,
    link_mode: str = "http",
    profile: str = "reference",
    site_name: Optional[str] = None,
    knowledge_metadata: str | None = None,
    knowledge_projection: KnowledgeProjection | None = None,
) -> SiteExportReport:
    """Validate that an exported static-site mirror is present and linked."""
    _validate_link_mode(link_mode)
    _validate_profile(profile)
    wiki = Path(wiki_dir).expanduser()
    out = Path(out_dir).expanduser()
    _validate_existing_dir(wiki, "wiki_dir")
    pages = wiki_surface.collect_wiki_pages(wiki)
    knowledge_summaries = _preflight_knowledge_projection(
        pages,
        knowledge_metadata=knowledge_metadata,
        knowledge_projection=knowledge_projection,
    )
    report = SiteExportReport(
        wiki_dir=str(wiki),
        out_dir=str(out),
        built_site_dir=str(Path(built_site_dir).expanduser())
        if built_site_dir is not None
        else "",
        profile=profile,
        site_name=site_name or "",
        link_mode=link_mode if built_site_dir is not None else "",
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

    if knowledge_summaries is not None:
        output_scan_issues = _check_existing_unexpected_knowledge_pages(
            out,
            expected_paths=_expected_mirror_markdown_paths(
                pages,
                profile=profile,
            ),
        )
        report.issues.extend(output_scan_issues)
        if any(
            issue["category"] == "unsafe_enriched_output_scan"
            for issue in output_scan_issues
        ):
            report.ok = False
            return report

    out_resolved = out.resolve()
    pages_without_front_matter: list[tuple[wiki_surface.WikiSurfacePage, Path]] = []
    front_matter_ids: dict[str, Path] = {}
    found_front_matter = False

    if profile == "user" and knowledge_summaries is not None:
        report.issues.extend(
            _check_projection_free_user_landing(out)
        )

    for page in pages:
        try:
            target = _safe_join(
                out,
                GENERATED_REFERENCE_PATH
                if profile == "user" and page.relative_path == "index.md"
                else page.relative_path,
            )
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
        if (
            profile == "user"
            and page.relative_path == "index.md"
            and knowledge_summaries is None
        ):
            continue
        front_matter = _parse_front_matter(target, content)
        if front_matter.issue is not None:
            report.issues.append(front_matter.issue)
            continue
        if not front_matter.exists:
            if knowledge_summaries is not None:
                report.issues.append(
                    {
                        "category": "missing_knowledge_metadata",
                        "path": str(target),
                        "target": page.relative_path,
                        "message": (
                            "Knowledge metadata mode requires front matter "
                            "from the selected projection."
                        ),
                    }
                )
                continue
            pages_without_front_matter.append((page, target))
            continue

        found_front_matter = True
        report.issues.extend(
            _check_front_matter_metadata(
                page,
                target,
                front_matter.metadata,
                docusaurus_id_prefix=docusaurus_id_prefix,
                docusaurus_id_override=(
                    GENERATED_REFERENCE_PATH.removesuffix(".md")
                    if profile == "user" and page.relative_path == "index.md"
                    else None
                ),
                knowledge_summary=(
                    knowledge_summaries.get(page.relative_path)
                    if knowledge_summaries is not None
                    else None
                ),
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

    if knowledge_summaries is not None:
        report.issues.extend(
            _check_knowledge_metadata_references(
                pages,
                out,
                profile=profile,
                expected_summaries=knowledge_summaries,
            )
        )

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

    if built_site_dir is not None:
        report.issues.extend(
            check_built_site_links(
                built_site_dir=built_site_dir,
                link_mode=link_mode,
            )
        )

    report.warnings.extend(_stale_asset_warnings(wiki, out))

    if profile == "user":
        quality_issues, quality_warnings = _check_user_profile_quality(
            out,
            site_name=site_name,
        )
        report.issues.extend(quality_issues)
        report.warnings.extend(quality_warnings)

    report.ok = not report.issues
    return report


def check_site_hub(
    *,
    out_dir: Union[str, Path],
    wiki_root: Union[str, Path, None] = None,
    wikis: Iterable[Union[str, Path]] | None = None,
    knowledge_metadata: str | None = None,
    knowledge_projections: Mapping[str, KnowledgeProjection] | None = None,
) -> SiteExportReport:
    """Validate a namespaced multi-wiki static-site hub."""
    out = Path(out_dir).expanduser()
    sources = _resolve_hub_sources(wiki_root=wiki_root, wikis=wikis)
    _preflight_hub_knowledge_projections(
        sources,
        knowledge_metadata=knowledge_metadata,
        knowledge_projections=knowledge_projections,
    )
    report = SiteExportReport(
        wiki_dir=str(Path(wiki_root).expanduser()) if wiki_root is not None else "",
        out_dir=str(out),
        source_count=len(sources),
        page_count=1,
    )
    global_scan_issue_keys: set[tuple[str, str]] = set()
    if knowledge_metadata is not None and out.exists():
        global_scan_issues = _check_existing_unexpected_knowledge_pages(
            out,
            expected_paths=_expected_hub_markdown_paths(sources),
        )
        report.issues.extend(global_scan_issues)
        global_scan_issue_keys = {
            (issue["category"], issue["path"])
            for issue in global_scan_issues
        }

    if not (out / "index.md").is_file():
        report.issues.append(
            {
                "category": "missing_hub_index",
                "path": str(out / "index.md"),
                "message": "Missing generated hub index page.",
            }
        )

    for source in sources:
        docusaurus_prefix = _hub_front_matter_id_prefix(
            source,
            knowledge_metadata=knowledge_metadata,
            knowledge_projections=knowledge_projections,
        )
        child = check_site_mirror(
            wiki_dir=source.wiki_dir,
            out_dir=out / source.source_id,
            docusaurus_id_prefix=docusaurus_prefix,
            knowledge_metadata=knowledge_metadata,
            knowledge_projection=(
                knowledge_projections.get(source.source_id)
                if knowledge_projections is not None
                else None
            ),
        )
        report.page_count += child.page_count
        report.issues.extend(
            issue
            for issue in child.issues
            if (issue["category"], issue["path"])
            not in global_scan_issue_keys
        )
        report.warnings.extend(child.warnings)

    unsafe_enriched_scan = (
        knowledge_metadata is not None
        and any(
            issue["category"]
            in {"unsafe_enriched_output_scan", "unsafe_output_path"}
            for issue in report.issues
        )
    )
    if not unsafe_enriched_scan:
        report.issues.extend(_check_hub_front_matter_id_collisions(out, sources))
        if knowledge_metadata is not None:
            report.issues.extend(_check_hub_knowledge_uid_collisions(out, sources))
    report.ok = not report.issues
    return report


def render_report_text(report: SiteExportReport, *, action: str) -> str:
    lines = [f"Static site {action}", f"Output: {report.out_dir}"]
    if report.wiki_dir:
        lines.append(f"Wiki: {report.wiki_dir}")
    lines.append(f"Format: {report.format}")
    lines.append(f"Profile: {report.profile}")
    if report.site_name:
        lines.append(f"Site name: {report.site_name}")
    lines.append(
        f"Distribution mode: {_distribution_mode_label(report.distribution_mode)}"
    )
    if report.built_site_dir:
        lines.append(f"Built site: {report.built_site_dir}")
        lines.append(f"Built link mode: {report.link_mode}")
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
    if report.asset_operations:
        lines.append("")
        lines.append("Asset operations:")
        for operation in report.asset_operations:
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
    knowledge_summary: Mapping[str, str] | None = None,
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
                knowledge_summary=knowledge_summary,
            ),
            "",
            transformed,
        ]
    )


def _build_generated_reference_page(
    page: wiki_surface.WikiSurfacePage,
    content: str,
    export_rel_by_source: dict[Path, str],
    *,
    site_format: str,
    display_title: str | None = None,
    front_matter: bool = False,
    sidebar_position: int = 1,
    knowledge_summary: Mapping[str, str] | None = None,
) -> str:
    transformed = _rewrite_markdown_links(content, page, export_rel_by_source)
    if site_format == "docusaurus":
        transformed = _escape_docusaurus_mdx_text(transformed)
    if front_matter:
        transformed = "\n".join(
            [
                _build_front_matter(
                    page,
                    display_title or "Generated Reference",
                    site_format=site_format,
                    sidebar_position=sidebar_position,
                    source_path=None,
                    docusaurus_id_override=(
                        GENERATED_REFERENCE_PATH.removesuffix(".md")
                    ),
                    knowledge_summary=knowledge_summary,
                ),
                "",
                transformed,
            ]
        )
    return transformed


def _build_user_index_page(
    pages: list[wiki_surface.WikiSurfacePage],
    page_contents: dict[str, str],
    display_titles: dict[str, str],
    *,
    site_name: str,
    site_format: str,
    front_matter: bool,
) -> str:
    lines: list[str] = []
    if front_matter:
        lines.extend(_build_title_front_matter(site_name, site_format=site_format))
        lines.append("")
    lines.extend(
        [
            f"# {site_name}",
            "",
            "## Overview",
            "",
            (
                f"{site_name} documentation combines curated guide pages with "
                "generated reference pages from the project wiki."
            ),
            "",
            "## Start Here",
            "",
        ]
    )
    _append_user_index_links(
        lines,
        _pages_by_kind(pages, wiki_surface.PageKind.GUIDES),
        display_titles,
        empty_text="No guide pages are present yet.",
    )
    lines.extend(["", "## Core Workflows", ""])
    _append_user_index_links(
        lines,
        _core_workflow_pages(pages, page_contents),
        display_titles,
        empty_text="No workflow pages are present yet.",
    )
    lines.extend(["", "## Architecture And Operations", ""])
    _append_user_index_links(
        lines,
        _architecture_pages(pages),
        display_titles,
        empty_text="No architecture or operations pages are present yet.",
    )
    lines.extend(
        [
            "",
            "## Generated Reference",
            "",
            "- [Generated Reference](generated-reference.md)",
            "",
        ]
    )
    return "\n".join(lines)


def _build_title_front_matter(title: str, *, site_format: str) -> list[str]:
    if site_format == "docusaurus":
        return [
            "---",
            'id: "index"',
            f"title: {_yaml_quote(title)}",
            f"sidebar_label: {_yaml_quote(title)}",
            "sidebar_position: 1",
            "---",
        ]
    return ["---", f"title: {_yaml_quote(title)}", "---"]


def _append_user_index_links(
    lines: list[str],
    pages: list[wiki_surface.WikiSurfacePage],
    display_titles: dict[str, str],
    *,
    empty_text: str,
) -> None:
    if not pages:
        lines.append(empty_text)
        return
    for page in pages:
        title = display_titles[page.relative_path]
        lines.append(f"- [{title}]({page.relative_path})")


def _pages_by_kind(
    pages: list[wiki_surface.WikiSurfacePage],
    kind: wiki_surface.PageKind,
) -> list[wiki_surface.WikiSurfacePage]:
    return [page for page in pages if page.kind is kind]


def _core_workflow_pages(
    pages: list[wiki_surface.WikiSurfacePage],
    page_contents: dict[str, str],
) -> list[wiki_surface.WikiSurfacePage]:
    workflows = _pages_by_kind(pages, wiki_surface.PageKind.WORKFLOWS)
    promoted_flows = [
        page
        for page in _pages_by_kind(pages, wiki_surface.PageKind.FLOWS)
        if _flow_has_substantive_behavior(page_contents.get(page.relative_path, ""))
    ]
    return workflows + promoted_flows


def _architecture_pages(
    pages: list[wiki_surface.WikiSurfacePage],
) -> list[wiki_surface.WikiSurfacePage]:
    architecture_kinds = {
        wiki_surface.PageKind.INFRASTRUCTURE,
        wiki_surface.PageKind.API_CONTRACTS,
        wiki_surface.PageKind.DEPENDENCIES,
        wiki_surface.PageKind.LOAD_ORDER,
    }
    return [page for page in pages if page.kind in architecture_kinds]


def _build_front_matter(
    page: wiki_surface.WikiSurfacePage,
    title: str,
    *,
    site_format: str,
    sidebar_position: int,
    source_path: Optional[str],
    docusaurus_id_prefix: str = "",
    docusaurus_id_override: str | None = None,
    knowledge_summary: Mapping[str, str] | None = None,
) -> str:
    lines = ["---"]
    if site_format == "docusaurus":
        lines.extend(
            [
                "id: "
                + _yaml_quote(
                    docusaurus_id_override
                    or _docusaurus_doc_id(page, prefix=docusaurus_id_prefix)
                ),
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
    if knowledge_summary is not None:
        for key, value in knowledge_summary.items():
            lines.append(f"  {key}: {_yaml_quote(value)}")
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


def _record_mkdocs_file_friendly_override(
    report: SiteExportReport,
    *,
    source: str,
    out: Path,
    file_friendly: bool,
) -> None:
    if not file_friendly:
        return
    _record_write_operation(
        report,
        source=source,
        target=_safe_join(out, f"{MKDOCS_FILE_FRIENDLY_OVERRIDE_DIR}/main.html"),
        content=MKDOCS_FILE_FRIENDLY_MAIN_TEMPLATE,
    )
    _record_write_operation(
        report,
        source=source,
        target=_safe_join(out, f"{MKDOCS_FILE_FRIENDLY_OVERRIDE_DIR}/404.html"),
        content=MKDOCS_FILE_FRIENDLY_404_TEMPLATE,
    )


def _record_asset_operations(
    report: SiteExportReport,
    *,
    wiki: Path,
    out: Path,
    page_contents: dict[str, str],
) -> None:
    asset_index = build_asset_index(wiki, page_contents)
    referenced = set(asset_index.referenced)
    for asset_rel in asset_index.referenced:
        source = wiki / Path(asset_rel)
        if not source.is_file():
            continue
        report.asset_count += 1
        target = _safe_join(out, asset_rel)
        _record_asset_copy_operation(report, source=source, target=target)

    for stale in _stale_exported_assets(referenced, out):
        report.asset_operations.append(
            SiteExportOperation(
                "stale_asset",
                str(out),
                str(_safe_join(out, stale)),
                "Previously exported asset is no longer referenced.",
            )
        )


def _record_asset_copy_operation(
    report: SiteExportReport,
    *,
    source: Path,
    target: Path,
) -> None:
    if report.dry_run:
        report.asset_operations.append(
            SiteExportOperation("would_copy", str(source), str(target))
        )
        return
    if target.is_file() and _same_file_bytes(source, target):
        report.asset_operations.append(
            SiteExportOperation("unchanged", str(source), str(target))
        )
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    report.asset_operations.append(
        SiteExportOperation("copy", str(source), str(target))
    )


def _same_file_bytes(left: Path, right: Path) -> bool:
    try:
        if left.stat().st_size != right.stat().st_size:
            return False
        with left.open("rb") as left_file, right.open("rb") as right_file:
            while True:
                left_chunk = left_file.read(64 * 1024)
                right_chunk = right_file.read(64 * 1024)
                if left_chunk != right_chunk:
                    return False
                if not left_chunk:
                    return True
    except OSError:
        return False


def _stale_exported_assets(referenced: set[str], out: Path) -> list[str]:
    return [asset for asset in _exported_asset_paths(out) if asset not in referenced]


def _stale_asset_warnings(wiki: Path, out: Path) -> list[dict[str, str]]:
    if not out.is_dir():
        return []
    source_assets = build_asset_index(wiki)
    referenced = set(source_assets.referenced)
    warnings: list[dict[str, str]] = []
    for asset_rel in _stale_exported_assets(referenced, out):
        warnings.append(
            {
                "category": "stale_asset",
                "path": str(_safe_join(out, asset_rel)),
                "target": asset_rel,
                "message": (
                    "Exported asset is no longer referenced by the source wiki: "
                    f"{asset_rel}"
                ),
            }
        )
    return warnings


def _exported_asset_paths(root: Path) -> list[str]:
    paths = []
    if not root.is_dir():
        return paths
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if media_type_for_path(rel) is not None:
            paths.append(rel)
    return sorted(paths, key=lambda value: (value.casefold(), value))


def _build_mkdocs_config(
    pages: list[wiki_surface.WikiSurfacePage],
    display_titles: dict[str, str],
    *,
    file_friendly: bool = False,
) -> str:
    lines = [
        "# Generated by llm-wiki site export.",
        "# Mermaid code fences are preserved as Markdown. Configure a MkDocs",
        "# Mermaid plugin in your site environment to render diagrams.",
        'site_name: "LLM Wiki"',
        'docs_dir: "."',
        'site_dir: "../_site"',
    ]
    if file_friendly:
        lines.extend(_mkdocs_file_friendly_config_lines())
    lines.append("nav:")
    for page in pages:
        title = display_titles[page.relative_path]
        lines.append(f"  - {_yaml_quote(title)}: {_yaml_quote(page.relative_path)}")
    lines.append("")
    return "\n".join(lines)


def _build_mkdocs_user_config(
    pages: list[wiki_surface.WikiSurfacePage],
    page_contents: dict[str, str],
    display_titles: dict[str, str],
    source_paths: dict[str, str],
    *,
    site_name: str,
    file_friendly: bool = False,
) -> str:
    lines = [
        "# Generated by llm-wiki site export.",
        "# Mermaid code fences are preserved as Markdown. Configure a MkDocs",
        "# Mermaid plugin in your site environment to render diagrams.",
        f"site_name: {_yaml_quote(site_name)}",
        'docs_dir: "."',
        'site_dir: "../_site"',
    ]
    if file_friendly:
        lines.extend(_mkdocs_file_friendly_config_lines())
    lines.append("nav:")
    for group, entries in _user_nav_groups(
        pages,
        page_contents,
        display_titles,
        source_paths,
        site_name=site_name,
    ):
        if not entries:
            continue
        lines.append(f"  - {_yaml_quote(group)}:")
        for title, path in entries:
            lines.append(f"    - {_yaml_quote(title)}: {_yaml_quote(path)}")
    lines.append("")
    return "\n".join(lines)


def _user_nav_groups(
    pages: list[wiki_surface.WikiSurfacePage],
    page_contents: dict[str, str],
    display_titles: dict[str, str],
    source_paths: dict[str, str],
    *,
    site_name: str,
) -> list[tuple[str, list[tuple[str, str]]]]:
    test_pages: list[wiki_surface.WikiSurfacePage] = []
    product_pages: list[wiki_surface.WikiSurfacePage] = []
    for page in pages:
        if page.relative_path == "index.md":
            continue
        if _is_test_or_fixture_page(page, source_paths):
            test_pages.append(page)
        else:
            product_pages.append(page)

    guides = _pages_by_kind(product_pages, wiki_surface.PageKind.GUIDES)
    workflows = _pages_by_kind(product_pages, wiki_surface.PageKind.WORKFLOWS)
    flows = _pages_by_kind(product_pages, wiki_surface.PageKind.FLOWS)
    promoted_flows = [
        page
        for page in flows
        if _flow_has_substantive_behavior(page_contents.get(page.relative_path, ""))
    ]
    lower_flows = [page for page in flows if page not in promoted_flows]
    architecture = _architecture_pages(product_pages)
    generated_reference = [
        page
        for page in product_pages
        if page.kind
        in {
            wiki_surface.PageKind.LOG,
            wiki_surface.PageKind.ENTITIES,
            wiki_surface.PageKind.MODULES,
        }
    ] + lower_flows
    return [
        (
            "Start Here",
            [(site_name, "index.md")] + _nav_entries(guides, display_titles),
        ),
        (
            "Core Workflows",
            _nav_entries(workflows + promoted_flows, display_titles),
        ),
        ("Architecture And Operations", _nav_entries(architecture, display_titles)),
        (
            "Generated Reference",
            [("Generated Reference", GENERATED_REFERENCE_PATH)]
            + _nav_entries(generated_reference, display_titles),
        ),
        ("Test And Fixture Reference", _nav_entries(test_pages, display_titles)),
    ]


def _nav_entries(
    pages: list[wiki_surface.WikiSurfacePage],
    display_titles: dict[str, str],
) -> list[tuple[str, str]]:
    return [(display_titles[page.relative_path], page.relative_path) for page in pages]


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


def _build_mkdocs_hub_config(
    sources: list[HubWikiSource],
    *,
    file_friendly: bool = False,
) -> str:
    lines = [
        "# Generated by llm-wiki site export.",
        "# Mermaid code fences are preserved as Markdown. Configure a MkDocs",
        "# Mermaid plugin in your site environment to render diagrams.",
        'site_name: "LLM Wiki Hub"',
        'docs_dir: "."',
        'site_dir: "../_site"',
    ]
    if file_friendly:
        lines.extend(_mkdocs_file_friendly_config_lines())
    lines.append("nav:")
    for source in sources:
        pages, display_titles = _hub_source_page_data(source)
        lines.append(f"  - {_yaml_quote(source.source_id)}:")
        for page in pages:
            title = display_titles[page.relative_path]
            path = f"{source.source_id}/{page.relative_path}"
            lines.append(f"    - {_yaml_quote(title)}: {_yaml_quote(path)}")
    lines.append("")
    return "\n".join(lines)


def _mkdocs_file_friendly_config_lines() -> list[str]:
    return [
        "use_directory_urls: false",
        "theme:",
        "  name: mkdocs",
        f"  custom_dir: {_yaml_quote(MKDOCS_FILE_FRIENDLY_OVERRIDE_DIR)}",
    ]


def _build_docusaurus_hub_sidebar(
    sources: list[HubWikiSource],
    *,
    docusaurus_id_prefixes: Mapping[str, str] | None = None,
) -> str:
    sidebar_items: list[Any] = []
    for source in sources:
        pages, _display_titles = _hub_source_page_data(source)
        sidebar_items.append(
            {
                "type": "category",
                "label": source.source_id,
                "items": _docusaurus_sidebar_items(
                    pages,
                    docusaurus_id_prefix=(
                        docusaurus_id_prefixes.get(
                            source.source_id,
                            source.source_id,
                        )
                        if docusaurus_id_prefixes is not None
                        else source.source_id
                    ),
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


def _build_docusaurus_user_sidebar(
    pages: list[wiki_surface.WikiSurfacePage],
    page_contents: dict[str, str],
    display_titles: dict[str, str],
    source_paths: dict[str, str],
    *,
    docusaurus_id_prefix: str = "",
) -> str:
    def doc_id(path: str) -> str:
        stem = path[:-3] if path.endswith(".md") else path
        return f"{docusaurus_id_prefix}/{stem}" if docusaurus_id_prefix else stem

    sidebar_items: list[Any] = []
    for group, entries in _user_nav_groups(
        pages,
        page_contents,
        display_titles,
        source_paths,
        site_name="Index",
    ):
        if not entries:
            continue
        sidebar_items.append(
            {
                "type": "category",
                "label": group,
                "items": [doc_id(path) for _title, path in entries],
            }
        )
    return json.dumps({"llmWikiSidebar": sidebar_items}, indent=2) + "\n"


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


def _flow_has_substantive_behavior(content: str) -> bool:
    behavior = _markdown_section(content, "Behavior")
    if behavior is None:
        return False
    stripped = behavior.strip()
    if not stripped or _contains_placeholder(stripped):
        return False
    words = re.findall(r"[A-Za-z0-9_]+", stripped)
    return len(words) >= 8


def _markdown_section(content: str, title: str) -> Optional[str]:
    lines = content.splitlines()
    start: Optional[int] = None
    for index, line in enumerate(lines):
        if line.strip().casefold() == f"## {title}".casefold():
            start = index + 1
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end])


def _is_test_or_fixture_page(
    page: wiki_surface.WikiSurfacePage,
    source_paths: dict[str, str],
) -> bool:
    source_path = source_paths.get(page.relative_path)
    if not source_path:
        return False
    normalized = source_path.replace("\\", "/").casefold()
    wrapped = f"/{normalized.strip('/')}"
    basename = posixpath.basename(normalized)
    return (
        "/tests/" in wrapped
        or "/fixtures/" in wrapped
        or "/mocks/" in wrapped
        or "/fake" in wrapped
        or basename.startswith("test_")
        or "_test" in basename
    )


def _contains_placeholder(content: str) -> bool:
    return any(phrase in content for phrase in _PLACEHOLDER_PHRASES)


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


def resolve_site_hub_sources(
    *,
    wiki_root: Union[str, Path, None],
    wikis: Iterable[Union[str, Path]] | None,
) -> list[HubWikiSource]:
    """Resolve hub inputs for callers that must prepare one projection each."""

    return _resolve_hub_sources(wiki_root=wiki_root, wikis=wikis)


def _hub_front_matter_id_prefix(
    source: HubWikiSource,
    *,
    knowledge_metadata: str | None,
    knowledge_projections: Mapping[str, KnowledgeProjection] | None,
) -> str:
    if knowledge_metadata is None or knowledge_projections is None:
        return source.source_id
    projection = knowledge_projections.get(source.source_id)
    if projection is None:
        # The hub preflight reports the full key mismatch before this helper is
        # reached.
        raise SiteExportError(
            f"Missing knowledge projection for hub source {source.source_id}."
        )
    bundle_id = projection.bundle.get("bundle_id")
    if not isinstance(bundle_id, str) or bundle_id == UNKNOWN_KNOWLEDGE_VALUE:
        raise SiteExportError(
            f"Missing governed bundle id for hub source {source.source_id}."
        )
    return bundle_id


def _preflight_hub_knowledge_projections(
    sources: list[HubWikiSource],
    *,
    knowledge_metadata: str | None,
    knowledge_projections: Mapping[str, KnowledgeProjection] | None,
) -> None:
    if knowledge_metadata is None:
        if knowledge_projections is not None:
            raise SiteExportError(
                "knowledge_projections requires knowledge_metadata='summary'."
            )
        return
    _validate_knowledge_metadata_mode(knowledge_metadata)
    if knowledge_projections is None:
        raise SiteExportError(
            "knowledge_metadata='summary' requires one validated projection "
            "per hub source."
        )
    expected = {source.source_id for source in sources}
    actual = set(knowledge_projections)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        details: list[str] = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if unexpected:
            details.append("unexpected=" + ",".join(unexpected))
        raise SiteExportError(
            "Hub knowledge projection source mismatch: " + "; ".join(details)
        )

    # Validate every child before the first output operation. This avoids a
    # partially enriched hub if a later source has stale or incomplete state.
    hub_uids: dict[str, str] = {}
    hub_bundles: dict[str, str] = {}
    for source in sources:
        projection = knowledge_projections[source.source_id]
        summaries = _preflight_knowledge_projection(
            wiki_surface.collect_wiki_pages(source.wiki_dir),
            knowledge_metadata=knowledge_metadata,
            knowledge_projection=projection,
        )
        if summaries is None:
            raise SiteExportError(
                f"Missing knowledge summaries for hub source {source.source_id}."
            )
        bundle_id = projection.bundle.get("bundle_id")
        if isinstance(bundle_id, str):
            prior_source = hub_bundles.get(bundle_id)
            if prior_source is not None:
                raise SiteExportError(
                    "Duplicate hub knowledge bundle id "
                    f"{bundle_id!r} in sources {prior_source!r} and "
                    f"{source.source_id!r}."
                )
            hub_bundles[bundle_id] = source.source_id
        for summary in summaries.values():
            uid = summary["knowledge_uid"]
            previous = hub_uids.get(uid)
            if previous is not None:
                raise SiteExportError(
                    "Duplicate hub knowledge uid "
                    f"{uid!r} in sources {previous!r} and "
                    f"{source.source_id!r}."
                )
            hub_uids[uid] = source.source_id


def _preflight_hub_root_output_collisions(
    sources: list[HubWikiSource],
    *,
    out: Path,
    format: str,
    file_friendly: bool,
) -> None:
    root_outputs = [_safe_join(out, "index.md")]
    if format == "mkdocs":
        root_outputs.append(_safe_join(out, "mkdocs.yml"))
        if file_friendly:
            root_outputs.append(
                _safe_join(out, MKDOCS_FILE_FRIENDLY_OVERRIDE_DIR)
            )
    elif format == "docusaurus":
        root_outputs.append(_safe_join(out, "sidebars.json"))

    for source in sources:
        child_output = _safe_join(out, source.source_id)
        for root_output in root_outputs:
            if _paths_overlap(child_output, root_output):
                raise SiteExportError(
                    "Hub source id "
                    f"{source.source_id!r} collides with reserved output "
                    f"{root_output.name!r}."
                )


def _expected_mirror_markdown_paths(
    pages: list[wiki_surface.WikiSurfacePage],
    *,
    profile: str,
) -> frozenset[str]:
    expected = {
        (
            GENERATED_REFERENCE_PATH
            if profile == "user" and page.relative_path == "index.md"
            else page.relative_path
        )
        for page in pages
    }
    if profile == "user":
        expected.add("index.md")
    return frozenset(expected)


def _expected_hub_markdown_paths(
    sources: list[HubWikiSource],
) -> frozenset[str]:
    expected = {"index.md"}
    for source in sources:
        source_paths = _expected_mirror_markdown_paths(
            wiki_surface.collect_wiki_pages(source.wiki_dir),
            profile="reference",
        )
        expected.update(
            posixpath.join(source.source_id, path)
            for path in source_paths
        )
    return frozenset(expected)


def _preflight_existing_unexpected_knowledge_pages(
    out: Path,
    *,
    expected_paths: frozenset[str],
) -> None:
    stale_pages = _find_unexpected_knowledge_pages(
        out,
        expected_paths=expected_paths,
    )
    if not stale_pages:
        return
    relative = ", ".join(
        path.relative_to(out).as_posix() for path in stale_pages
    )
    raise SiteExportError(
        "Existing output contains unexpected Markdown with projected "
        f"knowledge metadata: {relative}"
    )


def _check_existing_unexpected_knowledge_pages(
    out: Path,
    *,
    expected_paths: frozenset[str],
) -> list[dict[str, str]]:
    try:
        stale_pages = _find_unexpected_knowledge_pages(
            out,
            expected_paths=expected_paths,
        )
    except SiteExportError as exc:
        return [
            {
                "category": "unsafe_enriched_output_scan",
                "path": str(out),
                "message": str(exc),
            }
        ]
    return [
        {
            "category": "unexpected_knowledge_page",
            "path": str(path),
            "target": path.relative_to(out).as_posix(),
            "message": (
                "Unexpected Markdown page contains projected knowledge "
                "metadata and is not part of the current mirror."
            ),
        }
        for path in stale_pages
    ]


def _find_unexpected_knowledge_pages(
    out: Path,
    *,
    expected_paths: frozenset[str],
) -> list[Path]:
    if not out.exists():
        return []
    if out.is_symlink() or not out.is_dir():
        raise SiteExportError(
            "Cannot safely scan existing enriched output: "
            "output root must be a regular directory."
        )

    root_resolved = out.resolve(strict=True)
    for expected_path in expected_paths:
        _safe_join(out, expected_path)
    stack: list[tuple[Path, int]] = [(out, 0)]
    visited_entries = 0
    stale_pages: list[Path] = []
    while stack:
        directory, depth = stack.pop()
        try:
            resolved_directory = directory.resolve(strict=True)
        except OSError as exc:
            raise SiteExportError(
                "Cannot safely scan existing enriched output directory."
            ) from exc
        if (
            directory.is_symlink()
            or not _is_relative_to(resolved_directory, root_resolved)
        ):
            raise SiteExportError(
                "Cannot safely scan existing enriched output: "
                "directory path escapes through a symlink."
            )
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError as exc:
            raise SiteExportError(
                "Cannot safely scan existing enriched output directory."
            ) from exc
        for entry in entries:
            visited_entries += 1
            if visited_entries > MAX_ENRICHED_OUTPUT_SCAN_ENTRIES:
                raise SiteExportError(
                    "Cannot safely scan existing enriched output: "
                    "entry limit exceeded."
                )
            path = Path(entry.path)
            relative_path = path.relative_to(out).as_posix()
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise SiteExportError(
                    "Cannot safely inspect existing enriched output entry."
                ) from exc

            if stat.S_ISLNK(metadata.st_mode):
                raise SiteExportError(
                    "Cannot safely scan existing enriched output: "
                    f"symlink entry {relative_path!r}."
                )
            if (
                relative_path in expected_paths
                and not stat.S_ISREG(metadata.st_mode)
            ):
                raise SiteExportError(
                    "Cannot safely scan existing enriched output: "
                    f"expected page {relative_path!r} is not a regular file."
                )
            if stat.S_ISDIR(metadata.st_mode):
                if depth >= MAX_ENRICHED_OUTPUT_SCAN_DEPTH:
                    raise SiteExportError(
                        "Cannot safely scan existing enriched output: "
                        "directory depth limit exceeded."
                    )
                stack.append((path, depth + 1))
                continue
            if stat.S_ISREG(metadata.st_mode) and metadata.st_nlink != 1:
                raise SiteExportError(
                    "Cannot safely scan existing enriched output: "
                    f"hard-linked file {relative_path!r} is not isolated."
                )
            if path.suffix.casefold() != ".md":
                continue
            if relative_path in expected_paths:
                continue
            if not stat.S_ISREG(metadata.st_mode):
                raise SiteExportError(
                    "Cannot safely scan existing enriched output: "
                    f"Markdown candidate {relative_path!r} is not a regular file."
                )
            content = _read_bounded_enriched_markdown(
                path,
                root=root_resolved,
                expected_metadata=metadata,
            )
            if _contains_projected_knowledge_metadata(path, content):
                stale_pages.append(path)
    return stale_pages


def _read_bounded_enriched_markdown(
    path: Path,
    *,
    root: Path,
    expected_metadata: os.stat_result,
) -> str:
    if expected_metadata.st_size > MAX_ENRICHED_MARKDOWN_BYTES:
        raise SiteExportError(
            "Cannot safely scan existing enriched output: "
            "unexpected Markdown file exceeds the size limit."
        )
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise SiteExportError(
            "Cannot safely resolve existing enriched Markdown."
        ) from exc
    if not _is_relative_to(resolved, root):
        raise SiteExportError(
            "Cannot safely scan existing enriched output: "
            "Markdown path escapes the output directory."
        )

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
            or opened.st_dev != expected_metadata.st_dev
            or opened.st_ino != expected_metadata.st_ino
        ):
            raise SiteExportError(
                "Cannot safely scan existing enriched output: "
                "Markdown identity changed during inspection."
            )
        if opened.st_size > MAX_ENRICHED_MARKDOWN_BYTES:
            raise SiteExportError(
                "Cannot safely scan existing enriched output: "
                "unexpected Markdown file exceeds the size limit."
            )
        chunks: list[bytes] = []
        remaining = MAX_ENRICHED_MARKDOWN_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > MAX_ENRICHED_MARKDOWN_BYTES:
            raise SiteExportError(
                "Cannot safely scan existing enriched output: "
                "unexpected Markdown file exceeds the size limit."
            )
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SiteExportError(
                "Cannot safely scan existing enriched output: "
                "unexpected Markdown is not valid UTF-8."
            ) from exc
    except SiteExportError:
        raise
    except OSError as exc:
        raise SiteExportError(
            "Cannot safely read existing enriched Markdown."
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _contains_projected_knowledge_metadata(
    path: Path,
    content: str,
) -> bool:
    parsed = _parse_front_matter(path, content)
    if parsed.issue is not None:
        front_matter = content.split("---", 2)[1] if content.startswith("---") else ""
        return re.search(
            r"(?m)^\s*(?:llm_wiki|knowledge_[A-Za-z0-9_-]*|"
            r"source_knowledge_[A-Za-z0-9_-]*|source_path)\s*:",
            front_matter,
        ) is not None
    if not parsed.exists:
        return False
    for key in parsed.metadata:
        if (
            key == "source_path"
            or key.startswith("knowledge_")
            or key.startswith("source_knowledge_")
        ):
            return True
    llm_wiki = parsed.metadata.get("llm_wiki")
    if not isinstance(llm_wiki, Mapping):
        return False
    return any(
        key == "source_path"
        or key.startswith("knowledge_")
        or key.startswith("source_knowledge_")
        for key in llm_wiki
    )


def _preflight_knowledge_projection(
    pages: list[wiki_surface.WikiSurfacePage],
    *,
    knowledge_metadata: str | None,
    knowledge_projection: KnowledgeProjection | None,
) -> dict[str, dict[str, str]] | None:
    if knowledge_metadata is None:
        if knowledge_projection is not None:
            raise SiteExportError(
                "knowledge_projection requires knowledge_metadata='summary'."
            )
        return None
    _validate_knowledge_metadata_mode(knowledge_metadata)
    if not isinstance(knowledge_projection, KnowledgeProjection):
        raise SiteExportError(
            "knowledge_metadata='summary' requires a validated "
            "KnowledgeProjection."
        )
    try:
        return validate_projection_summaries(
            knowledge_projection,
            [page.relative_path for page in pages],
        )
    except KnowledgeProjectionError as exc:
        raise SiteExportError(f"Knowledge projection {exc}") from exc


def _validate_knowledge_metadata_mode(value: str) -> None:
    if value not in SUPPORTED_KNOWLEDGE_METADATA:
        supported = ", ".join(sorted(SUPPORTED_KNOWLEDGE_METADATA))
        raise SiteExportError(
            f"Unsupported knowledge metadata mode: {value}. "
            f"Supported modes: {supported}"
        )


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
            if key in metadata:
                return FrontMatterParseResult(
                    exists=True,
                    issue=_malformed_front_matter_issue(
                        page_path,
                        f"Duplicate front matter key: {key}",
                    ),
                )
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
            if key in section:
                return FrontMatterParseResult(
                    exists=True,
                    issue=_malformed_front_matter_issue(
                        page_path,
                        "Duplicate front matter key: "
                        f"{current_section}.{key}",
                    ),
                )
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
    docusaurus_id_override: str | None = None,
    knowledge_summary: Mapping[str, str] | None = None,
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

    if knowledge_summary is not None:
        for key in sorted(metadata):
            if (
                key == "source_path"
                or key.startswith("knowledge_")
                or key.startswith("source_knowledge_")
            ):
                issues.append(
                    {
                        "category": "unexpected_knowledge_metadata",
                        "path": str(page_path),
                        "target": key,
                        "message": (
                            "Unexpected top-level field in projected "
                            f"knowledge front matter: {key}"
                        ),
                    }
                )
        for key, expected in knowledge_summary.items():
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
        allowed = set(expected_llm_wiki) | set(knowledge_summary)
        for key in sorted(llm_wiki):
            if key in allowed:
                continue
            issues.append(
                {
                    "category": "unexpected_knowledge_metadata",
                    "path": str(page_path),
                    "target": f"llm_wiki.{key}",
                    "message": (
                        "Unexpected field in projected knowledge "
                        f"front matter: llm_wiki.{key}"
                    ),
                }
            )

    doc_id = metadata.get("id")
    expected_doc_id = (
        docusaurus_id_override
        or _docusaurus_doc_id(page, prefix=docusaurus_id_prefix)
    )
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


def _check_projection_free_user_landing(out: Path) -> list[dict[str, str]]:
    try:
        page_path = _safe_join(out, "index.md")
    except SiteExportError as exc:
        return [
            {
                "category": "unsafe_output_path",
                "path": str(out),
                "target": "index.md",
                "message": str(exc),
            }
        ]
    if not page_path.is_file():
        return []

    parsed = _parse_front_matter(page_path, read_md(page_path))
    if parsed.issue is not None:
        return [parsed.issue]
    if not parsed.exists:
        return [
            {
                "category": "missing_front_matter",
                "path": str(page_path),
                "message": (
                    "Knowledge-enriched user landing page requires "
                    "projection-free front matter."
                ),
            }
        ]

    issues: list[dict[str, str]] = []
    for key in sorted(parsed.metadata):
        if (
            key == "llm_wiki"
            or key == "source_path"
            or key.startswith("knowledge_")
            or key.startswith("source_knowledge_")
        ):
            issues.append(
                {
                    "category": "unexpected_knowledge_metadata",
                    "path": str(page_path),
                    "target": key,
                    "message": (
                        "The user landing page must remain projection-free; "
                        f"unexpected front matter field: {key}"
                    ),
                }
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


def _check_knowledge_metadata_references(
    pages: list[wiki_surface.WikiSurfacePage],
    out: Path,
    *,
    profile: str,
    expected_summaries: Mapping[str, Mapping[str, str]],
) -> list[dict[str, str]]:
    seen_uids: dict[str, Path] = {}
    successor_sources: dict[str, list[Path]] = {}
    expected_successor_counts: dict[str, int] = {}
    for summary in expected_summaries.values():
        expected = summary.get("knowledge_successor_uid")
        if isinstance(expected, str) and expected != UNKNOWN_KNOWLEDGE_VALUE:
            expected_successor_counts[expected] = (
                expected_successor_counts.get(expected, 0) + 1
            )
    issues: list[dict[str, str]] = []
    for page in pages:
        relative_path = (
            GENERATED_REFERENCE_PATH
            if profile == "user" and page.relative_path == "index.md"
            else page.relative_path
        )
        path = out / relative_path
        if not path.is_file():
            continue
        parsed = _parse_front_matter(path, read_md(path))
        if not parsed.exists or parsed.issue is not None:
            continue
        llm_wiki = parsed.metadata.get("llm_wiki")
        if not isinstance(llm_wiki, dict):
            continue
        uid = llm_wiki.get("knowledge_uid")
        if isinstance(uid, str) and uid != UNKNOWN_KNOWLEDGE_VALUE:
            previous = seen_uids.get(uid)
            if previous is not None:
                issues.append(
                    {
                        "category": "duplicate_knowledge_uid",
                        "path": str(path),
                        "target": str(previous),
                        "message": f"Duplicate knowledge uid: {uid}",
                    }
                )
            else:
                seen_uids[uid] = path
        successor = llm_wiki.get("knowledge_successor_uid")
        if not isinstance(successor, str) or successor == UNKNOWN_KNOWLEDGE_VALUE:
            continue
        if successor == uid:
            issues.append(
                {
                    "category": "self_referential_knowledge_successor",
                    "path": str(path),
                    "target": successor,
                    "message": f"Knowledge successor references itself: {successor}",
                }
            )
        paths = successor_sources.setdefault(successor, [])
        expected_count = expected_successor_counts.get(successor, 0)
        if len(paths) >= max(1, expected_count):
            issues.append(
                {
                    "category": "duplicate_knowledge_successor_uid",
                    "path": str(path),
                    "target": str(paths[0]) if paths else successor,
                    "message": (
                        "Unexpected duplicate knowledge successor uid: "
                        f"{successor}"
                    ),
                }
            )
        paths.append(path)

    for successor, paths in sorted(
        successor_sources.items(), key=lambda item: item[0]
    ):
        if successor not in seen_uids:
            issues.append(
                {
                    "category": "missing_knowledge_successor",
                    "path": str(paths[0]),
                    "target": successor,
                    "message": (
                        "Knowledge successor uid is absent from this mirror: "
                        f"{successor}"
                    ),
                }
            )
    return issues


def _check_hub_knowledge_uid_collisions(
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
            parsed = _parse_front_matter(path, read_md(path))
            llm_wiki = (
                parsed.metadata.get("llm_wiki")
                if parsed.exists and parsed.issue is None
                else None
            )
            uid = (
                llm_wiki.get("knowledge_uid")
                if isinstance(llm_wiki, dict)
                else None
            )
            if not isinstance(uid, str) or uid == UNKNOWN_KNOWLEDGE_VALUE:
                continue
            previous = seen.get(uid)
            if previous is not None:
                issues.append(
                    {
                        "category": "duplicate_hub_knowledge_uid",
                        "path": str(path),
                        "target": str(previous),
                        "message": f"Duplicate hub knowledge uid: {uid}",
                    }
                )
            else:
                seen[uid] = path
    return issues


def _check_user_profile_quality(
    out: Path,
    *,
    site_name: Optional[str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not site_name or not site_name.strip() or site_name.strip() == "LLM Wiki":
        issues.append(
            {
                "category": "default_user_site_name",
                "path": str(out / "index.md"),
                "message": "--profile user requires a non-default --site-name.",
            }
        )

    index_path = out / "index.md"
    if not index_path.is_file():
        issues.append(
            {
                "category": "missing_user_index",
                "path": str(index_path),
                "message": "User profile root index.md is missing.",
            }
        )
    else:
        index_content = read_md(index_path)
        if len(index_content.splitlines()) > 250:
            issues.append(
                {
                    "category": "human_index_too_long",
                    "path": str(index_path),
                    "message": "User profile root index.md exceeds 250 lines.",
                }
            )
        if len(_iter_markdown_link_targets(index_content)) > 80:
            issues.append(
                {
                    "category": "human_index_too_many_links",
                    "path": str(index_path),
                    "message": "User profile root index.md has more than 80 links.",
                }
            )

    guide_paths = (
        sorted((out / "guides").glob("*.md")) if (out / "guides").is_dir() else []
    )
    if not guide_paths:
        issues.append(
            {
                "category": "missing_user_guides",
                "path": str(out / "guides"),
                "message": "User profile requires at least one guides/*.md page.",
            }
        )
    elif not _primary_user_docs_have_media(index_path, guide_paths):
        warnings.append(
            {
                "category": "user_docs_missing_examples",
                "path": str(out / "guides"),
                "message": (
                    "User-profile primary docs contain no usage-example media."
                ),
            }
        )

    for path in [index_path] + guide_paths:
        if path.is_file():
            issues.extend(_placeholder_findings(path, category="published_placeholder"))

    generated_paths = _generated_reference_paths(out)
    for path in generated_paths:
        warnings.extend(
            _placeholder_findings(path, category="generated_reference_placeholder")
        )
    return issues, warnings


def _primary_user_docs_have_media(index_path: Path, guide_paths: list[Path]) -> bool:
    for path in [index_path] + guide_paths:
        if not path.is_file():
            continue
        content = read_md(path)
        rel = (
            path.name
            if path == index_path
            else path.relative_to(path.parents[1]).as_posix()
        )
        if collect_media_references(path, rel, content):
            return True
    return False


def _generated_reference_paths(out: Path) -> list[Path]:
    paths = []
    generated_reference = out / GENERATED_REFERENCE_PATH
    if generated_reference.is_file():
        paths.append(generated_reference)
    for directory in ("entities", "modules", "flows"):
        root = out / directory
        if root.is_dir():
            paths.extend(sorted(root.glob("*.md")))
    return paths


def _placeholder_findings(path: Path, *, category: str) -> list[dict[str, str]]:
    try:
        content = read_md(path)
    except OSError:
        return []
    findings = []
    for phrase in _PLACEHOLDER_PHRASES:
        if phrase in content:
            findings.append(
                {
                    "category": category,
                    "path": str(path),
                    "target": phrase,
                    "message": f"Published documentation contains placeholder text: {phrase}",
                }
            )
    return findings


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
    return [
        link.raw_target
        for link in iter_wiki_markdown_link_targets(strip_fenced_code_blocks(content))
        if not link.is_image
    ]


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
    if _is_allowed_raw_media_html(line):
        return line
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


def _is_allowed_raw_media_html(line: str) -> bool:
    return _RAW_MEDIA_HTML_RE.match(line) is not None


def _yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _validate_format(format: str) -> None:
    if format not in SUPPORTED_SITE_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_SITE_FORMATS))
        raise SiteExportError(
            f"Unsupported site export format: {format}. Supported formats: {supported}"
        )


def _validate_profile(profile: str) -> None:
    if profile not in SUPPORTED_SITE_PROFILES:
        supported = ", ".join(sorted(SUPPORTED_SITE_PROFILES))
        raise SiteExportError(
            f"Unsupported site profile: {profile}. Supported profiles: {supported}"
        )


def _validate_export_site_name(profile: str, site_name: Optional[str]) -> None:
    if profile != "user":
        return
    if not site_name or not site_name.strip():
        raise SiteExportError("--profile user requires --site-name.")
    if site_name.strip() == "LLM Wiki":
        raise SiteExportError(
            "--profile user requires --site-name different from 'LLM Wiki'."
        )


def _validate_file_friendly(format: str, *, file_friendly: bool) -> None:
    if file_friendly and format != "mkdocs":
        raise SiteExportError("--file-friendly requires --format mkdocs.")


def _validate_link_mode(link_mode: str) -> None:
    if link_mode not in SUPPORTED_LINK_MODES:
        supported = ", ".join(sorted(SUPPORTED_LINK_MODES))
        raise SiteExportError(
            f"Unsupported built-site link mode: {link_mode}. Supported modes: {supported}"
        )


def _distribution_mode(file_friendly: bool) -> str:
    return "file" if file_friendly else "http"


def _distribution_mode_label(mode: str) -> str:
    if mode == "file":
        return "direct-file browsing"
    return "HTTP serving"


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
        raise SiteExportError("Output directory overlaps the source wiki.")


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
