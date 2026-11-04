"""Committed implementation gaps stay unavailable during authenticated no-op reuse."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import maintenance_evidence
from llm_wiki_cli.services.maintenance_protocol import snapshot_wiki
from llm_wiki_cli.services.maintenance_state import maintenance_core
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.test_adopted_knowledge_reuse import _sync, _trap_builders


@pytest.fixture(params=("observation-limit", "unsupported-syntax"))
def committed_gap(tmp_path, monkeypatch, request):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    if request.param == "observation-limit":
        # Exercise the real installed bound, rather than mutating the producer
        # configuration while asking it to issue analysis-qualified evidence.
        source = "\n\n".join(f"class Item{index:03d}:\n    pass" for index in range(130)) + "\n"
    else:
        source = "VALUE = 1e999\n\nclass Safe:\n    pass\n"
    Path("src/app.py").write_text(source, encoding="utf-8")
    api.bootstrap_wiki("src", "wiki", knowledge_format="packed-v4-deflate")
    api.adopt_maintenance("src", "wiki", recovery_dir="recovery")
    _sync(rebuild_knowledge=True)
    owner = SyncManifest.load(Path("wiki")).maintenance_state
    assert owner is not None
    gaps = {key: row for key, row in owner["observations"].items()
            if row["implementation"]["unavailable_reason"] == request.param}
    assert gaps, "fixture did not exercise the real implementation gap"
    assert all(row["presence"] == row["target_presence"] == "present" for row in gaps.values())
    return request.param, owner, gaps


def _prepare():
    args = cli._build_parser().parse_args([
        "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--cache-dir", "cache", "--no-plugins",
    ])
    return sync_cmd._prepare_sync_run(sync_cmd._sync_run_options_from_args(args))


def test_current_bounded_gap_reuses_without_changing_review_or_availability(committed_gap, monkeypatch):
    _reason, owner, gaps = committed_gap
    before = snapshot_wiki("wiki")
    _trap_builders(monkeypatch)
    _sync()
    assert snapshot_wiki("wiki") == before
    assert SyncManifest.load(Path("wiki")).maintenance_state == owner
    record_id = next(iter(gaps))
    status = api.get_maintenance_status("src", "wiki", record_id=record_id)
    assert status["state_hash"] is not None
    assert not status["records"][0]["basis_available"]
    assert owner["records"][record_id]["status"] == "pending"
    with pytest.raises(api.WorkspaceStateError) as rejected:
        api.acknowledge_maintenance(
            "src", "wiki", record_id=record_id, expected_state_hash=status["state_hash"],
            expected_basis=owner["observations"][record_id]["basis"],
            actor_kind="agent", actor_id="cannot-acknowledge-a-gap",
        )
    assert rejected.value.code == "maintenance-conflict"
    assert snapshot_wiki("wiki") == before


def test_changed_gap_observation_cannot_use_unchanged_owner(committed_gap, monkeypatch):
    _reason, owner, _gaps = committed_gap
    capture = maintenance_evidence.captured_observations_from_knowledge

    def changed(*args, **kwargs):
        current = capture(*args, **kwargs)
        rows = {key: deepcopy(value) for key, value in current.by_owner.items()}
        row = next(row for row in rows.values() if row["implementation"]["status"] == "unavailable")
        row["implementation"]["unavailable_reason"] = "object-limit"
        return replace(current, by_owner=rows)

    monkeypatch.setattr(maintenance_evidence, "captured_observations_from_knowledge", changed)
    before = snapshot_wiki("wiki")
    assert isinstance(_prepare(), sync_cmd._PreparedSyncRun)
    assert snapshot_wiki("wiki") == before
    assert SyncManifest.load(Path("wiki")).maintenance_state == owner


def test_new_gap_owner_cannot_register_through_noop_reuse(committed_gap, monkeypatch):
    _reason, owner, _gaps = committed_gap
    capture = maintenance_evidence.captured_observations_from_knowledge

    def added(*args, **kwargs):
        current = capture(*args, **kwargs)
        rows = {key: deepcopy(value) for key, value in current.by_owner.items()}
        evidence = deepcopy(next(row["implementation"] for row in rows.values()
                                 if row["implementation"]["status"] == "unavailable"))
        evidence["scope"] = "class"
        evidence["coordinate"] = {"source_path": "app.py", "qualified_owner": "NewGap", "occurrence": 1}
        selected = {"canonical_path": "entities/NewGap.md", "ownership": "semantic",
                    "section_locator": "llm-wiki://entities/NewGap#section/Description~1"}
        observation = maintenance_core().observation(evidence, "sha256:" + "a" * 64, target=selected)
        rows[maintenance_evidence.owner_key(evidence["coordinate"], selected)] = observation
        return replace(current, by_owner=rows, issues=(*current.issues, {
            "reason": evidence["unavailable_reason"], "coordinate": evidence["coordinate"],
            "scope": evidence["scope"], "canonical_path": selected["canonical_path"],
        }))

    monkeypatch.setattr(maintenance_evidence, "captured_observations_from_knowledge", added)
    before = snapshot_wiki("wiki")
    assert isinstance(_prepare(), sync_cmd._PreparedSyncRun)
    assert snapshot_wiki("wiki") == before
    assert SyncManifest.load(Path("wiki")).maintenance_state == owner


def test_untracked_unsupported_gap_can_preserve_an_exact_owner(committed_gap, monkeypatch):
    _reason, owner, _gaps = committed_gap
    capture = maintenance_evidence.captured_observations_from_knowledge

    def untracked(*args, **kwargs):
        current = capture(*args, **kwargs)
        return replace(current, issues=(*current.issues, {
            "reason": "unsupported-producer", "canonical_path": "modules/untracked.md",
            "coordinate": {"source_path": "untracked.js", "qualified_owner": "__module__", "occurrence": 1},
            "scope": "module",
        }))

    monkeypatch.setattr(maintenance_evidence, "captured_observations_from_knowledge", untracked)
    before = snapshot_wiki("wiki")
    _trap_builders(monkeypatch)
    _sync()
    assert snapshot_wiki("wiki") == before
    assert SyncManifest.load(Path("wiki")).maintenance_state == owner


@pytest.mark.parametrize("reason", ("prose-unavailable", "invalid-capture"))
def test_other_capture_failures_cannot_be_treated_as_stable_implementation_gaps(committed_gap, monkeypatch, reason):
    capture = maintenance_evidence.captured_observations_from_knowledge

    def failed(*args, **kwargs):
        current = capture(*args, **kwargs)
        return replace(current, issues=(*current.issues, {"reason": reason, "canonical_path": "modules/app.md"}))

    monkeypatch.setattr(maintenance_evidence, "captured_observations_from_knowledge", failed)
    before = snapshot_wiki("wiki")
    assert isinstance(_prepare(), sync_cmd._PreparedSyncRun)
    assert snapshot_wiki("wiki") == before
