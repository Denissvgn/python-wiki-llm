"""Public ordinary review operations share exact capture and conflict behavior."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from unittest.mock import patch
from typing import Any, cast, get_args, get_type_hints

import pytest

from llm_wiki_cli import api, api_types, cli
from llm_wiki_cli.commands.maintenance_cmd import _render_status
from llm_wiki_cli.services.maintenance_protocol import (
    ADOPTION_FILENAME,
    snapshot_wiki,
    save_recovery_snapshot,
    load_adoption_marker,
)
from llm_wiki_cli.services.request_json import MAX_REQUEST_BYTES
from tests.developer_value.fixtures import POLICY_SOURCE


def _bytes(wiki):
    return {
        p.relative_to(wiki).as_posix(): p.read_bytes()
        for p in wiki.rglob("*")
        if p.is_file() and not p.name.endswith(".lock")
    }


def _project(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_bytes(POLICY_SOURCE.encode())
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    capsys.readouterr()
    result = api.adopt_maintenance("src", "wiki", recovery_dir="recovery")
    assert result["changed"]
    status = api.get_maintenance_status("src", "wiki")
    assert status["records"]
    return Path("wiki"), status, status["records"][0]


def _cli(capsys, *arguments):
    with patch.object(sys, "argv", ["llm-wiki", "maintenance", *arguments]):
        cli.main()
    return json.loads(capsys.readouterr().out)


def _ack(status, record, **options):
    return api.acknowledge_maintenance(
        "src",
        "wiki",
        record_id=record["record_id"],
        expected_state_hash=status["state_hash"],
        expected_basis=record["expected_basis"],
        actor_kind="agent",
        actor_id="review-agent",
        **options,
    )


def test_cli_python_status_parity_and_snapshot_are_read_only(
    tmp_path, monkeypatch, capsys
):
    wiki, status, record = _project(tmp_path, monkeypatch, capsys)
    before = _bytes(wiki)
    emitted = _cli(
        capsys, "status", "--src-dir", "src", "--wiki-dir", "wiki", "--format", "json"
    )
    assert emitted == status
    snapshot = api.get_maintenance_status(
        "src", "wiki", live=False, record_id=record["record_id"]
    )
    assert snapshot["live_evaluation_performed"] is False
    assert snapshot["records"][0]["effective_status"] is None
    assert snapshot["records"][0]["expected_basis"] is None
    assert _bytes(wiki) == before


def test_public_record_qualification_matches_real_current_snapshot_and_unavailable_values(
    tmp_path, monkeypatch, capsys
):
    _, status, record = _project(tmp_path, monkeypatch, capsys)
    declared = get_args(
        get_type_hints(api_types.MaintenanceRecordResult)["qualification"]
    )
    assert set(declared) == {"snapshot", "current-capture", "current-basis-unavailable"}
    assert record["qualification"] == "current-capture"
    snapshot = api.get_maintenance_status("src", "wiki", live=False)
    assert all(row["qualification"] == "snapshot" for row in snapshot["records"])
    Path("src/policy.py").unlink()
    missing = api.get_maintenance_status("src", "wiki", record_id=record["record_id"])
    assert missing["records"][0]["qualification"] == "current-basis-unavailable"
    assert missing["records"][0]["expected_basis"] is None
    assert all(
        isinstance(row["qualification"], str) and row["qualification"] in declared
        for payload in (status, snapshot, missing)
        for row in payload["records"]
    )


def test_text_status_retains_distinct_candidate_page_targets():
    rendered = _render_status(
        {
            "availability": "available",
            "analysis_scope": "full-inventory",
            "records": [
                {
                    "record_id": "record",
                    "target": {
                        "canonical_path": "old.md",
                        "section_locator": "behavior",
                    },
                    "effective_status": "pending",
                    "recorded_status": "pending",
                    "mapping": {
                        "state": "ambiguous",
                        "candidates": [
                            {
                                "target": {
                                    "canonical_path": "one.md",
                                    "section_locator": "behavior",
                                }
                            },
                            {
                                "target": {
                                    "canonical_path": "two.md",
                                    "section_locator": "behavior",
                                }
                            },
                        ],
                    },
                }
            ],
        }
    )
    assert "candidate: one.md :: behavior" in rendered
    assert "candidate: two.md :: behavior" in rendered


def test_api_acknowledgment_records_agent_without_governance_and_replays(
    tmp_path, monkeypatch, capsys
):
    wiki, status, record = _project(tmp_path, monkeypatch, capsys)
    result = _ack(status, record)
    assert result["changed"] and result["governance_effect"] == "none"
    assert result["actor"] == {
        "kind": "agent",
        "actor_id": "review-agent",
        "authority": "ordinary-maintenance",
    }
    assert not (wiki / ".llm-wiki-governance.json").exists()
    after = _bytes(wiki)
    repeated = _ack(status, record)
    assert repeated["changed"] is False
    assert _bytes(wiki) == after
    fresh = api.get_maintenance_status("src", "wiki", record_id=record["record_id"])
    assert fresh["records"][0]["effective_status"] == "acknowledged"


def test_cli_acknowledgment_uses_exact_basis_file_and_explicit_actor(
    tmp_path, monkeypatch, capsys
):
    _, status, record = _project(tmp_path, monkeypatch, capsys)
    Path("basis.json").write_text(json.dumps(record["expected_basis"]))
    result = _cli(
        capsys,
        "acknowledge",
        "--src-dir",
        "src",
        "--wiki-dir",
        "wiki",
        "--record-id",
        record["record_id"],
        "--expected-state-hash",
        status["state_hash"],
        "--basis-file",
        "basis.json",
        "--actor-kind",
        "human",
        "--actor-id",
        "local-reviewer",
    )
    assert result["actor"]["kind"] == "human"
    assert result["actor"]["authority"] == "ordinary-maintenance"
    assert result["governance_effect"] == "none"


@pytest.mark.parametrize("change", ["source", "prose", "state"])
def test_stale_review_is_workspace_conflict_and_leaves_authority_unchanged(
    tmp_path, monkeypatch, capsys, change
):
    wiki, status, record = _project(tmp_path, monkeypatch, capsys)
    if change == "source":
        Path("src/policy.py").write_bytes(
            POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]").encode()
        )
    elif change == "prose":
        page = wiki / "entities/Batch.md"
        page.write_bytes(page.read_bytes() + b"\nNew authored rationale.\n")
    else:
        status = {**status, "state_hash": "sha256:" + "0" * 64}
    before = _bytes(wiki)
    with pytest.raises(api.WorkspaceStateError) as error:
        _ack(status, record)
    assert error.value.code == "maintenance-conflict"
    assert _bytes(wiki) == before


@pytest.mark.parametrize("invalid", ["nan", "actor", "state-hash", "unknown-field"])
def test_invalid_review_inputs_are_rejected_before_writes(
    tmp_path, monkeypatch, capsys, invalid
):
    wiki, status, record = _project(tmp_path, monkeypatch, capsys)
    assert record["expected_basis"] is not None
    expected = cast(dict[str, Any], deepcopy(record["expected_basis"]))
    actor = "agent"
    if invalid == "nan":
        expected["source_hash"] = float("nan")
    elif invalid == "actor":
        actor = "human-governance"
    elif invalid == "state-hash":
        status = {**status, "state_hash": "not-a-hash"}
    else:
        expected["unexpected"] = True
    before = _bytes(wiki)
    with pytest.raises(api.InvalidRequestError):
        api.acknowledge_maintenance(
            "src",
            "wiki",
            record_id=record["record_id"],
            expected_state_hash=cast(str, status["state_hash"]),
            expected_basis=expected,
            actor_kind=cast(Any, actor),
            actor_id="review-agent",
        )
    assert _bytes(wiki) == before


@pytest.mark.parametrize(
    "payload",
    [b'{"x":1,"x":2}', b'{"x":NaN}', b"[" + b" " * MAX_REQUEST_BYTES + b"]"],
    ids=["duplicate", "nonfinite", "oversize"],
)
def test_cli_basis_json_is_strict_and_bounded(tmp_path, monkeypatch, capsys, payload):
    wiki, status, record = _project(tmp_path, monkeypatch, capsys)
    Path("basis.json").write_bytes(payload)
    before = _bytes(wiki)
    with pytest.raises(SystemExit) as error:
        _cli(
            capsys,
            "acknowledge",
            "--src-dir",
            "src",
            "--wiki-dir",
            "wiki",
            "--record-id",
            record["record_id"],
            "--expected-state-hash",
            status["state_hash"],
            "--basis-file",
            "basis.json",
            "--actor-kind",
            "agent",
            "--actor-id",
            "review-agent",
        )
    assert error.value.code == 1
    emitted = json.loads(capsys.readouterr().out)
    assert emitted["error"]["code"] == "invalid-request"
    assert _bytes(wiki) == before


def test_adopted_integrity_failure_preserves_specific_api_taxonomy(
    tmp_path, monkeypatch, capsys
):
    wiki, _, _ = _project(tmp_path, monkeypatch, capsys)
    marker = wiki / ADOPTION_FILENAME
    marker.write_bytes(marker.read_bytes() + b"\n")
    with pytest.raises(api.ArtifactIntegrityError) as error:
        api.get_maintenance_status("src", "wiki")
    assert error.value.code == "maintenance-integrity"
    assert error.value.details is not None
    assert error.value.details["reason"] == "adoption-invalid"


def test_public_recovery_keeps_explicit_identity_and_requires_sync_qualification(
    tmp_path, monkeypatch, capsys
):
    wiki, status, _ = _project(tmp_path, monkeypatch, capsys)
    marker = load_adoption_marker(wiki)
    assert marker is not None
    identity = status["adoption_id"]
    assert isinstance(identity, str)
    save_recovery_snapshot(
        Path("committed-recovery"), snapshot_wiki(wiki), marker=marker, kind="committed"
    )
    (wiki / ADOPTION_FILENAME).unlink()
    result = api.recover_maintenance(
        "wiki", recovery_dir="committed-recovery", expected_adoption_id=identity
    )
    assert result["restored"]
    assert result["requires_sync"] is False and result["prose_basis_validated"] is True
    page = wiki / "entities/Batch.md"
    page.write_bytes(page.read_bytes() + b"\nPreserved unanchored authored bytes.\n")
    authored = page.read_bytes()
    save_recovery_snapshot(
        Path("captured-recovery"),
        snapshot_wiki(wiki),
        marker=marker,
        kind="captured-preimage",
    )
    with pytest.raises(api.InvalidRequestError):
        api.recover_maintenance(
            "wiki", recovery_dir="captured-recovery", expected_adoption_id=identity
        )
    captured = api.recover_maintenance(
        "wiki",
        recovery_dir="captured-recovery",
        expected_adoption_id=identity,
        allow_captured_preimage=True,
    )
    assert (
        captured["requires_sync"] is True and captured["prose_basis_validated"] is False
    )
    assert page.read_bytes() == authored


@pytest.mark.parametrize(
    "arguments",
    [
        ["acknowledge", "--record-id", "id"],
        ["adopt"],
        ["status", "--limit", "0"],
        ["recover", "--recovery-dir", "recovery"],
    ],
    ids=[
        "missing-actor-basis",
        "missing-recovery",
        "invalid-limit",
        "missing-identity",
    ],
)
def test_cli_requires_explicit_review_and_recovery_inputs(arguments):
    with pytest.raises(SystemExit) as error:
        cli._build_parser().parse_args(["maintenance", *arguments])
    assert error.value.code == 2
