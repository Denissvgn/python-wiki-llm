"""Cached Python observations equal fresh extraction across source changes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_wiki_cli.extractors import python_extractor
from llm_wiki_cli.services.extraction_service import get_inventory_result
from llm_wiki_cli.services.inventory_cache import CACHE_FILENAME, InventoryCacheOptions


@pytest.fixture
def source_case(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text(
        "from pathlib import Path\ndef save(value):\n    Path('out').write_text(value)\n",
        encoding="utf-8",
    )
    (src / "b.py").write_text(
        "from a import save\ndef _run():\n    return save('value')\n", encoding="utf-8"
    )
    parsed = []
    original = python_extractor.ast.parse

    def observe(source, filename="<unknown>", *args, **kwargs):
        if str(filename).endswith(".py") and Path(filename).parent == src:
            parsed.append(Path(filename).name)
        return original(source, filename, *args, **kwargs)

    monkeypatch.setattr(python_extractor.ast, "parse", observe)
    return src, tmp_path / "cache", parsed


def extract(src, cache, *, effects=True, imports=True, enabled=True):
    return get_inventory_result(
        str(src),
        deep=True,
        cache_options=InventoryCacheOptions(enabled=enabled, cache_dir=str(cache)),
        capture_data_effect_observations=effects,
        capture_import_observations=imports,
    )


def semantic_payload(result):
    return result.inventory, result.data_effect_observations, result.import_observations


def test_warm_sidecars_elide_python_and_keep_exact_observations(source_case):
    src, cache, parsed = source_case
    first = extract(src, cache)
    assert sorted(parsed) == ["a.py", "b.py"]
    parsed.clear()
    warm = extract(src, cache)
    assert parsed == []
    assert warm.cache_stats is not None
    assert warm.cache_stats.hits == 2
    assert "python" in warm.extraction_job_plan.cache_elided_plan_ids
    assert semantic_payload(warm) == semantic_payload(first)


@pytest.mark.parametrize("change", ["edit", "delete", "rename"])
def test_changed_source_observations_match_full_extraction(source_case, change):
    src, cache, parsed = source_case
    extract(src, cache)
    if change == "edit":
        (src / "a.py").write_text(
            "def save(value):\n    return value\n", encoding="utf-8"
        )
        expected = ["a.py"]
    elif change == "delete":
        (src / "a.py").unlink()
        expected = []
    else:
        (src / "a.py").rename(src / "renamed.py")
        expected = ["renamed.py"]
    parsed.clear()
    incremental = extract(src, cache)
    assert parsed == expected
    oracle = extract(src, cache, enabled=False)
    assert semantic_payload(incremental) == semantic_payload(oracle)
    stored = json.loads((cache / CACHE_FILENAME).read_text())
    if change != "edit":
        assert "a.py" not in stored["files"]


def test_missing_capabilities_reextract_then_allow_warm_reuse(source_case):
    src, cache, parsed = source_case
    inventory_only = extract(src, cache, effects=False, imports=False)
    assert inventory_only.data_effect_observations is None
    assert inventory_only.import_observations is None
    parsed.clear()
    complete = extract(src, cache)
    assert sorted(parsed) == ["a.py", "b.py"]
    parsed.clear()
    assert semantic_payload(extract(src, cache)) == semantic_payload(complete)
    assert parsed == []


@pytest.mark.parametrize(
    "corruption",
    ["path", "schema", "coverage", "missing", "negative", "import_identity"],
)
def test_bad_sidecar_reextracts_only_its_owner(source_case, corruption):
    src, cache, parsed = source_case
    expected = extract(src, cache)
    path = cache / CACHE_FILENAME
    data = json.loads(path.read_text())
    sidecars = data["files"]["a.py"]["python_observations"]
    if corruption == "path":
        sidecars["imports"]["observations"][0]["source_path"] = "../outside.py"
    elif corruption == "schema":
        sidecars["data_effects"]["schema_version"] = "future"
    elif corruption == "coverage":
        sidecars["imports"]["coverage"]["omitted"] = 1
    elif corruption == "missing":
        del sidecars["imports"]
    elif corruption == "negative":
        sidecars["data_effects"]["callables"][0]["line"] = -1
    else:
        sidecars["imports"]["observations"][0]["module"] = "forged"
    path.write_text(json.dumps(data))
    parsed.clear()
    actual = extract(src, cache)
    assert parsed == ["a.py"]
    assert actual.cache_stats is not None
    assert actual.cache_stats.hits == 1
    assert semantic_payload(actual) == semantic_payload(expected)


def test_empty_and_private_files_keep_capability_distinction(source_case):
    src, cache, parsed = source_case
    (src / "empty.py").write_text("# No declarations\n", encoding="utf-8")
    first = extract(src, cache)
    parsed.clear()
    warm = extract(src, cache)
    assert parsed == []
    assert semantic_payload(warm) == semantic_payload(first)
    stored = json.loads((cache / CACHE_FILENAME).read_text())
    assert (
        stored["files"]["empty.py"]["python_observations"]["data_effects"]["callables"]
        == []
    )
    assert "b.py" in warm.inventory


def test_inventory_v2_is_discarded(source_case):
    src, cache, parsed = source_case
    first = extract(src, cache)
    path = cache / CACHE_FILENAME
    data = json.loads(path.read_text())
    data.update(schema="inventory-v2", version=2)
    path.write_text(json.dumps(data))
    parsed.clear()
    rebuilt = extract(src, cache)
    assert sorted(parsed) == ["a.py", "b.py"]
    assert semantic_payload(rebuilt) == semantic_payload(first)


def test_global_class_inference_recomputed_from_raw_cached_files(source_case):
    src, cache, parsed = source_case
    (src / "a.py").write_text(
        "from pydantic import BaseModel\nclass Base(BaseModel):\n    pass\n",
        encoding="utf-8",
    )
    (src / "b.py").write_text(
        "from a import Base\nclass Child(Base):\n    pass\n", encoding="utf-8"
    )
    first = extract(src, cache)
    assert first.inventory["b.py"]["classes"][0]["model_kind"] == "pydantic"
    (src / "a.py").write_text("class Base:\n    pass\n", encoding="utf-8")
    parsed.clear()
    incremental = extract(src, cache)
    assert parsed == ["a.py"]
    assert "model_kind" not in incremental.inventory["b.py"]["classes"][0]
    assert semantic_payload(incremental) == semantic_payload(
        extract(src, cache, enabled=False)
    )
