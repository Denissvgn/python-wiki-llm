"""Independent workflow contract controls, outside the scored triage corpus."""

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import analysis_capture
from llm_wiki_cli.services.context_packet import capture_context_read
from llm_wiki_cli.services.maintenance_protocol import ADOPTION_FILENAME
from llm_wiki_cli.services.maintenance_queue import build_maintenance_queue
from llm_wiki_cli.services.maintenance_status import compact_maintenance_summary
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.developer_value.fixtures import POLICY_SOURCE
from tests.test_knowledge_commands import _write_reviewed_description
from tests.test_maintenance_read_projections import _context


CLASS_PATH = "entities/Batch.md"
SOURCE = Path("src/policy.py")
WIKI = Path("wiki")

RESTART_READ_SCRIPT = """\
import json
import os
import sys

sys.path.insert(0, sys.argv[1])
from llm_wiki_cli import api
from llm_wiki_cli.services.context_packet import capture_context_read
from llm_wiki_cli.services.maintenance_queue import build_maintenance_queue
from tests.test_maintenance_read_projections import _context

context, _ = _context(capture_context_read("src", "wiki"))
print(json.dumps({
    "process_id": os.getpid(),
    "status": api.get_maintenance_status("src", "wiki"),
    "queue": build_maintenance_queue("src", "wiki", limit=1000),
    "inspection": api.inspect_concept(
        "llm-wiki://entities/Batch", src_dir="src", wiki_dir="wiki", live=True
    ),
    "context": context,
}))
"""


def _files(root):
    """Include timestamps so rewriting identical bytes cannot pass a read control."""
    return {
        p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


def _create(tmp_path, monkeypatch, capsys, *, adopted=True):
    monkeypatch.chdir(tmp_path)
    SOURCE.parent.mkdir()
    SOURCE.write_text(POLICY_SOURCE, encoding="utf-8")
    api.bootstrap_wiki("src", "wiki")
    if adopted:
        api.adopt_maintenance("src", "wiki", recovery_dir="recovery")
    capsys.readouterr()
    return tmp_path


@pytest.fixture
def owned(tmp_path, monkeypatch, capsys):
    return _create(tmp_path, monkeypatch, capsys)


def _state():
    value = SyncManifest.load(WIKI).maintenance_state
    assert value is not None
    return value


def _sync(capsys):
    with patch.object(
        sys,
        "argv",
        ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"],
    ):
        cli.main()
    capsys.readouterr()


def _acknowledge_all():
    original = api.get_maintenance_status("src", "wiki")
    assert original["records"]
    for previous in original["records"]:
        status = api.get_maintenance_status(
            "src", "wiki", record_id=previous["record_id"]
        )
        record = status["records"][0]
        assert record["expected_basis"] is not None
        result = _ack(status, record)
        assert result["changed"] and result["governance_effect"] == "none"
        assert result["actor"] == {
            "kind": "agent",
            "actor_id": "workflow-control",
            "authority": "ordinary-maintenance",
        }
    current = api.get_maintenance_status("src", "wiki")
    assert all(row["effective_status"] == "acknowledged" for row in current["records"])
    assert not (WIKI / ".llm-wiki-governance.json").exists()
    return current


def _ack(status, record):
    return api.acknowledge_maintenance(
        "src",
        "wiki",
        record_id=record["record_id"],
        expected_state_hash=status["state_hash"],
        expected_basis=record["expected_basis"],
        actor_kind="agent",
        actor_id="workflow-control",
    )


def _inspection_maintenance(result):
    if "maintenance" in result:
        return result["maintenance"]
    return result["concept"]["concept"]["maintenance"]


def _consistent_reads(root, *, paths=(CLASS_PATH,)):
    """Assert qualifications against status, not the queue's own classifications."""
    before = _files(root)
    status = api.get_maintenance_status("src", "wiki")
    captured = capture_context_read("src", "wiki")
    report = captured.knowledge_view.maintenance_report
    assert report is not None
    response, _ = _context(captured)
    expected = compact_maintenance_summary(status)
    assert compact_maintenance_summary(report) == expected
    assert response["knowledge"]["maintenance"] == expected
    queue = build_maintenance_queue("src", "wiki", limit=1000)
    assert queue["advisory"] is True and "exit_code" not in queue
    assert queue["returned"] + queue["omitted"] == queue["total"]
    assert queue["omitted"] == 0
    for path in paths:
        item = next(row for row in queue["items"] if row["path"] == path)
        scoped = report.for_path(path)
        assert item["maintenance"] == compact_maintenance_summary(scoped)
        inspected = api.inspect_concept(
            "llm-wiki://" + path[:-3], src_dir="src", wiki_dir="wiki", live=True
        )
        maintenance = _inspection_maintenance(inspected)
        assert maintenance["summary"] == item["maintenance"]
        assert {row["record_id"] for row in maintenance["records"]} == {
            row["record_id"] for row in scoped["records"]
        }
        for row in maintenance["records"]:
            status_row = next(
                value
                for value in status["records"]
                if value["record_id"] == row["record_id"]
            )
            assert row["qualification"] == status_row["qualification"]
            assert row["effective_status"] == status_row["effective_status"]
            assert row["expected_basis"] == status_row["expected_basis"]
    assert _files(root) == before
    return status, queue


@pytest.mark.parametrize("change", ["source", "prose"])
def test_acknowledged_edit_surfaces_pending_and_survives_sync_restart(
    owned, capsys, change
):
    _acknowledge_all()
    previous = deepcopy(_state())
    if change == "source":
        SOURCE.write_text(POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"))
        reason = "executable-syntax-changed"
    else:
        _write_reviewed_description(
            WIKI / CLASS_PATH, "Keep the corrected authored rationale."
        )
        reason = "prose-changed"
    prose = (WIKI / CLASS_PATH).read_bytes()
    status, queue = _consistent_reads(owned)
    affected = [row for row in status["records"] if reason in row["reasons"]]
    assert affected and all(
        row["recorded_status"] == "acknowledged"
        and row["effective_status"] == "pending"
        for row in affected
    )
    item = next(row for row in queue["items"] if row["path"] == CLASS_PATH)
    assert any(row["code"] == "maintenance:" + reason for row in item["reasons"])
    if change == "prose":
        assert status["requires_sync"] and item["maintenance"]["requires_sync"]
    _sync(capsys)
    state = deepcopy(_state())
    assert set(state["records"]) == set(previous["records"])
    for row in affected:
        record_id = row["record_id"]
        assert state["records"][record_id]["status"] == "pending"
        assert state["records"][record_id]["current_acknowledgment_id"] is None
        assert (
            state["records"][record_id]["acknowledgment_history"]
            == previous["records"][record_id]["acknowledgment_history"]
        )
    if change == "prose":
        assert (WIKI / CLASS_PATH).read_bytes() == prose
    _sync(capsys)
    assert _state() == state
    current, _ = _consistent_reads(owned)
    assert current["adoption_id"] == status["adoption_id"]
    assert all(
        next(row for row in current["records"] if row["record_id"] == old["record_id"])[
            "effective_status"
        ]
        == "pending"
        for old in affected
    )


def test_comment_only_edit_cannot_invent_executable_drift(owned, capsys):
    _acknowledge_all()
    previous = deepcopy(_state())
    SOURCE.write_text("# A formatting-only source explanation.\n" + POLICY_SOURCE)
    status = api.get_maintenance_status("src", "wiki")
    assert all(
        "executable-syntax-changed" not in row["reasons"] for row in status["records"]
    )
    # Exact source bytes belong to the review basis even when syntax is unchanged.
    assert all("source-basis-changed" in row["reasons"] for row in status["records"])
    _, queue = _consistent_reads(owned)
    assert all(
        reason["code"] != "maintenance:executable-syntax-changed"
        for item in queue["items"]
        for reason in item["reasons"]
    )
    _sync(capsys)
    current = _state()
    for record_id, row in current["records"].items():
        assert (
            row["acknowledgment_history"]
            == previous["records"][record_id]["acknowledgment_history"]
        )
        assert "executable-syntax-changed" not in row["reasons"]
    assert not (WIKI / ".llm-wiki-governance.json").exists()


@pytest.mark.parametrize("adopted", [False, True], ids=["legacy", "adopted"])
def test_source_edit_sync_does_not_implicitly_adopt_or_acknowledge(
    tmp_path, monkeypatch, capsys, adopted
):
    root = _create(tmp_path, monkeypatch, capsys, adopted=adopted)
    SOURCE.write_text(POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    before = _files(root)
    status = api.get_maintenance_status("src", "wiki")
    queue = build_maintenance_queue("src", "wiki", limit=1000)
    assert queue["advisory"] and "exit_code" not in queue
    assert _files(root) == before
    _sync(capsys)
    _sync(capsys)
    fresh = api.get_maintenance_status("src", "wiki")
    if adopted:
        assert fresh["adoption_id"] == status["adoption_id"]
        assert all(row["effective_status"] == "pending" for row in fresh["records"])
        assert all(not row["acknowledgment_history"] for row in fresh["records"])
    else:
        assert fresh["availability"] == status["availability"] == "unadopted"
        assert fresh["records"] == [] and fresh["state_hash"] is None
        assert SyncManifest.load(WIKI).maintenance_state is None
        assert not (WIKI / ADOPTION_FILENAME).exists()
    assert not (WIKI / ".llm-wiki-governance.json").exists()


@pytest.mark.parametrize("removal", ["delete", "deselect"])
def test_removal_preserves_record_history_and_discloses_loss_of_basis(
    owned, capsys, removal
):
    _acknowledge_all()
    previous = deepcopy(_state())
    if removal == "delete":
        SOURCE.unlink()
    else:
        Path("src/.gitignore").write_text("policy.py\n")
    _sync(capsys)
    current = deepcopy(_state())
    assert set(current["records"]) == set(previous["records"])
    status, _ = _consistent_reads(owned)
    assert all(row["effective_status"] == "pending" for row in status["records"])
    for record_id, record in current["records"].items():
        assert (
            record["acknowledgment_history"]
            == previous["records"][record_id]["acknowledgment_history"]
        )
        assert record["current_acknowledgment_id"] is None
        assert (
            current["observations"][record_id]["target"]
            == previous["observations"][record_id]["target"]
        )
        if removal == "delete":
            assert current["observations"][record_id]["presence"] == "deleted"
            assert "source-deleted" in record["reasons"]
        else:
            assert current["observations"][record_id]["presence"] != "deleted"
    _sync(capsys)
    assert _state() == current


@pytest.mark.parametrize("move", ["verified", "ambiguous"])
def test_moves_retain_ids_and_never_transfer_review_authority(owned, capsys, move):
    _acknowledge_all()
    previous = deepcopy(_state())
    class_ids = {
        record_id
        for record_id, observation in previous["observations"].items()
        if observation["implementation"]["scope"] == "class"
    }
    assert class_ids
    if move == "verified":
        SOURCE.rename("src/moved.py")
    else:
        SOURCE.unlink()
        Path("src/one.py").write_text(POLICY_SOURCE)
        Path("src/two.py").write_text(POLICY_SOURCE)
    _sync(capsys)
    current = deepcopy(_state())
    paths = set()
    for record_id in class_ids:
        record = current["records"][record_id]
        observation = current["observations"][record_id]
        assert (
            record["status"] == "pending"
            and record["current_acknowledgment_id"] is None
        )
        assert (
            record["acknowledgment_history"]
            == previous["records"][record_id]["acknowledgment_history"]
        )
        paths.add(observation["target"]["canonical_path"])
        if move == "verified":
            assert observation["coordinate"]["source_path"] == "moved.py"
            assert len(record["coordinate_history"]) == 2
            assert "confirmed-move-basis-changed" in record["reasons"]
        else:
            assert record["mapping"]["state"] == "ambiguous"
            assert len(record["mapping"]["candidates"]) == 2
            paths.update(
                candidate["target"]["canonical_path"]
                for candidate in record["mapping"]["candidates"]
            )
    status, queue = _consistent_reads(owned, paths=sorted(paths))
    for record_id in class_ids:
        row = next(row for row in status["records"] if row["record_id"] == record_id)
        assert row["effective_status"] == "pending"
        if move == "ambiguous":
            assert row["expected_basis"] is None
            targets = [
                row["target"],
                *(candidate["target"] for candidate in row["mapping"]["candidates"]),
            ]
            for target in targets:
                item = next(
                    item
                    for item in queue["items"]
                    if item["path"] == target["canonical_path"]
                )
                assert any(
                    value["target"] == target for value in item["semantic_targets"]
                )
    _sync(capsys)
    assert _state() == current


@pytest.mark.parametrize("change", ["source", "prose", "state-hash"])
def test_stale_acknowledgment_conflict_preserves_authority_and_cannot_clear_queue(
    owned, change
):
    # An identical acknowledged actor/basis replay is intentionally idempotent,
    # so exercise stale CAS on a record that has not already been acknowledged.
    status = (
        api.get_maintenance_status("src", "wiki")
        if change == "state-hash"
        else _acknowledge_all()
    )
    record = next(
        row
        for row in status["records"]
        if row["target"]["canonical_path"] == CLASS_PATH
    )
    if change == "source":
        SOURCE.write_text(POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    elif change == "prose":
        _write_reviewed_description(
            WIKI / CLASS_PATH, "Correct the stale source explanation."
        )
    else:
        status = {**status, "state_hash": "sha256:" + "0" * 64}
    before = (_files(WIKI), _files(SOURCE.parent))
    with pytest.raises(api.WorkspaceStateError) as failure:
        _ack(status, record)
    assert failure.value.code == "maintenance-conflict"
    # Rejected writes can capture recovery preimages outside the protected wiki.
    assert (_files(WIKI), _files(SOURCE.parent)) == before
    if change != "state-hash":
        fresh, queue = _consistent_reads(owned)
        assert any(row["effective_status"] == "pending" for row in fresh["records"])
        assert any(
            item.get("maintenance", {}).get("pending", 0) for item in queue["items"]
        )


@pytest.mark.parametrize("unavailable", ["missing-source", "producer-incompatible"])
def test_missing_or_incompatible_inputs_never_reuse_old_review(
    owned, monkeypatch, unavailable
):
    status = _acknowledge_all()
    if unavailable == "missing-source":
        SOURCE.unlink()
    else:
        original = analysis_capture.implementation_hash

        def incompatible(root, paths):
            return (
                "sha256:"
                + sha256(("new-producer:" + original(root, paths)).encode()).hexdigest()
            )

        monkeypatch.setattr(analysis_capture, "implementation_hash", incompatible)
    current, queue = _consistent_reads(owned)
    assert current["records"]
    assert all(row["effective_status"] == "pending" for row in current["records"])
    for row in current["records"]:
        if unavailable == "missing-source":
            assert row["expected_basis"] is None and not row["basis_available"]
            assert row["qualification"] == "current-basis-unavailable"
        else:
            assert "producer-incompatible" in row["reasons"]
            assert row["qualification"] == "current-capture" and row["basis_available"]
            previous = next(
                old for old in status["records"] if old["record_id"] == row["record_id"]
            )
            assert row["expected_basis"] is not None
            assert previous["expected_basis"] is not None
            assert (
                row["expected_basis"]["comparison_id"]
                != previous["expected_basis"]["comparison_id"]
            )
    assert any(
        reason["code"]
        in {
            "maintenance:current-basis-unavailable",
            "maintenance:producer-incompatible",
        }
        for item in queue["items"]
        for reason in item["reasons"]
    )
    before = (_files(WIKI), _files(SOURCE.parent))
    with pytest.raises(api.WorkspaceStateError):
        _ack(status, status["records"][0])
    assert (_files(WIKI), _files(SOURCE.parent)) == before


def test_snapshot_reads_disclose_noncurrent_review_without_source_analysis(
    owned, monkeypatch
):
    _acknowledge_all()
    before = _files(owned)
    monkeypatch.setattr(
        "llm_wiki_cli.services.context_packet.capture_context_read",
        lambda *args, **kwargs: pytest.fail("snapshot performed live source analysis"),
    )
    status = api.get_maintenance_status("src", "wiki", live=False)
    inspected = api.inspect_concept(
        "llm-wiki://entities/Batch", wiki_dir="wiki", live=False
    )
    maintenance = _inspection_maintenance(inspected)
    assert status["analysis_scope"] == maintenance["analysis_scope"] == "snapshot"
    assert (
        not status["live_evaluation_performed"]
        and not maintenance["live_evaluation_performed"]
    )
    for row in [*status["records"], *maintenance["records"]]:
        assert row["recorded_status"] == "acknowledged"
        assert row["effective_status"] is None and row["expected_basis"] is None
        assert row["qualification"] == "snapshot"
    assert _files(owned) == before


def test_drift_queue_cli_remains_advisory_and_does_not_create_review_authority(
    owned, capsys
):
    _acknowledge_all()
    SOURCE.write_text(POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    before = _files(owned)
    expected = build_maintenance_queue("src", "wiki", limit=1000)
    with patch.object(
        sys,
        "argv",
        [
            "llm-wiki",
            "queue",
            "--src-dir",
            "src",
            "--wiki-dir",
            "wiki",
            "--limit",
            "1000",
            "--format",
            "json",
        ],
    ):
        assert cli.main() is None
    emitted = json.loads(capsys.readouterr().out)
    assert emitted == expected
    assert emitted["advisory"] is True and "exit_code" not in emitted
    assert any(
        item.get("maintenance", {}).get("pending", 0) for item in emitted["items"]
    )
    assert _files(owned) == before
    assert not (WIKI / ".llm-wiki-governance.json").exists()


def test_fresh_process_reads_persisted_pending_review_without_writes(owned, capsys):
    _acknowledge_all()
    original = deepcopy(_state())
    SOURCE.write_text(POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    _sync(capsys)
    pending = deepcopy(_state())
    _sync(capsys)
    assert _state() == pending
    expected_status, expected_queue = _consistent_reads(owned)
    expected_pending_ids = {
        row["record_id"]
        for row in expected_status["records"]
        if row["effective_status"] == "pending"
    }
    assert expected_pending_ids == set(original["records"])
    assert all(
        "executable-syntax-changed" in row["reasons"]
        for row in expected_status["records"]
    )
    before = _files(owned)
    project_root = Path(__file__).resolve().parents[1]
    project_python = project_root / ".venv/bin/python"
    assert project_python.is_file()
    compile(RESTART_READ_SCRIPT, "restart-read-control", "exec")
    restarted = subprocess.run(
        [
            str(project_python),
            "-B",
            "-c",
            RESTART_READ_SCRIPT,
            str(project_root),
        ],
        cwd=owned,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert restarted.returncode == 0, restarted.stderr
    payload = json.loads(restarted.stdout)
    assert payload["process_id"] != os.getpid()
    assert payload["status"] == expected_status
    assert payload["queue"] == expected_queue
    assert {
        row["record_id"]
        for row in payload["status"]["records"]
        if row["effective_status"] == "pending"
    } == expected_pending_ids
    item = next(row for row in payload["queue"]["items"] if row["path"] == CLASS_PATH)
    maintenance = _inspection_maintenance(payload["inspection"])
    assert maintenance["summary"] == item["maintenance"]
    assert all(
        row["effective_status"] == "pending"
        and row["qualification"] == "current-capture"
        and "executable-syntax-changed" in row["reasons"]
        for row in maintenance["records"]
    )
    assert payload["context"]["knowledge"][
        "maintenance"
    ] == compact_maintenance_summary(expected_status)
    assert _files(owned) == before
    assert _state() == pending
    assert not (WIKI / ".llm-wiki-governance.json").exists()
