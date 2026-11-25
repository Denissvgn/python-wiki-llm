"""Analysis is the same whether a file was extracted now or served from the cache."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands.extract_cmd import get_inventory_result
from llm_wiki_cli.services import sync_analysis_cache
from llm_wiki_cli.services.api_contracts import build_static_api_contracts
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions, cache_representation
from llm_wiki_engine.io import write_json_atomic

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
APPLICATION = (
    "from fastapi import FastAPI\n\n"
    "def dep():\n    return 1\n\n"
    "app = FastAPI(version=dep(), title=dep(), description=dep(), debug=dep())\n"
)


def _ordered(value) -> str:
    """Serialize without sorting, so a difference in mapping order is visible."""
    return json.dumps(value, ensure_ascii=True)


def _project(tmp_path: Path) -> Path:
    source = tmp_path / "project"
    (source / "src").mkdir(parents=True)
    (source / "src" / "app.py").write_text(APPLICATION, encoding="utf-8")
    (source / "src" / "other.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    return source


def _extract(source: Path, options: InventoryCacheOptions | None):
    return get_inventory_result(
        source,
        deep=True,
        include_plugins=False,
        cache_options=options,
        capture_data_effect_observations=True,
        capture_import_observations=True,
    )


def _fresh_and_cached(source: Path, cache_dir: Path):
    fresh = _extract(source, InventoryCacheOptions(enabled=False))
    options = InventoryCacheOptions(enabled=True, cache_dir=str(cache_dir))
    _extract(source, options)
    cached = _extract(source, options)
    assert cached.cache_stats is not None and cached.cache_stats.status == "hit"
    assert cached.cache_stats.fresh_extracted == 0
    return fresh, cached


def test_cache_representation_is_what_the_cache_file_returns(tmp_path):
    entry = {
        "zeta": [{"b": 1, "a": (1, 2)}],
        "alpha": {"second": None, "first": {"y": "é", "x": 1.5}},
    }
    path = write_json_atomic(tmp_path / "cache.json", entry)

    served = json.loads(path.read_text(encoding="utf-8"))

    assert _ordered(cache_representation(entry)) == _ordered(served)
    assert list(cache_representation(entry)) == ["alpha", "zeta"]


def test_fresh_inventory_matches_cache_served_inventory_in_order(tmp_path):
    fresh, cached = _fresh_and_cached(_project(tmp_path), tmp_path / "cache")

    assert _ordered(fresh.inventory) == _ordered(cached.inventory)
    assert _ordered(fresh.data_effect_observations) == _ordered(cached.data_effect_observations)
    assert _ordered(fresh.import_observations) == _ordered(cached.import_observations)


def test_api_contract_analysis_does_not_depend_on_the_cache(tmp_path):
    fresh, cached = _fresh_and_cached(_project(tmp_path), tmp_path / "cache")

    fresh_contracts = build_static_api_contracts(fresh.inventory)
    cached_contracts = build_static_api_contracts(cached.inventory)

    unknowns = [row["field"] for row in fresh_contracts["applications"][0]["unknowns"]]
    assert len(unknowns) == 4
    assert _ordered(fresh_contracts) == _ordered(cached_contracts)


@pytest.mark.parametrize("example", ["python-basic", "fastapi-contracts", "native-knowledge"])
def test_example_project_analysis_does_not_depend_on_the_cache(tmp_path, example):
    source = tmp_path / "project"
    shutil.copytree(EXAMPLES / example, source)

    fresh, cached = _fresh_and_cached(source, tmp_path / "cache")

    assert fresh.inventory
    assert _ordered(fresh.inventory) == _ordered(cached.inventory)
    assert _ordered(build_static_api_contracts(fresh.inventory)) == _ordered(
        build_static_api_contracts(cached.inventory)
    )


def _run(monkeypatch, *arguments: str) -> None:
    monkeypatch.setattr(sys, "argv", ["llm-wiki", *arguments])
    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code in (0, None)


def test_preview_and_owning_sync_plan_the_same_analysis_commitment(tmp_path, monkeypatch):
    source = _project(tmp_path)
    (source / ".git").mkdir()
    monkeypatch.chdir(source)
    _run(monkeypatch, "bootstrap", "--src-dir", ".", "--wiki-dir", "wiki", "--api-contracts")
    with (source / "src" / "app.py").open("a", encoding="utf-8") as stream:
        stream.write("# changed\n")
    _run(monkeypatch, "sync", "--src-dir", ".", "--wiki-dir", "wiki")
    with (source / "src" / "other.py").open("a", encoding="utf-8") as stream:
        stream.write("# changed\n")

    planned: list[str] = []
    original = sync_analysis_cache.commitment

    def record(payload):
        result = original(payload)
        if result is not None:
            planned.append(result["payload_hash"])
        return result

    monkeypatch.setattr(sync_analysis_cache, "commitment", record)
    _run(monkeypatch, "sync", "--dry-run", "--src-dir", ".", "--wiki-dir", "wiki")
    preview = set(planned)
    planned.clear()
    _run(monkeypatch, "sync", "--src-dir", ".", "--wiki-dir", "wiki")

    assert preview and planned
    assert preview == set(planned)
