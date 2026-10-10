"""Durable authority transitions using the installed implementation validator."""

from copy import deepcopy
import ast
from functools import lru_cache

import pytest

from llm_wiki_cli.services.maintenance_state import (
    MaintenanceCore,
    MaintenanceError,
    new_identity,
    canonical_hash as hash_json,
)
from llm_wiki_cli.services.implementation_evidence import (
    validate_implementation_evidence,
)
from llm_wiki_cli.services.analysis_capture import capture_analysis
from llm_wiki_cli.services import python_implementation as pi


@lru_cache(maxsize=1)
def _analysis_hash():
    captured = capture_analysis(
        {"python": "llm_wiki_cli.extractors.python_extractor:PythonExtractor"}
    )
    result = pi.analysis_identity(captured)
    assert result is not None
    return result


def evidence(
    source="original",
    execution="original",
    *,
    reason=None,
    parser=None,
    path="policy.py",
    owner="Batch",
):
    descriptor = pi.producer(_analysis_hash())
    assert descriptor is not None
    text = f"# source {source!r}\nclass {owner}:\n    def run(self):\n        return {execution!r}\n"
    rows = pi.capture(
        ast.parse(text), text.encode(), path, configured=descriptor, parsed_source=text
    )["observations"]
    value = next(row["evidence"] for row in rows if row["evidence"]["scope"] == "class")
    if parser is not None:
        value["producer"]["parser_version"] = parser
        value["comparison_id"] = pi.comparison_id(value["producer"])
    if source == "original" and execution != "original":
        original = f"# source {source!r}\nclass {owner}:\n    def run(self):\n        return 'original'\n"
        from llm_wiki_cli.services.knowledge_storage import digest

        value["source_hash"] = digest(original.encode())
    if reason:
        value.update(
            status="unavailable",
            unavailable_reason=reason,
            executable_hash=None,
            documentation_hash=None,
        )
        value["aggregation"]["complete_scope"] = False
        if reason == "missing-source":
            value["source_hash"] = None
    return value


def target(section="Description", page="entities/Batch.md"):
    return {
        "canonical_path": page,
        "section_locator": "llm-wiki://" + page[:-3] + "#section/" + section + "~1",
        "ownership": "semantic",
    }


@pytest.fixture
def core():
    return MaintenanceCore(validate_implementation_evidence)


def adopt(core, multiple=False):
    guard = {
        "schema_version": "llm-wiki-maintenance-adoption/v1",
        "adoption_id": new_identity(),
        "min_manifest_version": 7,
        "features": {
            "implementation_evidence": 1,
            "maintenance_state": 1,
            "ordinary_acknowledgment": 1,
        },
    }
    first, second = new_identity(), new_identity()
    observations = {
        first: core.observation(evidence(), hash_json("prose"), target=target())
    }
    if multiple:
        observations[second] = core.observation(
            evidence(), hash_json("other prose"), target=target("Details")
        )
    return core.initial_state(guard, observations), first, second


def event(state, record, kind, **fields):
    return {
        "schema_version": "llm-wiki-maintenance-event/v1",
        "kind": kind,
        "record_id": record,
        "expected_state_hash": hash_json(state),
        **fields,
    }


def acknowledge(core, state, record):
    basis = state["observations"][record]["basis"]
    return core.transition(
        state,
        event(
            state,
            record,
            "acknowledge",
            basis=deepcopy(basis),
            actor={
                "kind": "agent",
                "actor_id": "implementation-agent",
                "authority": "ordinary-maintenance",
            },
        ),
        basis,
    )


def test_initial_unreviewed_and_sync_idempotent(core):
    state, first, _ = adopt(core)
    assert state["records"][first]["status"] == "pending"
    assert state["records"][first]["reasons"] == ["unreviewed"]
    assert (
        core.transition(
            state, event(state, first, "sync"), state["observations"][first]["basis"]
        )
        == state
    )


def test_acknowledgment_replay_and_actor_separation(core):
    state, first, _ = adopt(core)
    basis = state["observations"][first]["basis"]
    original_event = event(
        state,
        first,
        "acknowledge",
        basis=basis,
        actor={
            "kind": "agent",
            "actor_id": "agent",
            "authority": "ordinary-maintenance",
        },
    )
    changed = core.transition(state, original_event, basis)
    assert core.transition(changed, original_event, basis) == changed
    ack = changed["records"][first]["acknowledgment_history"][0]
    assert ack["governance_effect"] == "none"
    assert ack["actor"]["kind"] == "agent"


def test_stale_acknowledgment_and_state_rejected(core):
    state, first, _ = adopt(core)
    ack = event(
        state,
        first,
        "acknowledge",
        basis=state["observations"][first]["basis"],
        actor={"kind": "agent", "actor_id": "a", "authority": "ordinary-maintenance"},
    )
    changed = deepcopy(state["observations"][first]["basis"])
    changed["prose_hash"] = hash_json("edited")
    with pytest.raises(MaintenanceError, match="stale-acknowledgment"):
        core.transition(state, ack, changed)
    bad_event = event(state, first, "sync")
    bad_event["expected_state_hash"] = hash_json("stale state")
    with pytest.raises(MaintenanceError, match="state-changed"):
        core.transition(state, bad_event, state["observations"][first]["basis"])


@pytest.mark.parametrize(
    "parser,reason,expected",
    [
        (None, None, "executable-syntax-changed"),
        ("3.14.999", None, "producer-incompatible"),
        (None, "unsupported-syntax", "implementation-unavailable"),
    ],
)
def test_observation_comparison_is_qualified(core, parser, reason, expected):
    state, first, _ = adopt(core)
    state = acknowledge(core, state, first)
    incoming = core.observation(
        evidence("edited", "edited", parser=parser, reason=reason),
        hash_json("prose"),
        target=target(),
    )
    result = core.transition(
        state, event(state, first, "observe", observation=incoming), incoming["basis"]
    )
    reasons = result["records"][first]["reasons"]
    assert expected in reasons
    assert ("executable-syntax-changed" in reasons) is (
        parser is None and reason is None
    )
    assert len(result["records"][first]["acknowledgment_history"]) == 1


def test_identical_source_digest_contradiction_rejected(core):
    state, first, _ = adopt(core)
    incoming = core.observation(
        evidence(execution="contradiction"), hash_json("prose"), target=target()
    )
    with pytest.raises(MaintenanceError, match="identical-source-observation-mismatch"):
        core.transition(
            state,
            event(state, first, "observe", observation=incoming),
            incoming["basis"],
        )


def test_multiple_sections_source_update_and_delete_cascade(core):
    state, first, second = adopt(core, True)
    state = acknowledge(core, acknowledge(core, state, first), second)
    incoming = core.observation(
        evidence("edited", "edited"), hash_json("prose"), target=target()
    )
    changed = core.transition(
        state, event(state, first, "observe", observation=incoming), incoming["basis"]
    )
    assert all(r["status"] == "pending" for r in changed["records"].values())
    assert changed["observations"][second]["basis"]["prose_hash"] == hash_json(
        "other prose"
    )
    deleted = core.observation(
        evidence(reason="missing-source"),
        hash_json("prose"),
        presence="deleted",
        target=target(),
    )
    removed = core.transition(
        changed, event(changed, first, "delete", observation=deleted), deleted["basis"]
    )
    assert all(o["presence"] == "deleted" for o in removed["observations"].values())
    assert all(
        len(r["acknowledgment_history"]) == 1 for r in removed["records"].values()
    )
    assert all("source-deleted" in r["reasons"] for r in removed["records"].values())


def test_target_deletion_restoration_does_not_erase_peer_ack(core):
    state, first, second = adopt(core, True)
    state = acknowledge(core, acknowledge(core, state, first), second)
    removed = core.observation(
        evidence(), None, target=target(), target_presence="deleted"
    )
    changed = core.transition(
        state,
        event(state, first, "delete-target", observation=removed),
        removed["basis"],
    )
    assert changed["records"][second] == state["records"][second]
    restored = core.observation(evidence(), hash_json("prose"), target=target())
    result = core.transition(
        changed,
        event(changed, first, "observe", observation=restored),
        restored["basis"],
    )
    assert "target-restored" in result["records"][first]["reasons"]
    assert result["records"][first]["status"] == "pending"


def test_registration_cas_collision_and_history_preservation(core):
    state, first, second = adopt(core)
    state = acknowledge(core, state, first)
    incoming = core.observation(
        evidence(), hash_json("details"), target=target("Details")
    )
    result = core.transition(
        state, event(state, second, "register", observation=incoming), incoming["basis"]
    )
    assert result["records"][first] == state["records"][first]
    assert result["records"][second]["reasons"] == ["unreviewed"]
    with pytest.raises(MaintenanceError, match="record-collision"):
        core.transition(
            result,
            event(result, second, "register", observation=incoming),
            incoming["basis"],
        )


def test_confirmed_move_retains_identity_targets_and_ack_history(core):
    state, first, _ = adopt(core)
    state = acknowledge(core, state, first)
    current = state["observations"][first]
    incoming = core.observation(
        evidence(path="moved.py"),
        hash_json("prose"),
        target=target(page="entities/Moved.md"),
    )
    confirmation = {
        "actor": {
            "kind": "agent",
            "actor_id": "move-resolver",
            "authority": "ordinary-maintenance",
        },
        "from_basis_hash": hash_json(current["basis"]),
        "to_basis_hash": hash_json(incoming["basis"]),
        "from_coordinate": current["coordinate"],
        "to_coordinate": incoming["coordinate"],
        "from_target": current["target"],
        "to_target": incoming["target"],
        "governance_effect": "none",
    }
    result = core.transition(
        state,
        event(
            state,
            first,
            "confirm-move",
            observation=incoming,
            confirmation=confirmation,
        ),
        incoming["basis"],
    )
    assert result["records"][first]["record_id"] == first
    assert len(result["records"][first]["target_history"]) == 2
    assert len(result["records"][first]["acknowledgment_history"]) == 1


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s, r: s.update(extra=True),
        lambda s, r: s.__setitem__("generation", True),
        lambda s, r: s["records"][r]["reasons"].append(float("nan")),
        lambda s, r: s["records"][r].__setitem__(
            "current_acknowledgment_id", hash_json("invented")
        ),
        lambda s, r: s["observations"][r]["target"].__setitem__(
            "section_locator", "llm-wiki://entities/Batch#section/Description~01"
        ),
    ],
)
def test_malformed_and_contradictory_state_rejected(core, mutate):
    state, first, _ = adopt(core)
    mutate(state, first)
    with pytest.raises(MaintenanceError):
        core.validate_state(state)


def test_history_limit_never_prunes_silently(core):
    state, first, _ = adopt(core)
    state["records"][first]["target_history"] *= 1025
    with pytest.raises(MaintenanceError, match="schema-invalid"):
        core.validate_state(state)


def test_ambiguous_mapping_retains_pending_candidates_and_rejects_ack(core):
    state, first, _ = adopt(core)
    state = acknowledge(core, state, first)
    incoming = core.observation(
        evidence(reason="ambiguous-owner"),
        hash_json("prose"),
        presence="ambiguous",
        target=target(),
    )
    candidates = [
        {"coordinate": evidence(path=path)["coordinate"], "target": target(page=page)}
        for path, page in (("a.py", "entities/A.md"), ("b.py", "entities/B.md"))
    ]
    result = core.transition(
        state,
        event(
            state, first, "ambiguous-move", observation=incoming, candidates=candidates
        ),
        incoming["basis"],
    )
    assert result["records"][first]["mapping"]["candidates"] == candidates
    assert result["records"][first]["status"] == "pending"
    assert len(result["records"][first]["acknowledgment_history"]) == 1
    with pytest.raises(MaintenanceError, match="stale-acknowledgment"):
        acknowledge(core, result, first)


def test_partial_source_deletion_cannot_enter_committed_state(core):
    state, first, _ = adopt(core, True)
    state["observations"][first] = core.observation(
        evidence(reason="missing-source"),
        hash_json("prose"),
        presence="deleted",
        target=target(),
    )
    state["records"][first]["mapping"]["state"] = "deleted"
    with pytest.raises(MaintenanceError, match="partial-source-deletion"):
        core.validate_state(state)


def test_new_target_required_and_normalized_identity_enforced(core):
    with pytest.raises(TypeError):
        core.observation(evidence(), hash_json("prose"))
    state, first, _ = adopt(core)
    state["adoption_id"] = "adoption-local-label"
    with pytest.raises(MaintenanceError, match="identity-invalid"):
        core.validate_state(state)
