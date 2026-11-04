"""Large sync captures retain the same authenticated logical payload."""

import hashlib
import json

import pytest

from llm_wiki_cli.services import sync_analysis_storage as storage
from llm_wiki_cli.services.knowledge_evidence import canonical_json_bytes, hash_json


def payload():
    return {"inventory": {f"source_{i}.py": {"text": "é\n" * 180, "count": i}
                          for i in range(24)}, "graph": [{"from": i, "to": i + 1} for i in range(8)]}


def test_streaming_measure_matches_existing_encoding_and_exact_boundary():
    value = payload()
    size = len(canonical_json_bytes(value)) + 1
    assert storage.measure(value, size) == (size, hash_json(value))
    assert storage.measure(value, size - 1) is None


def test_large_capture_uses_bounded_shards_and_preserves_logical_commitment(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)
    path = tmp_path / "capture.json"
    value = payload()
    storage.save(path, value, root_limit=8192, total_limit=100_000)
    catalog = json.loads(path.read_bytes())
    assert catalog["schema_version"] == storage.SCHEMA
    assert catalog["payload_hash"] == hash_json(value)
    objects = list((tmp_path / "capture.json.objects").iterdir())
    assert len(objects) > 1
    for obj in objects:
        assert obj.stat().st_size <= 1024
        assert obj.stem == hashlib.sha256(obj.read_bytes()).hexdigest()
    assert storage.load(path, root_limit=8192, total_limit=100_000) == value
    before = {obj.name: obj.stat().st_mtime_ns for obj in objects}
    storage.save(path, value, root_limit=8192, total_limit=100_000)
    assert {obj.name: obj.stat().st_mtime_ns for obj in objects} == before


def test_small_and_legacy_capture_remains_the_same_single_file(tmp_path):
    path = tmp_path / "capture.json"
    value = {"schema_version": "llm-wiki-sync-analysis/v2", "inventory": {}}
    storage.save(path, value, root_limit=8192, total_limit=100_000)
    assert path.read_bytes() == canonical_json_bytes(value) + b"\n"
    assert not path.with_name(path.name + ".objects").exists()
    assert storage.load(path, root_limit=8192, total_limit=100_000) == value


def test_successful_replacement_removes_only_prior_unreferenced_shards(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)
    path = tmp_path / "capture.json"
    value = payload()
    storage.save(path, value, root_limit=8192, total_limit=100_000)
    directory = tmp_path / "capture.json.objects"
    before = {obj.name for obj in directory.iterdir()}
    unknown = directory / "keep-unknown"
    unknown.write_bytes(b"unrelated")
    value["inventory"]["source_0.py"]["text"] = "changed\n" * 100
    storage.save(path, value, root_limit=8192, total_limit=100_000)
    assert before - {obj.name for obj in directory.iterdir()}
    assert unknown.read_bytes() == b"unrelated"
    assert storage.load(path, root_limit=8192, total_limit=100_000) == value


def test_replaced_superseded_shard_is_preserved_by_delete_cas(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)
    path = tmp_path / "capture.json"
    value = payload()
    storage.save(path, value, root_limit=8192, total_limit=100_000)
    unlink = storage.unlink_guarded_bytes
    replaced = []
    def replace_before_unlink(target, *, expected):
        target.write_bytes(b"external replacement")
        replaced.append(target)
        unlink(target, expected=expected)
    monkeypatch.setattr(storage, "unlink_guarded_bytes", replace_before_unlink)
    value["inventory"]["source_0.py"]["text"] = "changed\n" * 100
    storage.save(path, value, root_limit=8192, total_limit=100_000)
    assert replaced
    assert all(target.read_bytes() == b"external replacement" for target in replaced)
    assert storage.load(path, root_limit=8192, total_limit=100_000) == value


@pytest.mark.parametrize("change", ["missing", "corrupt", "redirected", "oversized"])
def test_invalid_shard_cannot_be_reused(tmp_path, monkeypatch, change):
    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)
    path = tmp_path / "capture.json"
    storage.save(path, payload(), root_limit=8192, total_limit=100_000)
    obj = next((tmp_path / "capture.json.objects").iterdir())
    if change == "missing":
        obj.unlink()
    elif change == "redirected":
        outside = tmp_path / "outside"
        obj.rename(outside)
        obj.symlink_to(outside)
    elif change == "oversized":
        obj.write_bytes(b" " * 2048)
    else:
        obj.write_bytes(b"null\n")
    with pytest.raises((OSError, ValueError)):
        storage.load(path, root_limit=8192, total_limit=100_000)


@pytest.mark.parametrize("change", ["aggregate", "path", "count", "depth", "declared-size", "logical-hash"])
def test_catalog_limits_and_logical_binding(tmp_path, monkeypatch, change):
    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)
    path = tmp_path / "capture.json"
    storage.save(path, payload(), root_limit=8192, total_limit=100_000)
    catalog = json.loads(path.read_bytes())
    if change == "aggregate":
        catalog["payload_bytes"] = 100_001
    elif change == "declared-size":
        catalog["payload_bytes"] -= 1
    elif change == "logical-hash":
        catalog["payload_hash"] = "sha256:" + "0" * 64
    elif change == "path":
        catalog["tree"] = {"kind": "value", "hash": "../../outside", "bytes": 10}
    elif change == "count":
        monkeypatch.setattr(storage, "MAX_NODES", 2)
    else:
        monkeypatch.setattr(storage, "MAX_DEPTH", 0)
    path.write_text(json.dumps(catalog))
    if change not in {"declared-size", "logical-hash"}:
        original = storage.read_guarded
        def only_catalog(target, maximum):
            assert target == path, "catalog limits must be checked before any shard read"
            return original(target, maximum)
        monkeypatch.setattr(storage, "read_guarded", only_catalog)
    with pytest.raises(ValueError):
        storage.load(path, root_limit=8192, total_limit=100_000)


def test_failed_catalog_publication_preserves_previous_capture(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)
    path = tmp_path / "capture.json"
    prior = {"prior": "unchanged"}
    storage.save(path, prior, root_limit=8192, total_limit=100_000)
    write = storage.write_bytes_atomic
    def interrupted(target, raw):
        if target == path:
            raise OSError("interrupted before catalog publication")
        write(target, raw)
    with pytest.raises(OSError):
        storage.save(path, payload(), root_limit=8192, total_limit=100_000, writer=interrupted)
    assert storage.load(path, root_limit=8192, total_limit=100_000) == prior
    assert list((tmp_path / "capture.json.objects").iterdir()) == []
    assert not storage._pending(path).exists()


def test_late_partition_failure_removes_only_new_owned_shards(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)
    path = tmp_path / "capture.json"
    value = payload()
    value["z_oversized_scalar"] = "x" * 2048
    with pytest.raises(ValueError, match="scalar exceeds"):
        storage.save(path, value, root_limit=8192, total_limit=100_000)
    assert not path.exists()
    assert list(storage._objects(path).iterdir()) == []
    assert not storage._pending(path).exists()


def _leave_interrupted_attempt(path, monkeypatch):
    """Model process death after shards but before the normal failure handler."""
    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)

    def interrupted(target, raw):
        raise OSError("process stopped before catalog publication")

    with pytest.raises(OSError):
        storage._save_locked(path, payload(), root_limit=8192, total_limit=100_000, writer=interrupted)
    return set(storage._objects(path).iterdir())


def test_retry_recovers_journaled_shards_left_by_process_interruption(tmp_path, monkeypatch):
    path = tmp_path / "capture.json"
    abandoned = _leave_interrupted_attempt(path, monkeypatch)
    assert abandoned and storage._pending(path).exists()
    storage.save(path, {"next": "small successful capture"}, root_limit=8192, total_limit=100_000)
    assert not any(obj.exists() for obj in abandoned)
    assert not storage._pending(path).exists()


def test_postpublication_failure_does_not_collect_current_catalog_references(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)
    path = tmp_path / "capture.json"
    write = storage.write_bytes_atomic

    def interrupted(target, raw):
        write(target, raw)
        raise OSError("process stopped after catalog publication")

    with pytest.raises(OSError, match="after catalog"):
        storage.save(path, payload(), root_limit=8192, total_limit=100_000, writer=interrupted)
    assert storage.load(path, root_limit=8192, total_limit=100_000) == payload()
    assert not storage._pending(path).exists()


def test_interruption_after_root_replacement_retains_superseded_ownership_for_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)
    path = tmp_path / "capture.json"
    storage.save(path, payload(), root_limit=8192, total_limit=100_000)
    superseded = set(storage._objects(path).iterdir())
    write = storage.write_bytes_atomic

    def interrupted(target, raw):
        write(target, raw)
        raise OSError("process stopped before superseded cleanup")

    with pytest.raises(OSError):
        storage._save_locked(path, {"next": "published"}, root_limit=8192,
                             total_limit=100_000, writer=interrupted)
    assert superseded and all(obj.exists() for obj in superseded)
    storage.save(path, {"next": "published"}, root_limit=8192, total_limit=100_000)
    assert not any(obj.exists() for obj in superseded)
    assert not storage._pending(path).exists()


def test_shared_writer_lock_excludes_another_cache_publication(tmp_path, monkeypatch):
    from llm_wiki_cli.services.knowledge_governance import GovernanceConflictError

    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)
    path = tmp_path / "capture.json"
    write = storage.write_bytes_atomic
    probes = []

    def publish(target, raw):
        with pytest.raises(GovernanceConflictError):
            storage.save(tmp_path / "another.json", {"other": "writer"}, root_limit=8192, total_limit=100_000)
        probes.append(True)
        write(target, raw)

    storage.save(path, payload(), root_limit=8192, total_limit=100_000, writer=publish)
    assert probes
    assert storage.load(path, root_limit=8192, total_limit=100_000) == payload()


def test_failed_attempt_delete_cas_preserves_replacements_and_primary_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MAX_SHARD_BYTES", 1024)
    path = tmp_path / "capture.json"
    unlink = storage.unlink_guarded_bytes
    replaced = []

    def replace(target, *, expected):
        if target.parent == storage._objects(path):
            target.write_bytes(b"external replacement")
            replaced.append(target)
        unlink(target, expected=expected)

    def interrupted(target, raw):
        raise OSError("primary catalog failure")

    monkeypatch.setattr(storage, "unlink_guarded_bytes", replace)
    with pytest.raises(OSError, match="primary catalog failure"):
        storage.save(path, payload(), root_limit=8192, total_limit=100_000, writer=interrupted)
    assert replaced and all(obj.read_bytes() == b"external replacement" for obj in replaced)
    assert storage._pending(path).exists()


@pytest.mark.parametrize("damage", ["unknown-entry", "unknown-owner", "symlink", "invalid-root"])
def test_unknown_attempt_state_never_authorizes_cleanup(tmp_path, monkeypatch, damage):
    path = tmp_path / "capture.json"
    abandoned = _leave_interrupted_attempt(path, monkeypatch)
    pending = storage._pending(path)
    if damage == "unknown-entry":
        (pending / "foreign").write_bytes(b"preserve unknown data")
    elif damage == "unknown-owner":
        (pending / storage._ATTEMPT_OWNER).write_bytes(b"unknown owner")
    elif damage == "symlink":
        descriptor = next(entry for entry in pending.iterdir() if entry.name != storage._ATTEMPT_OWNER)
        outside = tmp_path / "outside"
        descriptor.rename(outside)
        descriptor.symlink_to(outside)
    else:
        path.write_bytes(b'{"schema_version":"unknown-future-catalog"}\n')
    with pytest.raises((OSError, ValueError)):
        storage._recover_pending(path, 8192)
    assert all(obj.exists() for obj in abandoned)
