"""Commands for exporting LLM Wiki into a static-site-friendly mirror."""

from __future__ import annotations

import sys

from ..config import DEFAULT_WIKI_DIR, validate_path
from ..services.knowledge_consumption import load_knowledge_read_view
from ..services.knowledge_model import KnowledgeProjectionProfile
from ..services.knowledge_projection import (
    KnowledgeProjection,
    project_knowledge,
)
from ..services.site_export import (
    SUPPORTED_KNOWLEDGE_METADATA,
    SUPPORTED_SITE_PROFILES,
    SUPPORTED_SITE_FORMATS,
    SiteExportError,
    check_site_hub,
    check_site_mirror,
    export_site_hub,
    export_site_mirror,
    render_report_json,
    render_report_text,
    resolve_site_hub_sources,
)
from ..services.site_html_check import SUPPORTED_LINK_MODES


SITE_FORMAT_CHOICES = sorted(SUPPORTED_SITE_FORMATS)
SITE_PROFILE_CHOICES = sorted(SUPPORTED_SITE_PROFILES)
LINK_MODE_CHOICES = sorted(SUPPORTED_LINK_MODES)
KNOWLEDGE_METADATA_CHOICES = sorted(SUPPORTED_KNOWLEDGE_METADATA)
KNOWLEDGE_PROFILE_CHOICES = sorted(
    profile.value for profile in KnowledgeProjectionProfile
)


def _print_report(report, output_format: str, *, action: str) -> None:
    if output_format == "json":
        print(render_report_json(report), end="")
    else:
        print(render_report_text(report, action=action), end="")


def _hub_requested(args) -> bool:
    return bool(getattr(args, "wiki_root", None) or getattr(args, "wiki", None))


def _validate_hub_args(args) -> tuple[str | None, list[str]]:
    wiki_root = getattr(args, "wiki_root", None)
    wikis = list(getattr(args, "wiki", None) or [])
    if wiki_root:
        validate_path(wiki_root, "--wiki-root")
    for wiki in wikis:
        validate_path(wiki, "--wiki")
    return wiki_root, wikis


def _knowledge_metadata(args) -> str | None:
    value = getattr(args, "knowledge_metadata", None)
    if not value:
        profile = getattr(
            args,
            "knowledge_profile",
            KnowledgeProjectionProfile.PUBLIC_PORTABLE.value,
        )
        public_identity = getattr(args, "public_repository_identity", None)
        if (
            profile != KnowledgeProjectionProfile.PUBLIC_PORTABLE.value
            or public_identity is not None
        ):
            raise SiteExportError(
                "--knowledge-profile internal and "
                "--knowledge-public-repository-identity require "
                "--knowledge-metadata summary"
            )
        return None
    if value not in SUPPORTED_KNOWLEDGE_METADATA:
        supported = ", ".join(KNOWLEDGE_METADATA_CHOICES)
        raise SiteExportError(
            f"Unsupported knowledge metadata mode: {value}. "
            f"Supported modes: {supported}"
        )
    return value


def _load_knowledge_projection(
    wiki_dir: str,
    args,
) -> KnowledgeProjection | None:
    if _knowledge_metadata(args) is None:
        return None
    try:
        view = load_knowledge_read_view(
            wiki_dir,
            snapshot_only=True,
            include_machine_verification=True,
        )
        return project_knowledge(
            view,
            profile=getattr(
                args,
                "knowledge_profile",
                KnowledgeProjectionProfile.PUBLIC_PORTABLE.value,
            ),
            public_repository_identity=getattr(
                args,
                "public_repository_identity",
                None,
            ),
        )
    except ValueError as exc:
        raise SiteExportError(f"Cannot project knowledge metadata: {exc}") from exc


def _load_hub_knowledge_projections(
    *,
    wiki_root: str | None,
    wikis: list[str],
    args,
) -> dict[str, KnowledgeProjection] | None:
    if _knowledge_metadata(args) is None:
        return None
    sources = resolve_site_hub_sources(wiki_root=wiki_root, wikis=wikis)
    projections: dict[str, KnowledgeProjection] = {}
    for source in sources:
        projection = _load_knowledge_projection(str(source.wiki_dir), args)
        if projection is None:  # Defensive; metadata mode was checked above.
            raise SiteExportError(
                f"Missing knowledge projection for hub source {source.source_id}."
            )
        projections[source.source_id] = projection
    return projections


def run(args) -> None:
    action = getattr(args, "site_action", None)
    output_format = getattr(args, "output_format", "text")

    try:
        if action == "export":
            wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
            out_dir = getattr(args, "out_dir")
            validate_path(out_dir, "--out-dir")
            if _hub_requested(args):
                wiki_root, wikis = _validate_hub_args(args)
                knowledge_projections = _load_hub_knowledge_projections(
                    wiki_root=wiki_root,
                    wikis=wikis,
                    args=args,
                )
                report = export_site_hub(
                    wiki_root=wiki_root,
                    wikis=wikis,
                    out_dir=out_dir,
                    format=getattr(args, "format", "plain"),
                    file_friendly=bool(getattr(args, "file_friendly", False)),
                    profile=getattr(args, "profile", "reference"),
                    site_name=getattr(args, "site_name", None),
                    front_matter=bool(getattr(args, "front_matter", False)),
                    dry_run=bool(getattr(args, "dry_run", False)),
                    knowledge_metadata=_knowledge_metadata(args),
                    knowledge_projections=knowledge_projections,
                )
            else:
                validate_path(wiki_dir, "--wiki-dir")
                knowledge_projection = _load_knowledge_projection(wiki_dir, args)
                report = export_site_mirror(
                    wiki_dir=wiki_dir,
                    out_dir=out_dir,
                    format=getattr(args, "format", "plain"),
                    file_friendly=bool(getattr(args, "file_friendly", False)),
                    profile=getattr(args, "profile", "reference"),
                    site_name=getattr(args, "site_name", None),
                    front_matter=bool(getattr(args, "front_matter", False)),
                    dry_run=bool(getattr(args, "dry_run", False)),
                    knowledge_metadata=_knowledge_metadata(args),
                    knowledge_projection=knowledge_projection,
                )
            _print_report(report, output_format, action="export")
            return

        if action == "check":
            wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
            out_dir = getattr(args, "out_dir")
            validate_path(out_dir, "--out-dir")
            built_site_dir = getattr(args, "built_site_dir", None)
            if built_site_dir:
                validate_path(built_site_dir, "--built-site-dir")
            if _hub_requested(args):
                wiki_root, wikis = _validate_hub_args(args)
                knowledge_projections = _load_hub_knowledge_projections(
                    wiki_root=wiki_root,
                    wikis=wikis,
                    args=args,
                )
                report = check_site_hub(
                    wiki_root=wiki_root,
                    wikis=wikis,
                    out_dir=out_dir,
                    built_site_dir=built_site_dir,
                    link_mode=getattr(args, "link_mode", "http"),
                    format=getattr(args, "format", None),
                    profile=getattr(args, "profile", "reference"),
                    site_name=getattr(args, "site_name", None),
                    knowledge_metadata=_knowledge_metadata(args),
                    knowledge_projections=knowledge_projections,
                )
            else:
                validate_path(wiki_dir, "--wiki-dir")
                knowledge_projection = _load_knowledge_projection(wiki_dir, args)
                report = check_site_mirror(
                    wiki_dir=wiki_dir,
                    out_dir=out_dir,
                    built_site_dir=built_site_dir,
                    link_mode=getattr(args, "link_mode", "http"),
                    format=getattr(args, "format", None),
                    profile=getattr(args, "profile", "reference"),
                    site_name=getattr(args, "site_name", None),
                    knowledge_metadata=_knowledge_metadata(args),
                    knowledge_projection=knowledge_projection,
                )
            _print_report(report, output_format, action="check")
            if not report.ok:
                raise SystemExit(1)
            return
    except SiteExportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print("Error: missing site action.", file=sys.stderr)
    raise SystemExit(1)
