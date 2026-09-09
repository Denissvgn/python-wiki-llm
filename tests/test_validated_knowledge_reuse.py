"""Validated snapshots are immutable, command-scoped, and never a parser bypass."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from llm_wiki_cli.services import (
    knowledge_artifacts,
    knowledge_freshness,
    knowledge_index,
    knowledge_orchestration,
)
from llm_wiki_cli.services.immutable import FrozenDict
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.test_knowledge_generation import _runtime_input_case
from tests.test_knowledge_loader import _committed_state


def test_artifact_validation_parses_model_once_and_keeps_canonical_bytes(tmp_path):
    _committed_state(tmp_path)
    with patch.object(
        knowledge_index,
        "parse_knowledge_index",
        wraps=knowledge_index.parse_knowledge_index,
    ) as parse:
        loaded = load_knowledge_state(tmp_path)
    assert parse.call_count == 1
    assert loaded.validated_artifacts is not None
    surface, knowledge = knowledge_artifacts.validated_artifact_bytes(
        loaded.validated_artifacts
    )
    assert knowledge == (tmp_path / ".llm-wiki-knowledge.json").read_bytes()
    assert surface == (tmp_path / ".llm-wiki-surface.json").read_bytes()


def test_loaded_freshness_reuses_model_but_public_inputs_still_validate(tmp_path):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    with patch.object(
        knowledge_freshness,
        "parse_knowledge_index",
        wraps=knowledge_freshness.parse_knowledge_index,
    ) as parse:
        fast = build_knowledge_read_view(loaded)
        assert parse.call_count == 0
        full = knowledge_freshness.evaluate_knowledge_freshness(loaded.knowledge)
        assert parse.call_count == 1
    assert fast.freshness == full
    assert loaded.knowledge is not None
    untrusted = replace(
        loaded, knowledge=replace(loaded.knowledge, schema_version="invalid")
    )
    with pytest.raises(knowledge_freshness.KnowledgeFreshnessError):
        build_knowledge_read_view(untrusted)


def test_nested_model_and_surface_mutations_are_rejected(tmp_path):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    assert loaded.surface is not None
    with pytest.raises(TypeError, match="immutable"):
        # Bypass static write restrictions to exercise runtime immutability.
        cast(Any, loaded.knowledge.extensions)["example.invalid/changed"] = True
    with pytest.raises(TypeError, match="immutable"):
        loaded.surface["pages"].append({})
    with pytest.raises(TypeError, match="immutable"):
        loaded.surface["pages"][0]["title"] = "changed"
    detached = deepcopy(loaded.surface)
    assert detached is not None
    detached["pages"][0]["title"] = "changed"
    assert detached != loaded.surface


def test_replaced_and_manual_artifact_objects_have_no_validation_authority(tmp_path):
    _committed_state(tmp_path)
    issued = load_knowledge_state(tmp_path).validated_artifacts
    assert issued is not None
    for forged in (
        replace(issued),
        replace(issued, knowledge_index_hash="sha256:forged"),
        deepcopy(issued),
    ):
        with pytest.raises(TypeError, match="validator|replaced"):
            knowledge_artifacts.validated_artifact_bytes(forged)
        with pytest.raises(knowledge_freshness.KnowledgeFreshnessError):
            knowledge_freshness.evaluate_knowledge_freshness(forged)


def test_prior_properties_share_one_capture_without_reading_again(
    tmp_path, monkeypatch
):
    _committed_state(tmp_path)
    manifest = SyncManifest.load(tmp_path)
    with patch.object(
        knowledge_orchestration,
        "validate_knowledge_artifacts",
        wraps=knowledge_orchestration.validate_knowledge_artifacts,
    ) as validate:
        state = knowledge_orchestration.capture_committed_knowledge(tmp_path, manifest)
        assert validate.call_count == 1
        monkeypatch.setattr(
            Path, "read_bytes", lambda *_: pytest.fail("reread prior artifacts")
        )
        assert (
            knowledge_orchestration.committed_runtime_provenance(
                tmp_path, manifest, committed_state=state
            )
            is not None
        )
        knowledge_orchestration.committed_governance_bundle_id(
            tmp_path, manifest, committed_state=state
        )
        assert (
            knowledge_orchestration._previous_committed_producer(
                tmp_path, manifest, committed_state=state
            )
            is not None
        )
        assert validate.call_count == 1
    with pytest.raises(TypeError, match="this wiki"):
        state.require_for(tmp_path / "other")


def test_artifact_change_after_capture_is_detected(tmp_path):
    _committed_state(tmp_path)
    state = knowledge_orchestration.capture_committed_knowledge(
        tmp_path, SyncManifest.load(tmp_path)
    )
    state.assert_current()
    target = tmp_path / ".llm-wiki-knowledge.json"
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(
        knowledge_artifacts.KnowledgeArtifactError, match="changed during"
    ):
        state.assert_current()


def test_runtime_commit_rechecks_captured_state_after_planning(tmp_path, monkeypatch):
    runtime, _, _ = _runtime_input_case(tmp_path, inventory_complete=True)
    real_plan = knowledge_orchestration.build_runtime_knowledge_plan
    root = Path(runtime.target_wiki_dir)

    def raced(inputs):
        plan = real_plan(inputs)
        (root / ".llm-wiki-knowledge.json").write_bytes(b"concurrent writer")
        return plan

    monkeypatch.setattr(knowledge_orchestration, "build_runtime_knowledge_plan", raced)
    with pytest.raises(
        knowledge_artifacts.KnowledgeArtifactError, match="changed during"
    ):
        knowledge_orchestration.finalize_runtime_knowledge(runtime)
    assert not (root / ".llm-wiki-manifest.json").exists()


def test_public_serialization_still_rejects_manually_invalid_model(tmp_path):
    _committed_state(tmp_path)
    model = load_knowledge_state(tmp_path).knowledge
    assert model is not None
    changed = replace(model, schema_version="future")
    with pytest.raises(ValueError):
        knowledge_index.serialize_knowledge_index(changed)
    forged_extensions = replace(model, extensions=FrozenDict({"unqualified": True}))
    with pytest.raises(ValueError):
        knowledge_index.serialize_knowledge_index(forged_extensions)


def test_revision_change_with_new_inputs_builds_only_one_candidate(tmp_path):
    from llm_wiki_cli.services.knowledge_envelope import RepositoryEvidence

    runtime, _, _ = _runtime_input_case(tmp_path, inventory_complete=True)
    first = replace(runtime, repository_evidence=RepositoryEvidence(evaluated_revision="a" * 40))
    knowledge_orchestration.finalize_runtime_knowledge(first)
    current = replace(
        runtime,
        previous_manifest=SyncManifest.load(Path(runtime.target_wiki_dir)),
        repository_evidence=RepositoryEvidence(evaluated_revision="b" * 40),
        generation_options={**runtime.generation_options, "preserve_semantic": False},
    )
    with patch.object(knowledge_orchestration, "build_knowledge_generation_plan", wraps=knowledge_orchestration.build_knowledge_generation_plan) as build:
        result = knowledge_orchestration.finalize_runtime_knowledge(current)
    assert build.call_count == 1
    assert result.changed
