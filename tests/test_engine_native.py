"""The engine's own Engine runs with no application code."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from llm_wiki_engine import Engine, integrations
from llm_wiki_engine.host import NoProcessHost
from llm_wiki_engine.pack_interfaces import (
    DomainPack,
    ExtensionSourceClassifier,
    active_pack,
)

ROOT = Path(__file__).resolve().parents[1]
NOTES = DomainPack("example/notes", ExtensionSourceClassifier({"notes": (".md",)}))


def test_importing_the_engine_loads_no_application_code():
    probe = (
        "import sys; from llm_wiki_engine import Engine; "
        "from llm_wiki_engine.pack_interfaces import DomainPack, ExtensionSourceClassifier; "
        "from llm_wiki_engine.host import NoProcessHost; "
        "engine = Engine(host=NoProcessHost(), pack=DomainPack('x/y', ExtensionSourceClassifier({'n': ('.md',)}))); "
        "engine.capabilities(); "
        "print(sorted(m for m in sys.modules if m.split('.')[0] == 'llm_wiki_cli'))"
    )
    result = subprocess.run([sys.executable, "-I", "-c", probe], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "[]"


def test_capabilities_follow_the_published_format():
    import jsonschema

    schema = json.loads(
        (ROOT / "src/llm_wiki_cli/schemas/llm-wiki-engine-capabilities-v1.schema.json").read_text(encoding="utf-8")
    )
    document = Engine(host=NoProcessHost(), pack=NOTES).capabilities()
    jsonschema.validate(document, schema)
    assert document["helper_preparation"] == "never"
    assert document["publication_targets"] == {"kinds": []}
    assert document["pack"]["page_namer"] == "llm_wiki_engine.pack_interfaces.StemPageNamer"


def test_an_operation_applies_the_pack_and_integrations():
    isolated = integrations.IntegrationSet(inherit=False)
    engine = Engine(host=NoProcessHost(), pack=NOTES, integrations=isolated)
    assert active_pack() is None
    with engine.operation() as operation:
        assert active_pack() is NOTES and operation.pack is NOTES
        with pytest.raises(integrations.IntegrationUnavailable):
            integrations.provider("source_snapshots")
    assert active_pack() is None


def test_the_engine_checks_what_it_is_given():
    with pytest.raises(TypeError, match="pack"):
        Engine(pack="notes")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="host"):
        Engine(pack=NOTES, host="host")  # type: ignore[arg-type]


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


@pytest.fixture
def notes(tmp_path, monkeypatch) -> Path:
    import subprocess as process

    def no_process(*args, **kwargs):
        pytest.fail("the engine started a subprocess")

    (tmp_path / "notes/ops").mkdir(parents=True)
    (tmp_path / "notes/ops/runbook.md").write_text(RUNBOOK, encoding="utf-8", newline="")
    (tmp_path / "notes/onboarding.md").write_text(ONBOARDING, encoding="utf-8", newline="")
    (tmp_path / "notes/script.py").write_text("class NotANote:\n    pass\n", encoding="utf-8", newline="")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(process, "run", no_process)
    monkeypatch.setattr(process, "Popen", no_process)
    return tmp_path


@pytest.fixture
def notes_engine() -> Engine:
    from tests.notes_parts import ENGINE_NOTES_PACK

    return Engine(host=NoProcessHost(), pack=ENGINE_NOTES_PACK)


def _pages(root: Path) -> list[str]:
    return sorted(p.relative_to(root / "wiki").as_posix() for p in (root / "wiki").rglob("*.md"))


def test_bootstrap_writes_note_and_section_pages(notes, notes_engine):
    from llm_wiki_engine.wiki_operations import BootstrapRequest

    result = notes_engine.bootstrap(BootstrapRequest(source_root="notes", wiki_root="wiki"))
    assert result.sources == 2
    pages = _pages(notes)
    assert {"modules/runbook.md", "modules/onboarding.md", "index.md", "log.md"} <= set(pages)
    assert {"entities/Deploy.md", "entities/Rollback.md", "entities/Accounts.md"} <= set(pages)
    assert not any("NotANote" in page or "script" in page for page in pages)
    runbook = (notes / "wiki/modules/runbook.md").read_text(encoding="utf-8")
    assert runbook.startswith("# Operations Runbook\n")
    assert "[Deploy](../entities/Deploy.md)" in runbook
    assert (notes / "wiki/.llm-wiki-manifest.json").exists()


def test_sync_follows_note_edits_and_keeps_reviewed_text(notes, notes_engine):
    from llm_wiki_engine.markdown_sections import replace_section_body, section_body
    from llm_wiki_engine.wiki_operations import BootstrapRequest, SyncRequest

    notes_engine.bootstrap(BootstrapRequest(source_root="notes", wiki_root="wiki"))
    page = notes / "wiki/modules/onboarding.md"
    page.write_text(
        replace_section_body(page.read_text(encoding="utf-8"), "Description", "What a new teammate does first."),
        encoding="utf-8", newline="",
    )
    (notes / "notes/onboarding.md").write_text(ONBOARDING + "\n## Laptops\n\nOrder one.\n", encoding="utf-8", newline="")
    (notes / "notes/ops/runbook.md").unlink()

    outcome = notes_engine.sync(SyncRequest(source_root="notes", wiki_root="wiki"))

    assert outcome.status == "synced"
    pages = _pages(notes)
    assert "entities/Laptops.md" in pages
    assert "modules/runbook.md" not in pages and "entities/Deploy.md" not in pages
    synced = page.read_text(encoding="utf-8")
    assert section_body(synced, "Description") == "What a new teammate does first."
    assert "Laptops" in synced and synced.startswith("# Team Onboarding\n")
    again = notes_engine.sync(SyncRequest(source_root="notes", wiki_root="wiki"))
    assert again.status == "up-to-date"


def test_lint_passes_a_fresh_wiki_and_reports_drift(notes, notes_engine):
    from llm_wiki_engine.wiki_operations import BootstrapRequest, LintRequest

    notes_engine.bootstrap(BootstrapRequest(source_root="notes", wiki_root="wiki"))
    report = notes_engine.lint(LintRequest(source_root="notes", wiki_root="wiki"))
    assert report.passed, report.to_dict()
    (notes / "notes/onboarding.md").write_text(ONBOARDING + "\nMore.\n", encoding="utf-8", newline="")
    (notes / "wiki/entities/Rollback.md").unlink()
    categories = {issue.category for issue in notes_engine.lint(LintRequest(source_root="notes", wiki_root="wiki")).issues}
    assert {"stale-source", "missing-page", "broken-link"} <= categories


def test_bootstrap_refuses_an_existing_wiki_and_sync_needs_one(notes, notes_engine):
    from llm_wiki_engine.wiki_operations import BootstrapRequest, SyncRequest, WikiOperationError

    with pytest.raises(WikiOperationError, match="bootstrap it first"):
        notes_engine.sync(SyncRequest(source_root="notes", wiki_root="wiki"))
    notes_engine.bootstrap(BootstrapRequest(source_root="notes", wiki_root="wiki"))
    with pytest.raises(WikiOperationError, match="already holds a wiki"):
        notes_engine.bootstrap(BootstrapRequest(source_root="notes", wiki_root="wiki"))


def test_engine_events_report_each_use_case(notes):
    from llm_wiki_engine.wiki_operations import BootstrapRequest
    from tests.notes_parts import ENGINE_NOTES_PACK

    events = []
    engine = Engine(host=NoProcessHost(events=events.append), pack=ENGINE_NOTES_PACK)
    engine.bootstrap(BootstrapRequest(source_root="notes", wiki_root="wiki"))
    kinds = [event.kind for event in events]
    assert kinds[0] == "operation.started" and kinds[-1] == "operation.finished"
    assert {event.operation for event in events} == {"bootstrap"}


def test_the_notes_pack_runs_bootstrap_sync_and_lint_without_the_cli(tmp_path):
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes/onboarding.md").write_text(ONBOARDING, encoding="utf-8", newline="")
    probe = (
        "import sys, subprocess\n"
        "def refuse(*a, **k): raise SystemExit('subprocess started')\n"
        "subprocess.run = subprocess.Popen = refuse\n"
        "from llm_wiki_engine import Engine\n"
        "from llm_wiki_engine.host import NoProcessHost\n"
        "from llm_wiki_engine.wiki_operations import BootstrapRequest, SyncRequest, LintRequest\n"
        "from tests.notes_parts import ENGINE_NOTES_PACK\n"
        "engine = Engine(host=NoProcessHost(), pack=ENGINE_NOTES_PACK)\n"
        "engine.bootstrap(BootstrapRequest(source_root='notes', wiki_root='wiki'))\n"
        "open('notes/onboarding.md', 'a', encoding='utf-8').write('\\n## Laptops\\n')\n"
        "assert engine.sync(SyncRequest(source_root='notes', wiki_root='wiki')).status == 'synced'\n"
        "assert engine.lint(LintRequest(source_root='notes', wiki_root='wiki')).passed\n"
        "print(sorted(m for m in sys.modules if m.split('.')[0] == 'llm_wiki_cli'))\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, {str(ROOT)!r}); exec({probe!r})"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "[]"
