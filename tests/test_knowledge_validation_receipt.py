"""Final-model receipts remove a parse, never an authority or parity check."""
from contextvars import copy_context
from copy import deepcopy
from collections.abc import MutableMapping
from typing import cast
from dataclasses import replace
import json
from typing import Any

import pytest

from llm_wiki_cli.services import contracts, knowledge_artifacts as artifacts
from llm_wiki_cli.services import knowledge_index as index, knowledge_model as model
from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.knowledge_generation import build_knowledge_generation_plan
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_artifacts import _plan
from tests.test_knowledge_generation import _planner_inputs
from llm_wiki_cli.services.knowledge_packs import build_storage


def _case(root):
    plan = _plan(root, one_module_two_entities_fixture())
    knowledge = model.parse_knowledge_index(json.loads(plan.knowledge_index.content))
    return plan, knowledge


def _consume(plan, receipt, root, **overrides):
    options = dict(surface_index_bytes=plan.surface_index.content,
        knowledge_index_bytes=getattr(receipt, "content", plan.knowledge_index.content), manifest=plan.committed_manifest,
        _validation_receipt=receipt, _receipt_wiki_root=root)
    options.update(overrides)
    return artifacts.validate_knowledge_artifacts(**options)


@pytest.mark.parametrize("storage_format", ["sharded-v2", "packed-v4-deflate"])
def test_storage_receipt_matches_full_read_and_remains_scoped(tmp_path, storage_format):
    plan, knowledge = _case(tmp_path)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        store = build_storage(index._model_to_payload(receipt.model), storage_format)
        options: dict[str, Any] = dict(surface_index_bytes=plan.surface_index.content,
                       knowledge_index_bytes=store.root_bytes,
                       manifest=plan.committed_manifest,
                       object_reader=lambda path, maximum: store.objects[path])
        full = artifacts.validate_knowledge_artifacts(**options)
        reused = artifacts.validate_knowledge_artifacts(**options,
                _storage_validation_receipt=receipt, _receipt_wiki_root=tmp_path)
        assert reused.knowledge == full.knowledge
        assert reused.knowledge_index_hash == full.knowledge_index_hash
        for forged in (replace(receipt), index._ValidatedIndexReceipt(receipt.model, receipt.content, tmp_path)):
            with pytest.raises((TypeError, ValueError)):
                artifacts.validate_knowledge_artifacts(**options,
                    _storage_validation_receipt=forged, _receipt_wiki_root=tmp_path)
        bad_options = {**options, "object_reader": lambda path, maximum: b"corrupt"}
        with pytest.raises(artifacts.KnowledgeArtifactError):
            artifacts.validate_knowledge_artifacts(**bad_options,
                _storage_validation_receipt=receipt, _receipt_wiki_root=tmp_path)
    with pytest.raises(TypeError, match="operation"):
        artifacts.validate_knowledge_artifacts(**options,
            _storage_validation_receipt=receipt, _receipt_wiki_root=tmp_path)


def test_storage_parity_callback_cannot_expire_validator_authority(tmp_path, monkeypatch):
    plan, knowledge = _case(tmp_path)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        store = build_storage(index._model_to_payload(receipt.model), "packed-v4-deflate")
        original = artifacts._validate_manifest_knowledge_parity
        def changed(*args):
            original(*args)
            monkeypatch.setattr(index, "_validate_builder_model", lambda value: None)
        monkeypatch.setattr(artifacts, "_validate_manifest_knowledge_parity", changed)
        with pytest.raises(TypeError, match="validators"):
            artifacts.validate_knowledge_artifacts(surface_index_bytes=plan.surface_index.content,
                knowledge_index_bytes=store.root_bytes, manifest=plan.committed_manifest,
                object_reader=lambda path, maximum: store.objects[path],
                _storage_validation_receipt=receipt, _receipt_wiki_root=tmp_path)


def test_receipt_requires_live_operation_and_exact_root(tmp_path):
    plan, knowledge = _case(tmp_path)
    with pytest.raises(TypeError, match='active wiki operation'):
        index._validated_index_receipt(knowledge, tmp_path)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        assert _consume(plan, receipt, tmp_path).knowledge is receipt.model
        with pytest.raises(TypeError, match='root'):
            _consume(plan, receipt, tmp_path / 'another')
        with pytest.raises(artifacts.KnowledgeArtifactError, match='exact wiki root'):
            _consume(plan, receipt, tmp_path, wiki_dir=tmp_path / 'another')
        with index._knowledge_validation_operation(tmp_path):
            with pytest.raises(TypeError, match='operation'):
                _consume(plan, receipt, tmp_path)
        assert _consume(plan, receipt, tmp_path).knowledge is receipt.model
    with index._knowledge_validation_operation(tmp_path):
        with pytest.raises(TypeError, match='operation'):
            _consume(plan, receipt, tmp_path)
    with pytest.raises(TypeError, match='operation'):
        _consume(plan, receipt, tmp_path)



def test_copied_context_cannot_retain_expired_operation(tmp_path):
    plan, knowledge = _case(tmp_path)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        copied = copy_context()
        assert copied.run(_consume, plan, receipt, tmp_path).knowledge is receipt.model
    assert not copied.run(index._has_validation_operation, tmp_path)
    with pytest.raises(TypeError, match='operation'):
        copied.run(_consume, plan, receipt, tmp_path)
    with pytest.raises(TypeError, match='active wiki operation'):
        copied.run(index._validated_index_receipt, knowledge, tmp_path)

def test_receipt_cannot_be_forged_replaced_or_mutated(tmp_path):
    plan, knowledge = _case(tmp_path)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        for forged in [object(), index._ValidatedIndexReceipt(receipt.model, receipt.content, tmp_path),
                       replace(receipt), replace(receipt, content=receipt.content + b'\n')]:
            with pytest.raises(TypeError, match='issued'):
                _consume(plan, forged, tmp_path)
        with pytest.raises(TypeError, match='issued'):
            index._IndexValidationProof(receipt.model, receipt.content, None, issuer=object())
        assert deepcopy(receipt) is receipt
        assert receipt._proof is not None
        with pytest.raises(AttributeError):
            setattr(receipt._proof, "content", b"{}")
        with pytest.raises(AttributeError):
            setattr(receipt._proof, "model", knowledge)
        with pytest.raises(AttributeError):
            setattr(receipt._proof, "validator_identity", ())
        with pytest.raises(TypeError):
            cast(MutableMapping[str, object], receipt.model.extensions)['injected'] = True
        object.__setattr__(receipt.model, 'schema_version', 'llm-wiki-knowledge/v99')
        with pytest.raises(TypeError, match='model differs'):
            _consume(plan, receipt, tmp_path)


@pytest.mark.parametrize('alter', [lambda b: b + b'\n', lambda b: b.replace(b'knowledge/v1', b'knowledge/v9'), lambda b: b'{}'])
def test_receipt_rejects_changed_canonical_bytes(tmp_path, alter):
    plan, knowledge = _case(tmp_path)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        with pytest.raises(TypeError, match='bytes'):
            _consume(plan, receipt, tmp_path, knowledge_index_bytes=alter(receipt.content))


@pytest.mark.parametrize('owner,field', [(index, 'parse_knowledge_index'), (model, 'parse_knowledge_index'),
    (index, 'validate_knowledge_index'), (index, '_validate_builder_model'), (index, '_serialize_payload')])
def test_receipt_rejects_changed_validator_identity(tmp_path, monkeypatch, owner, field):
    plan, knowledge = _case(tmp_path)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        original = getattr(owner, field)
        monkeypatch.setattr(owner, field, lambda *a, **k: original(*a, **k))
        with pytest.raises(TypeError, match='validators'):
            _consume(plan, receipt, tmp_path)


@pytest.mark.parametrize('owner', [index, model, contracts])
def test_receipt_rejects_changed_schema_identity(tmp_path, monkeypatch, owner):
    plan, knowledge = _case(tmp_path)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        monkeypatch.setattr(owner, 'KNOWLEDGE_SCHEMA_VERSION', 'llm-wiki-knowledge/v99')
        with pytest.raises(TypeError, match='validators'):
            _consume(plan, receipt, tmp_path)



def test_receipt_rejects_code_change_on_same_validator_function(tmp_path):
    plan, knowledge = _case(tmp_path)
    function = index._validate_builder_model
    original_code = function.__code__
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        try:
            function.__code__ = (lambda value: None).__code__
            with pytest.raises(TypeError, match='validators'):
                _consume(plan, receipt, tmp_path)
        finally:
            function.__code__ = original_code
        assert _consume(plan, receipt, tmp_path).knowledge is receipt.model

def test_final_modified_model_is_freshly_validated(tmp_path):
    _, knowledge = _case(tmp_path)
    payload = index._model_to_payload(knowledge)
    payload['concepts'][0]['extensions'] = {'application/owned': {'nested': [False, None, 0]}}
    changed = model.parse_knowledge_index(payload)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(changed, tmp_path)
        assert receipt.model.concepts[0].extensions['application/owned']['nested'] == [False, None, 0]
        payload['concepts'][0]['extensions']['application/owned']['nested'][0] = True
        assert receipt.model.concepts[0].extensions['application/owned']['nested'][0] is False
        invalid = replace(changed, schema_version='llm-wiki-knowledge/v99')
        with pytest.raises(ValueError):
            index._validated_index_receipt(invalid, tmp_path)


def test_receipt_keeps_surface_and_manifest_parity_checks(tmp_path):
    plan, knowledge = _case(tmp_path)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        surface = json.loads(plan.surface_index.content)
        surface['pages'][0]['title'] = 'Changed independent surface'
        raw = (json.dumps(surface, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
        with pytest.raises(artifacts.KnowledgeArtifactError, match='surface-index bytes'):
            _consume(plan, receipt, tmp_path, surface_index_bytes=raw)
        payload = json.loads(json.dumps(plan.committed_manifest.to_payload()))
        source = next(iter(payload['sources']))
        payload['sources'][source]['hash'] = sha256_bytes(b'changed source')
        for path, baseline in payload['evidence_baselines'].items():
            if payload['page_source_mappings'][path]['source_path'] == source and baseline['basis'] is not None:
                baseline['basis']['source_content_hash'] = payload['sources'][source]['hash']
        altered = SyncManifest.from_payload(payload)
        with pytest.raises(artifacts.KnowledgeArtifactError):
            _consume(plan, receipt, tmp_path, manifest=altered)


def test_parity_callback_validator_change_cannot_publish_a_receipt(tmp_path, monkeypatch):
    plan, knowledge = _case(tmp_path)
    original = artifacts._validate_manifest_knowledge_parity
    def change_validator(*args):
        original(*args)
        monkeypatch.setattr(index, '_validate_builder_model', lambda value: None)
    monkeypatch.setattr(artifacts, '_validate_manifest_knowledge_parity', change_validator)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        with pytest.raises(TypeError, match='validators'):
            _consume(plan, receipt, tmp_path)


def test_one_final_parse_removed_and_public_paths_still_parse(tmp_path, monkeypatch):
    plan, knowledge = _case(tmp_path)
    original = index.parse_knowledge_index
    calls = []
    def counted(value):
        calls.append(value)
        return original(value)
    monkeypatch.setattr(index, 'parse_knowledge_index', counted)
    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        assert len(calls) == 1
        _consume(plan, receipt, tmp_path)
        assert len(calls) == 1
    artifacts.validate_knowledge_artifacts(surface_index_bytes=plan.surface_index.content,
        knowledge_index_bytes=receipt.content, manifest=plan.committed_manifest)
    assert len(calls) == 2
    artifacts.build_knowledge_commit_plan(tmp_path, surface_index_bytes=plan.surface_index.content,
        knowledge_index=knowledge, manifest=plan.committed_manifest)
    assert len(calls) == 4


def test_actual_generation_outputs_equal_full_path_and_scope_released(tmp_path, monkeypatch):
    inputs = _planner_inputs(tmp_path)
    original = index.parse_knowledge_index
    calls = []
    def counted(value):
        calls.append(value)
        return original(value)
    monkeypatch.setattr(index, 'parse_knowledge_index', counted)
    optimized = build_knowledge_generation_plan(inputs)
    assert len(calls) == 1
    assert not index._has_validation_operation(tmp_path)
    monkeypatch.setattr(index, '_has_validation_operation', lambda root: False)
    calls.clear()
    full = build_knowledge_generation_plan(inputs)
    assert len(calls) == 3
    assert optimized.surface_index.content == full.surface_index.content
    assert optimized.knowledge_index.content == full.knowledge_index.content
    assert optimized.manifest.content == full.manifest.content
    assert optimized.evaluated_envelope_hash == full.evaluated_envelope_hash


@pytest.mark.parametrize('storage', ['sharded-v2', 'packed-v4-deflate'])
def test_storage_paths_retain_full_validation_and_corruption_refusal(tmp_path, monkeypatch, storage):
    _, knowledge = _case(tmp_path)
    fixture = one_module_two_entities_fixture()
    flat = _plan(tmp_path, fixture)
    def no_receipt(*args, **kwargs):
        pytest.fail('physical storage borrowed a flat-model receipt')
    monkeypatch.setattr(index, '_validated_index_receipt', no_receipt)
    plan = artifacts.build_knowledge_commit_plan(tmp_path,
        surface_index_bytes=fixture.surface_bytes, knowledge_index=knowledge,
        manifest=flat.committed_manifest, knowledge_format=storage)
    objects = {write.relative_path: write.content for write in plan.storage_objects}
    first = next(iter(objects))
    objects[first] += b'corrupt'
    with pytest.raises(artifacts.KnowledgeArtifactError):
        artifacts.validate_knowledge_artifacts(surface_index_bytes=plan.surface_index.content,
            knowledge_index_bytes=plan.knowledge_index.content, manifest=plan.committed_manifest,
            object_reader=lambda path, maximum: objects[path])
