"""Planner-only exact-store reuse preserves physical integrity and new parity."""

from dataclasses import replace
from unittest.mock import patch

import pytest

from llm_wiki_cli.services import knowledge_artifacts as artifacts
from llm_wiki_cli.services.knowledge_evidence import formatted_json_bytes
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_packs import PackedKnowledgeStoreReader
from llm_wiki_cli.services.knowledge_storage import KnowledgeStoreReader
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.test_knowledge_loader import _committed_state


@pytest.fixture(params=["sharded-v2", "packed-v3-deflate", "packed-v4-deflate"])
def stored(tmp_path, request):
    _, original, _ = _committed_state(tmp_path)
    plan = artifacts.build_knowledge_commit_plan(
        tmp_path, surface_index_bytes=original.surface_index.content,
        knowledge_index_bytes=original.knowledge_index.content,
        manifest=original.committed_manifest, knowledge_format=request.param,
    )
    artifacts.commit_knowledge_artifacts(plan)
    state = load_knowledge_state(tmp_path)
    assert state.knowledge is not None and state.validated_artifacts is not None
    return tmp_path, state, plan


def build(stored, **kwargs):
    root, state, original = stored
    args = dict(surface_index_bytes=original.surface_index.content, knowledge_index=state.knowledge,
                manifest=state.manifest_basis, prior=state.validated_artifacts)
    args.update(kwargs)
    return artifacts.build_knowledge_commit_plan(root, **args)


def test_same_store_does_not_materialize_again_but_public_validation_does(stored, monkeypatch):
    _, state, original = stored
    with monkeypatch.context() as guard:
        guard.setattr(KnowledgeStoreReader, "materialize", lambda *a, **k: pytest.fail("same captured store inflated again"))
        plan = build(stored)
    assert not plan.changed
    assert plan.knowledge_index.content == original.knowledge_index.content
    cls = PackedKnowledgeStoreReader if plan.storage_format.startswith("packed") else KnowledgeStoreReader
    with patch.object(cls, "materialize", autospec=True, side_effect=cls.materialize) as materialize:
        artifacts.validate_knowledge_artifacts(
            surface_index_bytes=plan.surface_index.content,
            knowledge_index_bytes=plan.knowledge_index.content,
            manifest=state.manifest_basis,
            object_reader=lambda path, maximum: state.validated_artifacts.storage_objects[path],
        )
    assert materialize.call_count == 1


def test_changed_root_keeps_full_validation_and_matches_independent_builder(stored):
    _, state, _ = stored
    changed = replace(state.knowledge, extensions={**state.knowledge.extensions, "example/changed": True})
    cls = PackedKnowledgeStoreReader if stored[2].storage_format.startswith("packed") else KnowledgeStoreReader
    with patch.object(cls, "materialize", autospec=True, side_effect=cls.materialize) as materialize:
        plan = build(stored, knowledge_index=changed)
    assert materialize.call_count == 1
    independent = build(stored, knowledge_index=changed, prior=None)
    assert plan.knowledge_index.content == independent.knowledge_index.content
    assert {w.relative_path: w.content for w in plan.storage_objects} == {
        w.relative_path: w.content for w in independent.storage_objects}


def test_same_store_prior_cannot_skip_changed_validator(stored, monkeypatch):
    from llm_wiki_cli.services import knowledge_index
    from llm_wiki_cli.services.knowledge_model import KnowledgeModelError

    def refuse(*args, **kwargs):
        raise KnowledgeModelError("knowledge", "changed validator refuses this model")
    monkeypatch.setattr(knowledge_index, "parse_knowledge_index", refuse)
    with pytest.raises(artifacts.KnowledgeArtifactError, match="changed validator"):
        build(stored)


@pytest.mark.parametrize("change", ["root", "object"])
def test_corrupt_prepared_bytes_cannot_inherit_prior_validation(stored, monkeypatch, change):
    real = artifacts.build_storage
    def corrupt(*args, **kwargs):
        plan = real(*args, **kwargs)
        if change == "root":
            return replace(plan, root_bytes=b"{")
        objects = dict(plan.objects)
        name = next(iter(objects))
        objects[name] += b"corrupt"
        return replace(plan, objects=objects)
    monkeypatch.setattr(artifacts, "build_storage", corrupt)
    with pytest.raises(artifacts.KnowledgeArtifactError):
        build(stored)


def test_replaced_prior_has_no_authority(stored):
    with pytest.raises(TypeError, match="validator|replaced"):
        build(stored, prior=replace(stored[1].validated_artifacts))


@pytest.mark.parametrize("change", ["surface", "manifest"])
def test_same_store_still_checks_new_surface_and_manifest_parity(stored, monkeypatch, change):
    _, state, _ = stored
    monkeypatch.setattr(KnowledgeStoreReader, "materialize", lambda *a, **k: pytest.fail("parity should retain exact-store reuse"))
    if change == "surface":
        surface = dict(state.validated_artifacts.surface_payload)
        surface["pages"] = [dict(row) for row in surface["pages"]]
        surface["pages"][0]["title"] += " changed"
        args = {"surface_index_bytes": formatted_json_bytes(surface)}
    else:
        manifest = SyncManifest.from_payload(state.manifest_basis.to_payload())
        manifest.sources["src/accounts.py"]["hash"] = "sha256:" + "0" * 64
        args = {"manifest": manifest}
    with pytest.raises(artifacts.KnowledgeArtifactError):
        build(stored, **args)


def test_same_store_rechecks_prepared_objects_after_parity_callbacks(stored, monkeypatch):
    real_storage = artifacts.build_storage
    prepared = []
    def retain(*args, **kwargs):
        plan = real_storage(*args, **kwargs)
        prepared.append(plan)
        return plan
    real_parity = artifacts._validate_surface_knowledge_parity
    def mutate(*args):
        real_parity(*args)
        objects = prepared[0].objects
        objects[next(iter(objects))] += b"changed during validation"
    monkeypatch.setattr(artifacts, "build_storage", retain)
    monkeypatch.setattr(artifacts, "_validate_surface_knowledge_parity", mutate)
    with pytest.raises(artifacts.KnowledgeArtifactError, match="changed during validated storage reuse"):
        build(stored)


def test_same_store_does_not_waive_actual_disk_corruption(stored):
    root, state, _ = stored
    path = next(path for path in state.validated_artifacts.storage_objects if path.startswith(".llm-wiki-knowledge/"))
    (root / path).write_bytes(b"actual immutable object corrupted")
    with pytest.raises(artifacts.KnowledgeArtifactError, match="immutable object is corrupt"):
        build(stored)


@pytest.mark.parametrize("before,after", [(0, False), (0.0, -0.0), (1, 1.0)])
def test_same_store_proof_uses_exact_json_identity_not_python_equality(stored, monkeypatch, before, after):
    from llm_wiki_cli.services import knowledge_index
    root, state, original = stored
    initial = replace(state.knowledge, extensions={**state.knowledge.extensions, "example/exact": before})
    artifacts.commit_knowledge_artifacts(build(stored, knowledge_index=initial))
    state = load_knowledge_state(root)
    model, prior = state.knowledge, state.validated_artifacts
    assert model is not None and prior is not None
    changed = replace(model, extensions={**model.extensions, "example/exact": after})
    _, prior_root = artifacts.validated_artifact_bytes(prior)
    real = artifacts.build_storage
    def wrong_root(*args, **kwargs):
        plan = real(*args, **kwargs)
        return replace(plan, root_bytes=prior_root, objects={path: raw for path, raw in
                       prior.storage_objects.items() if path.startswith(".llm-wiki-knowledge/")})
    monkeypatch.setattr(artifacts, "build_storage", wrong_root)
    with knowledge_index._knowledge_validation_operation(root):
        with pytest.raises(artifacts.KnowledgeArtifactError, match="storage differs from its validated logical model"):
            build((root, state, original), knowledge_index=changed)
