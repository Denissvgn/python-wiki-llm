"""Cache custody, real-input invalidation, ownership parity and write recovery."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from llm_wiki_cli.commands import sync_cmd, bootstrap_cmd
from llm_wiki_cli.services import sync_analysis_cache, knowledge_generation
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.lint_service import build_report


def sync(wiki="wiki", **kwargs):
    args = dict(src_dir="src", wiki_dir=wiki, cache_dir="cache", force=True, no_plugins=True)
    args.update(kwargs)
    if args.get("no_cache"):
        args.pop("cache_dir")
    sync_cmd.run(SimpleNamespace(**args))


def edit(wiki="wiki", text="Authored description."):
    page = Path(wiki) / "modules/app.md"
    original = page.read_text()
    first, rest = original.split("## Description\n", 1)
    _, tail = rest.split("\n## ", 1)
    page.write_text(first + "## Description\n\n" + text + "\n\n## " + tail)


@pytest.fixture(params=("v1", "packed-v4-deflate"))
def primed(tmp_path, monkeypatch, request):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/app.py").write_text('class Item:\n    pass\ndef compute(value=3):\n    return value + 1\ndef run():\n    return compute()\n')
    bootstrap_cmd.run(SimpleNamespace(src_dir="src", wiki_dir="wiki", depth="full",
                                     overwrite=False, source_adapter=True, knowledge_format=request.param))
    edit()
    sync()
    assert Path("cache", sync_analysis_cache.FILENAME).exists()
    state = load_knowledge_state("wiki")
    assert state.knowledge is not None
    assert sync_analysis_cache.EXTENSION in state.knowledge.extensions
    return tmp_path


def test_markdown_edit_reuses_static_inputs_but_completes_actual_commit(primed, monkeypatch, capsys):
    edit(text="Second authored description.")
    monkeypatch.setattr(sync_cmd, "_extract_current_inventory", lambda *a, **kw: pytest.fail("source extracted again"))
    monkeypatch.setattr(sync_cmd, "_prepare_sync_page_maps", lambda *a: pytest.fail("maps rebuilt"))
    monkeypatch.setattr(sync_cmd, "_build_sync_graph_observations", lambda *a, **kw: pytest.fail("graph observations rebuilt"))
    monkeypatch.setattr(knowledge_generation, "materialize_typed_graph", lambda *a, **kw: pytest.fail("typed graph rebuilt"))
    sync()
    assert "reuse: hit" in capsys.readouterr().out
    assert "Second authored description." in Path("wiki/modules/app.md").read_text()
    state = load_knowledge_state("wiki")
    assert state.knowledge is not None
    assert build_report("wiki", "src", strict=True).passed


def test_cached_reanchor_matches_independent_full_builder(primed):
    shutil.copytree("wiki", "oracle")
    edit(text="Independent parity description.")
    edit("oracle", text="Independent parity description.")
    sync()
    sync("oracle", rebuild_knowledge=True)
    for name in (".llm-wiki-surface.json", ".llm-wiki-knowledge.json", ".llm-wiki-manifest.json"):
        assert Path("wiki", name).read_bytes() == Path("oracle", name).read_bytes()
    assert {p.relative_to("wiki"): p.read_bytes() for p in Path("wiki").rglob("*.md")} == {
        p.relative_to("oracle"): p.read_bytes() for p in Path("oracle").rglob("*.md")
    }


@pytest.mark.parametrize("change", ["source", "addition", "deletion", "selection", "implementation", "schema", "analyzer", "plugin", "rebuild", "no-cache"])
def test_changed_invocation_inputs_cannot_reuse_analysis(primed, monkeypatch, change):
    options = {}
    if change == "source":
        Path("src/app.py").write_text("class Changed: pass\n")
    elif change == "addition":
        Path("src/new.py").write_text("class New: pass\n")
    elif change == "deletion":
        Path("src/app.py").unlink()
    elif change == "selection":
        Path("src/.llm-wiki").mkdir()
        Path("src/.llm-wiki/source-selection.json").write_text(json.dumps({
            "schema_version": "llm-wiki-source-selection/v1", "include": ["app.py"], "exclude": [],
        }))
    elif change == "implementation":
        monkeypatch.setattr(sync_analysis_cache, "implementation_hash", lambda: "sha256:" + "1" * 64)
    elif change == "schema":
        monkeypatch.setattr(sync_analysis_cache, "SCHEMA", "future-schema")
    elif change == "analyzer":
        monkeypatch.setattr(sync_analysis_cache, "capture_analysis", lambda *a, **kw: {})
    elif change == "plugin":
        Path(".llm-wiki").mkdir()
        Path(".llm-wiki/plugins.lock.json").write_text("{}")
    elif change == "rebuild":
        options["rebuild_knowledge"] = True
    else:
        options["no_cache"] = True
    reached = []
    def fresh(*a, **kw):
        reached.append(True)
        raise RuntimeError("fresh extraction required")
    monkeypatch.setattr(sync_cmd, "_extract_current_inventory", fresh)
    with pytest.raises((RuntimeError, SystemExit)):
        sync(**options)
    assert reached or change == "selection"  # Persisted selection may reject before extraction.


@pytest.mark.parametrize("change", ["missing", "truncated", "forged", "redirected"])
def test_missing_or_corrupted_cache_is_only_a_fallback(primed, monkeypatch, change):
    path = Path("cache", sync_analysis_cache.FILENAME)
    if change == "missing":
        path.unlink()
    elif change == "truncated":
        path.write_text("{")
    elif change == "forged":
        data = json.loads(path.read_text())
        data["inventory"]["app.py"]["functions"][0]["name"] = "invented"
        path.write_text(json.dumps(data))
    else:
        original = path.read_bytes()
        path.unlink()
        Path("elsewhere.json").write_bytes(original)
        path.symlink_to(Path("../elsewhere.json"))
    edit(text="Fallback still preserves prose.")
    with patch.object(sync_cmd, "_extract_current_inventory", wraps=sync_cmd._extract_current_inventory) as extract:
        sync()
    assert extract.call_count == 1
    assert "Fallback still preserves prose." in Path("wiki/modules/app.md").read_text()
    assert load_knowledge_state("wiki").knowledge is not None


@pytest.mark.parametrize("change", ["missing", "generated-drift"])
def test_page_recovery_and_generated_ownership_still_run(primed, change):
    page = Path("wiki/modules/app.md")
    if change == "missing":
        page.unlink()
    else:
        page.write_text(page.read_text().replace("| `compute` |", "| `invented` |"))
    with patch.object(sync_cmd, "_extract_current_inventory", wraps=sync_cmd._extract_current_inventory) as extract:
        sync()
    if change == "missing":
        assert "| `compute` |" in page.read_text()
    else:
        assert extract.call_count == 1  # Generated drift cannot use the cache shortcut.
    assert load_knowledge_state("wiki").knowledge is not None


def test_concurrent_source_mutation_aborts_cached_run(primed, monkeypatch):
    edit(text="Pending semantic edit.")
    marker = Path("wiki/.llm-wiki-manifest.json").read_bytes()
    original = sync_analysis_cache.inventory_result
    def changing(*args):
        result = original(*args)
        Path("src/app.py").write_text("class Raced: pass\n")
        return result
    monkeypatch.setattr(sync_analysis_cache, "inventory_result", changing)
    with pytest.raises((ValueError, SystemExit)):
        sync()
    assert Path("wiki/.llm-wiki-manifest.json").read_bytes() == marker


@pytest.mark.parametrize("change", ["wiki", "provider"])
def test_concurrent_wiki_or_provider_mutation_aborts_cached_run(primed, monkeypatch, change):
    edit(text="Pending authored text.")
    marker = Path("wiki/.llm-wiki-manifest.json").read_bytes()
    original = sync_analysis_cache.inventory_result
    def changing(*args):
        result = original(*args)
        if change == "wiki":
            Path("wiki/modules/app.md").write_text("Concurrent wiki replacement\n")
        else:
            monkeypatch.setattr(sync_analysis_cache, "implementation_hash", lambda: "sha256:" + "2" * 64)
        return result
    monkeypatch.setattr(sync_analysis_cache, "inventory_result", changing)
    with pytest.raises((ValueError, SystemExit)):
        sync()
    assert Path("wiki/.llm-wiki-manifest.json").read_bytes() == marker


def test_interruption_does_not_replace_a_required_write_with_cached_success(primed, monkeypatch):
    edit(text="Retain interrupted authored edit.")
    cache = Path("cache", sync_analysis_cache.FILENAME)
    before = (cache.read_bytes(), cache.stat().st_mtime_ns)
    marker = Path("wiki/.llm-wiki-manifest.json").read_bytes()
    with monkeypatch.context() as failing:
        failing.setattr(sync_cmd, "finalize_runtime_knowledge", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("interrupted")))
        with pytest.raises(RuntimeError, match="interrupted"):
            sync()
    assert (cache.read_bytes(), cache.stat().st_mtime_ns) == before
    assert Path("wiki/.llm-wiki-manifest.json").read_bytes() == marker
    sync()
    assert Path("wiki/.llm-wiki-manifest.json").read_bytes() != marker
    assert build_report("wiki", "src", strict=True).passed


@pytest.mark.parametrize("artifact", [".llm-wiki-surface.json", ".llm-wiki-knowledge.json", ".llm-wiki-manifest.json"])
def test_corrupt_commit_cannot_authorize_analysis_reuse(primed, monkeypatch, artifact):
    Path("wiki", artifact).write_text("{}")
    hits = []
    original = sync_analysis_cache.inventory_result
    def restored(*a):
        hits.append(True)
        return original(*a)
    monkeypatch.setattr(sync_analysis_cache, "inventory_result", restored)
    try:
        sync()
    except (ValueError, SystemExit):
        pass
    assert hits == []


def test_strict_readers_still_reject_actual_source_drift(primed):
    Path("src/app.py").write_text("class Changed: pass\n")
    assert not build_report("wiki", "src", strict=True).passed
    result = subprocess.run([sys.executable, "-m", "llm_wiki_cli.cli", "ci-check",
                             "--wiki-dir", "wiki", "--src-dir", "src", "--no-report",
                             "--format", "json", "--cache-dir", "cache"], capture_output=True, text=True)
    assert result.returncode != 0
    assert not json.loads(result.stdout)["ok"]
