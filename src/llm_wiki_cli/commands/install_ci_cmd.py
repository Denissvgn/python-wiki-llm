"""CLI adapter for installing the portable LLM Wiki integrity workflow."""

from __future__ import annotations

import sys

from ..config import DEFAULT_WIKI_DIR
from ..services.ci_installer import InstallCiError, install_ci_workflow


def run(args) -> None:
    try:
        result = install_ci_workflow(
            action_ref=getattr(args, "action_ref"),
            src_dir=getattr(args, "src_dir", "."),
            wiki_dir=getattr(args, "wiki_dir", DEFAULT_WIKI_DIR),
            dry_run=bool(getattr(args, "dry_run", False)),
            force=bool(getattr(args, "force", False)),
        )
    except InstallCiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if result.operation == "unchanged":
        print(f"CI workflow is already current: {result.path}")
        return

    verb = "create" if result.operation == "create" else "update"
    if result.dry_run:
        print(f"Would {verb} LLM Wiki integrity workflow: {result.path}")
        print("Dry run: no files were changed.")
        return

    completed = "Created" if result.operation == "create" else "Updated"
    print(f"{completed} LLM Wiki integrity workflow: {result.path}")
    print(f"Pinned reusable action commit: {result.action_ref}")


__all__ = ["run"]
