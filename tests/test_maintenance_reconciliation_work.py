"""Producer refresh validates complete owners once and affected groups per event."""

from copy import deepcopy

import pytest

from llm_wiki_cli.services import maintenance_state as state_module
from llm_wiki_cli.services.maintenance_evidence import (
    MaintenanceCapture, owner_key, reconcile_pending_maintenance,
)
from llm_wiki_cli.services.maintenance_state import canonical_hash, maintenance_core, new_identity
from llm_wiki_cli.services.knowledge_storage import canonical_bytes
from tests.test_maintenance_reconciliation import marker
from tests.test_maintenance_state import adopt, evidence, event, target


def test_producer_refresh_uses_one_detached_state_and_local_group_validation(monkeypatch):
    core = maintenance_core()
    guard = marker()
    observations, incoming = {}, {}
    groups = 40
    for index in range(groups):
        implementation = evidence(path=f"unit_{index}.py", owner=f"Owner{index}")
        refreshed = evidence(path=f"unit_{index}.py", owner=f"Owner{index}", parser="3.14.6")
        for heading in ("Description", "Details"):
            selected = target(heading, page=f"entities/Owner{index}.md")
            current = core.observation(implementation, canonical_hash(heading), target=selected)
            observations[new_identity()] = current
            replacement = core.observation(refreshed, canonical_hash(heading), target=selected)
            incoming[owner_key(replacement["coordinate"], replacement["target"])] = replacement
    initial = core.initial_state(guard, observations)
    before = deepcopy(initial)
    validation_sizes, whole_copies = [], []
    validate = core.validate_state
    copy = state_module.deepcopy

    def counted_validation(state):
        validation_sizes.append(len(state["records"]))
        return validate(state)

    def counted_copy(value, *args, **kwargs):
        if isinstance(value, dict) and value.get("schema_version") == "llm-wiki-maintenance-state/v1":
            whole_copies.append(len(value["records"]))
        return copy(value, *args, **kwargs)

    monkeypatch.setattr(core, "validate_state", counted_validation)
    monkeypatch.setattr(state_module, "deepcopy", counted_copy)
    result = reconcile_pending_maintenance(initial, guard, MaintenanceCapture(incoming))
    assert initial == before
    assert whole_copies == [groups * 2]
    assert validation_sizes.count(groups * 2) == 2
    assert validation_sizes.count(2) == groups
    assert result["generation"] == initial["generation"] + groups
    assert all(observed["implementation"]["producer"]["parser_version"] == "3.14.6"
               for observed in result["observations"].values())


def test_fast_observe_enforces_global_pending_limit_before_another_event(monkeypatch):
    core = maintenance_core()
    first, second = new_identity(), new_identity()
    initial = core.initial_state(marker(), {
        first: core.observation(evidence(), canonical_hash("prose"), target=target()),
        second: core.observation(evidence(path="other.py", owner="Other"), canonical_hash("other prose"),
                                 target=target(page="entities/Other.md")),
    })
    actor = {"kind": "agent", "actor_id": "test-agent", "authority": "ordinary-maintenance"}
    basis = initial["observations"][first]["basis"]
    initial = core.transition(initial, event(initial, first, "acknowledge", actor=actor, basis=basis), basis)
    monkeypatch.setitem(state_module.LIMITS, "pending_records", 1)
    incoming = core.observation(evidence("changed", "changed"), canonical_hash("prose"), target=target())
    value = event(initial, first, "observe", observation=incoming)
    with pytest.raises(state_module.MaintenanceError, match="pending record limit"):
        core.transition(initial, value, incoming["basis"])
    with state_module._maintenance_reconciliation(initial, core=core) as operation:
        with pytest.raises(state_module.MaintenanceError, match="pending record limit"):
            operation.apply(value, incoming["basis"])
        with pytest.raises(state_module.MaintenanceError):
            operation.finish()


def test_fast_observe_enforces_actual_whole_state_byte_limit(monkeypatch):
    core = maintenance_core()
    initial, first, _ = adopt(core, multiple=True)
    incoming = core.observation(evidence("changed", "changed"), canonical_hash("prose"), target=target())
    value = event(initial, first, "observe", observation=incoming)
    expected = core.transition(initial, value, incoming["basis"])
    limit = len(canonical_bytes(initial))
    assert len(canonical_bytes(expected)) > limit
    monkeypatch.setitem(state_module.LIMITS, "state_bytes", limit)
    with pytest.raises(state_module.MaintenanceError, match="exceeds 64 MiB"):
        core.transition(initial, value, incoming["basis"])
    with state_module._maintenance_reconciliation(initial, core=core) as operation:
        with pytest.raises(state_module.MaintenanceError, match="exceeds 64 MiB"):
            operation.apply(value, incoming["basis"])
