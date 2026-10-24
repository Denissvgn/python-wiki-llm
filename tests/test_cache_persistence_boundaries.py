"""Transported cache data retains source and native-commit boundaries."""

from __future__ import annotations

import os
import shutil
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import analysis_capture
from llm_wiki_cli.services.extraction_service import InventoryRequest, get_inventory_result
from llm_wiki_cli.services.inventory_cache import CACHE_FILENAME, InventoryCacheOptions
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.lint_service import build_report
from llm_wiki_cli.services.sync_analysis_cache import EXTENSION, FILENAME


def _inventory(source, cache, *, implementation=False, enabled=True):
    return get_inventory_result(InventoryRequest(
        src_dir=source, deep=True, include_plugins=False, parallel_jobs=1,
        cache_options=InventoryCacheOptions(enabled=enabled, cache_dir=str(cache)),
        capture_data_effect_observations=True, capture_import_observations=True,
        capture_implementation_observations=implementation,
    ))


def test_same_size_source_change_with_restored_timestamp_cannot_hit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    path = source / "app.py"
    path.write_text("class Item: pass\n", encoding="utf-8")
    cache = tmp_path / "cache"
    _inventory(source, cache)
    warm = _inventory(source, cache)
    assert warm.cache_stats is not None and warm.cache_stats.hits == 1
    original = path.stat()
    path.write_text("class Done: pass\n", encoding="utf-8")
    os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
    assert (path.stat().st_size, path.stat().st_mtime_ns) == (original.st_size, original.st_mtime_ns)
    changed = _inventory(source, cache)
    assert changed.cache_stats is not None
    assert changed.cache_stats.hits == 0 and changed.cache_stats.changed == 1
    assert changed.cache_stats.fresh_extracted == 1
    assert changed.inventory["app.py"]["classes"][0]["name"] == "Done"
    assert changed.inventory == _inventory(source, cache, enabled=False).inventory


def test_warm_inventory_does_not_skip_required_implementation_capture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("def run(value):\n    return value + 1\n", encoding="utf-8")
    cache = tmp_path / "cache"
    _inventory(source, cache)
    ordinary = _inventory(source, cache)
    assert ordinary.cache_stats is not None
    assert ordinary.cache_stats.hits == 1 and ordinary.cache_stats.fresh_extracted == 0
    qualified = _inventory(source, cache, implementation=True)
    assert qualified.cache_stats is not None
    assert qualified.cache_stats.hits == 0 and qualified.cache_stats.fresh_extracted == 1
    fresh = _inventory(source, cache, implementation=True, enabled=False)
    assert qualified.inventory == fresh.inventory
    assert qualified.implementation_observations is not None
    assert qualified.implementation_observations == fresh.implementation_observations
    assert qualified.data_effect_observations == fresh.data_effect_observations
    assert qualified.import_observations == fresh.import_observations


def test_copying_inventory_to_another_source_root_preserves_invalidation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    for source in (first, second):
        (source / "app.py").write_text("class Item: pass\n", encoding="utf-8")
    first_cache = tmp_path / "first-cache"
    second_cache = tmp_path / "second-cache"
    expected = _inventory(first, first_cache)
    second_cache.mkdir()
    shutil.copyfile(first_cache / CACHE_FILENAME, second_cache / CACHE_FILENAME)
    result = _inventory(second, second_cache)
    assert result.cache_stats is not None
    assert result.cache_stats.status == "invalid" and result.cache_stats.stale == 1
    assert result.cache_stats.hits == 0 and result.cache_stats.fresh_extracted == 1
    assert result.inventory == expected.inventory


@pytest.mark.parametrize("dimension", ["implementation", "runtime"])
def test_changed_analysis_basis_invalidates_warm_inventory(tmp_path, monkeypatch, dimension):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("class Item: pass\n", encoding="utf-8")
    cache = tmp_path / "cache"
    _inventory(source, cache)
    warm = _inventory(source, cache)
    assert warm.cache_stats is not None and warm.cache_stats.hits == 1
    if dimension == "implementation":
        monkeypatch.setattr(analysis_capture, "implementation_hash", lambda *args: "sha256:" + "f" * 64)
    else:
        # Model an unqualified runtime; this is not native execution on that runtime.
        monkeypatch.setattr(analysis_capture.platform, "python_version", lambda: "99.0.0")
    changed = _inventory(source, cache)
    assert changed.cache_stats is not None
    assert changed.cache_stats.status == "invalid" and changed.cache_stats.stale == 1
    assert changed.cache_stats.hits == 0 and changed.cache_stats.fresh_extracted == 1
    assert changed.inventory == _inventory(source, cache, enabled=False).inventory


def _edit_description(wiki, text):
    path = wiki / "modules/app.md"
    head, rest = path.read_text(encoding="utf-8").split("## Description\n", 1)
    _, tail = rest.split("\n## ", 1)
    path.write_text(head + "## Description\n\n" + text + "\n\n## " + tail, encoding="utf-8")


def _sync(wiki, cache):
    sync_cmd.run(SimpleNamespace(src_dir="src", wiki_dir=str(wiki), cache_dir=str(cache),
                                 no_plugins=True, jobs=1))


def test_restored_analysis_payload_cannot_authorize_its_own_reuse(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text(
        "class Item:\n    pass\ndef compute(value=3):\n    return value + 1\n", encoding="utf-8",
    )
    donor = tmp_path / "donor"
    receiver = tmp_path / "receiver"
    api.bootstrap_wiki("src", "donor")
    shutil.copytree(donor, receiver)  # Complete native baseline; no invented authority.
    state = load_knowledge_state(receiver)
    assert state.knowledge is not None and EXTENSION not in state.knowledge.extensions
    donor_cache = tmp_path / "donor-cache"
    _edit_description(donor, "Prime the donor's committed static analysis.")
    _sync(donor, donor_cache)
    receiver_cache = tmp_path / "receiver-cache"
    receiver_cache.mkdir()
    shutil.copyfile(donor_cache / FILENAME, receiver_cache / FILENAME)
    _edit_description(receiver, "Restored data is not its own authority.")
    capsys.readouterr()
    with patch.object(sync_cmd, "_extract_current_inventory", wraps=sync_cmd._extract_current_inventory) as fresh:
        _sync(receiver, receiver_cache)
    assert fresh.call_count == 1
    assert "Sync analysis reuse: miss (no-committed-analysis)" in capsys.readouterr().out
    assert build_report(str(receiver), "src", strict=True, include_plugins=False).passed
    assert "Restored data is not its own authority." in (receiver / "modules/app.md").read_text(encoding="utf-8")
