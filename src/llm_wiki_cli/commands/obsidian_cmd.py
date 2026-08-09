"""Commands for exporting LLM Wiki into an Obsidian-friendly mirror."""

from __future__ import annotations

import sys

from ..config import DEFAULT_WIKI_DIR, validate_path, validate_source_root
from ..services.knowledge_consumption import load_knowledge_read_view
from ..services.knowledge_projection import (
    KnowledgeProjection,
    KnowledgeProjectionError,
    project_knowledge,
)
from ..services.obsidian import (
    DEFAULT_NOTES_DIR,
    DEFAULT_PLUGIN_SOURCE,
    ObsidianError,
    check_obsidian_vault,
    export_obsidian_vault,
    install_obsidian_plugin,
    render_report_json,
    render_report_text,
    validate_obsidian_export_source_selection,
)


def _knowledge_projection(args, wiki_dir: str) -> KnowledgeProjection | None:
    knowledge_metadata = getattr(args, "knowledge_metadata", None)
    if knowledge_metadata is None:
        profile = getattr(args, "knowledge_profile", "public-portable")
        public_identity = getattr(
            args,
            "knowledge_public_repository_identity",
            None,
        )
        if profile != "public-portable" or public_identity is not None:
            raise ObsidianError(
                "--knowledge-profile internal and "
                "--knowledge-public-repository-identity require "
                "--knowledge-metadata summary"
            )
        return None
    if knowledge_metadata != "summary":
        raise ObsidianError("knowledge metadata mode must be 'summary'")
    try:
        view = load_knowledge_read_view(
            wiki_dir,
            snapshot_only=True,
            include_machine_verification=True,
        )
        return project_knowledge(
            view,
            profile=getattr(args, "knowledge_profile", "public-portable"),
            public_repository_identity=getattr(
                args,
                "knowledge_public_repository_identity",
                None,
            ),
        )
    except (KnowledgeProjectionError, TypeError, ValueError) as exc:
        raise ObsidianError(
            f"knowledge metadata projection failed: {exc}"
        ) from exc


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
            allow_external = bool(getattr(args, "allow_external_src", False))
            source_root = validate_source_root(
                src_dir,
                "--src-dir",
                allow_external=allow_external,
            )
            if allow_external:
                src_dir = str(source_root)
            source_snapshot = validate_obsidian_export_source_selection(
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                source_selection=getattr(args, "source_selection", None),
            )
            knowledge_projection = _knowledge_projection(args, wiki_dir)
            report = export_obsidian_vault(
                src_dir=src_dir,
                wiki_dir=wiki_dir,
                vault_dir=getattr(args, "vault_dir"),
                notes_dir=getattr(args, "notes_dir", DEFAULT_NOTES_DIR),
                dry_run=bool(getattr(args, "dry_run", False)),
                source_selection=source_snapshot.source_selection_path,
                knowledge_metadata=getattr(args, "knowledge_metadata", None),
                knowledge_projection=knowledge_projection,
            )
            _print_report(report, output_format, action="export")
            return

        if action == "check":
            wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
            validate_path(wiki_dir, "--wiki-dir")
            knowledge_projection = _knowledge_projection(args, wiki_dir)
            report = check_obsidian_vault(
                wiki_dir=wiki_dir,
                vault_dir=getattr(args, "vault_dir"),
                knowledge_metadata=getattr(args, "knowledge_metadata", None),
                knowledge_projection=knowledge_projection,
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
