from __future__ import annotations

import json

import pytest

from llm_wiki_cli.config import AGENT_CHOICES
from llm_wiki_cli.commands import lint_cmd
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from llm_wiki_cli.services.wiki_lifecycle import (
    WikiLifecycleState,
    classify_wiki_lifecycle,
)
from llm_wiki_cli.services.wiki_scaffold import (
    INITIAL_WIKI_INDEX_MARKDOWN,
    INITIAL_WIKI_LOG_MARKDOWN,
)
from llm_wiki_cli.services.wiki_surface import iter_page_kinds


def _write_init_scaffold(root, *, agent: bool = False):
    root.mkdir(parents=True)
    for entry in iter_page_kinds():
        if entry.directory is None:
            continue
        directory = root / entry.directory
        directory.mkdir()
        (directory / ".gitkeep").write_bytes(b"")
    (root / ".gitkeep").write_bytes(b"")
    (root / "index.md").write_text(INITIAL_WIKI_INDEX_MARKDOWN, encoding="utf-8")
    (root / "log.md").write_text(INITIAL_WIKI_LOG_MARKDOWN, encoding="utf-8")
    if agent:
        (root / ".llm-wiki-agent").write_text(
            json.dumps(
                {
                    "agent": AGENT_CHOICES[0],
                    "quality_hints": True,
                    "reference_skill": True,
                    "issue_reporting": False,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def test_wiki_lifecycle_classifies_first_use_targets(tmp_path):
    missing = tmp_path / "missing"
    empty = tmp_path / "empty"
    empty.mkdir()
    scaffold = tmp_path / "scaffold"
    _write_init_scaffold(scaffold, agent=True)

    assert classify_wiki_lifecycle(missing) is WikiLifecycleState.FIRST_USE
    assert classify_wiki_lifecycle(empty) is WikiLifecycleState.FIRST_USE
    assert classify_wiki_lifecycle(scaffold) is WikiLifecycleState.FIRST_USE


def test_wiki_lifecycle_classifies_seedable_partial_and_managed(tmp_path):
    seedable = tmp_path / "seedable"
    seedable.mkdir()
    (seedable / "index.md").write_text("# Existing wiki\n", encoding="utf-8")
    (seedable / "modules").mkdir()
    (seedable / "modules" / "module.md").write_text("# Module\n", encoding="utf-8")

    partial = tmp_path / "partial"
    (partial / "modules").mkdir(parents=True)
    (partial / "modules" / "module.md").write_text("# Module\n", encoding="utf-8")

    managed = tmp_path / "managed"
    managed.mkdir()
    (managed / MANIFEST_FILENAME).write_text("{}", encoding="utf-8")

    assert (
        classify_wiki_lifecycle(seedable) is WikiLifecycleState.SYNC_SEEDABLE
    )
    assert (
        classify_wiki_lifecycle(partial) is WikiLifecycleState.MIGRATION_REQUIRED
    )
    assert classify_wiki_lifecycle(managed) is WikiLifecycleState.MANAGED


def test_noncanonical_scaffold_requires_migration(tmp_path):
    scaffold = tmp_path / "scaffold"
    _write_init_scaffold(scaffold)
    (scaffold / "log.md").write_text("# Modified\n", encoding="utf-8")

    assert (
        classify_wiki_lifecycle(scaffold)
        is WikiLifecycleState.SYNC_SEEDABLE
    )

    (scaffold / "index.md").unlink()
    assert (
        classify_wiki_lifecycle(scaffold)
        is WikiLifecycleState.MIGRATION_REQUIRED
    )


def test_lint_manifest_guidance_matches_partial_and_seedable_state(tmp_path):
    partial = tmp_path / "partial"
    (partial / "modules").mkdir(parents=True)
    (partial / "modules" / "module.md").write_text("# Module\n", encoding="utf-8")
    partial_report = lint_cmd.LintReport(
        wiki_dir=str(partial),
        src_dir=str(tmp_path),
    )
    lint_cmd._check_sync_manifest(partial_report, partial, str(tmp_path))

    assert "llm-wiki migrate --dry-run" in partial_report.issues[0].message
    assert "bootstrap" not in partial_report.issues[0].message.lower()

    seedable = tmp_path / "seedable"
    seedable.mkdir()
    (seedable / "index.md").write_text("# Existing\n", encoding="utf-8")
    seedable_report = lint_cmd.LintReport(
        wiki_dir=str(seedable),
        src_dir=str(tmp_path),
    )
    lint_cmd._check_sync_manifest(seedable_report, seedable, str(tmp_path))

    assert "llm-wiki sync --jobs 1" in seedable_report.issues[0].message


@pytest.mark.parametrize("target_kind", ["missing", "empty", "scaffold"])
def test_lint_manifest_guidance_routes_every_first_use_state_to_bootstrap(
    tmp_path,
    target_kind,
):
    wiki = tmp_path / target_kind
    if target_kind == "empty":
        wiki.mkdir()
    elif target_kind == "scaffold":
        _write_init_scaffold(wiki)
    report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))

    lint_cmd._check_sync_manifest(report, wiki, str(tmp_path))

    message = report.issues[0].message
    assert "llm-wiki bootstrap --src-dir" in message
    assert "llm-wiki sync --jobs 1" not in message
    assert "llm-wiki migrate --dry-run" not in message
