"""Implementation read qualification stays independent of structural freshness."""

from __future__ import annotations

import ast
import json
from dataclasses import replace
from importlib import import_module
from types import SimpleNamespace

import pytest

from llm_wiki_cli.services import context_packet, context_service
from llm_wiki_cli.services import python_implementation
from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.services import analysis_compatibility
from llm_wiki_cli.services.analysis_capture import capture_analysis
from llm_wiki_cli.services.knowledge_consumption import (
    KnowledgeReadMode,
    attach_implementation_read_view,
    build_knowledge_read_view,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_freshness import LiveKnowledgeEvaluation
from llm_wiki_cli.services.documentation_query_builder import (
    build_live_documentation_query_service,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_loader import _committed_state


def _loaded(tmp_path):
    _committed_state(tmp_path)
    return load_knowledge_state(tmp_path)


def _modern_loaded(tmp_path):
    loaded = _loaded(tmp_path)
    assert loaded.knowledge is not None
    module = next(
        concept
        for concept in loaded.knowledge.concepts
        if concept.document.page_kind.value == "modules"
    )
    assert module.facets.structure.basis is not None
    path = module.facets.structure.basis.source_path
    assert path is not None
    captured_analysis = capture_analysis(EXTRACTOR_REGISTRY, languages={"python"})
    analysis_hash = python_implementation.analysis_identity(captured_analysis)
    assert analysis_hash is not None
    original_producer = loaded.knowledge.bundle.producer

    def with_analysis(component):
        inputs = captured_analysis[component.component_id]
        metadata = analysis_compatibility.make_record(
            component.component_id,
            "structural-observations/v1",
            inputs["implementation"],
            component.configuration_hash,
            inputs["runtime"],
            inputs["provenance"],
        )
        return replace(
            component,
            configuration_hash=analysis_compatibility.configuration_commitment(
                metadata
            ),
            extensions={analysis_compatibility.EXTENSION: metadata},
        )

    producer = replace(
        original_producer,
        tool=with_analysis(original_producer.tool),
        extractors=tuple(with_analysis(c) for c in original_producer.extractors),
    )
    source = "class Batch:\n    def cap(self, values):\n        return values[:3]\n"
    captured = python_implementation.capture(
        ast.parse(source),
        source.encode(),
        path,
        configured=python_implementation.producer(analysis_hash),
        parsed_source=source,
    )
    primary = next(
        row["evidence"]
        for row in captured["observations"]
        if row["evidence"]["scope"] == "module"
    )
    modern = replace(module, extensions={"llm-wiki/implementation": primary})
    knowledge = replace(
        loaded.knowledge,
        bundle=replace(loaded.knowledge.bundle, producer=producer),
        concepts=tuple(modern if c is module else c for c in loaded.knowledge.concepts),
    )
    return replace(loaded, knowledge=knowledge, validated_artifacts=None)


def test_snapshot_implementation_ignores_supplied_live_capture(tmp_path, monkeypatch):
    implementation_evidence = import_module(
        "llm_wiki_cli.services.implementation_evidence"
    )
    loaded = _modern_loaded(tmp_path)
    assert loaded.knowledge is not None
    live = replace(
        _live_evaluation(loaded.knowledge),
        implementation_observations={"untrusted-live-capture": True},
    )
    calls = []
    real_compare = implementation_evidence.compare_knowledge_implementation

    def compare(knowledge, observations, **options):
        calls.append((observations, options))
        return real_compare(knowledge, observations, **options)

    monkeypatch.setattr(
        implementation_evidence, "compare_knowledge_implementation", compare
    )
    view = build_knowledge_read_view(loaded, live_evaluation=live, snapshot_only=True)
    assert calls == [(None, {"analysis_scope": "snapshot"})]
    assert view.mode is KnowledgeReadMode.SNAPSHOT_ONLY
    assert view.freshness is None
    assert view.implementation_report is not None
    assert all(
        result.state == "unavailable" and not result.live_comparison_performed
        for result in view.implementation_report.by_locator.values()
    )


def test_missing_legacy_evidence_never_becomes_executable_unchanged(tmp_path):
    loaded = _loaded(tmp_path)
    assert loaded.knowledge is not None
    live = replace(
        _live_evaluation(loaded.knowledge),
        implementation_observations=python_implementation.envelope({}),
    )
    view = build_knowledge_read_view(loaded, live_evaluation=live)
    assert view.freshness is not None
    assert view.implementation_report is not None
    assert all(
        result.state == "unavailable"
        for result in view.implementation_report.by_locator.values()
    )


def test_selected_attachment_preserves_snapshot_scope_and_never_reparses(
    tmp_path, monkeypatch
):
    implementation_evidence = import_module(
        "llm_wiki_cli.services.implementation_evidence"
    )
    loaded = _modern_loaded(tmp_path)
    snapshot = build_knowledge_read_view(loaded, snapshot_only=True)
    calls = []
    real_compare = implementation_evidence.compare_knowledge_implementation

    def compare(knowledge, observations, **options):
        calls.append(options)
        return real_compare(knowledge, observations, **options)

    def no_parse(*args, **kwargs):
        raise AssertionError(
            "read-view attachment must reuse captured implementation evidence"
        )

    monkeypatch.setattr(
        implementation_evidence, "compare_knowledge_implementation", compare
    )
    monkeypatch.setattr(ast, "parse", no_parse)
    selected = attach_implementation_read_view(
        snapshot,
        implementation_observations=None,
        analysis_scope="selected-source",
        captured_paths=("selected.py",),
        source_content_hashes={},
    )
    assert calls[0]["analysis_scope"] == "selected-source"
    assert calls[0]["captured_paths"] == ("selected.py",)
    assert calls[0]["missing_source_paths"] == ()
    assert selected.mode is KnowledgeReadMode.SNAPSHOT_ONLY
    assert selected.freshness is None
    assert selected.knowledge is snapshot.knowledge
    assert selected.counts is snapshot.counts
    assert selected.manifest_basis is snapshot.manifest_basis
    assert selected.validated_artifacts is snapshot.validated_artifacts


def test_capture_metadata_is_opt_in_and_not_in_inventory_payload(monkeypatch):
    calls = []
    inventory = {"policy.py": {"language": "python"}}
    result = SimpleNamespace(
        failed=False, inventory=inventory, implementation_observations={"private": True}
    )

    def collect(*args, **options):
        calls.append(options)
        return result

    monkeypatch.setattr(context_service, "get_inventory_result", collect)
    assert context_service.get_inventory(".") is inventory
    assert "capture_implementation_observations" not in calls[-1]
    assert (
        context_service.get_inventory(".", capture_implementation_observations=True)
        is inventory
    )
    assert calls[-1]["capture_implementation_observations"] is True
    assert "implementation_observations" not in inventory


@pytest.mark.parametrize("enabled", [False, True])
def test_captured_context_keeps_sidecar_private_and_read_only(
    tmp_path, monkeypatch, enabled
):
    root = tmp_path / "project"
    root.mkdir()
    (root / "policy.py").write_text(
        "class Batch:\n    def cap(self, values):\n        return values[:3]\n"
    )
    wiki = root / "docs" / "llm_wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_text("# Project\n")
    before = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    monkeypatch.chdir(root)
    captured = context_packet.capture_context_read(
        ".", "docs/llm_wiki", capture_implementation_observations=enabled
    )
    assert (
        captured.inventory_result.implementation_observations is not None
    ) is enabled
    assert all(
        "implementation_observations" not in record
        for record in captured.inventory.values()
    )
    after = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert after == before


@pytest.mark.parametrize("value", [1, "true", None])
def test_invalid_capture_flag_is_rejected_before_io(value):
    with pytest.raises(TypeError, match="capture_implementation_observations"):
        context_service.get_inventory(".", capture_implementation_observations=value)
    with pytest.raises(TypeError, match="capture_implementation_observations"):
        context_packet.capture_context_read(
            ".", ".", capture_implementation_observations=value
        )


def test_context_summary_has_no_raw_commitments_and_rejects_injected_records(tmp_path):
    implementation_evidence = import_module(
        "llm_wiki_cli.services.implementation_evidence"
    )
    view = build_knowledge_read_view(_modern_loaded(tmp_path), snapshot_only=True)
    assert view.implementation_report is not None
    comparison = next(iter(view.implementation_report.by_locator.values()))
    summary = implementation_evidence.compact_implementation_summary(comparison)
    assert not {"coordinate", "recorded", "live"} & set(summary)
    assert not any(key.endswith("_hash") for key in summary)
    context_packet._validate_implementation_summary(summary, "implementation")
    bad = {**summary, "recorded": {"source_hash": "sha256:" + "a" * 64}}
    with pytest.raises(context_packet.ContextPacketMalformedError):
        context_packet._validate_implementation_summary(bad, "implementation")


def test_legacy_snapshot_and_default_live_view_do_not_add_an_optional_report(tmp_path):
    loaded = _loaded(tmp_path)
    assert loaded.knowledge is not None
    assert (
        build_knowledge_read_view(loaded, snapshot_only=True).implementation_report
        is None
    )
    assert (
        build_knowledge_read_view(
            loaded, live_evaluation=_live_evaluation(loaded.knowledge)
        ).implementation_report
        is None
    )


def test_selected_syntax_verdict_does_not_upgrade_structural_snapshot(tmp_path):
    loaded = _modern_loaded(tmp_path)
    assert loaded.knowledge is not None
    module = next(
        c
        for c in loaded.knowledge.concepts
        if "llm-wiki/implementation" in c.extensions
    )
    recorded = module.extensions["llm-wiki/implementation"]
    path = recorded["coordinate"]["source_path"]
    source = "class Batch:\n    def cap(self, values):\n        return values[:2]\n"
    capture = python_implementation.capture(
        ast.parse(source),
        source.encode(),
        path,
        configured=python_implementation.producer(
            recorded["producer"]["analysis_compatibility_hash"]
        ),
        parsed_source=source,
    )
    view = attach_implementation_read_view(
        build_knowledge_read_view(loaded, snapshot_only=True),
        implementation_observations=python_implementation.envelope({path: capture}),
        analysis_scope="selected-source",
        captured_paths=(path,),
        source_content_hashes={path: capture["source_hash"]},
        analysis_compatibility_hash=recorded["producer"]["analysis_compatibility_hash"],
    )
    assert view.implementation_report is not None
    comparison = view.implementation_report.by_locator[module.locator]
    assert comparison.state == "changed"
    assert comparison.analysis_scope == "selected-source"
    assert comparison.live_comparison_performed
    assert view.freshness is None
    assert view.mode is KnowledgeReadMode.SNAPSHOT_ONLY


def test_original_positional_comparison_policy_is_preserved(tmp_path):
    loaded = _loaded(tmp_path)
    assert loaded.knowledge is not None
    live = _live_evaluation(loaded.knowledge)
    original_call = LiveKnowledgeEvaluation(
        live.schema_version,
        live.producer,
        live.generation_options_hash,
        live.source_content_hashes,
        live.missing_source_paths,
        live.concept_bases,
        "exact-v1",
    )
    assert original_call.comparison_policy == "exact-v1"
    assert original_call.implementation_observations is None


@pytest.mark.parametrize("ignored", [False, True])
def test_selected_builder_distinguishes_confirmed_missing_and_existing_ignored_source(
    tmp_path, ignored
):
    wiki = tmp_path / "wiki"
    loaded = _modern_loaded(wiki)
    assert loaded.knowledge is not None
    module = next(
        c
        for c in loaded.knowledge.concepts
        if "llm-wiki/implementation" in c.extensions
    )
    path = module.extensions["llm-wiki/implementation"]["coordinate"]["source_path"]
    source = tmp_path / "source"
    source.mkdir()
    if ignored:
        target = source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("class Batch: pass\n")
        (source / ".gitignore").write_text(path + "\n")
    service = build_live_documentation_query_service(
        source_root=source,
        wiki_root=wiki,
        limit=10,
        read_only=True,
        include_plugins=False,
        paths=[path],
        source_snapshot_builder=lambda root, **options: build_source_snapshot(
            root, respect_ignores=True, coherent=True, **options
        ),
        snapshot_view_loader=lambda *args, **kwargs: build_knowledge_read_view(
            loaded, snapshot_only=True
        ),
    )
    view = service.knowledge_view
    assert view is not None and view.implementation_report is not None
    comparison = view.implementation_report.by_locator[module.locator]
    assert comparison.state == "unavailable"
    assert comparison.reason == ("source-not-captured" if ignored else "missing-source")
    assert view.mode is KnowledgeReadMode.SNAPSHOT_ONLY
    assert view.freshness is None


def test_missing_confirmation_does_not_follow_symlink_parent(tmp_path):
    root, external = tmp_path / "source", tmp_path / "external"
    root.mkdir()
    external.mkdir()
    (root / "link").symlink_to(external, target_is_directory=True)
    snapshot = build_source_snapshot(
        root, only_files=["link/missing.py"], coherent=True, respect_ignores=True
    )
    assert (
        context_packet.confirmed_missing_source_paths(snapshot, ["link/missing.py"])
        == frozenset()
    )


def test_missing_confirmation_rejects_directory_mutation_during_absence_check(
    tmp_path, monkeypatch
):
    root = tmp_path / "source"
    root.mkdir()
    snapshot = build_source_snapshot(
        root, only_files=["missing.py"], coherent=True, respect_ignores=True
    )
    real_stat = context_packet.os.stat

    def concurrent_creation(path, *args, **kwargs):
        if path == "missing.py" and "dir_fd" in kwargs:
            (root / "missing.py").write_text("VALUE=1\n")
            raise FileNotFoundError(path)
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(context_packet.os, "stat", concurrent_creation)
    with pytest.raises(context_packet.ContextPacketSourceMutationError):
        context_packet.confirmed_missing_source_paths(snapshot, ["missing.py"])


def test_missing_confirmation_respects_configured_selection_and_ignored_absence(
    tmp_path,
):
    root = tmp_path / "source"
    root.mkdir()
    (root / "allowed.py").write_text("VALUE=1\n")
    (root / "private.py").write_text("VALUE=2\n")
    profile = root / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": "llm-wiki-source-selection/v1",
                "include": ["allowed.py"],
                "exclude": [],
            }
        )
    )
    snapshot = build_source_snapshot(
        root, only_files=["private.py"], coherent=True, respect_ignores=True
    )
    assert "private.py" not in snapshot.captured_content_hashes
    assert (
        context_packet.confirmed_missing_source_paths(
            snapshot, ["private.py", "excluded-missing.py"]
        )
        == frozenset()
    )
    other = tmp_path / "ignored"
    other.mkdir()
    (other / ".gitignore").write_text("missing.py\n")
    ignored = build_source_snapshot(
        other, only_files=["missing.py"], coherent=True, respect_ignores=True
    )
    assert (
        context_packet.confirmed_missing_source_paths(ignored, ["missing.py"])
        == frozenset()
    )
