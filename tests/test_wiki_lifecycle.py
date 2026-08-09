from __future__ import annotations

import json

import pytest

from llm_wiki_cli.config import AGENT_CHOICES
from llm_wiki_cli.commands import lint_cmd
from llm_wiki_cli.services import wiki_lifecycle, wiki_scaffold
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from llm_wiki_cli.services.wiki_lifecycle import (
    WikiLifecycleState,
    bootstrap_guidance,
    classify_wiki_lifecycle,
    migration_guidance,
    sync_guidance,
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


def test_wiki_scaffold_public_prose_uses_neutral_content_wording():
    docstring = wiki_scaffold.__doc__ or ""

    assert "pristine scaffold content" in docstring
    assert "placeholder" not in docstring.casefold()


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


@pytest.mark.parametrize(
    ("guidance", "expected"),
    [
        (
            bootstrap_guidance,
            "Run `llm-wiki bootstrap --src-dir '/tmp/source dir' "
            "--wiki-dir '/tmp/wiki dir'` to create the initial wiki and manifest.",
        ),
        (
            migration_guidance,
            "Preview the existing wiki migration with "
            "`llm-wiki migrate --dry-run --src-dir '/tmp/source dir' "
            "--wiki-dir '/tmp/wiki dir'`.",
        ),
        (
            sync_guidance,
            "Seed the existing wiki safely with "
            "`llm-wiki sync --jobs 1 --src-dir '/tmp/source dir' "
            "--wiki-dir '/tmp/wiki dir'`.",
        ),
    ],
)
def test_lifecycle_guidance_uses_posix_shell_join(
    monkeypatch,
    guidance,
    expected,
):
    monkeypatch.setattr(wiki_lifecycle, "_uses_windows_command_line", lambda: False)

    assert guidance(src_dir="/tmp/source dir", wiki_dir="/tmp/wiki dir") == expected


@pytest.mark.parametrize(
    ("guidance", "src_dir", "wiki_dir", "expected_command"),
    [
        (
            bootstrap_guidance,
            r"C:\Source",
            r"C:\Wiki",
            r"llm-wiki bootstrap --src-dir C:\Source --wiki-dir C:\Wiki",
        ),
        (
            bootstrap_guidance,
            r"C:\Source Dir",
            r"C:\Wiki Dir",
            'llm-wiki bootstrap --src-dir "C:\\Source Dir" '
            '--wiki-dir "C:\\Wiki Dir"',
        ),
        (
            migration_guidance,
            r"C:\Source Dir",
            r"C:\Wiki Dir",
            'llm-wiki migrate --dry-run --src-dir "C:\\Source Dir" '
            '--wiki-dir "C:\\Wiki Dir"',
        ),
        (
            sync_guidance,
            r"C:\Source Dir",
            r"C:\Wiki Dir",
            'llm-wiki sync --jobs 1 --src-dir "C:\\Source Dir" '
            '--wiki-dir "C:\\Wiki Dir"',
        ),
    ],
)
def test_lifecycle_guidance_uses_native_windows_command_line(
    monkeypatch,
    guidance,
    src_dir,
    wiki_dir,
    expected_command,
):
    monkeypatch.setattr(wiki_lifecycle, "_uses_windows_command_line", lambda: True)

    message = guidance(src_dir=src_dir, wiki_dir=wiki_dir)

    assert f"`{expected_command}`" in message


def test_windows_lifecycle_guidance_escapes_embedded_quotes(monkeypatch):
    monkeypatch.setattr(wiki_lifecycle, "_uses_windows_command_line", lambda: True)

    message = bootstrap_guidance(
        src_dir='C:\\Source Dir\\quoted "value"',
        wiki_dir=r"C:\Wiki Dir",
    )

    assert '"C:\\Source Dir\\quoted \\"value\\""' in message
