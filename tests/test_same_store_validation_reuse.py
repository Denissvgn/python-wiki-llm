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


def count_materializations(stored, monkeypatch):
    # Instrument before validation issues its proof: changing a decoder later
    # must expire that proof, even when the change only counts calls.
    calls = []
    real = KnowledgeStoreReader.materialize

    def counted(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(KnowledgeStoreReader, "materialize", counted)
    root, _, original = stored
    state = load_knowledge_state(root)
    assert calls
    calls.clear()
    return (root, state, original), calls


def test_same_store_does_not_materialize_again_but_public_validation_does(stored, monkeypatch):
    stored, calls = count_materializations(stored, monkeypatch)
    _, state, original = stored
    assert state.manifest_basis is not None and state.validated_artifacts is not None
    prior = state.validated_artifacts
    plan = build(stored)
    assert not calls
    assert not plan.changed
    assert plan.knowledge_index.content == original.knowledge_index.content
    artifacts.validate_knowledge_artifacts(
        surface_index_bytes=plan.surface_index.content,
        knowledge_index_bytes=plan.knowledge_index.content,
        manifest=state.manifest_basis,
        object_reader=lambda path, maximum: prior.storage_objects[path],
    )
    assert len(calls) == 1


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


@pytest.mark.parametrize("policy", ["decoder", "route_audit", "object_limit", "open_alias", "objects_alias"])
def test_same_store_prior_cannot_skip_changed_storage_policy(stored, monkeypatch, policy):
    from llm_wiki_cli.services import knowledge_packs, knowledge_storage

    def refuse(*args, **kwargs):
        raise knowledge_storage.KnowledgeStorageError("objects", "new physical storage policy")

    if policy == "decoder":
        if stored[2].storage_format == "sharded-v2":
            monkeypatch.setattr(knowledge_storage, "decode_bytes", refuse)
        else:
            monkeypatch.setattr(knowledge_packs, "decode_member", refuse)
    elif policy == "route_audit":
        monkeypatch.setattr(KnowledgeStoreReader, "_audit_lookup", refuse)
    elif policy in {"open_alias", "objects_alias"}:
        monkeypatch.setattr(artifacts, "open_knowledge_store" if policy == "open_alias" else "physical_objects", refuse)
    else:
        monkeypatch.setattr(knowledge_storage, "MAX_READ_OBJECTS", 1)
    for prior in (stored[1].validated_artifacts, None):
        with pytest.raises(artifacts.KnowledgeArtifactError, match="physical storage policy|max_objects"):
            build(stored, prior=prior)


@pytest.mark.parametrize("helper", ["_parse_concept", "_parse_extensions"])
def test_same_store_prior_cannot_skip_changed_semantic_helper(stored, monkeypatch, helper):
    from llm_wiki_cli.services import knowledge_model

    def refuse(*args, **kwargs):
        raise knowledge_model.KnowledgeModelError("knowledge", "new nested semantic policy")

    monkeypatch.setattr(knowledge_model, helper, refuse)
    for prior in (stored[1].validated_artifacts, None):
        with pytest.raises(artifacts.KnowledgeArtifactError, match="new nested semantic policy"):
            build(stored, prior=prior)


def test_same_store_prior_cannot_skip_changed_local_semantic_helper(stored, monkeypatch):
    from llm_wiki_cli.services import knowledge_index, knowledge_model

    def refuse(*args, **kwargs):
        raise knowledge_model.KnowledgeModelError("structure", "changed local semantic helper")

    monkeypatch.setattr(knowledge_index, "_require_structure_state", refuse)
    for prior in (stored[1].validated_artifacts, None):
        with pytest.raises(artifacts.KnowledgeArtifactError, match="changed local semantic helper"):
            build(stored, prior=prior)


def test_same_store_prior_cannot_skip_changed_local_semantic_policy(stored, monkeypatch):
    from llm_wiki_cli.services import knowledge_index, knowledge_model

    monkeypatch.setitem(knowledge_index._STRUCTURAL_SCOPE_BY_PAGE_KIND,
                        knowledge_index.PageKind.MODULES, knowledge_model.ObservationScope.ENTITY)
    for prior in (stored[1].validated_artifacts, None):
        with pytest.raises(artifacts.KnowledgeArtifactError, match="scope"):
            build(stored, prior=prior)


def test_same_store_reuse_supports_cyclic_callable_defaults(stored, monkeypatch):
    from llm_wiki_cli.services import knowledge_model

    original = knowledge_model._parse_concept

    def forwarding(value, path, *, policy=None):
        return original(value, path)

    forwarding.__kwdefaults__ = {"policy": {"validator": forwarding}}
    monkeypatch.setattr(knowledge_model, "_parse_concept", forwarding)
    root, _, original_plan = stored
    state = load_knowledge_state(root)
    refreshed = root, state, original_plan
    independent = build(refreshed, prior=None)
    reused = build(refreshed)
    assert reused.knowledge_index.content == independent.knowledge_index.content
    assert not reused.changed


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
    stored, calls = count_materializations(stored, monkeypatch)
    _, state, _ = stored
    assert state.manifest_basis is not None and state.validated_artifacts is not None
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
    assert not calls


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


def test_same_store_rechecks_storage_policy_after_parity_callbacks(stored, monkeypatch):
    from llm_wiki_cli.services import knowledge_packs

    real = artifacts._validate_surface_knowledge_parity

    def mutate(*args):
        real(*args)
        monkeypatch.setattr(knowledge_packs, "MAX_PACK_MEMBERS", 0)

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
