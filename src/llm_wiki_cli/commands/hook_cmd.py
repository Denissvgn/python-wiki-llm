"""Compatibility imports for legacy hook recognition; installation is retired."""

from __future__ import annotations

import sys

from ..services.legacy_hooks import (
    HOOK_SIGNATURE as HOOK_SIGNATURE,
    _build_ide_post_commit as _build_ide_post_commit,
    _build_post_commit as _build_post_commit,
    _build_validation_pre_commit as _build_validation_pre_commit,
    _legacy_auto_sync_post_commit as _legacy_auto_sync_post_commit,
    _legacy_ide_post_commit as _legacy_ide_post_commit,
    is_managed_hook_content as is_managed_hook_content,
)


def run(args) -> None:
    """Reject calls from integrations that still import the old command module."""
    print(
        "Git hook installation has been removed. Run `llm-wiki upgrade` to remove "
        "unmodified legacy LLM Wiki hooks. Use `llm-wiki sync --jobs 1` and "
        "`llm-wiki lint --strict --jobs 1` explicitly.",
        file=sys.stderr,
    )
    raise SystemExit(2)
