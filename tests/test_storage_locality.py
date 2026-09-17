"""Opt-in locality and compact receipts preserve independently observed facts."""

from copy import deepcopy
from importlib.resources import files
import json

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import knowledge_packs as packs
from llm_wiki_cli.services.knowledge_artifacts import (
    build_knowledge_commit_plan, commit_knowledge_artifacts, current_knowledge_format, validated_artifact_bytes,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage import COLLECTIONS, KnowledgeStorageError, canonical_bytes
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage, recover_knowledge_storage
from llm_wiki_cli.services.storage_receipts import compact_storage_receipt, expand_storage_receipt
from llm_wiki_cli.services.workflow_profile import content_id
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_loader import _committed_state


@pytest.mark.parametrize("compression", ["stored", "deflate"])
def test_local_profile_is_explicit_lossless_and_preserved_by_writers(tmp_path, compression):
    _, previous, _ = _committed_state(tmp_path)
    target = "packed-v4" + ("-deflate" if compression == "deflate" else "")
    receipt = migrate_knowledge_storage(tmp_path, to=target, recovery_dir=tmp_path.parent / (tmp_path.name + '-backup'))
    assert receipt["minimum_reader"] == packs.LOCAL_PACKED_SCHEMA
    assert current_knowledge_format(tmp_path) == target
    state = load_knowledge_state(tmp_path)
    assert state.knowledge is not None
    reader = packs.open_knowledge_store(validated_artifact_bytes(state.validated_artifacts)[1],
        lambda path, _: state.validated_artifacts.storage_objects[path])
    assert reader.materialize() == json.loads(previous.knowledge_index.content)
    unchanged = build_knowledge_commit_plan(tmp_path, surface_index_bytes=previous.surface_index.content,
        knowledge_index_bytes=previous.knowledge_index.content, manifest=state.manifest_basis,
        prior=state.validated_artifacts)
    commit_knowledge_artifacts(unchanged)
    assert current_knowledge_format(tmp_path) == target
    recover_knowledge_storage(tmp_path, tmp_path.parent / (tmp_path.name + '-backup'))
    assert (tmp_path / '.llm-wiki-knowledge.json').read_bytes() == previous.knowledge_index.content


def test_local_profile_schema_and_catalog_bounds():
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    payload = json.loads(one_module_two_entities_fixture().knowledge_bytes)
    # Force many independent immutable objects without changing logical facts.
    logical = packs.build_knowledge_store(payload, target_bytes=512)
    plan = packs._pack_logical(logical, 'deflate', None, None, packs.LOCAL_PACK_PROFILE)
    reader = packs.open_knowledge_store(plan.root_bytes, lambda path, _: plan.objects[path])
    assert reader.materialize() == payload
    schemas = [json.loads(files('llm_wiki_cli').joinpath('schemas', name).read_text()) for name in (
        'llm-wiki-knowledge-v1.schema.json', 'llm-wiki-knowledge-v2.schema.json', 'llm-wiki-knowledge-v4.schema.json',
        'llm-wiki-knowledge-pack-index-v2.schema.json')]
    registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in schemas)
    Draft202012Validator(schemas[2], registry=registry).validate(json.loads(plan.root_bytes))
    assert all(len(node.get('members', node.get('packs', {}))) <= 24 for node in reader._indexes.values())
    changed = json.loads(plan.root_bytes)
    changed['packing']['profile'] = 'future'
    with pytest.raises(KnowledgeStorageError, match='profile'):
        packs.parse_packed_root(canonical_bytes(changed))


@pytest.mark.parametrize('fmt', ['sharded-v2', 'packed-v3', 'packed-v4-deflate'])
def test_collection_projection_matches_complete_reference_without_expanding_omitted_records(fmt):
    payload = json.loads(one_module_two_entities_fixture().knowledge_bytes)
    plan = packs.build_storage(payload, fmt)
    reader = packs.open_knowledge_store(plan.root_bytes, lambda path, _: plan.objects[path])
    full = reader.select(['source:src/accounts.py']).to_payload()
    reader = packs.open_knowledge_store(plan.root_bytes, lambda path, _: plan.objects[path])
    selected = reader.select(['source:src/accounts.py'], collections=['concepts']).to_payload()
    assert selected['schema_version'] == 'llm-wiki-knowledge-slice/v3'
    assert selected['selected_collections'] == ['concepts']
    assert selected['records']['concepts'] == full['records']['concepts']
    for kind in set(COLLECTIONS[:5]) - {'concepts'}:
        assert selected['records'][kind] == []
        assert selected['unverified_records'][kind] == reader.root['collections'][kind]['count']
    assert selected['work']['expanded_bytes'] < full['work']['expanded_bytes']


@pytest.mark.parametrize('fmt', ['sharded-v2', 'packed-v3-deflate', 'packed-v4-deflate'])
def test_compact_task_receipts_roundtrip_and_preserve_fact_scope(tmp_path, monkeypatch, fmt):
    monkeypatch.chdir(tmp_path)
    wiki = tmp_path / 'wiki'
    wiki.mkdir()
    _, previous, _ = _committed_state(wiki)
    plan = build_knowledge_commit_plan(wiki, surface_index_bytes=previous.surface_index.content,
        knowledge_index_bytes=previous.knowledge_index.content, manifest=previous.committed_manifest, knowledge_format=fmt)
    commit_knowledge_artifacts(plan)
    request = {'schema_version': 'llm-wiki-task-request/v2',
        'options': {'read_scope': 'snapshot', 'knowledge_mode': 'required'},
        'requirements': [{'id': 'concept', 'facet': 'concept', 'selector': 'entities/AccountService.md'}],
        'storage_options': {'selection': 'required-facets-v1', 'receipt': 'expanded-v1'}}
    expanded = api.build_task_context(request, wiki_dir=str(wiki))
    api.validate_task_context(expanded.rendered, request)
    request['storage_options']['receipt'] = 'compact-v1'
    compact = api.build_task_context(request, wiki_dir=str(wiki))
    payload = api.validate_task_context(compact.rendered, request)
    assert payload['storage']['layout'] == 'compact-v1'
    assert payload['facts'] == expanded.to_payload()['facts']
    assert api.expand_task_storage_receipt(payload['storage']) == expanded.to_payload()['storage']
    assert compact_storage_receipt(expand_storage_receipt(payload['storage'])) == payload['storage']
    assert len(canonical_bytes(payload['storage'])) < len(canonical_bytes(expanded.to_payload()['storage']))
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(expanded.rendered, request)
    damaged = deepcopy(payload)
    damaged['storage']['files'][0][-2] = '0' * 64
    damaged['result_id'] = content_id('llm-wiki-task-context/v2', {k: v for k, v in damaged.items() if k != 'result_id'})
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(canonical_bytes(damaged).decode(), request)


@pytest.mark.parametrize('storage', [{'selection': 'automatic'}, {'receipt': 'zip'}, {'collections': []}])
def test_storage_options_are_rejected_before_reading(tmp_path, monkeypatch, storage):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(api.InvalidRequestError):
        api.build_task_context({'schema_version': 'llm-wiki-task-request/v2', 'storage_options': storage})


@pytest.mark.parametrize('mutation', ['bad-digest', 'extra-pack', 'false-whole-range', 'invalid-range-id', 'bad-file-tag'])
def test_compact_tables_reject_ambiguous_or_incomplete_proofs(tmp_path, monkeypatch, mutation):
    monkeypatch.chdir(tmp_path)
    wiki = tmp_path / 'wiki'
    wiki.mkdir()
    _committed_state(wiki)
    migrate_knowledge_storage(wiki, to='packed-v4-deflate', recovery_dir=tmp_path / 'backup')
    request = {'schema_version': 'llm-wiki-task-request/v2',
        'options': {'read_scope': 'snapshot', 'knowledge_mode': 'required'},
        'requirements': [{'id': 'a', 'facet': 'concept', 'selector': 'entities/AccountService.md'}],
        'storage_options': {'receipt': 'compact-v1'}}
    receipt = api.build_task_context(request, wiki_dir=str(wiki)).to_payload()['storage']
    if mutation == 'bad-digest':
        receipt['packs'][0][0] = 'not-a-digest'
    elif mutation == 'extra-pack':
        receipt['packs'].append(receipt['packs'][0])
    elif mutation == 'false-whole-range':
        row = next(r for r in receipt['ranges'] if r[1] or r[2] < receipt['packs'][r[0]][2])
        row[3] = None
    elif mutation == 'invalid-range-id':
        receipt['ranges'][0][0] = True
    else:
        receipt['files'][0][0] = 999
    with pytest.raises(ValueError):
        expand_storage_receipt(receipt)


def test_paged_metadata_corruption_and_extent_lies_are_rejected():
    logical = json.loads(one_module_two_entities_fixture().knowledge_bytes)
    plan = packs.build_storage(logical, 'packed-v4-deflate')
    root = json.loads(plan.root_bytes)
    descriptor = root['packing']['catalog']
    path = packs.index_page_path(descriptor['extent']['container'])
    changed = dict(plan.objects)
    raw = bytearray(changed[path])
    raw[descriptor['extent']['offset']] ^= 1
    changed[path] = bytes(raw)
    reader = packs.open_knowledge_store(plan.root_bytes, lambda name, _: changed[name],
        read_range=lambda name, offset, count, size: changed[name][offset:offset + count])
    with pytest.raises(KnowledgeStorageError, match='checksum'):
        reader.select(['source:src/accounts.py'])
    descriptor['extent']['offset'] = descriptor['extent']['file_bytes']
    with pytest.raises(KnowledgeStorageError, match='range'):
        packs.parse_packed_root(canonical_bytes(root))
