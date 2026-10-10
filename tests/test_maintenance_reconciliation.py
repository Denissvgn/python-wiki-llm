"""Durable reconciliation joins real captures and independently authored sections."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services.extraction_service import get_inventory_result
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.maintenance_evidence import (
    captured_observations_from_knowledge,
    reconcile_pending_maintenance,
)
from llm_wiki_cli.services.maintenance_projection import (
    project_maintenance_knowledge,
    validate_maintenance_projection,
)
from llm_wiki_cli.services.maintenance_state import (
    MaintenanceError,
    canonical_hash,
    maintenance_core,
    new_identity,
    validate_maintenance_state,
)
from llm_wiki_cli.services.python_implementation import analysis_identity

SOURCE = (
    "class Batch:\n    def cap(self, values, limit=3):\n        return values[:limit]\n"
)
MARKDOWN = "# Batch\n\n## Description\n\nOwned purpose.\n\n### First note\n\nOwned first rationale.\n\n### Second note\n\nOwned second rationale.\n"


def marker():
    return {
        "schema_version": "llm-wiki-maintenance-adoption/v1",
        "adoption_id": new_identity(),
        "min_manifest_version": 7,
        "features": {
            "implementation_evidence": 1,
            "maintenance_state": 1,
            "ordinary_acknowledgment": 1,
        },
    }


@pytest.fixture
def project(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(SOURCE)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    loaded = load_knowledge_state(Path("wiki"))
    assert loaded.knowledge is not None and loaded.manifest_basis is not None
    class_concept = next(
        c
        for c in loaded.knowledge.concepts
        if c.document.canonical_path == "entities/Batch.md"
    )
    knowledge = replace(loaded.knowledge, concepts=(class_concept,))
    return knowledge, loaded.manifest_basis.page_source_mappings


def capture(
    project,
    *,
    previous=None,
    markdown=MARKDOWN,
    text=SOURCE,
    selected=True,
    missing=False,
    qualified=True,
):
    knowledge, mappings = project
    if missing:
        Path("src/policy.py").unlink(missing_ok=True)
    else:
        Path("src/policy.py").write_text(text)
    collected = get_inventory_result(
        "src", deep=True, capture_implementation_observations=True
    )
    snapshot = collected.source_snapshot
    assert snapshot is not None
    return captured_observations_from_knowledge(
        knowledge,
        content_by_page={"entities/Batch.md": markdown},
        page_source_mappings=mappings,
        captures=collected.implementation_observations,
        source_content_hashes=snapshot.captured_content_hashes if selected else {},
        captured_paths={"policy.py"} if selected else (),
        missing_source_paths={"policy.py"} if missing else (),
        analysis_compatibility_hash=analysis_identity(collected.analysis_components)
        if qualified
        else None,
        previous_state=previous,
    )


def adopted(project):
    guard = marker()
    captured = capture(project)
    state = reconcile_pending_maintenance(None, guard, captured)
    return guard, state


def acknowledged(state):
    core = maintenance_core()
    result = deepcopy(state)
    actor = {
        "kind": "agent",
        "actor_id": "test-agent",
        "authority": "ordinary-maintenance",
    }
    for record_id in sorted(result["records"]):
        basis = result["observations"][record_id]["basis"]
        event = {
            "schema_version": "llm-wiki-maintenance-event/v1",
            "kind": "acknowledge",
            "record_id": record_id,
            "expected_state_hash": canonical_hash(result),
            "actor": actor,
            "basis": basis,
        }
        result = core.transition(result, event, basis)
    return result


def by_heading(state, title):
    return next(
        record_id
        for record_id, value in state["observations"].items()
        if ("/" + title.replace(" ", "%20") + "~1")
        in value["target"]["section_locator"]
    )


def test_initial_targets_are_real_semantic_sections_and_never_human_review(project):
    guard, state = adopted(project)
    assert len(state["records"]) == 3
    assert all(
        r["reasons"] == ["unreviewed"]
        and r["status"] == "pending"
        and r["acknowledgment_history"] == []
        for r in state["records"].values()
    )
    assert state["guard_hash"] == canonical_hash(guard)
    observed = capture(project, previous=state)
    assert observed.source_backed_semantic_total == observed.tracked_semantic_total == 3
    assert observed.issues == ()


def test_sync_restart_replay_preserves_identity_history_and_generation(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    before = deepcopy(state)
    captured = capture(project, previous=state)
    restarted = validate_maintenance_state(deepcopy(state))

    def allocation():
        pytest.fail("unchanged replay must not allocate another record")

    after = reconcile_pending_maintenance(
        restarted, guard, captured, allocate_id=allocation
    )
    assert after == before
    assert all(r["status"] == "acknowledged" for r in after["records"].values())


def test_executable_edit_reopens_all_sections_without_losing_agent_history(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    changed = capture(
        project,
        previous=state,
        text=SOURCE.replace("values[:limit]", "values[:limit - 1]"),
    )
    result = reconcile_pending_maintenance(state, guard, changed)
    assert set(result["records"]) == set(state["records"])
    for record_id, row in result["records"].items():
        assert (
            row["status"] == "pending" and "executable-syntax-changed" in row["reasons"]
        )
        assert row["current_acknowledgment_id"] is None
        assert (
            row["acknowledgment_history"]
            == state["records"][record_id]["acknowledgment_history"]
        )
        assert all(
            a["governance_effect"] == "none" for a in row["acknowledgment_history"]
        )
    assert reconcile_pending_maintenance(result, guard, changed) == result


def test_prose_edit_reopens_exact_section_and_affected_ancestor_only(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    changed = capture(
        project,
        previous=state,
        markdown=MARKDOWN.replace(
            "Owned second rationale.", "A corrected authored reason."
        ),
    )
    result = reconcile_pending_maintenance(state, guard, changed)
    assert (
        result["records"][by_heading(state, "First note")]["status"] == "acknowledged"
    )
    changed_id = by_heading(state, "Second note")
    assert result["records"][changed_id]["status"] == "pending"
    assert "prose-changed" in result["records"][changed_id]["reasons"]
    assert "executable-syntax-changed" not in result["records"][changed_id]["reasons"]


def test_target_deletion_keeps_source_execution_and_unaffected_peer_ack(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    changed = capture(
        project, previous=state, markdown=MARKDOWN.split("### Second note")[0]
    )
    result = reconcile_pending_maintenance(state, guard, changed)
    missing_id, peer = by_heading(state, "Second note"), by_heading(state, "First note")
    assert result["observations"][missing_id]["target_presence"] == "deleted"
    assert result["observations"][missing_id]["presence"] == "present"
    assert (
        result["observations"][missing_id]["implementation"]
        == state["observations"][missing_id]["implementation"]
    )
    assert "target-deleted" in result["records"][missing_id]["reasons"]
    assert result["records"][peer]["status"] == "acknowledged"


def test_source_deletion_invalidates_all_sections_and_preserves_history(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    result = reconcile_pending_maintenance(
        state, guard, capture(project, previous=state, missing=True)
    )
    assert all(
        o["presence"] == "deleted" and o["implementation"]["source_hash"] is None
        for o in result["observations"].values()
    )
    assert all(
        r["status"] == "pending" and "source-deleted" in r["reasons"]
        for r in result["records"].values()
    )
    assert all(r["acknowledgment_history"] for r in result["records"].values())


@pytest.mark.parametrize("qualified,selected", [(False, True), (True, False)])
def test_unqualified_or_unselected_inputs_reopen_without_fake_source_absence(
    project, qualified, selected
):
    guard, state = adopted(project)
    state = acknowledged(state)
    current = capture(project, previous=state, qualified=qualified, selected=selected)
    result = reconcile_pending_maintenance(state, guard, current)
    assert current.issues
    assert all(
        o["presence"] == "present" and o["implementation"]["status"] == "unavailable"
        for o in result["observations"].values()
    )
    assert all(
        r["status"] == "pending" and "implementation-unavailable" in r["reasons"]
        for r in result["records"].values()
    )
    assert all(
        "source-deleted" not in r["reasons"]
        and "executable-syntax-changed" not in r["reasons"]
        for r in result["records"].values()
    )


def test_initial_unqualified_coverage_is_explicit_and_no_producer_is_fabricated(
    project,
):
    current = capture(project, qualified=False)
    assert (
        current.source_backed_semantic_total == 3
        and current.tracked_semantic_total == 0
    )
    assert current.by_owner == {} and current.issues
    result = reconcile_pending_maintenance(None, marker(), current)
    assert result["records"] == {}


def test_new_authored_section_registers_once_preserving_existing_history(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    current = capture(
        project,
        previous=state,
        markdown=MARKDOWN + "\n### Third note\n\nNew rationale.\n",
    )
    result = reconcile_pending_maintenance(state, guard, current)
    assert len(result["records"]) == 4
    new_id = next(r for r in result["records"] if r not in state["records"])
    assert result["records"][new_id]["reasons"] == ["unreviewed"]
    assert (
        result["records"][by_heading(state, "First note")]["acknowledgment_history"]
        == state["records"][by_heading(state, "First note")]["acknowledgment_history"]
    )
    assert reconcile_pending_maintenance(result, guard, current) == result


def test_projection_is_bounded_and_binds_exact_authority_and_marker(project):
    guard, state = adopted(project)
    projected = project_maintenance_knowledge(project[0], state, guard)
    validate_maintenance_projection(projected, state=state, marker=guard)
    assert projected.extensions["llm-wiki/maintenance-binding"][
        "state_hash"
    ] == canonical_hash(state)
    corrupt = replace(
        projected,
        extensions={
            **projected.extensions,
            "llm-wiki/maintenance-binding": {
                **projected.extensions["llm-wiki/maintenance-binding"],
                "state_hash": canonical_hash("wrong"),
            },
        },
    )
    with pytest.raises(MaintenanceError, match="projection-state-mismatch"):
        validate_maintenance_projection(corrupt, state=state, marker=guard)


def test_exact_prose_line_ending_change_invalidates_old_acknowledgment_basis(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    current = capture(project, previous=state, markdown=MARKDOWN.replace("\n", "\r\n"))
    result = reconcile_pending_maintenance(state, guard, current)
    assert all(
        row["status"] == "pending" and "prose-changed" in row["reasons"]
        for row in result["records"].values()
    )
    for record_id in state["records"]:
        before = state["observations"][record_id]["basis"]
        after = result["observations"][record_id]["basis"]
        assert before["prose_hash"] != after["prose_hash"]
        assert before["executable_hash"] == after["executable_hash"]


def test_exact_cp1252_and_crlf_prose_bytes_are_qualified_without_utf8_substitution():
    from llm_wiki_cli.services.maintenance_evidence import captured_semantic_sections
    from llm_wiki_cli.services.knowledge_storage import digest

    prose = "## Description\r\n\r\nCafé — owned policy.\r\n\r\n"
    text = "# Batch\r\n\r\n" + prose + "## Methods\r\n\r\nGenerated fields.\r\n"
    raw = text.encode("cp1252")
    sections = captured_semantic_sections(
        text.replace("\r\n", "\n"),
        "llm-wiki://entities/Batch",
        "entities",
        raw_content=raw,
    )
    actual = sections["llm-wiki://entities/Batch#section/Batch~1/Description~1"][
        "prose_hash"
    ]
    assert actual == digest(prose.encode("cp1252"))
    assert actual != digest(prose.encode("utf-8"))
    assert actual != digest(prose.replace("\r\n", "\n").encode("cp1252"))


def test_raw_prose_mismatch_is_unavailable_and_cannot_create_a_fake_current_basis(
    project,
):
    knowledge, mappings = project
    collected = get_inventory_result(
        "src", deep=True, capture_implementation_observations=True
    )
    assert collected.source_snapshot is not None
    current = captured_observations_from_knowledge(
        knowledge,
        content_by_page={"entities/Batch.md": MARKDOWN},
        raw_content_by_page={"entities/Batch.md": b"unrelated raw preimage"},
        page_source_mappings=mappings,
        captures=collected.implementation_observations,
        source_content_hashes=collected.source_snapshot.captured_content_hashes,
        analysis_compatibility_hash=analysis_identity(collected.analysis_components),
    )
    assert current.by_owner == {}
    assert any(
        issue["reason"] == "prose-encoding-unavailable" for issue in current.issues
    )


def test_bound_omission_keeps_durable_work_and_cannot_invent_source_deletion(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    grown = (
        "\n".join(f"def preceding{i}(): return {i}" for i in range(150)) + "\n" + SOURCE
    )
    current = capture(project, previous=state, text=grown)
    result = reconcile_pending_maintenance(state, guard, current)
    assert current.issues
    assert all(
        o["presence"] == "present" and o["implementation"]["status"] == "unavailable"
        for o in result["observations"].values()
    )
    assert all(
        row["status"] == "pending" and "implementation-unavailable" in row["reasons"]
        for row in result["records"].values()
    )
    assert all(
        "source-deleted" not in row["reasons"]
        and "executable-syntax-changed" not in row["reasons"]
        for row in result["records"].values()
    )
    assert all(row["acknowledgment_history"] for row in result["records"].values())


def test_projection_record_limit_is_disclosed_and_never_discards_authority(project):
    from llm_wiki_cli.services.knowledge_storage import canonical_bytes

    text = "# Batch\n\n## Description\n\n" + "\n".join(
        f"### Owned {i}\n\nRationale {i}.\n" for i in range(140)
    )
    current = capture(project, markdown=text)
    guard = marker()
    state = reconcile_pending_maintenance(None, guard, current)
    before = deepcopy(state)
    assert len(state["records"]) == 141
    knowledge = project_maintenance_knowledge(project[0], state, guard)
    records = knowledge.concepts[0].extensions["llm-wiki/maintenance-record"]
    assert records["bounds"]["observations_total"] == 141
    assert records["bounds"]["observations_returned"] <= 128
    assert records["bounds"]["truncated"] is True
    assert len(canonical_bytes(records)) <= 65536
    assert state == before
    forged = deepcopy(records)
    forged["bounds"]["truncated"] = False
    bad = replace(
        knowledge,
        concepts=(
            replace(
                knowledge.concepts[0],
                extensions={
                    **knowledge.concepts[0].extensions,
                    "llm-wiki/maintenance-record": forged,
                },
            ),
        ),
    )
    with pytest.raises(MaintenanceError, match="bounds"):
        validate_maintenance_projection(bad, state=state, marker=guard)


def test_unknown_heading_never_becomes_semantic_description_by_guess(project):
    current = capture(
        project, markdown="# Batch\n\n## Operator notes\n\nA custom region.\n"
    )
    assert current.by_owner == {}
    assert current.source_backed_semantic_total == 0


def test_full_prose_projection_validation_uses_exact_raw_capture_and_rejects_stale_ack_basis(
    project,
):
    guard, state = adopted(project)
    projected = project_maintenance_knowledge(project[0], state, guard)
    raw = {"entities/Batch.md": MARKDOWN.encode()}
    validate_maintenance_projection(
        projected, state=state, marker=guard, raw_content_by_page=raw
    )
    with pytest.raises(MaintenanceError, match="prose-binding"):
        validate_maintenance_projection(
            projected,
            state=state,
            marker=guard,
            raw_content_by_page={
                "entities/Batch.md": MARKDOWN.replace(
                    "Owned first rationale.", "Changed rationale."
                ).encode()
            },
        )


def test_packaged_maintenance_schema_families_validate_actual_authority_and_projection(
    project,
):
    import json
    from jsonschema import Draft202012Validator

    guard, state = adopted(project)
    projected = project_maintenance_knowledge(project[0], state, guard)
    schema_dir = Path(__file__).parents[1] / "src/llm_wiki_cli/schemas"
    cases = {
        "adoption": guard,
        "basis": next(iter(state["observations"].values()))["basis"],
        "state": state,
        "binding": projected.extensions["llm-wiki/maintenance-binding"],
        "record-binding": projected.concepts[0].extensions[
            "llm-wiki/maintenance-record"
        ],
    }
    for kind, payload in cases.items():
        schema = json.loads(
            (schema_dir / f"llm-wiki-maintenance-{kind}-v1.schema.json").read_text()
        )
        Draft202012Validator.check_schema(schema)
        assert list(Draft202012Validator(schema).iter_errors(payload)) == []
