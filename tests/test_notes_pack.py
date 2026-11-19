"""A non-code domain pack runs every engine use case through the pack interfaces."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.engine import (
    BootstrapRequest,
    DomainPack,
    Engine,
    ExtensionSourceClassifier,
    LintRequest,
    NoHelperToolchain,
    NoProcessHost,
    SyncRequest,
)
from llm_wiki_cli.services import context_service, helper_preparation
from tests.notes_pack import NOTES_PACK

RUNBOOK = """# Operations Runbook

How the team operates the service. See [onboarding](../onboarding.md).

## Deploy

Ship a release.

## Rollback

Undo a release.
"""
ONBOARDING = """# Team Onboarding

## Accounts

Request access.
"""


def _no_process(*args, **kwargs):
    pytest.fail("the notes pack started a subprocess")


@pytest.fixture
def notes(tmp_path, monkeypatch) -> Path:
    (tmp_path / "notes/ops").mkdir(parents=True)
    (tmp_path / "notes/ops/runbook.md").write_text(RUNBOOK, encoding="utf-8")
    (tmp_path / "notes/onboarding.md").write_text(ONBOARDING, encoding="utf-8")
    (tmp_path / "notes/script.py").write_text("class NotANote:\n    pass\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))
    monkeypatch.setattr(subprocess, "run", _no_process)
    monkeypatch.setattr(subprocess, "Popen", _no_process)
    monkeypatch.setattr(
        helper_preparation, "prepare_operation_helpers",
        lambda *a, **k: pytest.fail("the notes pack prepared a helper"),
    )
    return tmp_path


@pytest.fixture
def engine() -> Engine:
    return Engine(host=NoProcessHost(), pack=NOTES_PACK)


def _pages(root: Path) -> list[str]:
    return sorted(p.relative_to(root / "wiki").as_posix() for p in (root / "wiki").rglob("*.md"))


def test_bootstrap_writes_note_and_section_pages(notes, engine):
    result = engine.bootstrap(BootstrapRequest(source_root="notes", wiki_root="wiki"))
    assert result is not None
    pages = _pages(notes)
    assert {"modules/runbook.md", "modules/onboarding.md"} <= set(pages)
    assert {"entities/Deploy.md", "entities/Rollback.md", "entities/Accounts.md"} <= set(pages)
    assert not any("NotANote" in page or "script" in page for page in pages)
    runbook = (notes / "wiki/modules/runbook.md").read_text(encoding="utf-8")
    assert runbook.splitlines()[next(
        i for i, line in enumerate(runbook.splitlines()) if line.startswith("# ")
    )] == "# Operations Runbook"


def test_sync_follows_note_edits_and_keeps_reviewed_text(notes, engine):
    engine.bootstrap(BootstrapRequest(source_root="notes", wiki_root="wiki"))
    page = notes / "wiki/modules/onboarding.md"
    text = page.read_text(encoding="utf-8")
    marker = "## Description\n"
    assert marker in text
    head, tail = text.split(marker, 1)
    rest = tail.split("\n## ", 1)
    page.write_text(
        head + marker + "\nWhat a new teammate does first.\n" + ("\n## " + rest[1] if len(rest) > 1 else ""),
        encoding="utf-8",
    )
    (notes / "notes/onboarding.md").write_text(
        ONBOARDING + "\n## Laptops\n\nOrder one.\n", encoding="utf-8"
    )

    outcome = engine.sync(SyncRequest(source_root="notes", wiki_root="wiki"))

    assert outcome.status == "synced"
    assert "entities/Laptops.md" in _pages(notes)
    synced = page.read_text(encoding="utf-8")
    assert "What a new teammate does first." in synced
    assert "Laptops" in synced and "# Team Onboarding" in synced


def test_search_lint_and_context_use_the_pack(notes, engine, monkeypatch):
    engine.bootstrap(BootstrapRequest(source_root="notes", wiki_root="wiki"))

    found = engine.call(api.search_wiki, "Rollback", src_dir="notes", wiki_dir="wiki")
    assert found["results"][0]["path"] == "entities/Rollback.md"

    lint = engine.lint(LintRequest(source_root="notes", wiki_root="wiki"))
    assert lint.passed, [(issue.category, issue.message) for issue in lint.issues]

    # Without git the host reports no changes; every note is listed.
    unchanged = engine.call(api.build_context, "notes", wiki_dir="wiki", budget=4000)
    assert set(unchanged["files"]) == {"onboarding.md", "ops/runbook.md"}

    # A changed note is focused, and the notes it links with are related.
    monkeypatch.setattr(context_service, "_git_changed_files", lambda src_dir: ["onboarding.md"])
    context = engine.call(api.build_context, "notes", wiki_dir="wiki", budget=4000)
    files = context["files"]
    assert files["onboarding.md"]["priority"] == "high"
    assert files["ops/runbook.md"]["priority"] == "medium"
    assert files["onboarding.md"]["title"] == "Team Onboarding"
    assert files["onboarding.md"]["sections"] == ["Accounts"]
    assert files["onboarding.md"]["links"] == []
    # Related notes get less detail: sections, but not links.
    assert files["ops/runbook.md"]["sections"] == ["Deploy", "Rollback"]
    assert "links" not in files["ops/runbook.md"]

    small = engine.call(api.build_context, "notes", wiki_dir="wiki", budget=40)
    assert small["downgraded_files"] or small["omitted_files"]


def test_the_pack_declares_no_code_helpers_or_references(engine):
    pack = engine.capabilities()["pack"]
    assert pack == NOTES_PACK.describe()
    assert NOTES_PACK.describe()["source_kinds"] == {"notes": [".md"]}
    assert NOTES_PACK.describe()["reference_providers"] == []
    assert NOTES_PACK.describe()["helper_toolchain"].endswith("NoHelperToolchain")
    assert NOTES_PACK.describe()["extractors"] == {"notes": "tests.notes_pack:NotesExtractor"}


def test_pack_extractors_must_name_declared_kinds_and_entry_points():
    classifier = ExtensionSourceClassifier({"notes": (".md",)})
    with pytest.raises(ValueError, match="not declared"):
        DomainPack("x/y", classifier, extractors={"docs": "tests.notes_pack:NotesExtractor"})
    with pytest.raises(ValueError, match="entry point"):
        DomainPack("x/y", classifier, extractors={"notes": "tests.notes_pack.NotesExtractor"})
    with pytest.raises(TypeError):
        DomainPack("x/y", classifier, extractors=["notes"])  # type: ignore[arg-type]
    pack = DomainPack("x/y", classifier, helper_toolchain=NoHelperToolchain())
    assert pack.with_extractor("notes", "tests.notes_pack:NotesExtractor").extractors == {
        "notes": "tests.notes_pack:NotesExtractor"
    }
