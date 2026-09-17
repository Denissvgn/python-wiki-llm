"""Manifest catalogs preserve full semantics and bound selected policy reads."""

from copy import deepcopy
import json

import pytest

from llm_wiki_cli.services.knowledge_artifacts import (
    CommitStage, build_knowledge_commit_plan, commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError, canonical_bytes
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from llm_wiki_cli.services.knowledge_storage_lifecycle import (
    migrate_knowledge_storage, prune_knowledge_storage, recover_knowledge_storage,
)
from llm_wiki_cli.services.manifest_storage import (
    OBJECT_LIMIT, ROOT_LIMIT, ManifestStoreReader, build_manifest_store,
    object_path, read_manifest_header,
)
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME, SyncManifest, SyncManifestError
from tests.test_knowledge_loader import _committed_state


def test_manifest_field_catalogs_reconstruct_and_selected_header_is_constant():
    payload = SyncManifest(generation_inputs={"example": "policy"}).to_payload()
    sizes = []
    for count in (100, 10_000):
        payload["sources"] = {f"src/unit_{i}.py": {"hash": "sha256:" + "a" * 64, "notes": "é" * 60}
                              for i in range(count)}
        store = build_manifest_store(payload)
        root = json.loads(store.root_bytes)
        assert len(store.root_bytes) < 16_384 < ROOT_LIMIT
        assert all(len(raw) <= OBJECT_LIMIT for raw in store.objects.values())
        reader = ManifestStoreReader(root, lambda name, _: store.objects[name])
        assert reader.materialize() == payload
        reads = []
        def read(name, maximum):
            reads.append(name)
            return store.objects[name]
        header = read_manifest_header(store.root_bytes, read)
        assert header.generation_inputs == payload["generation_inputs"]
        assert not reads
        assert not hasattr(header, "sources")
        sizes.append(len(store.root_bytes))
    assert sizes[1] - sizes[0] < 10  # only decimal byte-count width changes


def test_large_policy_is_referenced_and_verified():
    payload = SyncManifest(generation_inputs={"example": "🦊\n" * 100_000}).to_payload()
    store = build_manifest_store(payload)
    root = json.loads(store.root_bytes)
    assert "generation_inputs" not in root["header"]
    assert len(store.root_bytes) < 16_384
    header = read_manifest_header(store.root_bytes, lambda name, _: store.objects[name])
    assert header.generation_inputs == payload["generation_inputs"]
    bad = dict(store.objects)
    desc = root["catalogs"]["generation_inputs"]
    bad[object_path(desc["hash"])] = b"{}\n"
    with pytest.raises(KnowledgeStorageError, match="commitment"):
        read_manifest_header(store.root_bytes, lambda name, _: bad[name])


def test_missing_wrong_catalog_and_unbounded_expansion_fail():
    payload = SyncManifest().to_payload()
    store = build_manifest_store(payload)
    root = json.loads(store.root_bytes)
    with pytest.raises(KeyError):
        SyncManifest.from_payload(root, object_reader=lambda name, _: {}[name])
    with pytest.raises(SyncManifestError, match="committed catalog"):
        SyncManifest.from_payload(root)
    changed = deepcopy(root)
    changed["logical_hash"] = "sha256:" + "0" * 64
    with pytest.raises(KnowledgeStorageError, match="logical commitment"):
        SyncManifest.from_payload(changed, object_reader=lambda name, _: store.objects[name])
    changed = deepcopy(root)
    changed["catalogs"]["sources"]["expanded_bytes"] = 2**60
    with pytest.raises(KnowledgeStorageError, match="size"):
        read_manifest_header(canonical_bytes(changed), lambda name, _: store.objects[name])


@pytest.mark.parametrize("knowledge_format", ["v1", "sharded-v2", "packed-v3", "packed-v3-deflate"])
def test_owning_plan_preserves_v6_and_full_semantics(tmp_path, knowledge_format):
    _, original, _ = _committed_state(tmp_path)
    state = load_knowledge_state(tmp_path)
    plan = build_knowledge_commit_plan(tmp_path, surface_index_bytes=original.surface_index.content,
        knowledge_index=state.knowledge, manifest=original.committed_manifest.without_artifact_hashes(),
        knowledge_format=knowledge_format, manifest_format="indexed-v6")
    stages = []
    commit_knowledge_artifacts(plan, fault_injector=stages.append)
    assert stages[-1] is CommitStage.MANIFEST_WRITTEN
    current = load_knowledge_state(tmp_path)
    assert current.knowledge == state.knowledge
    assert current.manifest_basis.storage_version == 6
    assert current.manifest_basis.sources == state.manifest_basis.sources
    assert current.manifest_basis.evidence_baselines == state.manifest_basis.evidence_baselines
    again = build_knowledge_commit_plan(tmp_path, surface_index_bytes=original.surface_index.content,
        knowledge_index=state.knowledge, manifest=original.committed_manifest.without_artifact_hashes())
    assert not again.changed
    if knowledge_format != "v1":
        read = capture_knowledge_slice(tmp_path, ["source:src/accounts.py"])
        assert read.manifest.storage_version == 6
        assert not any(name.startswith(".llm-wiki-manifest/") for name in read.session.observations)
        read.finish()
    assert not prune_knowledge_storage(tmp_path)["unreferenced_objects"]


def test_manifest_migration_recovery_and_interruption(tmp_path):
    root = tmp_path / "wiki"
    root.mkdir()
    _, original, _ = _committed_state(root)
    before = (root / MANIFEST_FILENAME).read_bytes()
    state = load_knowledge_state(root)
    plan = build_knowledge_commit_plan(root, surface_index_bytes=original.surface_index.content,
        knowledge_index=state.knowledge, manifest=original.committed_manifest.without_artifact_hashes(),
        manifest_format="indexed-v6")
    def fail(stage):
        if stage is CommitStage.KNOWLEDGE_OBJECTS_WRITTEN:
            raise RuntimeError("interrupted")
    with pytest.raises(RuntimeError, match="interrupted"):
        commit_knowledge_artifacts(plan, fault_injector=fail)
    assert (root / MANIFEST_FILENAME).read_bytes() == before
    assert load_knowledge_state(root).knowledge == state.knowledge
    migrate_knowledge_storage(root, to="indexed-v6", recovery_dir=tmp_path / "backup")
    assert SyncManifest.load(root).storage_version == 6
    recover_knowledge_storage(root, tmp_path / "backup")
    assert (root / MANIFEST_FILENAME).read_bytes() == before


def test_recovery_refuses_new_manifest_with_the_same_knowledge_root(tmp_path):
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    migrate_knowledge_storage(root, to="indexed-v6", recovery_dir=tmp_path / "backup")
    manifest = SyncManifest.load(root)
    manifest.generation_inputs["example/new-policy"] = "new generation"
    manifest.save(root)
    before = (root / MANIFEST_FILENAME).read_bytes()
    with pytest.raises(KnowledgeStorageError, match="manifest is outside"):
        recover_knowledge_storage(root, tmp_path / "backup")
    assert (root / MANIFEST_FILENAME).read_bytes() == before


@pytest.mark.parametrize('fmt', ['packed-v3-deflate', 'packed-v4', 'packed-v4-deflate'])
def test_documentation_import_reconstructs_v6_catalogs(tmp_path, fmt):
    from llm_wiki_cli.services.documentation_wiki_input import adopt_documentation_wiki_snapshot
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    migrate_knowledge_storage(root, to=fmt, recovery_dir=tmp_path / "packed")
    migrate_knowledge_storage(root, to="indexed-v6", recovery_dir=tmp_path / "manifest")
    result = adopt_documentation_wiki_snapshot(root, tmp_path / "workspace", freshness_policy="allow-unverified")
    assert result.manifest_schema_version == 6
    assert result.artifact_form == "manifest_v6_native"
    assert not any(p.startswith(".llm-wiki-manifest/") for p in result.unknown_entries)
    assert not any(p.startswith(".llm-wiki-knowledge/") for p in result.unknown_entries)
    if fmt.startswith('packed-v4'):
        containers = [p for p in result.copied_paths if p.startswith('.llm-wiki-knowledge/index-pages/')]
        assert containers
        assert all((root / p).read_bytes() == (tmp_path / 'workspace' / p).read_bytes() for p in containers)


@pytest.mark.parametrize('suffix', [
    'aa/' + 'b' * 64 + '.bin',
    'aa/' + 'a' * 63 + '.bin',
    'aa/' + 'a' * 64 + '.json',
    'aa/nested/' + 'a' * 64 + '.bin',
    '../aa/' + 'a' * 64 + '.bin',
])
def test_documentation_import_keeps_malformed_index_page_paths_unknown(suffix):
    from llm_wiki_cli.services.documentation_wiki_input import _is_known_wiki_path
    assert not _is_known_wiki_path('.llm-wiki-knowledge/index-pages/' + suffix)
