"""Logical review completes bounded delivery without weakening snapshot validation."""

from copy import deepcopy
import base64
import hashlib
import json
import shutil
import sys

import pytest

from llm_wiki_cli.cli import main
from llm_wiki_cli.services.knowledge_artifacts import build_knowledge_commit_plan, commit_knowledge_artifacts
from llm_wiki_cli.services.knowledge_index import serialize_knowledge_index
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import knowledge_index_to_payload
from llm_wiki_cli.services.knowledge_storage import canonical_bytes, digest
from llm_wiki_cli.services.knowledge_storage_diagnostics import review_storage, storage_report
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.test_knowledge_loader import _committed_state


def snapshot_tree(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def commit_payload(root, payload, mode):
    plan = build_knowledge_commit_plan(
        root, surface_index_bytes=(root / ".llm-wiki-surface.json").read_bytes(),
        knowledge_index_bytes=serialize_knowledge_index(payload).encode("utf-8"),
        manifest=SyncManifest.load(root), knowledge_format=mode,
    )
    commit_knowledge_artifacts(plan)
    assert storage_report(root, full=True)["ok"]


def review_pair(root, mode="packed-v4-deflate", *, chars=0, duplicates=False):
    left, right = root / "before", root / "after"
    left.mkdir(parents=True)
    _committed_state(left)
    shutil.copytree(left, right)
    state = load_knowledge_state(left)
    assert state.knowledge is not None
    original = knowledge_index_to_payload(state.knowledge)
    for directory, value in ((left, False), (right, 0)):
        payload = deepcopy(original)
        for n in range(12):
            payload.setdefault("extensions", {})[f"acme/delta-{n:02}"] = {
                'unusual / ~ " \\ é\n': [value, "雪\"\\\n" * chars],
            }
        if duplicates and directory == right:
            link = next(row for row in payload["relationships"] if row["kind"] == "links_to")
            payload["relationships"].extend([deepcopy(link)] * 2)
        commit_payload(directory, payload, mode)
    return left, right


def recover_record(root, against, page, row, max_bytes):
    raw = bytearray()
    offset = 0
    while True:
        reply = review_storage(root, against=against, record_index=row["record_index"],
                               review_id=page["review_id"], record_offset=offset, max_bytes=max_bytes)
        assert len(canonical_bytes(reply)) <= max_bytes
        assert reply["offset"] == offset
        raw.extend(base64.b64decode(reply["data_base64"], validate=True))
        if reply["next_offset"] is None:
            assert reply["hash"] == digest(bytes(raw))
            assert len(raw) == reply["bytes"]
            return json.loads(raw)
        assert reply["next_offset"] > offset
        offset = reply["next_offset"]


def collect(root, against=None, *, limit=2, max_bytes=4096, selectors=None):
    cursor = None
    rows = []
    while True:
        page = review_storage(root, against=against, limit=limit, max_bytes=max_bytes,
                              cursor=cursor, selectors=selectors)
        assert len(canonical_bytes(page)) <= max_bytes
        assert len(page["records"]) <= limit
        assert page["offset"] == len(rows)
        assert page["omitted"] == page["total"] - len(page["records"])
        assert page["remaining"] == page["total"] - len(rows) - len(page["records"])
        for row in page["records"]:
            if row.get("values_omitted"):
                assert selectors is None  # Separate scoped follow-up checked below.
                row = recover_record(root, against, page, row, max_bytes)
            rows.append(row)
        cursor = page["next_cursor"]
        if cursor is None:
            assert page["remaining"] == 0
            assert page["enumeration_complete"]
            assert page["complete"] == (page["offset"] == 0 and not page["values_omitted"])
            return rows
        assert page["records"], "a continuation must make progress even for an oversized key"


@pytest.mark.parametrize("mode", ["v1", "sharded-v2", "packed-v3-deflate", "packed-v4-deflate"])
@pytest.mark.parametrize("max_bytes,chars", [(1024, 0), (4096, 1000)])
def test_complete_multi_page_diff_and_exact_oversized_values(tmp_path, mode, max_bytes, chars):
    left, right = review_pair(tmp_path, mode, chars=chars, duplicates=True)
    before = snapshot_tree(tmp_path)
    rows = collect(right, left, max_bytes=max_bytes)
    keys = [row["key"] for row in rows]
    assert keys == sorted(set(keys))
    assert len(rows) == 14
    assert [row["record_index"] for row in rows] == list(range(14))
    deltas = [row for row in rows if row["key"].startswith("extension:acme/")]
    assert len(deltas) == 12
    for row in deltas:
        assert row["change"] == "modified"
        assert list(row["values"]["before"].values())[0][0] is False
        assert type(list(row["values"]["after"].values())[0][0]) is int
        assert list(row["values"]["after"].values())[0][1] == "雪\"\\\n" * chars
    additions = [row for row in rows if row["change"] == "added"]
    assert len(additions) == 2
    assert all(row["key"].startswith("relationship:") for row in additions)
    assert {row["key"].rsplit(":", 1)[1] for row in additions} == {"1", "2"}
    assert snapshot_tree(tmp_path) == before


@pytest.mark.parametrize("changed", ["before", "after"])
def test_continuations_and_record_reads_reject_either_changed_snapshot(tmp_path, changed):
    left, right = review_pair(tmp_path, chars=1000)
    page = review_storage(right, against=left, limit=1, max_bytes=1024)
    root = left if changed == "before" else right
    loaded = load_knowledge_state(root)
    assert loaded.knowledge is not None
    payload = knowledge_index_to_payload(loaded.knowledge)
    payload["extensions"]["acme/new"] = {"changed": True}
    commit_payload(root, payload, "packed-v4-deflate")
    before = snapshot_tree(tmp_path)
    with pytest.raises(ValueError, match="snapshot|scope"):
        review_storage(right, against=left, cursor=page["next_cursor"])
    with pytest.raises(ValueError, match="snapshot|scope"):
        review_storage(right, against=left, record_index=0, review_id=page["review_id"])
    assert snapshot_tree(tmp_path) == before


def test_binding_includes_operation_root_location_and_selected_scope(tmp_path):
    left, right = review_pair(tmp_path)
    page = review_storage(right, against=left, limit=1)
    copy = tmp_path / "copy"
    shutil.copytree(right, copy)
    for root, against in ((copy, left), (right, None), (left, right)):
        with pytest.raises(ValueError, match="snapshot|scope"):
            review_storage(root, against=against, cursor=page["next_cursor"])
    selected = review_storage(right, selectors=["source:src/accounts.py"], limit=1)
    assert selected["validation_scope"] == "selected-records-and-policy"
    assert selected["whole_snapshot_validated"] is False
    assert selected["next_cursor"]
    with pytest.raises(ValueError, match="snapshot|scope"):
        review_storage(right, cursor=selected["next_cursor"])
    with pytest.raises(ValueError, match="snapshot|scope"):
        review_storage(right, selectors=["page:modules/accounts.md"], cursor=selected["next_cursor"])
    row = selected["records"][0]
    part = review_storage(right, selectors=["source:src/accounts.py"], record_index=row["record_index"],
                          review_id=selected["review_id"], max_bytes=1024)
    assert part["validation_scope"] == "selected-records-and-policy"
    assert not part["whole_snapshot_validated"]
    with pytest.raises(ValueError, match="scoped comparison"):
        review_storage(right, against=left, selectors=["source:src/accounts.py"])


def test_oversized_exact_identity_has_bounded_followup(tmp_path, monkeypatch):
    # This is a delivery-boundary control, not an accepted native extension name.
    from llm_wiki_cli.services import knowledge_storage_diagnostics as owner
    key = "record:" + 'é"\\\n' * 5000
    monkeypatch.setattr(owner, "_review_records", lambda root: ({key: {"value": True}}, {"root": str(root)}))
    page = review_storage(tmp_path, max_bytes=1024)
    assert len(canonical_bytes(page)) <= 1024
    assert page["values_omitted"] == 1 and not page["complete"]
    assert page["records"][0]["key_omitted"]
    row = recover_record(tmp_path, None, page, page["records"][0], 1024)
    assert row["key"] == key and row["values"] == {"after": {"value": True}}


def test_empty_added_removed_and_cross_format_semantics(tmp_path):
    left, right = review_pair(tmp_path, "v1")
    state = load_knowledge_state(right)
    assert state.knowledge is not None
    payload = knowledge_index_to_payload(state.knowledge)
    del payload["extensions"]["acme/delta-00"]
    payload["extensions"]["acme/new"] = {"value": 1}
    commit_payload(right, payload, "packed-v4-deflate")
    rows = collect(right, left)
    assert len(rows) == 13
    by_key = {row["key"]: row for row in rows}
    assert by_key["extension:acme/delta-00"]["change"] == "removed"
    assert "after" not in by_key["extension:acme/delta-00"]["values"]
    assert by_key["extension:acme/new"]["change"] == "added"
    empty = review_storage(right, against=right, max_bytes=1024)
    assert empty["total"] == 0 and empty["complete"] and empty["next_cursor"] is None
    assert collect(right, max_bytes=1024)


@pytest.mark.parametrize("options", [
    {"cursor": "bad"}, {"cursor": "x" * 1025}, {"cursor": 1},
    {"record_index": True, "review_id": "a" * 64},
    {"record_index": 0}, {"review_id": "a" * 64}, {"record_offset": 1},
    {"record_index": 0, "review_id": "a" * 64, "record_offset": -1},
    {"record_index": 0, "review_id": "a" * 64, "cursor": "bad"},
])
def test_invalid_requests_fail_without_mutation(tmp_path, options):
    with pytest.raises(ValueError):
        review_storage(tmp_path, **options)
    assert not list(tmp_path.iterdir())


def test_bad_position_and_corrupt_snapshot_do_not_produce_success(tmp_path):
    left, right = review_pair(tmp_path)
    page = review_storage(right, against=left, limit=1)
    for index, offset in ((-1, 0), (12, 0), (0, 1000000)):
        with pytest.raises(ValueError):
            review_storage(right, against=left, record_index=index, review_id=page["review_id"], record_offset=offset)
    (right / ".llm-wiki-knowledge.json").write_bytes(b"{}")
    before = snapshot_tree(tmp_path)
    with pytest.raises(ValueError):
        review_storage(right, against=left, cursor=page["next_cursor"])
    assert snapshot_tree(tmp_path) == before


def test_malformed_cursor_positions_are_rejected_on_valid_inputs(tmp_path):
    left, right = review_pair(tmp_path)
    page = review_storage(right, against=left, limit=1)
    payload = json.loads(base64.urlsafe_b64decode(page["next_cursor"]))
    invalid = ["bad", base64.b64encode(b"[]").decode("ascii")]
    for field, value in (("v", True), ("offset", True), ("offset", 0),
                         ("offset", 12), ("id", "sha256:" + "0" * 64)):
        invalid.append(base64.urlsafe_b64encode(canonical_bytes({**payload, field: value})).decode("ascii"))
    before = snapshot_tree(tmp_path)
    for cursor in invalid:
        with pytest.raises(ValueError, match="cursor: invalid continuation"):
            review_storage(right, against=left, cursor=cursor)
    assert snapshot_tree(tmp_path) == before


def test_record_chunk_byte_accounting_at_small_envelope_boundaries():
    from llm_wiki_cli.services.knowledge_storage_diagnostics import _review_record_chunk
    for length in (1, 9, 99, 999, 1000):
        row = {"record_index": 0, "key": "example", "values": {"after": "雪" * length}}
        for maximum in (1024, 1025, 1026):
            offset = 0
            recovered = bytearray()
            while True:
                part = _review_record_chunk(row, review_id="sha256:" + "0" * 64, offset=offset,
                                            max_bytes=maximum, validation_scope="full-committed-snapshots")
                assert len(canonical_bytes(part)) <= maximum
                recovered.extend(base64.b64decode(part["data_base64"]))
                offset = part["next_offset"]
                if offset is None:
                    break
            assert recovered == canonical_bytes(row)


def test_cli_pages_and_record_chunks_with_exact_json_byte_bound(tmp_path, monkeypatch, capsys):
    left, right = review_pair(tmp_path, chars=1000)
    def command(*extra):
        monkeypatch.setattr(sys, "argv", ["llm-wiki", "knowledge", "diff-storage", "--wiki-dir", str(right),
                                         "--against-wiki", str(left), "--max-bytes", "1024", *extra])
        main()
        text = capsys.readouterr().out
        assert len(text.encode("utf-8")) <= 1024
        return json.loads(text)
    first = command("--limit", "1")
    second = command("--cursor", first["next_cursor"], "--limit", "1")
    assert second["offset"] == 1
    assert first["records"][0]["values_omitted"]
    record = command("--record-index", "0", "--review-id", first["review_id"])
    assert record["next_offset"] is not None
    following = command("--record-index", "0", "--review-id", first["review_id"],
                        "--record-offset", str(record["next_offset"]))
    assert following["offset"] == record["next_offset"]
