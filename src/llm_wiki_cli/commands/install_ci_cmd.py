"""CLI adapter for installing portable LLM Wiki workflows."""

from __future__ import annotations

import sys

from ..config import DEFAULT_WIKI_DIR
from ..services.ci_installer import (
    InstallCiError,
    install_ci_workflow,
    install_documentation_ci_workflow,
)
from ..services.publication_config import PUBLICATION_CONFIG_PATH


def run(args) -> None:
    profile = getattr(args, "profile", "integrity")
    src_dir = getattr(args, "src_dir", None)
    dry_run = getattr(args, "dry_run", False)
    force = getattr(args, "force", False)
    require_ready = getattr(args, "require_ready", False)
    try:
        if profile == "documentation":
            if getattr(args, "wiki_dir", DEFAULT_WIKI_DIR) != DEFAULT_WIKI_DIR:
                raise InstallCiError(
                    "--wiki-dir applies to the integrity profile; set architecture.root in --config"
                )
            result = install_documentation_ci_workflow(
                action_ref=args.action_ref,
                src_dir=src_dir,
                dry_run=dry_run,
                force=force,
                config=PUBLICATION_CONFIG_PATH if args.config is None else args.config,
                working_directory="."
                if args.working_directory is None
                else args.working_directory,
                target_dir=args.target_dir,
                baseline=args.baseline,
                reviews=args.reviews,
                previous_receipt=args.previous_receipt,
                candidate_review=args.candidate_review,
                require_ready=require_ready,
            )
        else:
            publication_options = (
                "config",
                "working_directory",
                "target_dir",
                "baseline",
                "reviews",
                "previous_receipt",
                "candidate_review",
            )
            if require_ready or any(
                getattr(args, name, None) is not None for name in publication_options
            ):
                raise InstallCiError(
                    "Publication options require --profile documentation"
                )
            result = install_ci_workflow(
                action_ref=args.action_ref,
                src_dir="." if src_dir is None else src_dir,
                dry_run=dry_run,
                force=force,
                wiki_dir=getattr(args, "wiki_dir", DEFAULT_WIKI_DIR),
            )
    except InstallCiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if result.operation == "unchanged":
        print(f"CI workflow is already current: {result.path}")
        return

    verb = "create" if result.operation == "create" else "update"
    if result.dry_run:
        print(f"Would {verb} LLM Wiki {profile} workflow: {result.path}")
        print("Dry run: no files were changed.")
        return

    completed = "Created" if result.operation == "create" else "Updated"
    print(f"{completed} LLM Wiki {profile} workflow: {result.path}")
    print(f"Pinned reusable action commit: {result.action_ref}")


__all__ = ["run"]
