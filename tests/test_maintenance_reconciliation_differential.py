"""Private observe batches agree with independent strict public transitions."""

from __future__ import annotations

from contextvars import copy_context
from copy import deepcopy

import pytest

from llm_wiki_cli.services import maintenance_shapes, maintenance_state as state_module, python_implementation
from llm_wiki_cli.services.maintenance_evidence import (
    MaintenanceCapture, owner_key, reconcile_pending_maintenance,
)
from llm_wiki_cli.services.maintenance_state import (
    MaintenanceCore, MaintenanceError, canonical_hash, maintenance_core, new_identity,
)
from tests.test_maintenance_state import adopt, evidence, event, target


ACTOR = {"kind": "agent", "actor_id": "implementation-agent", "authority": "ordinary-maintenance"}


def _ack(record_id, *, stale=False):
    def step(state):
        basis = deepcopy(state["observations"][record_id]["basis"])
        value = event(state, record_id, "acknowledge", basis=basis, actor=deepcopy(ACTOR))
        if stale:
            value["expected_state_hash"] = "sha256:" + "0" * 64
        return value, basis
    return step


def _observe(core, record_id, *, implementation=None, prose="updated prose", target_presence="present"):
    def step(state):
        current = state["observations"][record_id]
        observed = core.observation(
            deepcopy(implementation or current["implementation"]),
            canonical_hash(prose) if target_presence == "present" else None,
            target=deepcopy(current["target"]), target_presence=target_presence,
        )
        kind = "delete-target" if target_presence == "deleted" else "observe"
        return event(state, record_id, kind, observation=observed), observed["basis"]
    return step


def _move(core, record_id, implementation, selected_target):
    def step(state):
        current = state["observations"][record_id]
        observed = core.observation(implementation, canonical_hash("moved prose"), target=selected_target)
        confirmation = {
            "actor": deepcopy(ACTOR), "governance_effect": "none",
            "from_coordinate": deepcopy(current["coordinate"]),
            "to_coordinate": deepcopy(observed["coordinate"]),
            "from_target": deepcopy(current["target"]), "to_target": deepcopy(observed["target"]),
            "from_basis_hash": canonical_hash(state["records"][record_id]["last_present_basis"]),
            "to_basis_hash": canonical_hash(observed["basis"]),
        }
        return event(state, record_id, "confirm-move", observation=observed,
                     confirmation=confirmation), observed["basis"]
    return step


def _history(core, initial, steps):
    reference = deepcopy(initial)
    events = []
    for step in steps:
        value, basis = step(reference)
        events.append((deepcopy(value), deepcopy(basis)))
        reference = core.transition(reference, value, basis)
    return reference, events


def _case(core, name):
    initial, first, second = adopt(core, multiple=True)
    changed = evidence(source="changed", execution="changed")
    if name == "shared-source-prose-history":
        steps = [_ack(first), _ack(second), _observe(core, first, implementation=changed),
                 _ack(first), _observe(core, first, implementation=changed, prose="later prose")]
    elif name == "producer-and-unavailable":
        steps = [_ack(first), _ack(second), _observe(core, first, implementation=evidence(parser="3.14.6")),
                 _observe(core, first, implementation=evidence(reason="unsupported-producer"))]
    elif name == "target-delete-restore":
        steps = [_ack(first), _observe(core, first, target_presence="deleted"),
                 _observe(core, first, prose="restored prose"), _ack(first)]
    elif name == "delete-confirm-move":
        def delete(state):
            observed = core.observation(evidence(reason="missing-source"), canonical_hash("prose"),
                                        presence="deleted", target=target())
            return event(state, first, "delete", observation=observed), observed["basis"]
        moved = evidence(path="moved.py", owner="Moved")
        steps = [_ack(first), _ack(second), delete,
                 _move(core, first, moved, target(page="entities/Moved.md")),
                 _observe(core, first, implementation=evidence(source="changed", execution="changed",
                                                              path="moved.py", owner="Moved"))]
    elif name == "ambiguous-confirm-move":
        moved = evidence(path="moved.py", owner="Moved")
        destination = target(page="entities/Moved.md")
        alternative = evidence(path="other.py", owner="Other")

        def ambiguous(state):
            observed = core.observation(evidence(reason="ambiguous-owner"), canonical_hash("prose"),
                                        presence="ambiguous", target=target())
            candidates = [{"coordinate": moved["coordinate"], "target": destination},
                          {"coordinate": alternative["coordinate"], "target": target(page="entities/Other.md")}]
            return event(state, first, "ambiguous-move", observation=observed,
                         candidates=candidates), observed["basis"]
        steps = [_ack(first), ambiguous, _move(core, first, moved, destination),
                 _observe(core, first, implementation=moved)]
    elif name == "register-observe-ack":
        added = new_identity()
        selected = evidence(path="added.py", owner="Added")

        def register(state):
            observed = core.observation(selected, canonical_hash("initial prose"),
                                        target=target(page="entities/Added.md"))
            return event(state, added, "register", observation=observed), observed["basis"]
        steps = [register, _observe(core, added, implementation=selected), _ack(added)]
    else:
        steps = [_ack(first), _ack(first, stale=True)]
    return initial, *_history(core, initial, steps)


@pytest.mark.parametrize("name", [
    "shared-source-prose-history", "producer-and-unavailable", "target-delete-restore",
    "delete-confirm-move", "ambiguous-confirm-move", "register-observe-ack", "stale-ack-replay",
])
def test_batch_exact_json_and_hash_match_public_transition_history(name):
    core = maintenance_core()
    initial, reference, events = _case(core, name)
    before = deepcopy(initial)
    with state_module._maintenance_reconciliation(initial, core=core) as batch:
        for value, basis in events:
            fields = {key: item for key, item in value.items()
                      if key not in {"schema_version", "record_id", "kind", "expected_state_hash"}}
            minted = batch._event_owned(batch._state, value["record_id"], value["kind"], **fields)
            if name != "stale-ack-replay":
                assert minted == value
                batch.apply(minted, basis)
            else:
                batch.apply(value, basis)  # Retain the intentionally stale public replay CAS.
        result = batch.finish()
    assert result == reference and canonical_hash(result) == canonical_hash(reference)
    assert initial == before
    result["records"].clear()
    assert initial == before


def test_failed_fast_observe_expires_batch_and_preserves_caller():
    core = maintenance_core()
    initial, first, _ = adopt(core, multiple=True)
    before = deepcopy(initial)
    good = _observe(core, first, implementation=evidence(source="changed", execution="changed"))
    advanced, events = _history(core, initial, [good])
    bad_evidence = deepcopy(advanced["observations"][first]["implementation"])
    bad_evidence["executable_hash"] = "sha256:" + "0" * 64
    bad, basis = _observe(core, first, implementation=bad_evidence)(advanced)
    with pytest.raises(MaintenanceError) as reference:
        core.transition(advanced, bad, basis)
    with state_module._maintenance_reconciliation(initial, core=core) as batch:
        batch.apply(*events[0])
        with pytest.raises(MaintenanceError) as failure:
            batch.apply(bad, basis)
        assert failure.value.code == reference.value.code == "identical-source-observation-mismatch"
        with pytest.raises((TypeError, MaintenanceError)):
            batch.finish()
    assert initial == before


def test_batch_does_not_alias_events_or_bases():
    core = maintenance_core()
    initial, first, _ = adopt(core, multiple=True)
    reference, events = _history(core, initial, [_observe(core, first)])
    value, basis = events[0]
    with state_module._maintenance_reconciliation(initial, core=core) as batch:
        batch.apply(value, basis)
        value["observation"]["basis"]["prose_hash"] = "sha256:" + "0" * 64
        basis["prose_hash"] = "sha256:" + "1" * 64
        result = batch.finish()
    assert result == reference


def test_nested_reconciliation_cannot_borrow_or_replace_outer_ownership():
    core = maintenance_core()
    initial, first, _ = adopt(core)
    reference, events = _history(core, initial, [_observe(core, first)])
    with state_module._maintenance_reconciliation(initial, core=core) as outer:
        with pytest.raises((TypeError, MaintenanceError)):
            with state_module._maintenance_reconciliation(initial, core=core):
                pytest.fail("nested batch acquired outer ownership")
        outer.apply(*events[0])
        copied = copy_context()
        assert outer.finish() == reference
    with pytest.raises((TypeError, MaintenanceError)):
        copied.run(outer.apply, *events[0])


def test_foreign_owned_state_cannot_continue_after_adapter_failure():
    core = maintenance_core()
    initial, first, _ = adopt(core)
    _, events = _history(core, initial, [_observe(core, first)])
    with state_module._maintenance_reconciliation(initial, core=core) as batch:
        with pytest.raises((TypeError, MaintenanceError)):
            batch._apply_owned(deepcopy(initial), *events[0])
        with pytest.raises((TypeError, MaintenanceError)):
            batch.finish()


def test_public_transition_output_validation_cannot_be_skipped_by_caller_mutation():
    from llm_wiki_cli.services.implementation_evidence import validate_implementation_evidence

    caller = []

    def validate(value):
        validate_implementation_evidence(value)
        if caller and value["status"] == "available":
            caller[0]["generation"] = caller[1] + 1

    core = MaintenanceCore(validate)
    initial, first, _ = adopt(core)
    missing = core.observation(evidence(reason="missing-source"), canonical_hash("prose"),
                               presence="deleted", target=target())
    deleted = core.transition(initial, event(initial, first, "delete", observation=missing), missing["basis"])
    caller.extend([deleted, deleted["generation"]])
    incoming = core.observation(evidence(), canonical_hash("new section"), target=target("Details"))
    registered = event(deleted, new_identity(), "register", observation=incoming)
    with pytest.raises(MaintenanceError, match="partial-source-deletion"):
        core.transition(deleted, registered, incoming["basis"])


def test_public_allocator_can_reconcile_an_independent_owner_before_registering():
    core = maintenance_core()
    outer, first, _ = adopt(core)
    inner, inner_first, _ = adopt(core)
    outer_before, inner_before = deepcopy(outer), deepcopy(inner)

    def guard(state):
        return {"schema_version": "llm-wiki-maintenance-adoption/v1",
                "adoption_id": state["adoption_id"], "min_manifest_version": 7,
                "features": {"implementation_evidence": 1, "maintenance_state": 1,
                             "ordinary_acknowledgment": 1}}

    old = outer["observations"][first]
    registered = core.observation(evidence(path="added.py", owner="Added"), canonical_hash("added prose"),
                                  target=target(page="entities/Added.md"))
    outer_capture = MaintenanceCapture({owner_key(old["coordinate"], old["target"]): old,
                                       owner_key(registered["coordinate"], registered["target"]): registered})
    inner_event, inner_basis = _observe(core, inner_first, prose="independent inner prose")(inner)
    inner_observation = inner_event["observation"]
    inner_capture = MaintenanceCapture({owner_key(inner_observation["coordinate"], inner_observation["target"]): inner_observation})
    added_id = new_identity()
    inner_results = []

    def allocate():
        inner_results.append(reconcile_pending_maintenance(inner, guard(inner), inner_capture))
        return added_id

    result = reconcile_pending_maintenance(outer, guard(outer), outer_capture, allocate_id=allocate)
    expected_outer = core.transition(outer, event(outer, added_id, "register", observation=registered), registered["basis"])
    expected_inner = core.transition(inner, inner_event, inner_basis)
    assert result == expected_outer and inner_results == [expected_inner]
    assert outer == outer_before and inner == inner_before


@pytest.mark.parametrize("change", [
    "nested-shape", "limits", "event-fields", "same-function-code", "schema-constant", "configuration",
])
def test_validator_or_schema_change_expires_optimization_before_use(monkeypatch, change):
    core = maintenance_core()
    initial, first, _ = adopt(core)
    before = deepcopy(initial)
    _, events = _history(core, initial, [_observe(core, first)])
    with state_module._maintenance_reconciliation(initial, core=core) as batch:
        if change == "nested-shape":
            original = maintenance_shapes.shape_20
            monkeypatch.setattr(maintenance_shapes, "shape_20", lambda *args: original(*args))
        elif change == "limits":
            monkeypatch.setitem(state_module.LIMITS, "state_bytes", state_module.LIMITS["state_bytes"] + 1)
        elif change == "event-fields":
            monkeypatch.setitem(state_module.EVENT_FIELDS, "observe", {"observation", "unexpected"})
        elif change == "schema-constant":
            monkeypatch.setattr(python_implementation, "MAX_OBJECT_BYTES", python_implementation.MAX_OBJECT_BYTES + 1)
        elif change == "configuration":
            monkeypatch.setitem(python_implementation.CONFIGURATION, "max_object_bytes", python_implementation.MAX_OBJECT_BYTES + 1)
        else:
            monkeypatch.setattr(core.evidence_validator, "__code__", (lambda value: value).__code__)
        with pytest.raises((TypeError, MaintenanceError)):
            batch.apply(*events[0])
    assert initial == before


@pytest.mark.parametrize("change", ["state", "cached-hash"])
def test_cached_event_hash_cannot_authorize_changed_or_forged_current_state(change):
    core = maintenance_core()
    initial, first, _ = adopt(core, multiple=True)
    before = deepcopy(initial)
    _, events = _history(core, initial, [_observe(core, first)])
    with state_module._maintenance_reconciliation(initial, core=core) as batch:
        batch.apply(*events[0])
        if change == "state":
            batch._state["generation"] += 1
        else:
            batch._state_hash = "sha256:" + "0" * 64
        current = batch._state["observations"][first]
        observed = core.observation(deepcopy(current["implementation"]), canonical_hash("next prose"),
                                    target=deepcopy(current["target"]))
        minted = batch._event_owned(batch._state, first, "observe", observation=observed)
        assert minted["expected_state_hash"] == batch._state_hash
        with pytest.raises(MaintenanceError, match="state-changed"):
            batch.apply(minted, observed["basis"])
        with pytest.raises((TypeError, MaintenanceError)):
            batch.finish()
    assert initial == before


@pytest.mark.parametrize("name", ["_event_owned", "_refresh_groups"])
def test_private_event_factory_and_helper_identity_are_bound_to_the_invocation(monkeypatch, name):
    core = maintenance_core()
    initial, first, _ = adopt(core)
    before = deepcopy(initial)
    _, events = _history(core, initial, [_observe(core, first)])
    with state_module._maintenance_reconciliation(initial, core=core) as batch:
        original = getattr(batch, name)
        monkeypatch.setattr(batch, name, lambda *args, **kwargs: original(*args, **kwargs))
        with pytest.raises(MaintenanceError, match="validator-changed"):
            batch.apply(*events[0])
        with pytest.raises((TypeError, MaintenanceError)):
            batch.finish()
    assert initial == before
