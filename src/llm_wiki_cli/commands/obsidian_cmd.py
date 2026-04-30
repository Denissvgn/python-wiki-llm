"""Commands for exporting LLM Wiki into an Obsidian-friendly mirror."""

from __future__ import annotations

import sys

from ..config import DEFAULT_WIKI_DIR, validate_path
from ..services.obsidian import (
    DEFAULT_NOTES_DIR,
    DEFAULT_PLUGIN_SOURCE,
    ObsidianError,
    check_obsidian_vault,
    export_obsidian_vault,
    install_obsidian_plugin,
    render_report_json,
    render_report_text,
)


def _print_report(report, output_format: str, *, action: str) -> None:
    if output_format == "json":
        print(render_report_json(report), end="")
    else:
        print(render_report_text(report, action=action), end="")


def run(args) -> None:
    action = getattr(args, "obsidian_action", None)
    output_format = getattr(args, "format", "text")

    try:
        if action == "export":
            wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
            src_dir = getattr(args, "src_dir", ".")
            validate_path(wiki_dir, "--wiki-dir")
            validate_path(src_dir, "--src-dir")
            report = export_obsidian_vault(
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                vault_dir=getattr(args, "vault_dir"),
                notes_dir=getattr(args, "notes_dir", DEFAULT_NOTES_DIR),
                dry_run=bool(getattr(args, "dry_run", False)),
            )
            _print_report(report, output_format, action="export")
            return

        if action == "check":
            wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
            validate_path(wiki_dir, "--wiki-dir")
            report = check_obsidian_vault(
                wiki_dir=wiki_dir,
                vault_dir=getattr(args, "vault_dir"),
            )
            _print_report(report, output_format, action="check")
            if not report.ok:
                raise SystemExit(1)
            return

        if action == "install-plugin":
            report = install_obsidian_plugin(
                vault_dir=getattr(args, "vault_dir"),
                plugin_dir=getattr(args, "plugin_dir", DEFAULT_PLUGIN_SOURCE),
            )
            _print_report(report, "text", action="install-plugin")
            return
    except ObsidianError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print("Error: missing obsidian action.", file=sys.stderr)
    raise SystemExit(1)
