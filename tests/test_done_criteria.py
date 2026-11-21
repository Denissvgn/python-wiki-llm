"""The engine's done criteria, each shown end to end.

Criteria proven elsewhere: importing either engine loads no CLI, command or
API modules (``test_engine.py``, ``test_engine_native.py``); engines never
prepare helpers unless granted (``test_engine.py``,
``test_automatic_helper_preparation.py``); existing wikis stay
byte-identical (``test_sync_snapshots.py``); core formats have schemas and
conformance cases (``test_conformance_cases.py``); a non-code pack runs every
use case (``test_notes_pack.py``); providers never leak between engines
(``test_engine_integrations.py``). Windows lanes run all of these.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import threading

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Run in a fresh interpreter so module loading and process use are observable.
_PRELUDE = (
    "import os, sys, subprocess\n"
    f"sys.path.insert(0, {str(ROOT)!r})\n"
    "def refuse(*args, **kwargs):\n"
    "    raise SystemExit('a subprocess was started')\n"
    "subprocess.run = subprocess.Popen = refuse\n"
)
_REPORT = (
    "import json\n"
    "loaded = sorted(m for m in sys.modules if m == 'llm_wiki_cli.cli' or m.startswith('llm_wiki_cli.commands'))\n"
    "print(json.dumps({'loaded': loaded, 'cli_loaded': any(m.split('.')[0] == 'llm_wiki_cli' for m in sys.modules)}))\n"
)


def _snapshot(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


def _make_read_only(root: Path) -> None:
    for path in [root, *root.rglob("*")]:
        mode = path.stat().st_mode
        path.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def _make_writable(root: Path) -> None:
    for path in [root, *root.rglob("*")]:
        path.chmod(path.stat().st_mode | stat.S_IWUSR)


def _run(tmp_path: Path, body: str) -> dict:
    environment = {
        key: value for key, value in os.environ.items()
        if key not in {"LLM_WIKI_CACHE_DIR", "PYTHONPATH"}
    }
    environment.update(
        GIT_CEILING_DIRECTORIES=os.fspath(tmp_path.parent),
        # No git on PATH: the engines must not need it.
        PATH=os.fspath(tmp_path / "no-tools"),
        LLM_WIKI_CACHE_DIR=os.fspath(tmp_path / "cache"),
        PYTHONUTF8="1",
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", _PRELUDE + body + _REPORT],
        cwd=tmp_path, env=environment, capture_output=True, text=True, encoding="utf-8", timeout=300,
    )
    assert result.returncode == 0, result.stderr[-4000:]
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.fixture
def read_only(tmp_path):
    roots: list[Path] = []

    def protect(root: Path) -> dict[str, bytes]:
        before = _snapshot(root)
        _make_read_only(root)
        roots.append(root)
        return before

    yield protect
    for root in roots:
        _make_writable(root)


def test_cli_engine_runs_on_a_read_only_tree_without_git_or_processes(tmp_path, read_only):
    project = tmp_path / "project"
    (project / "pkg").mkdir(parents=True)
    (project / "pkg/__init__.py").write_text("", encoding="utf-8", newline="")
    (project / "pkg/widget.py").write_text(
        'class Widget:\n    """A widget."""\n\n    def run(self):\n        return 1\n',
        encoding="utf-8", newline="",
    )
    before = read_only(project)
    report = _run(tmp_path, (
        "from llm_wiki_cli.engine import BootstrapRequest, Engine, LintRequest, NoProcessHost, SyncRequest\n"
        "engine = Engine(host=NoProcessHost())\n"
        "engine.bootstrap(BootstrapRequest(source_root='project', wiki_root='wiki'))\n"
        "engine.sync(SyncRequest(source_root='project', wiki_root='wiki'))\n"
        "assert engine.lint(LintRequest(source_root='project', wiki_root='wiki')).passed\n"
        "assert 'subprocess' in engine.capabilities()['missing']\n"
    ))
    assert report["loaded"] == []
    assert _snapshot(project) == before
    assert (tmp_path / "wiki/modules").is_dir()


def test_engine_runs_a_pack_on_a_read_only_tree_with_no_application_code(tmp_path, read_only):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "onboarding.md").write_text("# Team Onboarding\n\n## Accounts\n\nRequest access.\n", encoding="utf-8", newline="")
    before = read_only(notes)
    report = _run(tmp_path, (
        "from llm_wiki_engine import Engine\n"
        "from llm_wiki_engine.host import NoProcessHost\n"
        "from llm_wiki_engine.wiki_operations import BootstrapRequest, LintRequest, SyncRequest\n"
        "from tests.notes_parts import ENGINE_NOTES_PACK\n"
        "engine = Engine(host=NoProcessHost(), pack=ENGINE_NOTES_PACK)\n"
        "engine.bootstrap(BootstrapRequest(source_root='notes', wiki_root='wiki'))\n"
        "assert engine.sync(SyncRequest(source_root='notes', wiki_root='wiki')).status == 'up-to-date'\n"
        "assert engine.lint(LintRequest(source_root='notes', wiki_root='wiki')).passed\n"
        "assert 'subprocess' in engine.capabilities()['missing']\n"
    ))
    assert report == {"loaded": [], "cli_loaded": False}
    assert _snapshot(notes) == before


def test_engines_with_different_packs_and_workspaces_run_side_by_side(tmp_path):
    from llm_wiki_engine import Engine
    from llm_wiki_engine.host import NoProcessHost
    from llm_wiki_engine.pack_interfaces import DomainPack, ExtensionSourceClassifier
    from llm_wiki_engine.wiki_operations import BootstrapRequest
    from tests.notes_parts import ENGINE_NOTES_PACK, NotesRenderer

    text_pack = DomainPack(
        "example/text-notes",
        ExtensionSourceClassifier({"text": (".txt",)}),
        page_renderer=NotesRenderer(),
        extractors={"text": "tests.notes_parts:NotesExtractor"},
    )
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "plan.md").write_text("# Plan\n\n## Goals\n", encoding="utf-8", newline="")
    (sources / "diary.txt").write_text("# Diary\n\n## Monday\n", encoding="utf-8", newline="")
    engines = {
        "markdown": (Engine(host=NoProcessHost(), pack=ENGINE_NOTES_PACK), "wiki-markdown"),
        "text": (Engine(host=NoProcessHost(), pack=text_pack), "wiki-text"),
    }
    both_started = threading.Barrier(2, timeout=30)
    errors: list[BaseException] = []

    def run(engine, wiki):
        try:
            with engine.operation():
                both_started.wait()
            engine.bootstrap(BootstrapRequest(source_root=sources, wiki_root=tmp_path / wiki))
        except BaseException as error:  # reported below
            errors.append(error)

    threads = [threading.Thread(target=run, args=pair) for pair in engines.values()]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=120)
    assert errors == []
    pages = {
        name: sorted(p.relative_to(tmp_path / wiki).as_posix() for p in (tmp_path / wiki).rglob("*.md"))
        for name, (_, wiki) in engines.items()
    }
    assert "modules/plan.md" in pages["markdown"] and "modules/diary.md" not in pages["markdown"]
    assert "modules/diary.md" in pages["text"] and "modules/plan.md" not in pages["text"]
