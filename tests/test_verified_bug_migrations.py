"""Artifact transitions for the verified provenance and structural fixes."""

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services import (
    extraction_service,
    knowledge_orchestration,
    knowledge_reuse,
    sync_analysis_cache,
)
from llm_wiki_cli.services.doctor_service import build_doctor_report
from llm_wiki_cli.services.extractor_helpers import (
    ENV_CACHE_DIR,
    resolve_helper_cache_root,
    typescript_dependencies_ready,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_index import knowledge_index_to_payload
from llm_wiki_cli.services.knowledge_evidence import is_valid_sha256


def _bootstrap(**options):
    bootstrap_cmd.run(
        SimpleNamespace(
            **{
                "src_dir": "src",
                "wiki_dir": "wiki",
                "depth": "full",
                "overwrite": False,
                "skip_workflows": True,
                **options,
            }
        )
    )


def _sync(**options):
    sync_cmd.run(SimpleNamespace(src_dir="src", wiki_dir="wiki", **options))


def _artifacts():
    return {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in Path("wiki").glob(".llm-wiki-*.json")
    }


def _semantic_artifacts():
    """Keep all semantic/review facts while isolating the two operational hints."""
    state = load_knowledge_state("wiki")
    assert state.knowledge is not None and state.manifest_basis is not None
    assert state.validated_artifacts is not None
    knowledge = json.loads(json.dumps(knowledge_index_to_payload(state.knowledge)))
    manifest = state.manifest_basis.to_payload()
    hints = {
        key: knowledge["extensions"].pop(key)
        for key in (knowledge_reuse.REUSE_EXTENSION_KEY, sync_analysis_cache.EXTENSION)
        if key in knowledge["extensions"]
    }
    generation_inputs = manifest["generation_inputs"]
    artifact_hashes = manifest["artifact_hashes"]
    assert isinstance(generation_inputs, dict) and isinstance(artifact_hashes, dict)
    assert generation_inputs.pop(knowledge_reuse.REUSE_INPUT_KEY, None) == hints.get(
        knowledge_reuse.REUSE_EXTENSION_KEY
    )
    assert artifact_hashes.pop("knowledge_index_hash") == state.validated_artifacts.knowledge_index_hash
    markdown = {
        path.relative_to("wiki").as_posix(): path.read_bytes()
        for path in Path("wiki").rglob("*.md")
    }
    semantic_json = json.dumps([knowledge, manifest], sort_keys=True, separators=(",", ":"), allow_nan=False)
    return (semantic_json, markdown), hints


@pytest.mark.skipif(
    not typescript_dependencies_ready(Path(__file__).parents[1]),
    reason="requires an already prepared TypeScript helper",
)
@pytest.mark.parametrize("legacy", [False, True])
def test_javascript_health_refresh_and_first_sync_converge(
    tmp_path, monkeypatch, legacy
):
    helper_root = resolve_helper_cache_root(Path(__file__).resolve().parents[1])
    assert helper_root is not None
    # Consume the validated prepared cache at its bound location.
    cache_dir = helper_root.parent
    monkeypatch.setenv(ENV_CACHE_DIR, str(cache_dir))
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/main.js").write_text(
        "export function answer() { return 42; }\n", encoding="utf-8"
    )
    original = knowledge_orchestration._producer_evidence

    def old_producer(*args, **kwargs):
        refs, complete, extractors, plugins = original(*args, **kwargs)
        return (
            refs,
            complete,
            tuple(
                replace(component, configuration=None, extensions={})
                if component.component_id == "llm-wiki/extractor/javascript"
                else component
                for component in extractors
            ),
            plugins,
        )

    with monkeypatch.context() as historical:
        if legacy:
            historical.setattr(
                knowledge_orchestration, "_producer_evidence", old_producer
            )
            historical.setattr(
                knowledge_reuse, "implementation_hash", lambda: "sha256:" + "0" * 64
            )
        _bootstrap()

    if legacy:
        assert build_doctor_report("wiki", "src", strict=True).exit_code == 2
        _sync(rebuild_knowledge=True)
    assert build_doctor_report("wiki", "src", strict=True).exit_code == 0
    before = _artifacts()
    semantic_before, hints_before = _semantic_artifacts()
    _sync()
    assert _artifacts() == before
    assert _semantic_artifacts() == (semantic_before, hints_before)
    _sync(rebuild_knowledge=True)
    primed = _artifacts()
    semantic_after, hints_after = _semantic_artifacts()
    assert semantic_after == semantic_before
    assert set(hints_after) == {knowledge_reuse.REUSE_EXTENSION_KEY, sync_analysis_cache.EXTENSION}
    knowledge_reuse.validate_reuse_commitment(hints_after[knowledge_reuse.REUSE_EXTENSION_KEY])
    capture = hints_after[sync_analysis_cache.EXTENSION]
    assert capture["schema_version"] == sync_analysis_cache.SCHEMA
    assert capture["coverage"] == "full"
    assert set(capture) == {
        "schema_version", "coverage", "input_hash", "payload_hash", "graph_concepts_hash",
        "extraction_files", "implementation_files",
    }
    assert all(is_valid_sha256(capture[key]) for key in ("input_hash", "payload_hash", "graph_concepts_hash"))
    if legacy:
        # This branch was primed above when its incompatible producer was repaired.
        assert primed == before
        assert hints_after == hints_before
    else:
        # An explicit first rebuild may seed hints; ordinary sync did not do so.
        assert hints_before == {}
        assert primed.keys() == before.keys()
        changed = {name for name in before if primed[name][0] != before[name][0]}
        assert changed == {".llm-wiki-knowledge.json", ".llm-wiki-manifest.json"}
        assert all(primed[name] == before[name] for name in before.keys() - changed)
    _sync(rebuild_knowledge=True)
    assert _artifacts() == primed
    _sync()
    assert _artifacts() == primed
    assert _semantic_artifacts() == (semantic_after, hints_after)


@pytest.mark.parametrize("authored", [False, True])
def test_obsolete_annotation_workflow_retirement_preserves_authored_behavior(
    tmp_path, monkeypatch, authored
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    for name in ("a", "b", "c"):
        Path(f"src/{name}.py").write_text(
            f"class {name.upper()}: pass\n", encoding="utf-8"
        )
    Path("src/app.py").write_text(
        "from a import A\nfrom b import B\nfrom c import C\n"
        "def legacy(a: A, b: B) -> C:\n    return a\n",
        encoding="utf-8",
    )

    def annotation_chain(fn, *args):
        if fn["name"] == "legacy":
            return {"a.py", "b.py", "c.py"}, ["a.A", "b.B", "c.C"], []
        return set(), [], []

    with monkeypatch.context() as historical:
        historical.setattr(extraction_service, "_workflow_call_chain", annotation_chain)
        historical.setattr(
            knowledge_reuse, "implementation_hash", lambda: "sha256:" + "0" * 64
        )
        _bootstrap(skip_workflows=False)
    page = Path("wiki/workflows/legacy.md")
    assert page.is_file()
    if authored:
        page.write_text(
            sync_cmd._replace_section_body(
                page.read_text(encoding="utf-8"),
                "Behavior",
                "Keep this operator-authored explanation.",
            ),
            encoding="utf-8",
        )
        before = {
            path: path.read_bytes()
            for path in Path("wiki").rglob("*")
            if path.is_file()
        }
        with pytest.raises(SystemExit) as error:
            _sync()
        assert error.value.code == 2
        assert {
            path: path.read_bytes()
            for path in Path("wiki").rglob("*")
            if path.is_file()
        } == before
    else:
        _sync()
        assert not page.exists()
        assert "workflows/legacy" not in Path("wiki/index.md").read_text(
            encoding="utf-8"
        )
        assert "workflows/legacy" not in Path("wiki/.llm-wiki-surface.json").read_text(
            encoding="utf-8"
        )
        before = _artifacts()
        _sync()
        assert _artifacts() == before


def test_typed_dict_presence_refreshes_pages_and_structural_observations(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    source = Path("src/models.py")
    source.write_text(
        "from typing import TypedDict\nclass Result(TypedDict, total=False):\n    selection: str\n",
        encoding="utf-8",
    )
    _bootstrap()
    page = Path("wiki/entities/Result.md")
    assert "| `selection` | `str` | *optional* |" in page.read_text(encoding="utf-8")

    def basis():
        state = load_knowledge_state("wiki")
        assert state.knowledge is not None
        concept = next(
            c
            for c in state.knowledge.concepts
            if c.locator == "llm-wiki://entities/Result"
        )
        assert concept.facets.structure.basis is not None
        return concept.facets.structure.basis.concept_observation_hash

    previous = basis()
    source.write_text(
        source.read_text(encoding="utf-8").replace("total=False", "total=True"),
        encoding="utf-8",
    )
    _sync(force=True)
    assert "| `selection` | `str` | *required* |" in page.read_text(encoding="utf-8")
    assert basis() != previous
    before = _artifacts()
    _sync()
    assert _artifacts() == before
