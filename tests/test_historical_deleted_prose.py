"""Historical source deletion never hides exact retained or restored prose."""

from __future__ import annotations

from copy import deepcopy

import pytest

from llm_wiki_cli.services.maintenance_evidence import (
    MaintenanceCapture, _unavailable, owner_key, reconcile_pending_maintenance,
)
from llm_wiki_cli.services.maintenance_projection import (
    project_maintenance_knowledge, validate_maintenance_projection, validate_maintenance_prose,
)
from llm_wiki_cli.services.maintenance_state import MaintenanceError, canonical_hash, maintenance_core
from llm_wiki_cli.services.python_implementation import comparison_id
from tests.test_maintenance_reconciliation import (
    MARKDOWN, acknowledged, adopted, capture, marker, project as project,
)


def _deleted_history(project):
    guard, initial = adopted(project)
    reviewed = acknowledged(initial)
    removed = capture(project, previous=reviewed, markdown="# Batch\n", missing=True)
    deleted = reconcile_pending_maintenance(reviewed, guard, removed)
    assert all(row["presence"] == row["target_presence"] == "deleted"
               and row["basis"]["prose_hash"] is None for row in deleted["observations"].values())
    return guard, deleted


def test_restored_selected_source_prose_updates_historical_targets_without_revival_or_ack(project, monkeypatch):
    guard, deleted = _deleted_history(project)
    before = deepcopy(deleted)
    fresh = capture(project, previous=deleted)
    fresh_before = fresh.to_payload()
    assert all(row["presence"] == "present" and row["implementation"]["status"] == "available"
               for row in fresh.by_owner.values())
    core = maintenance_core()
    transition = core.transition
    events = []

    def counted(state, event, basis):
        events.append(event["kind"])
        return transition(state, event, basis)

    with monkeypatch.context() as count:
        count.setattr(core, "transition", counted)
        result = reconcile_pending_maintenance(deleted, guard, fresh)
        assert events == ["delete"] * len(deleted["records"])
        events.clear()
        repeated = reconcile_pending_maintenance(result, guard, fresh)
        assert events == []
    assert repeated == result and canonical_hash(repeated) == canonical_hash(result)
    assert deleted == before and fresh.to_payload() == fresh_before
    assert set(result["records"]) == set(deleted["records"])
    for record_id, old in deleted["observations"].items():
        current = result["observations"][record_id]
        observed = fresh.by_owner[owner_key(old["coordinate"], old["target"])]
        assert current["presence"] == "deleted" and current["target_presence"] == "present"
        assert current["implementation"] == old["implementation"]
        assert current["implementation"]["status"] == "unavailable"
        assert current["implementation"]["unavailable_reason"] == "missing-source"
        assert current["basis"]["source_hash"] is None
        assert current["basis"]["prose_hash"] == observed["basis"]["prose_hash"]
        record = result["records"][record_id]
        assert record["status"] == "pending" and record["current_acknowledgment_id"] is None
        for name in ("mapping", "last_present_basis", "coordinate_history", "target_history", "acknowledgment_history"):
            assert record[name] == deleted["records"][record_id][name]


def test_historical_prose_refresh_retains_strict_exact_byte_and_deleted_target_guards(project):
    guard, deleted = _deleted_history(project)
    fresh = capture(project, previous=deleted)
    result = reconcile_pending_maintenance(deleted, guard, fresh)
    knowledge = project[0]
    raw = {"entities/Batch.md": MARKDOWN.encode()}
    with pytest.raises(MaintenanceError, match="deleted semantic target"):
        validate_maintenance_prose(deleted, knowledge, raw)
    projected = project_maintenance_knowledge(knowledge, result, guard)
    validate_maintenance_projection(projected, state=result, marker=guard, raw_content_by_page=raw)
    with pytest.raises(MaintenanceError, match="prose-binding"):
        validate_maintenance_prose(result, knowledge, {
            "entities/Batch.md": MARKDOWN.replace("Owned purpose.", "Changed exact prose.").encode(),
        })


@pytest.mark.parametrize("unknown", ["prose", "ambiguous-source"])
def test_unknown_capture_cannot_restore_a_historical_target(project, unknown):
    guard, deleted = _deleted_history(project)
    fresh = capture(project, previous=deleted)
    core = maintenance_core()
    unavailable = {}
    for key, row in fresh.by_owner.items():
        implementation = deepcopy(row["implementation"])
        if unknown == "ambiguous-source":
            implementation = _unavailable(implementation, reason="ambiguous-owner",
                                          source_hash=implementation["source_hash"])
        unavailable[key] = core.observation(
            implementation, None if unknown == "prose" else row["basis"]["prose_hash"],
            presence="present" if unknown == "prose" else "ambiguous", target=deepcopy(row["target"]),
        )
    result = reconcile_pending_maintenance(deleted, guard, MaintenanceCapture(unavailable))
    assert result == deleted


def test_divergent_deleted_peer_producers_keep_conservative_history_and_strict_prose_guard(project, monkeypatch):
    guard, deleted = _deleted_history(project)
    divergent = deepcopy(deleted)
    record_id = next(iter(divergent["records"]))
    row = divergent["observations"][record_id]
    row["implementation"]["producer"]["parser_version"] = "3.14.6"
    row["implementation"]["comparison_id"] = comparison_id(row["implementation"]["producer"])
    core = maintenance_core()
    row["basis"] = core.basis_for(row["implementation"], None, row["target"])
    core.validate_state(divergent)  # Distinct unavailable historical producers are legal.
    before = deepcopy(divergent)
    fresh = capture(project, previous=divergent)
    with monkeypatch.context() as unchanged:
        unchanged.setattr(core, "transition", lambda *args: pytest.fail("divergent history must not be homogenized"))
        result = reconcile_pending_maintenance(divergent, guard, fresh)
    assert result == before and divergent == before
    with pytest.raises(MaintenanceError, match="deleted semantic target"):
        validate_maintenance_prose(result, project[0], {"entities/Batch.md": MARKDOWN.encode()})


def test_truly_absent_target_stays_deleted_and_can_be_deleted_again_after_prose_restoration(project):
    guard, deleted = _deleted_history(project)
    absent = capture(project, previous=deleted, markdown="# Batch\n")
    assert reconcile_pending_maintenance(deleted, guard, absent) == deleted
    restored = reconcile_pending_maintenance(deleted, guard, capture(project, previous=deleted))
    absent_again = capture(project, previous=restored, markdown="# Batch\n")
    result = reconcile_pending_maintenance(restored, guard, absent_again)
    assert all(row["presence"] == row["target_presence"] == "deleted"
               and row["basis"]["prose_hash"] is None for row in result["observations"].values())
    validate_maintenance_prose(result, project[0], {"entities/Batch.md": b"# Batch\n"})


def test_active_source_deleted_target_guard_remains_strict(project):
    guard, active = adopted(project)
    absent = capture(project, previous=active, markdown="# Batch\n")
    result = reconcile_pending_maintenance(active, guard, absent)
    assert all(row["presence"] == "present" and row["target_presence"] == "deleted"
               for row in result["observations"].values())
    with pytest.raises(MaintenanceError, match="deleted semantic target"):
        validate_maintenance_prose(result, project[0], {"entities/Batch.md": MARKDOWN.encode()})


def test_explicit_confirmed_transfer_can_still_resolve_historical_source_identity(project):
    text = "# Batch\n\n## Description\n\nOwned purpose.\n"
    guard = marker()
    initial = reconcile_pending_maintenance(None, guard, capture(project, markdown=text))
    reviewed = acknowledged(initial)
    deleted = reconcile_pending_maintenance(reviewed, guard, capture(
        project, previous=reviewed, markdown="# Batch\n", missing=True,
    ))
    fresh = capture(project, previous=deleted, markdown=text)
    record_id = next(iter(deleted["records"]))
    old = deleted["observations"][record_id]
    observed = deepcopy(fresh.by_owner[owner_key(old["coordinate"], old["target"])])
    confirmation = {
        "actor": {"kind": "agent", "actor_id": "confirmed-transfer", "authority": "ordinary-maintenance"},
        "governance_effect": "none", "from_coordinate": old["coordinate"],
        "to_coordinate": observed["coordinate"], "from_target": old["target"], "to_target": observed["target"],
        "from_basis_hash": canonical_hash(deleted["records"][record_id]["last_present_basis"]),
        "to_basis_hash": canonical_hash(observed["basis"]),
    }
    result = reconcile_pending_maintenance(deleted, guard, fresh, confirmed_transfers=({
        "record_id": record_id, "observation": observed, "confirmation": confirmation,
    },))
    assert result["observations"][record_id]["presence"] == "present"
    assert result["records"][record_id]["mapping"]["state"] == "resolved"
    assert result["records"][record_id]["status"] == "pending"
    assert result["records"][record_id]["current_acknowledgment_id"] is None
    assert result["records"][record_id]["acknowledgment_history"] == deleted["records"][record_id]["acknowledgment_history"]
