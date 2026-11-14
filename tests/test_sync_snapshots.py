"""End-to-end byte snapshots of bootstrap, sync and upgrade on python-basic.

Moving sync behind a library entry point must not change what it writes. The
first scenario follows the tutorial: initialize and bootstrap, sync unchanged
input, then add an authored sentence and a source field and sync again. The
second covers the route where upgrade drives sync itself: a canonical wiki with
no native knowledge, manifest or surface roots is seeded by upgrade, and the
next sync applies the edits made before the upgrade.

Generated pages, the surface index, agent files and edited sources are pinned
byte for byte. Content-addressed knowledge, manifest and recovery stores embed
a random adoption identity or recovery times, so they are pinned only through
the unchanged-resync check. The log's run dates and generator version are
normalized because no clock or version can be injected yet.
Regenerate the fixture deliberately with ``LLM_WIKI_UPDATE_SYNC_SNAPSHOTS=1``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "examples" / "python-basic" / "project"
FIXTURES = ROOT / "tests" / "fixtures" / "sync-snapshots"
FIXTURE = FIXTURES / "python-basic.json"
UPGRADE_FIXTURE = FIXTURES / "python-basic-upgrade.json"
NATIVE_ROOTS = (".llm-wiki-knowledge.json", ".llm-wiki-manifest.json", ".llm-wiki-surface.json")
UPDATE_ENV = "LLM_WIKI_UPDATE_SYNC_SNAPSHOTS"
MACHINE_STORES = (
    "wiki/.llm-wiki-knowledge/",
    "wiki/.llm-wiki-manifest/",
    "wiki/.llm-wiki-knowledge.json",
    "wiki/.llm-wiki-manifest.json",
    "wiki/.llm-wiki-maintenance-adoption.json",
    ".llm-wiki-maintenance-recovery/",
)
AUTHORED_SENTENCE = "Keep task titles in the user's original spelling."


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _normalized_log(text: str) -> str:
    # The log records the run date and package version; nothing else varies.
    text = re.sub(r"^## \d{4}-\d{2}-\d{2}$", "## <date>", text, flags=re.MULTILINE)
    return re.sub(
        r"^- Generator version: `[^`]+`$", "- Generator version: `<version>`",
        text, flags=re.MULTILINE,
    )


def _pinned(tree: dict[str, bytes]) -> dict[str, str]:
    pinned = {
        path: content.decode("utf-8")
        for path, content in tree.items()
        if not path.startswith(MACHINE_STORES)
    }
    pinned["wiki/log.md"] = _normalized_log(pinned["wiki/log.md"])
    return pinned


def _cli(project: Path, *args: str) -> None:
    environment = os.environ.copy()
    environment.pop("LLM_WIKI_CACHE_DIR", None)
    temporary = project.parent / "tmp"
    temporary.mkdir(exist_ok=True)
    environment.update(
        PYTHONPATH=str(ROOT / "src"),
        PYTHONUTF8="1",
        PYTHONIOENCODING="utf-8",
        GIT_CEILING_DIRECTORIES=str(project.parent),
        # Upgrade keeps recovery copies under the temporary directory.
        TMPDIR=str(temporary),
    )
    result = subprocess.run(
        [sys.executable, "-m", "llm_wiki_cli.cli", *args],
        cwd=project, env=environment, capture_output=True,
        text=True, encoding="utf-8", timeout=180,
    )
    assert result.returncode == 0, (args, result.stdout, result.stderr)


def _sync(project: Path) -> None:
    _cli(project, "sync", "--jobs", "1", "--src-dir", ".", "--wiki-dir", "wiki")


def _edit_task_and_model(project: Path) -> None:
    page = project / "wiki" / "entities" / "Task.md"
    text = page.read_text(encoding="utf-8")
    start = text.index("## Description\n")
    end = text.index("\n## ", start + 1)
    page.write_text(
        text[:end].rstrip("\n") + f"\n\n{AUTHORED_SENTENCE}\n" + text[end:],
        encoding="utf-8",
    )
    model = project / "models.py"
    source = model.read_text(encoding="utf-8")
    assert "done: bool = False\n" in source
    model.write_text(
        source.replace("done: bool = False\n", "done: bool = False\n    priority: int = 1\n", 1),
        encoding="utf-8",
    )


def _copy_project(tmp_path: Path) -> Path:
    project = tmp_path / "python-basic"
    shutil.copytree(
        PROJECT, project,
        ignore=shutil.ignore_patterns("wiki", ".llm-wiki", "AGENTS.md", "__pycache__"),
    )
    _cli(project, "init", "--agent", "generic", "--no-skills", "--wiki-dir", "wiki")
    return project


def _assert_matches_fixture(fixture: Path, actual: dict[str, dict[str, str]]) -> None:
    if os.environ.get(UPDATE_ENV) == "1":
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text(
            json.dumps(actual, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    expected = json.loads(fixture.read_text(encoding="utf-8"))
    assert sorted(actual) == sorted(expected)
    for stage in expected:
        assert sorted(actual[stage]) == sorted(expected[stage]), stage
        for path, content in expected[stage].items():
            assert actual[stage][path] == content, f"{stage}: {path}"


def test_python_basic_bootstrap_and_sync_bytes(tmp_path: Path) -> None:
    project = _copy_project(tmp_path)
    _cli(project, "bootstrap", "--src-dir", ".", "--wiki-dir", "wiki")
    bootstrapped = _tree(project)
    _sync(project)
    assert _tree(project) == bootstrapped, "sync of unchanged input must not rewrite any file"

    _edit_task_and_model(project)
    _sync(project)
    changed = _tree(project)
    task = changed["wiki/entities/Task.md"].decode("utf-8")
    assert AUTHORED_SENTENCE in task and "priority" in task
    assert all(any(path.startswith(store) for path in changed) for store in MACHINE_STORES)

    _assert_matches_fixture(
        FIXTURE, {"bootstrap": _pinned(bootstrapped), "source-change": _pinned(changed)}
    )


def test_python_basic_upgrade_seeds_legacy_wiki_through_sync(tmp_path: Path) -> None:
    project = _copy_project(tmp_path)
    _cli(project, "bootstrap", "--src-dir", ".", "--wiki-dir", "wiki", "--knowledge-format", "v1")
    # Older canonical wikis carry pages but no native authority.
    for name in NATIVE_ROOTS:
        (project / "wiki" / name).unlink()
    _edit_task_and_model(project)
    legacy = _tree(project)

    _cli(project, "upgrade", "--wiki-dir", "wiki", "--src-dir", ".")
    upgraded = _tree(project)
    assert list((tmp_path / "tmp" / "llm-wiki-upgrade-recovery").glob("*/legacy")), (
        "upgrade must take the legacy seed route"
    )
    assert _pinned(upgraded) == {
        **_pinned(legacy),
        "wiki/.llm-wiki-surface.json": upgraded["wiki/.llm-wiki-surface.json"].decode("utf-8"),
    }, "seeding through sync must leave existing pages untouched"

    _sync(project)
    synced = _tree(project)
    task = synced["wiki/entities/Task.md"].decode("utf-8")
    assert AUTHORED_SENTENCE in task and "priority" in task
    _sync(project)
    assert _tree(project) == synced, "sync after the applied edits must not rewrite any file"

    _assert_matches_fixture(
        UPGRADE_FIXTURE, {"upgrade": _pinned(upgraded), "post-upgrade-sync": _pinned(synced)}
    )
