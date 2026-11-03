"""Read-only retirement previews do not authorize deleting authored content."""

import json
from pathlib import Path
import sys

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services.knowledge_storage_lifecycle import _committed_inputs
from llm_wiki_cli.services.maintenance_protocol import ADOPTION_FILENAME


def _run(monkeypatch, *arguments):
    monkeypatch.setattr(sys, "argv", ["llm-wiki", *arguments])
    cli.main()


def _snapshot(root):
    locks = {"llm-wiki-governance.lock", "llm-wiki-storage.lock"}
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file() and p.relative_to(root).as_posix() not in locks}


def _project_state(root):
    return {name: _snapshot(root / name) for name in ("src", "wiki")}


def _project(tmp_path, monkeypatch, *, adopted, authored=True, retire=True):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    entry = src / "entry.py"
    entry.write_text(
        "from first import load\nfrom second import transform\nfrom third import emit\n\n"
        "def pipeline():\n    return emit(transform(load()))\n", encoding="utf-8")
    for name, text in {
        "first": "def load():\n    return 1\n",
        "second": "def transform(value):\n    return value + 1\n",
        "third": "def emit(value):\n    return value\n",
    }.items():
        (src / (name + ".py")).write_text(text, encoding="utf-8")
    _run(monkeypatch, "bootstrap", "--src-dir", "src", "--wiki-dir", "wiki",
         *([] if adopted else ["--knowledge-format", "v1"]))
    page = tmp_path / "wiki/workflows/pipeline.md"
    assert "## Behavior" in page.read_text(encoding="utf-8")
    if authored:
        page.write_text(page.read_text(encoding="utf-8").rstrip()
                        + "\n\nPreserve this authored explanation of the workflow.\n", encoding="utf-8")
    common = ["--src-dir", "src", "--wiki-dir", "wiki", "--jobs", "1", "--no-cache", "--no-plugins"]
    _run(monkeypatch, "sync", *common)
    _committed_inputs("wiki")
    assert (tmp_path / "wiki" / ADOPTION_FILENAME).exists() is adopted
    if retire:
        entry.write_text('"""The pipeline entry point was intentionally removed."""\n', encoding="utf-8")
    return page, common


@pytest.mark.parametrize("adopted", [False, True])
def test_cli_protected_workflow_preview_is_complete_and_never_authorizes_apply(
    tmp_path, monkeypatch, capsys, adopted
):
    page, common = _project(tmp_path, monkeypatch, adopted=adopted)
    before = _project_state(tmp_path)
    capsys.readouterr()
    for flags in ([], ["--dry-run"], ["--force", "--dry-run"], []):
        if "--dry-run" in flags:
            _run(monkeypatch, "sync", *common, *flags)
            output = capsys.readouterr().out
            assert "protected generated surface retirement: 1" in output
            assert "workflows/pipeline.md" in output
            assert "human-authored Behavior" in output
            assert "requires --force: yes" in output
            assert "Knowledge index:" in output and "Manifest:" in output
            assert "Preview completed." in output
            assert "this preview is not an approval token" in output
        else:
            with pytest.raises(SystemExit) as stopped:
                _run(monkeypatch, "sync", *common)
            assert stopped.value.code == 2
            error = capsys.readouterr().err
            assert "human-authored Behavior" in error and "--force" in error
        assert _project_state(tmp_path) == before

    _run(monkeypatch, "sync", *common, "--force")
    assert not page.exists()
    _committed_inputs("wiki")
    surface = json.loads(Path("wiki/.llm-wiki-surface.json").read_bytes())
    assert all(p["canonical_path"] != "workflows/pipeline.md" for p in surface["pages"])
    capsys.readouterr()
    after = _project_state(tmp_path)
    _run(monkeypatch, "sync", *common)
    assert "Wiki is up to date." in capsys.readouterr().out
    assert _project_state(tmp_path) == after


@pytest.mark.parametrize("adopted", [False, True])
def test_source_selection_retirement_preview_preserves_the_original_bindings(
    tmp_path, monkeypatch, capsys, adopted
):
    page, common = _project(tmp_path, monkeypatch, adopted=adopted, retire=False)
    profile = tmp_path / "src/selection.json"
    profile.write_text(json.dumps({"schema_version": "llm-wiki-source-selection/v1",
                                   "include": ["first.py", "second.py", "third.py"], "exclude": []}),
                       encoding="utf-8")
    arguments = [*common, "--source-selection", profile.name]
    before = _project_state(tmp_path)
    original_profile = profile.read_bytes(), profile.stat().st_mtime_ns
    capsys.readouterr()
    with pytest.raises(SystemExit) as stopped:
        _run(monkeypatch, "sync", *arguments)
    assert stopped.value.code == 2
    error = capsys.readouterr().err
    assert "--source-selection" in error and profile.name in error

    _run(monkeypatch, "sync", *arguments, "--dry-run")
    output = capsys.readouterr().out
    assert "workflows/pipeline.md" in output
    assert "protected generated surface retirement: 1" in output
    assert "requires --force: yes" in output and "Preview completed." in output
    assert _project_state(tmp_path) == before
    assert (profile.read_bytes(), profile.stat().st_mtime_ns) == original_profile

    _run(monkeypatch, "sync", *arguments, "--force")
    assert not page.exists()
    assert _snapshot(tmp_path / "src") == before["src"]
    assert (profile.read_bytes(), profile.stat().st_mtime_ns) == original_profile
    state, _, _ = _committed_inputs("wiki")
    assert state.manifest_basis is not None and "entry.py" not in state.manifest_basis.sources


@pytest.mark.parametrize("adopted", [False, True])
def test_authored_content_added_after_preview_requires_a_new_protected_plan(
    tmp_path, monkeypatch, capsys, adopted
):
    page, common = _project(tmp_path, monkeypatch, adopted=adopted, authored=False)
    cache = tmp_path / "inventory-cache"
    common = [argument for argument in common if argument != "--no-cache"]
    common.extend(["--cache-dir", str(cache)])
    before = _project_state(tmp_path)
    capsys.readouterr()
    _run(monkeypatch, "sync", *common, "--dry-run")
    assert "requires --force: no" in capsys.readouterr().out
    assert _project_state(tmp_path) == before
    assert not cache.exists()

    page.write_text(page.read_text(encoding="utf-8").rstrip()
                    + "\n\nAuthored after the first preview: preserve this explanation.\n", encoding="utf-8")
    revised = _project_state(tmp_path)
    with pytest.raises(SystemExit) as stopped:
        _run(monkeypatch, "sync", *common)
    assert stopped.value.code == 2
    assert "human-authored Behavior" in capsys.readouterr().err
    assert _project_state(tmp_path) == revised

    cached = _snapshot(cache)
    _run(monkeypatch, "sync", *common, "--dry-run")
    output = capsys.readouterr().out
    assert "protected generated surface retirement: 1" in output
    assert "requires --force: yes" in output and "Preview completed." in output
    assert _project_state(tmp_path) == revised
    assert _snapshot(cache) == cached
    _run(monkeypatch, "sync", *common, "--force")
    assert not page.exists()
    _committed_inputs("wiki")


@pytest.mark.parametrize("damage", ["symlink", "missing-owner", "corrupt-knowledge", "unproved-surface"])
@pytest.mark.parametrize("force", [False, True])
def test_protected_retirement_preview_still_rejects_unsafe_or_corrupt_authority(
    tmp_path, monkeypatch, capsys, damage, force
):
    page, common = _project(tmp_path, monkeypatch, adopted=damage != "unproved-surface")
    if damage == "symlink":
        external = tmp_path / "authored.md"
        external.write_bytes(page.read_bytes())
        page.unlink()
        page.symlink_to(external)
    elif damage == "missing-owner":
        Path("wiki", ADOPTION_FILENAME).unlink()
    elif damage == "corrupt-knowledge":
        Path("wiki/.llm-wiki-knowledge.json").write_text("{}\n", encoding="utf-8")
    else:
        surface = Path("wiki/.llm-wiki-surface.json")
        payload = json.loads(surface.read_bytes())
        row = next(p for p in payload["pages"] if p["canonical_path"] == "workflows/pipeline.md")
        row["canonical_path"] = "../authored.md"
        surface.write_text(json.dumps(payload), encoding="utf-8")
    before = _snapshot(tmp_path)
    capsys.readouterr()
    with pytest.raises(SystemExit) as stopped:
        _run(monkeypatch, "sync", *common, "--dry-run", *(["--force"] if force else []))
    assert stopped.value.code != 0
    assert "Preview completed." not in capsys.readouterr().out
    assert _snapshot(tmp_path) == before
