"""Complete recovery catalogs deduplicate bytes without losing pinned history."""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from llm_wiki_cli.services import maintenance_recovery as recovery
from llm_wiki_cli.services.knowledge_storage import digest
from llm_wiki_cli.services.maintenance_protocol import MaintenanceProtocolError, load_adoption_marker, save_recovery_snapshot, snapshot_wiki
from llm_wiki_cli.services.maintenance_service import adopt_maintenance_authority, load_recovery_snapshot
from llm_wiki_cli.services.maintenance_state import new_identity


@pytest.fixture
def marker():
    return {
        "schema_version": "llm-wiki-maintenance-adoption/v1",
        "adoption_id": new_identity(), "min_manifest_version": 7,
        "features": {"implementation_evidence": 1, "maintenance_state": 1, "ordinary_acknowledgment": 1},
    }


def _managed(store, owner, marker, files, *, kind="captured-preimage"):
    key = recovery.recovery_catalog_key(owner, marker, {name: digest(raw) for name, raw in files.items()})
    directory = store / key
    if kind == "committed":
        directory = directory / "committed"
    metadata = recovery.save_recovery_catalog(directory, files, marker=marker, kind=kind, owner_root=owner)
    return directory, metadata


def _generation(store, owner, marker, number):
    files = {"page.md": b"shared authored bytes\r\n", "root.json": str(number).encode()}
    preimage, _ = _managed(store, owner, marker, files)
    committed, _ = _managed(store, owner, marker, files, kind="committed")
    recovery.mark_recovery_complete(preimage, committed)
    return preimage, committed, files


def test_managed_catalogs_deduplicate_complete_file_bytes(tmp_path, marker):
    store = tmp_path / "maintenance-preimages"
    owner = tmp_path / "worktree/wiki"
    original = {"page.md": b"shared", "copy.md": b"shared", "root.json": b"first"}
    first, metadata = _managed(store, owner, marker, original)
    second_files = {**original, "root.json": b"second"}
    second, newer = _managed(store, owner, marker, second_files, kind="committed")
    blobs = list((store / ".objects").rglob("*.blob"))
    assert len(blobs) == 3
    assert sum(path.stat().st_size for path in blobs) == len(b"sharedfirstsecond")
    assert not (first / "page.md").exists()
    assert recovery.load_recovery_catalog(first, metadata) == original
    assert recovery.load_recovery_catalog(second, newer) == second_files
    assert all(path.stat().st_nlink == 1 for path in blobs)


@pytest.mark.parametrize("damage", ["changed", "missing", "redirected"])
def test_catalog_blob_corruption_cannot_be_loaded(tmp_path, marker, damage):
    files = {"page.md": b"exact bytes"}
    directory, metadata = _managed(tmp_path / "maintenance-preimages", tmp_path / "wiki", marker, files)
    blob = next((directory.parent / ".objects").rglob("*.blob"))
    if damage == "changed":
        blob.write_bytes(b"other bytes")
    elif damage == "missing":
        blob.unlink()
    else:
        outside = tmp_path / "outside"
        outside.write_bytes(blob.read_bytes())
        blob.unlink()
        blob.symlink_to(outside)
    with pytest.raises((ValueError, OSError)):
        recovery.load_recovery_catalog(directory, metadata)


def test_catalog_rejects_arbitrary_blob_location_metadata(tmp_path, marker):
    directory, metadata = _managed(tmp_path / "maintenance-preimages", tmp_path / "wiki", marker, {"page.md": b"exact"})
    changed = deepcopy(metadata)
    changed["blob_store"] = "../../outside"
    with pytest.raises(MaintenanceProtocolError):
        recovery.load_recovery_catalog(directory, changed)


def test_retention_keeps_failed_and_other_worktree_recoveries(tmp_path, marker):
    store = tmp_path / "maintenance-preimages"
    owner = tmp_path / "first/wiki"
    generations = [_generation(store, owner, marker, number) for number in range(4)]
    failed, failed_metadata = _managed(store, owner, marker, {"failed.md": b"pinned interrupted bytes"})
    other, other_metadata = _managed(store, tmp_path / "second/wiki", marker, {"other.md": b"other worktree bytes"})
    recovery.mark_recovery_complete(other, _managed(store, tmp_path / "second/wiki", marker,
        {"other.md": b"other worktree bytes"}, kind="committed")[0])
    report = recovery.retain_recovery_catalogs(store, owner_root=owner, marker=marker,
        newest_committed=generations[-1][1], keep_successful=2)
    assert report["removed_catalogs"] == 4
    assert report["blob_gc"] == "complete"
    assert report["removed_blobs"] == 2
    assert report["reclaimed_bytes"] == 2
    for preimage, committed, _files in generations[:2]:
        assert not (preimage / recovery.CATALOG_FILENAME).exists()
        assert not (committed / recovery.CATALOG_FILENAME).exists()
    for preimage, committed, _files in generations[2:]:
        assert (preimage / recovery.CATALOG_FILENAME).exists()
        assert (committed / recovery.CATALOG_FILENAME).exists()
    assert recovery.load_recovery_catalog(failed, failed_metadata) == {"failed.md": b"pinned interrupted bytes"}
    assert recovery.load_recovery_catalog(other, other_metadata) == {"other.md": b"other worktree bytes"}


def test_new_attempt_cannot_inherit_old_completion_permission(tmp_path, marker):
    store = tmp_path / "maintenance-preimages"
    owner = tmp_path / "wiki"
    preimage, _committed, files = _generation(store, owner, marker, 0)
    assert (preimage / recovery.COMPLETION_FILENAME).exists()
    recovery.save_recovery_catalog(preimage, files, marker=marker, kind="captured-preimage", owner_root=owner)
    assert not (preimage / recovery.COMPLETION_FILENAME).exists()
    newest = [_generation(store, owner, marker, number) for number in (1, 2, 3)][-1][1]
    recovery.retain_recovery_catalogs(store, owner_root=owner, marker=marker, newest_committed=newest, keep_successful=1)
    assert (preimage / recovery.CATALOG_FILENAME).exists()
    assert recovery.load_recovery_catalog(preimage, json.loads((preimage / recovery.CATALOG_FILENAME).read_bytes())) == files


@pytest.mark.parametrize("unknown", ["unknown-entry", "malformed-catalog", "unknown-blob"])
def test_unknown_storage_prevents_blob_collection(tmp_path, marker, unknown):
    store = tmp_path / "maintenance-preimages"
    owner = tmp_path / "wiki"
    directory, _metadata = _managed(store, owner, marker, {"live.md": b"referenced"})
    orphan = b"orphan blob"
    logical_hash = digest(orphan)[7:]
    orphan_path = store / ".objects" / logical_hash[:2] / (logical_hash + ".blob")
    orphan_path.parent.mkdir(parents=True, exist_ok=True)
    orphan_path.write_bytes(orphan)
    if unknown == "unknown-entry":
        (store / "foreign-data").write_bytes(b"unrelated")
    elif unknown == "malformed-catalog":
        (directory / recovery.CATALOG_FILENAME).write_bytes(b"{")
    else:
        (orphan_path.parent / "unrecognized.blob").write_bytes(b"unknown")
    report = recovery.collect_recovery_blobs(store)
    assert report["blob_gc"] == "incomplete"
    assert report["removed_blobs"] == 0
    assert orphan_path.read_bytes() == orphan


def test_explicit_local_catalogs_are_not_automatically_marked(tmp_path, marker):
    root = tmp_path / "explicit-recovery"
    files = {"page.md": b"local bytes"}
    metadata = recovery.save_recovery_catalog(root, files, marker=marker, owner_root=tmp_path / "wiki")
    assert metadata["blob_store"] == "local/v1"
    assert recovery.load_recovery_catalog(root, metadata) == files
    recovery.mark_recovery_complete(root, root)
    assert not (root / recovery.COMPLETION_FILENAME).exists()


def test_complete_v1_and_v2_recovery_have_identical_semantics(tmp_path, monkeypatch):
    from tests.test_maintenance_lifecycle import _legacy

    wiki = _legacy(tmp_path, monkeypatch)
    adopt_maintenance_authority("src", wiki, recovery_dir="adoption")
    marker = load_adoption_marker(wiki)
    assert marker is not None
    files = snapshot_wiki(wiki)
    old = tmp_path / "legacy-copy"
    save_recovery_snapshot(old, files, marker=marker)
    current = tmp_path / "catalog-copy"
    recovery.save_recovery_catalog(current, files, marker=marker, owner_root=wiki)
    old_metadata, old_files, old_manifest = load_recovery_snapshot(old)
    metadata, recovered, manifest = load_recovery_snapshot(current)
    assert old_metadata["schema_version"].endswith("/v1")
    assert metadata["schema_version"] == recovery.CATALOG_SCHEMA
    assert recovered == old_files == files
    assert manifest.to_payload() == old_manifest.to_payload()
    assert load_recovery_snapshot("adoption/committed")[1] == files


def test_recovery_lock_is_accepted_and_excludes_another_writer(tmp_path):
    from llm_wiki_cli.services.knowledge_governance import governance_lock, GovernanceConflictError

    store = tmp_path / "maintenance-preimages"
    with governance_lock(store, _lock_filename="maintenance-recovery.lock"):
        with pytest.raises(GovernanceConflictError):
            with governance_lock(store, _lock_filename="maintenance-recovery.lock"):
                pytest.fail("a second shared-store writer acquired the lock")


def test_blob_collection_cannot_race_unpublished_catalog_bytes(tmp_path, marker, monkeypatch):
    from llm_wiki_cli.services.knowledge_governance import GovernanceConflictError

    store = tmp_path / "maintenance-preimages"
    original_write = recovery._immutable_write
    probes = []

    def write(path, raw):
        original_write(path, raw)
        if path.suffix == ".blob":
            with pytest.raises(GovernanceConflictError):
                recovery.collect_recovery_blobs(store)
            probes.append(path)

    monkeypatch.setattr(recovery, "_immutable_write", write)
    directory, metadata = _managed(store, tmp_path / "wiki", marker, {"page.md": b"new bytes"})
    assert probes
    assert recovery.load_recovery_catalog(directory, metadata) == {"page.md": b"new bytes"}


def test_legacy_managed_snapshots_remain_pinned_by_retention(tmp_path, marker):
    store = tmp_path / "maintenance-preimages"
    owner = tmp_path / "wiki"
    legacy = store / ("0" * 64)
    save_recovery_snapshot(legacy, {"page.md": b"legacy bytes"}, marker=marker)
    original = {path.relative_to(legacy): path.read_bytes() for path in legacy.rglob("*") if path.is_file()}
    newest = [_generation(store, owner, marker, number) for number in (1, 2, 3)][-1][1]
    recovery.retain_recovery_catalogs(store, owner_root=owner, marker=marker, newest_committed=newest, keep_successful=1)
    assert {path.relative_to(legacy): path.read_bytes() for path in legacy.rglob("*") if path.is_file()} == original


def test_recovery_key_namespaces_copied_adoptions_by_canonical_wiki(tmp_path, marker):
    hashes = {"page.md": digest(b"same exact bytes")}
    first = recovery.recovery_catalog_key(tmp_path / "first/wiki", marker, hashes)
    second = recovery.recovery_catalog_key(tmp_path / "second/wiki", marker, hashes)
    assert first != second
    assert recovery.recovery_catalog_key(tmp_path / "first/wiki/.", marker, hashes) == first
