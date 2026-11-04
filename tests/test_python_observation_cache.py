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


def extract(src, cache, *, effects=True, imports=True, enabled=True,
            implementations=False, artifacts=None):
    return get_inventory_result(
        str(src),
        deep=True,
        cache_options=InventoryCacheOptions(enabled=enabled, cache_dir=str(cache)),
        capture_data_effect_observations=effects,
        capture_import_observations=imports,
        capture_implementation_observations=implementations,
        implementation_cache_artifacts=artifacts,
    )


def semantic_payload(result):
    return result.inventory, result.data_effect_observations, result.import_observations, result.implementation_observations


def committed_capture(root, result, *, bundles=True):
    from dataclasses import replace
    from llm_wiki_cli.services.knowledge_artifacts import build_knowledge_commit_plan, commit_knowledge_artifacts
    from llm_wiki_cli.services.knowledge_evidence import hash_json
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    from llm_wiki_cli.services.sync_analysis_cache import EXTENSION, SCHEMA
    from tests.test_knowledge_loader import _committed_state
    _, original, _ = _committed_state(root)
    state = load_knowledge_state(root)
    assert state.knowledge is not None and state.manifest_basis is not None
    commitment = {"schema_version": SCHEMA, "implementation_files": {
        path: hash_json(row) for path, row in result.implementation_observations["files"].items()}}
    if bundles:
        commitment["extraction_files"] = result.extraction_cache_hashes
    knowledge = replace(state.knowledge, extensions={**state.knowledge.extensions, EXTENSION: commitment})
    plan = build_knowledge_commit_plan(root, surface_index_bytes=original.surface_index.content,
                                     knowledge_index=knowledge, manifest=state.manifest_basis,
                                     prior=state.validated_artifacts)
    commit_knowledge_artifacts(plan)
    return load_knowledge_state(root).validated_artifacts


def test_implementation_cache_requires_authenticated_capture_then_elides_parse(source_case):
    src, cache, parsed = source_case
    first = extract(src, cache, implementations=True)
    parsed.clear()
    extract(src, cache, implementations=True)
    assert sorted(parsed) == ["a.py", "b.py"]  # A writable cache cannot authorize evidence.
    artifacts = committed_capture(src.parent / "authority", first)
    parsed.clear()
    before = (cache / CACHE_FILENAME).stat().st_mtime_ns
    warm = extract(src, cache, implementations=True, artifacts=artifacts)
    assert parsed == []
    assert semantic_payload(warm) == semantic_payload(first)
    assert warm.cache_stats.hits == 2
    assert (cache / CACHE_FILENAME).stat().st_mtime_ns == before


@pytest.mark.parametrize("change", ["source", "executable", "producer", "missing", "coordinate"])
def test_implementation_cache_invalidates_only_affected_file(source_case, change):
    src, cache, parsed = source_case
    first = extract(src, cache, implementations=True)
    artifacts = committed_capture(src.parent / "authority", first)
    if change == "source":
        (src / "a.py").write_text("def save(value):\n    return value\n")
    else:
        path = cache / CACHE_FILENAME
        content = json.loads(path.read_text())
        row = content["files"]["a.py"]["python_implementation"]
        if change == "missing":
            del content["files"]["a.py"]["python_implementation"]
        elif change == "executable":
            row["observations"][0]["evidence"]["executable_hash"] = "sha256:" + "0" * 64
        elif change == "producer":
            row["producer"]["analysis_compatibility_hash"] = "sha256:" + "0" * 64
        else:
            row["observations"][0]["evidence"]["coordinate"]["source_path"] = "b.py"
        path.write_text(json.dumps(content))
    parsed.clear()
    incremental = extract(src, cache, implementations=True, artifacts=artifacts)
    assert parsed == ["a.py"]
    assert incremental.cache_stats.hits == 1
    assert semantic_payload(incremental) == semantic_payload(extract(src, cache, implementations=True, enabled=False))


def test_replaced_artifacts_cannot_authorize_cached_implementation(source_case):
    from dataclasses import replace
    src, cache, parsed = source_case
    first = extract(src, cache, implementations=True)
    artifacts = committed_capture(src.parent / "authority", first)
    with pytest.raises(TypeError, match="not issued by the validator"):
        extract(src, cache, implementations=True, artifacts=replace(artifacts))


@pytest.mark.parametrize("field", ["inventory", "imports", "effects"])
def test_committed_capture_authenticates_entire_raw_extraction_bundle(source_case, field):
    src, cache, parsed = source_case
    first = extract(src, cache, implementations=True)
    artifacts = committed_capture(src.parent / "authority", first)
    path = cache / CACHE_FILENAME
    content = json.loads(path.read_text())
    entry = content["files"]["a.py"]
    if field == "inventory":
        entry["inventory"]["functions"][0]["docstring"] = "Invented from writable cache"
    elif field == "imports":
        entry["python_observations"]["imports"]["observations"][0]["line"] += 10
    else:
        entry["python_observations"]["data_effects"]["callables"][0]["line"] += 10
    path.write_text(json.dumps(content))
    parsed.clear()
    actual = extract(src, cache, implementations=True, artifacts=artifacts)
    assert parsed == ["a.py"]
    assert actual.cache_stats.hits == 1
    assert semantic_payload(actual) == semantic_payload(extract(src, cache, implementations=True, enabled=False))


def test_legacy_implementation_only_commitment_cannot_authorize_bundle(source_case):
    src, cache, parsed = source_case
    first = extract(src, cache, implementations=True)
    artifacts = committed_capture(src.parent / "authority", first, bundles=False)
    parsed.clear()
    actual = extract(src, cache, implementations=True, artifacts=artifacts)
    assert sorted(parsed) == ["a.py", "b.py"]
    assert actual.cache_stats.hits == 0


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
