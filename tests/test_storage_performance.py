"""Performance changes retain canonical bytes, integrity and bounded work."""

import hashlib
import json
import random

import pytest

from llm_wiki_cli.services.canonical_json import canonical_chunks, scalar_size
from llm_wiki_cli.services.knowledge_storage import canonical_bytes, logical_digest
from llm_wiki_cli.services import knowledge_storage, knowledge_packs, validation
from tests.knowledge_fixtures import one_module_two_entities_fixture


@pytest.mark.parametrize("compression", ["stored", "deflate"])
def test_repacked_cached_members_match_pinned_zip_bytes(compression):
    members = {"concepts/abc.json": b"example\n" * 200, "values/abc.json": "é".encode() * 100}
    expected, positions = knowledge_packs._zip_bytes(members, compression)
    reusable = {}
    for name, offset, size, _, crc in positions.values():
        reusable[name] = (expected[offset + 30 + len(name):offset + 30 + len(name) + size], crc)
    for retained in ({}, reusable, {next(iter(reusable)): next(iter(reusable.values()))}):
        actual, coordinates = knowledge_packs._zip_reusing(members, compression, retained)
        assert actual == expected
        assert coordinates == positions


@pytest.mark.parametrize("fmt", ["sharded-v2", "packed-v3", "packed-v3-deflate"])
def test_spooled_plan_and_complete_streaming_audit(tmp_path, monkeypatch, fmt):
    from tests.test_knowledge_loader import _committed_state
    from llm_wiki_cli.services.knowledge_artifacts import build_knowledge_commit_plan, commit_knowledge_artifacts
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    from llm_wiki_cli.services.knowledge_stream_audit import audit_knowledge_stream
    from llm_wiki_cli.services.storage_spool import ByteSpool, SpooledArtifactWrite
    from llm_wiki_cli.services.knowledge_storage_diagnostics import review_storage
    _, old, _ = _committed_state(tmp_path)
    expected = build_knowledge_commit_plan(tmp_path, surface_index_bytes=old.surface_index.content,
        knowledge_index_bytes=old.knowledge_index.content, manifest=old.committed_manifest, knowledge_format=fmt)
    with ByteSpool() as spool:
        plan = build_knowledge_commit_plan(tmp_path, surface_index_bytes=old.surface_index.content,
            knowledge_index_bytes=old.knowledge_index.content, manifest=old.committed_manifest,
            knowledge_format=fmt, spool=spool)
        assert plan.knowledge_index.content == expected.knowledge_index.content
        assert all(isinstance(w, SpooledArtifactWrite) for w in plan.storage_objects)
        assert {w.relative_path: w.content for w in plan.storage_objects} == {w.relative_path: w.content for w in expected.storage_objects}
        commit_knowledge_artifacts(plan)
        assert load_knowledge_state(tmp_path).knowledge is not None
    with pytest.raises(KeyError):
        _ = plan.storage_objects[0].content
    def forbidden(*args, **kwargs):
        pytest.fail("streaming/scoped audit must not materialize a complete native model")
    monkeypatch.setattr(knowledge_storage.KnowledgeStoreReader, "materialize", forbidden)
    result = audit_knowledge_stream(tmp_path)
    assert result["ok"] and not result["whole_snapshot_validated"]
    assert result["records"]["concepts"] > 0
    selected = review_storage(tmp_path, selectors=["source:src/accounts.py"], limit=1)
    assert selected["ok"] and selected["validation_scope"] == "selected-records-and-policy"
    assert len(selected["records"]) == 1


def test_spill_limits_and_cancellation_cleanup():
    from llm_wiki_cli.services.storage_spool import ByteSpool
    from llm_wiki_cli.services.storage_sort import SortedRuns
    with pytest.raises(knowledge_storage.KnowledgeStorageError, match="quota"):
        with ByteSpool(max_bytes=4) as spool:
            spool["too-big"] = b"12345"
    assert spool._file.closed
    with pytest.raises(RuntimeError):
        with SortedRuns(batch_bytes=10, record_bytes=128) as runs:
            for i in range(100):
                runs.add([100 - i])
            assert list(runs) == [[i] for i in range(1, 101)]
            from pathlib import Path
            directory = Path(runs._directory.name)
            raise RuntimeError("cancelled")
    assert not directory.exists()
    with SortedRuns(batch_bytes=10) as suspended:
        suspended.add([1])
        suspended.add([2])
        iterator = iter(suspended)
        assert next(iterator) == [1]
        assert suspended._readers
    assert not suspended._readers
    iterator.close()


@pytest.mark.parametrize("compression", ["stored", "deflate"])
def test_validated_pack_reuse_avoids_compression_and_invalidates_changed_members(tmp_path, monkeypatch, compression):
    from tests.test_knowledge_loader import _committed_state
    from llm_wiki_cli.services.knowledge_artifacts import build_knowledge_commit_plan, commit_knowledge_artifacts
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    from llm_wiki_cli.services.knowledge_index import _model_to_payload
    _, old, _ = _committed_state(tmp_path)
    fmt = "packed-v3-deflate" if compression == "deflate" else "packed-v3"
    plan = build_knowledge_commit_plan(tmp_path, surface_index_bytes=old.surface_index.content,
        knowledge_index_bytes=old.knowledge_index.content, manifest=old.committed_manifest,
        knowledge_format=fmt)
    commit_knowledge_artifacts(plan)
    state = load_knowledge_state(tmp_path)
    assert state.knowledge is not None and state.manifest_basis is not None
    payload = _model_to_payload(state.knowledge)
    with monkeypatch.context() as patch:
        def unexpected(*args, **kwargs):
            pytest.fail("unchanged storage must not invoke a ZIP writer or compressor")
        patch.setattr(knowledge_packs, "_zip_bytes", unexpected)
        patch.setattr(knowledge_packs, "_zip_reusing", unexpected)
        reused = knowledge_packs.build_storage(payload, fmt, prior=state.validated_artifacts)
        assert reused.root_bytes == plan.knowledge_index.content
        assert reused.objects == {w.relative_path: w.content for w in plan.storage_objects}
        assert reused.statistics["encoded_members"] == 0
        again = build_knowledge_commit_plan(tmp_path, surface_index_bytes=old.surface_index.content,
            knowledge_index=state.knowledge, manifest=state.manifest_basis, prior=state.validated_artifacts)
        assert not again.changed
    payload.setdefault("extensions", {})["example/new"] = "localized change"
    incremental = knowledge_packs.build_storage(payload, fmt, prior=state.validated_artifacts)
    rebuilt = knowledge_packs.build_storage(payload, fmt)
    assert incremental.root_bytes == rebuilt.root_bytes
    assert incremental.objects == rebuilt.objects
    assert incremental.statistics["reused_members"] > incremental.statistics["encoded_members"]


@pytest.mark.parametrize("value", [None, True, False, 0, -123456789, 1.25, -0.0, 1e-200, "", "a\n\t\b\r\f\0\x01\"\\", "é🙂\u2028", "x" * 10000])
def test_scalar_accounting_is_exact(value):
    assert scalar_size(value) == len(canonical_bytes(value)) - 1


def test_streaming_matches_independent_standard_json_and_bounds_chunks():
    rng = random.Random(260916)
    payload = {"records": [{"i": i, "value": rng.random(), "text": "🙂\n\\" * (i % 9)} for i in range(3000)],
               "large": "\0😀é\\\n" * 30000, "nested": {"a": [None, True, False, -0.0]}}
    expected = (json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":")) + "\n").encode()
    chunks = list(canonical_chunks(payload, chunk_bytes=1024))
    assert max(map(len, chunks)) <= 1024
    assert b"".join(chunks) == expected
    assert logical_digest(payload) == "sha256:" + hashlib.sha256(expected).hexdigest()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "\ud800", {"a": float("inf")}])
def test_streaming_rejects_non_json_values(value):
    with pytest.raises((ValueError, UnicodeError)):
        b"".join(canonical_chunks(value))


def test_streaming_rejects_cycles():
    cyclic = []
    cyclic.append(cyclic)
    with pytest.raises(ValueError, match="circular"):
        b"".join(canonical_chunks(cyclic))


def test_cached_syntax_preserves_collision_and_policy_checks():
    validation.require_portable_relative_path("Folder/File.md")
    with pytest.raises(validation.SharedValidationError, match="collide"):
        validation.require_portable_relative_path("Folder/File.md", collision_seen={"folder/file.md": "folder/file.md"})
    assert validation.require_portable_relative_path("a\\b", normalize_backslashes=True) == "a/b"
    with pytest.raises(validation.SharedValidationError):
        validation.require_portable_relative_path("a\\b", normalize_backslashes=False)
    assert validation.require_portable_relative_path("e\u0301.md", defer_non_nfc_error=True) == "e\u0301.md"
    with pytest.raises(validation.SharedValidationError):
        validation.require_portable_relative_path("e\u0301.md")
    for i in range(validation._PATH_SYNTAX_LIMIT + 50):
        validation.require_portable_relative_path(f"bounded/{i}.md")
    assert len(validation._PATH_SYNTAX) <= validation._PATH_SYNTAX_LIMIT


def test_control_scan_preserves_ascii_and_unicode_boundaries():
    for code in [*range(256), 0x2028, 0x2029, 0xD800, 0x10FFFF]:
        for delete in (False, True):
            value = "before" + chr(code) + "after"
            assert validation.contains_control_character(value, reject_delete_character=delete) == (
                code < 32 or delete and code == 127)


@pytest.mark.parametrize("compression", ["stored", "deflate"])
def test_full_audit_does_not_rebuild_storage_or_repeat_member_inflation(monkeypatch, compression):
    payload = json.loads(one_module_two_entities_fixture().knowledge_bytes)
    plan = knowledge_packs.build_packed_store(payload, compression=compression)
    reader = knowledge_packs.open_knowledge_store(plan.root_bytes, lambda name, _: plan.objects[name])
    monkeypatch.setattr(knowledge_storage, "build_knowledge_store", lambda *a, **kw: pytest.fail("audit rebuilt storage"))
    original = knowledge_packs.zlib.decompressobj
    calls = []
    def decompressor(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(knowledge_packs.zlib, "decompressobj", decompressor)
    assert reader.materialize() == payload
    assert len(calls) == (len(reader.objects) if compression == "deflate" else 0)
    assert reader.statistics()["logical_objects"] == len(reader.objects)
