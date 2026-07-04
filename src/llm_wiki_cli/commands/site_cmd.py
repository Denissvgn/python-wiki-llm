"""Commands for exporting LLM Wiki into a static-site-friendly mirror."""

from __future__ import annotations

import sys

from ..config import DEFAULT_WIKI_DIR, validate_path
from ..services.site_export import (
    SUPPORTED_SITE_FORMATS,
    SiteExportError,
    check_site_hub,
    check_site_mirror,
    export_site_hub,
    export_site_mirror,
    render_report_json,
    render_report_text,
)


SITE_FORMAT_CHOICES = sorted(SUPPORTED_SITE_FORMATS)


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
                report = export_site_hub(
                    wiki_root=wiki_root,
                    wikis=wikis,
                    out_dir=out_dir,
                    format=getattr(args, "format", "plain"),
                    front_matter=bool(getattr(args, "front_matter", False)),
                    dry_run=bool(getattr(args, "dry_run", False)),
                )
            else:
                validate_path(wiki_dir, "--wiki-dir")
                report = export_site_mirror(
                    wiki_dir=wiki_dir,
                    out_dir=out_dir,
                    format=getattr(args, "format", "plain"),
                    front_matter=bool(getattr(args, "front_matter", False)),
                    dry_run=bool(getattr(args, "dry_run", False)),
                )
            _print_report(report, output_format, action="export")
            return

        if action == "check":
            wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
            out_dir = getattr(args, "out_dir")
            validate_path(out_dir, "--out-dir")
            if _hub_requested(args):
                wiki_root, wikis = _validate_hub_args(args)
                report = check_site_hub(
                    wiki_root=wiki_root,
                    wikis=wikis,
                    out_dir=out_dir,
                )
            else:
                validate_path(wiki_dir, "--wiki-dir")
                report = check_site_mirror(wiki_dir=wiki_dir, out_dir=out_dir)
            _print_report(report, output_format, action="check")
            if not report.ok:
                raise SystemExit(1)
            return
    except SiteExportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print("Error: missing site action.", file=sys.stderr)
    raise SystemExit(1)
