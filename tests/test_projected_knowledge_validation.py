"""Final projected models validate once and match the strict intermediate path."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from llm_wiki_cli.services import knowledge_generation as generation, knowledge_index as index
from llm_wiki_cli.services.knowledge_governance import (
    GovernanceLedger, concept_references_from_knowledge, reconcile_concepts,
)
from llm_wiki_cli.services.knowledge_model import parse_knowledge_index
from llm_wiki_cli.services.maintenance_state import maintenance_core, new_identity
from tests.test_knowledge_generation import _planner_inputs


def _projected_inputs(root, *, maintenance, governed, storage_format):
    inputs = _planner_inputs(root)
    base = generation.build_knowledge_generation_plan(inputs)
    model = parse_knowledge_index(json.loads(base.knowledge_index.content))
    if governed:
        inputs = replace(inputs, governance=reconcile_concepts(
            GovernanceLedger.empty("kb_projected-validation"),
            concept_references_from_knowledge(model),
        ))
    if maintenance:
        marker = {"schema_version": "llm-wiki-maintenance-adoption/v1",
                  "adoption_id": new_identity(), "min_manifest_version": 7,
                  "features": {"implementation_evidence": 1, "maintenance_state": 1,
                               "ordinary_acknowledgment": 1}}
        manifest = base.committed_manifest.with_maintenance_state(
            maintenance_core().initial_state(marker, {}),
        )
        inputs = replace(inputs, next_manifest=manifest, previous_manifest=manifest,
                         maintenance_adoption=marker)
        # Allocate opaque maintenance records once, then compare identical replay
        # history rather than two independent adoptions with different IDs.
        adopted = generation.build_knowledge_generation_plan(inputs)
        inputs = replace(inputs, next_manifest=adopted.committed_manifest,
                         previous_manifest=adopted.committed_manifest)
    return replace(inputs, knowledge_format=storage_format)


@pytest.mark.parametrize("storage_format", ["v1", "packed-v4-deflate"])
@pytest.mark.parametrize("maintenance,governed", [(True, False), (False, True), (True, True)])
def test_final_projection_validates_once_and_matches_strict_builder(
    tmp_path, monkeypatch, storage_format, maintenance, governed,
):
    inputs = _projected_inputs(tmp_path, maintenance=maintenance, governed=governed,
                               storage_format=storage_format)
    original = index.parse_knowledge_index
    parsed = []

    def count(value):
        parsed.append(value)
        return original(value)

    monkeypatch.setattr(index, "parse_knowledge_index", count)
    optimized = generation.build_knowledge_generation_plan(inputs)
    assert len(parsed) == 1
    assert not index._has_validation_operation(tmp_path)
    monkeypatch.setattr(generation, "_assemble_knowledge_index", index.build_knowledge_index)
    parsed.clear()
    strict = generation.build_knowledge_generation_plan(inputs)
    assert len(parsed) == 2
    assert optimized.surface_index.content == strict.surface_index.content
    assert optimized.knowledge_index.content == strict.knowledge_index.content
    assert optimized.manifest.content == strict.manifest.content
    assert {obj.relative_path: obj.content for obj in optimized.storage_objects} == {
        obj.relative_path: obj.content for obj in strict.storage_objects
    }


@pytest.mark.parametrize("storage_format", ["v1", "packed-v4-deflate"])
def test_invalid_late_projection_cannot_bypass_final_validation(tmp_path, monkeypatch, storage_format):
    inputs = _projected_inputs(tmp_path, maintenance=False, governed=True,
                               storage_format=storage_format)
    original = generation.apply_governance_projection

    def corrupt(*args, **kwargs):
        return replace(original(*args, **kwargs), schema_version="llm-wiki-knowledge/invalid")

    monkeypatch.setattr(generation, "apply_governance_projection", corrupt)
    with pytest.raises(generation.KnowledgeGenerationError, match="schema_version"):
        generation.build_knowledge_generation_plan(inputs)
    assert not index._has_validation_operation(tmp_path)
    assert list(tmp_path.iterdir()) == []
