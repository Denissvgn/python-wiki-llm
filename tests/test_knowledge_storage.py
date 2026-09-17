"""Storage controls use the existing independently authored logical fixture."""

from copy import deepcopy
import json
from importlib.resources import files

import pytest

from llm_wiki_cli.services.knowledge_storage import (
    MAX_OBJECT_BYTES, MAX_ROOT_BYTES, KnowledgeStorageError, KnowledgeStoreReader,
    build_knowledge_store, canonical_bytes, digest, object_path, parse_store_root,
)
from llm_wiki_cli.services.knowledge_storage_io import StorageReadSession, read_guarded
from tests.knowledge_fixtures import one_module_two_entities_fixture


@pytest.fixture
def logical():
    return json.loads(one_module_two_entities_fixture().knowledge_bytes)


def reader(plan, **kwargs):
    return KnowledgeStoreReader(plan.root_bytes, lambda path, _: plan.objects[path], **kwargs)


def test_roundtrip_preserves_native_facts_and_opaque_extension_literals(logical):
    logical.setdefault("extensions", {})["consumer/opaque"] = {
        "$value": "literal", "$basis": {"nested": [1, None, True]},
        "$object": [["x", "not a storage escape"]], "unicode": "á🙂",
    }
    plan = build_knowledge_store(logical, target_bytes=1024)
    result = reader(plan).materialize()
    assert result == logical
    assert [c["title"] for c in result["concepts"] if c["concept_kind"] == "code-entity"] == ["AccountService", "User"]
    assert len(plan.root_bytes) <= MAX_ROOT_BYTES
    assert all(len(raw) <= MAX_OBJECT_BYTES for raw in plan.objects.values())


def test_bundled_schemas_resolve_offline_and_validate_actual_objects(logical):
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    schemas = [json.loads(files("llm_wiki_cli").joinpath("schemas").joinpath(name).read_text())
               for name in ("llm-wiki-knowledge-v1.schema.json", "llm-wiki-knowledge-v2.schema.json",
                            "llm-wiki-knowledge-object-v1.schema.json")]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    plan = build_knowledge_store(logical)
    Draft202012Validator(schemas[1], registry=registry).validate(json.loads(plan.root_bytes))
    validator = Draft202012Validator(schemas[2], registry=registry)
    for raw in plan.objects.values():
        validator.validate(json.loads(raw))


def test_identical_builds_are_byte_identical(logical):
    first = build_knowledge_store(logical)
    second = build_knowledge_store(deepcopy(logical))
    assert second == first


def test_repeated_observations_are_not_collapsed(logical):
    logical["relationships"].append(deepcopy(logical["relationships"][0]))
    logical["relationships"].sort(key=canonical_bytes)
    plan = build_knowledge_store(logical)
    assert reader(plan).materialize()["relationships"] == logical["relationships"]


def test_scoped_reads_disclose_unread_records_and_do_not_read_custom_extensions(logical):
    logical.setdefault("extensions", {})["consumer/large"] = "irrelevant" * 30_000
    plan = build_knowledge_store(logical)
    storage = reader(plan)
    result = storage.select(["source:src/accounts.py"]).to_payload()
    assert result["validation_scope"] == "selected-committed-records"
    assert result["whole_store_validated"] is False
    assert result["live_evaluated"] is False
    assert result["lookup_complete"] is True
    assert result["records"]["extensions"] == []
    assert result["unverified_records"]["extensions"] >= 1
    assert {r["value"]["title"] for r in result["records"]["concepts"]} >= {"User", "AccountService"}
    assert storage.bytes_read < 100_000
    assert len(storage.objects) < len(plan.objects)


def test_small_record_limit_discloses_truncation(logical):
    result = reader(build_knowledge_store(logical)).select(["source:src/accounts.py"], max_records=1).to_payload()
    assert result["lookup_complete"] is False
    assert sum(len(rows) for rows in result["records"].values()) == 1


def test_budget_is_checked_before_opening_an_object(logical):
    plan = build_knowledge_store(logical)
    opened = []
    def read(path, maximum):
        opened.append(path)
        return plan.objects[path]
    storage = KnowledgeStoreReader(plan.root_bytes, read, max_bytes=len(plan.root_bytes))
    with pytest.raises(KnowledgeStorageError, match="budget"):
        storage.select(["source:src/accounts.py"])
    assert opened == []


def test_expansion_budget_fails_before_a_large_result_is_built(logical):
    storage = reader(build_knowledge_store(logical), max_expanded_bytes=32)
    with pytest.raises(KnowledgeStorageError, match="expanded data budget"):
        storage.select(["source:src/accounts.py"])


def test_corrupt_required_object_is_not_an_empty_lookup(logical):
    plan = build_knowledge_store(logical)
    root = json.loads(plan.root_bytes)
    bad = object_path(root["collections"]["lookup"]["hash"])
    def read(path, maximum):
        raw = plan.objects[path]
        return raw[:-2] + b" \n" if path == bad else raw
    storage = KnowledgeStoreReader(plan.root_bytes, read)
    with pytest.raises(KnowledgeStorageError, match="commitment"):
        storage.select(["source:src/accounts.py"])


def test_unread_corruption_is_not_claimed_checked_but_full_audit_fails(logical):
    plan = build_knowledge_store(logical)
    root = json.loads(plan.root_bytes)
    bad = object_path(root["collections"]["extensions"]["hash"])
    def read(path, maximum):
        return b"{}\n" if path == bad else plan.objects[path]
    scoped = KnowledgeStoreReader(plan.root_bytes, read).select(["source:src/accounts.py"]).to_payload()
    assert scoped["whole_store_validated"] is False
    assert bad not in scoped["inspected_objects"]
    with pytest.raises(KnowledgeStorageError, match="commitment"):
        KnowledgeStoreReader(plan.root_bytes, read).materialize()


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(unknown=True),
    lambda r: r.update(schema_version="llm-wiki-knowledge/v99"),
    lambda r: r["collections"]["lookup"].update(count=True),
    lambda r: r["collections"]["lookup"].update(hash="../../outside"),
    lambda r: r["basis"].update({"snapshot.fake": "sha256:" + "0" * 64}),
])
def test_strict_root_rejects_incompatible_or_inconsistent_metadata(logical, mutation):
    root = json.loads(build_knowledge_store(logical).root_bytes)
    mutation(root)
    with pytest.raises(KnowledgeStorageError):
        parse_store_root(canonical_bytes(root))


def test_noncanonical_and_duplicate_key_roots_are_rejected(logical):
    raw = build_knowledge_store(logical).root_bytes
    with pytest.raises(KnowledgeStorageError, match="canonical"):
        parse_store_root(json.dumps(json.loads(raw), indent=2).encode())
    with pytest.raises(KnowledgeStorageError, match="duplicate"):
        parse_store_root(raw.replace(b'{"basis":', b'{"basis":{},"basis":', 1))


def test_oversized_single_record_fails_without_publishing(logical):
    logical.setdefault("extensions", {})["consumer/huge"] = "x" * MAX_OBJECT_BYTES
    with pytest.raises(KnowledgeStorageError, match="8 MiB"):
        build_knowledge_store(logical)


def test_full_audit_rejects_rehashed_empty_secondary_index(logical):
    plan = build_knowledge_store(logical)
    root = json.loads(plan.root_bytes)
    objects = dict(plan.objects)
    raw = canonical_bytes({"schema_version": "llm-wiki-knowledge-object/v1", "collection": "lookup",
                           "prefix": "", "kind": "catalog", "children": {}})
    root["collections"]["lookup"] = {"hash": digest(raw), "bytes": len(raw), "count": 0}
    objects[object_path(digest(raw))] = raw
    with pytest.raises(KnowledgeStorageError, match="exactly index"):
        KnowledgeStoreReader(canonical_bytes(root), lambda path, _: objects[path]).materialize()


def test_guarded_reads_reject_symlinks_and_bound_bytes(tmp_path):
    (tmp_path / "data.json").write_bytes(b"data")
    with pytest.raises(KnowledgeStorageError, match="limit"):
        read_guarded(tmp_path / "data.json", 3)
    (tmp_path / "alias").symlink_to(tmp_path / "data.json")
    with pytest.raises(KnowledgeStorageError, match="symlink"):
        read_guarded(tmp_path / "alias", 4)


def test_session_rechecks_charge_work_and_detect_same_size_edit(tmp_path):
    path = tmp_path / "data.json"
    path.write_bytes(b"before")
    storage = StorageReadSession(tmp_path, max_bytes=24)
    assert storage.read("data.json", 6) == b"before"
    storage.recheck()
    assert storage.bytes_read == 12
    path.write_bytes(b"after!")
    with pytest.raises(KnowledgeStorageError, match="changed"):
        storage.recheck()


def test_shared_basis_change_does_not_rewrite_record_shards(logical):
    first = build_knowledge_store(logical)
    changed = deepcopy(logical)
    old = logical["bundle"]["snapshot"]["source_snapshot_hash"]
    new = "sha256:" + "9" * 64
    # Change every occurrence of a shared generation basis, preserving records.
    changed = json.loads(json.dumps(changed).replace(old, new))
    second = build_knowledge_store(changed)
    assert first.root_bytes != second.root_bytes
    assert first.objects == second.objects
    assert reader(second).materialize() == changed
