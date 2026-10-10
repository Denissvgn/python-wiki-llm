"""Read-only reports retain authority and require independent current capture."""

from copy import deepcopy
from typing import Any, cast

import pytest

from llm_wiki_cli.services.maintenance_status import (
    build_maintenance_status,
    compact_maintenance_summary,
    validate_maintenance_summary,
)
from llm_wiki_cli.services.maintenance_state import canonical_hash
from llm_wiki_cli.services.python_implementation import analysis_identity
from llm_wiki_cli.services.extraction_service import get_inventory_result
from tests.test_maintenance_reconciliation import (
    SOURCE,
    MARKDOWN,
    adopted,
    acknowledged,
    capture,
    marker,
    project as project,
)


def report(
    project,
    state,
    guard,
    *,
    text=SOURCE,
    markdown=MARKDOWN,
    analysis=True,
    coherent=True,
):
    current = capture(project, previous=state, text=text, markdown=markdown)
    collected = get_inventory_result(
        "src", deep=True, capture_implementation_observations=True
    )
    return build_maintenance_status(
        state,
        guard,
        current,
        implementation_observations=collected.implementation_observations,
        analysis_scope="full-inventory",
        native_prose_coherent=coherent,
        analysis_compatibility_hash=analysis_identity(collected.analysis_components)
        if analysis
        else None,
    )


def test_snapshot_retains_recorded_ack_but_no_current_basis_or_verdict(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    before = deepcopy(state)
    value = build_maintenance_status(state, guard).to_payload()
    assert (
        value["state_hash"] == canonical_hash(state)
        and not value["live_evaluation_performed"]
    )
    assert all(
        row["recorded_status"] == "acknowledged"
        and row["effective_status"] is None
        and row["expected_basis"] is None
        and not row["basis_available"]
        for row in value["records"]
    )
    assert state == before
    assert compact_maintenance_summary(value)["acknowledged"] == 0


def test_live_syntax_drift_projects_pending_without_registering_or_mutating(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    before = deepcopy(state)
    current = report(
        project,
        state,
        guard,
        text=SOURCE.replace("values[:limit]", "values[:limit - 1]"),
    )
    value = current.to_payload()
    assert value["state_hash"] == canonical_hash(state)
    assert all(
        row["recorded_status"] == "acknowledged"
        and row["effective_status"] == "pending"
        and "executable-syntax-changed" in row["reasons"]
        and row["expected_basis"] is not None
        for row in value["records"]
    )
    assert state == before
    assert set(current.by_record) == set(state["records"])


def test_missing_independent_analysis_never_earns_current_basis(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    value = report(project, state, guard, analysis=False).to_payload()
    assert all(
        not row["basis_available"]
        and row["expected_basis"] is None
        and row["effective_status"] == "pending"
        for row in value["records"]
    )


def test_prose_drift_keeps_available_basis_but_discloses_native_sync_gate(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    value = report(
        project,
        state,
        guard,
        markdown=MARKDOWN.replace("Owned first rationale.", "A corrected rationale."),
        coherent=False,
    ).to_payload()
    assert value["requires_sync"] and not value["native_prose_coherent"]
    assert any("prose-changed" in row["reasons"] for row in value["records"])
    assert any(row["expected_basis"] is not None for row in value["records"])


def test_unregistered_target_is_coverage_gap_and_no_status_allocation(project):
    guard, state = adopted(project)
    value = report(
        project,
        state,
        guard,
        markdown=MARKDOWN + "\n### Unregistered\n\nOwned new prose.\n",
    ).to_payload()
    assert len(value["records"]) == len(state["records"])
    assert value["coverage"]["untracked_semantic_total"] >= 1
    assert value["coverage"]["untracked_targets"]


def test_selected_record_retains_exact_basis_and_bounded_history(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    current = report(project, state, guard)
    record_id = next(iter(state["records"]))
    value = current.to_payload(record_id=record_id, limit=1)
    assert value["bounds"]["returned"] == 1
    row = value["records"][0]
    assert row["expected_basis"] == state["observations"][record_id]["basis"]
    assert row["history_bounds"] == {
        "total": 1,
        "returned": 1,
        "omitted": 0,
        "truncated": False,
    }
    value["records"][0]["expected_basis"]["prose_hash"] = None
    assert current.by_record[record_id]["expected_basis"]["prose_hash"] is not None


def test_summary_is_closed_and_excludes_hashes_history_and_paths(project):
    guard, state = adopted(project)
    value = compact_maintenance_summary(build_maintenance_status(state, guard))
    assert value["pending"] == len(state["records"])
    assert (
        "state_hash" not in value
        and "expected_basis" not in value
        and "records" not in value
    )
    for injected in ("coordinate", "acknowledgment_history", "state_hash", "target"):
        with pytest.raises(ValueError):
            validate_maintenance_summary({**value, injected: {}})


def test_unadopted_report_does_not_fabricate_record_or_adoption():
    value = build_maintenance_status(None, None).to_payload()
    assert (
        value["availability"] == "unadopted"
        and value["records"] == []
        and value["state_hash"] is None
    )
    with pytest.raises(ValueError, match="no durable owner"):
        build_maintenance_status(None, marker())


@pytest.mark.parametrize("scope", ["snapshot", "selected-header"])
def test_summary_refuses_false_live_header_acknowledgment(project, scope):
    guard, state = adopted(project)
    summary = compact_maintenance_summary(build_maintenance_status(state, guard))
    summary.update(analysis_scope=scope, live_evaluation_performed=True, acknowledged=1)
    with pytest.raises(ValueError):
        validate_maintenance_summary(summary)
    summary.update(
        live_evaluation_performed=False, acknowledged=0, pending=summary["total"] + 1
    )
    with pytest.raises(ValueError, match="counts"):
        validate_maintenance_summary(summary)


@pytest.mark.parametrize("field", ["availability", "analysis_scope", "limitations"])
def test_summary_wrong_container_types_are_rejected_as_malformed(project, field):
    guard, state = adopted(project)
    summary = compact_maintenance_summary(build_maintenance_status(state, guard))
    summary[field] = None if field == "limitations" else []
    with pytest.raises(ValueError):
        validate_maintenance_summary(summary)


def test_exact_selected_record_takes_precedence_over_large_unrelated_coverage(project):
    from dataclasses import replace
    from llm_wiki_cli.services.knowledge_storage import canonical_bytes

    guard, state = adopted(project)
    value = report(project, state, guard)
    payload = deepcopy(value.payload)
    payload["coverage"]["issues"] = [
        {"canonical_path": "entities/unrelated.md", "reason": "x" * 4096}
        for _ in range(1000)
    ]
    payload["coverage"]["untracked_targets"] = [
        {
            "canonical_path": "entities/unrelated.md",
            "section_locator": "x" * 4096,
            "ownership": "semantic",
        }
        for _ in range(1000)
    ]
    payload["coverage"]["untracked_semantic_total"] = 1000
    current = replace(value, payload=payload)
    record_id = next(iter(state["records"]))
    selected = current.to_payload(record_id=record_id)
    assert (
        selected["records"][0]["expected_basis"]
        == state["observations"][record_id]["basis"]
    )
    assert selected["coverage"]["issue_bounds"]["total"] == 1000
    assert selected["coverage"]["issue_bounds"]["returned"] == 0
    assert selected["coverage"]["untracked_target_bounds"]["total"] == 1000
    assert len(canonical_bytes(selected)) <= 65536
    ordinary = current.to_payload()
    assert len(canonical_bytes(ordinary)) <= 65536
    assert ordinary["coverage"]["issue_bounds"]["truncated"]


def test_large_per_path_history_is_bounded_without_omitting_expected_basis(project):
    from dataclasses import replace
    from llm_wiki_cli.services.knowledge_storage import canonical_bytes

    guard, state = adopted(project)
    value = report(project, state, guard)
    rows = cast(dict[str, Any], deepcopy(value.by_record))
    record_id = next(iter(rows))
    rows[record_id]["acknowledgment_history"] = [
        {"actor": {"kind": "agent", "actor_id": str(i)}, "captured_payload": "x" * 4096}
        for i in range(128)
    ]
    current = replace(value, by_record=rows)
    selected = current.to_payload(record_id=record_id)
    row = selected["records"][0]
    assert row["history_bounds"]["total"] == 128 and row["history_bounds"]["truncated"]
    assert row["expected_basis"] is not None
    path = row["target"]["canonical_path"]
    scoped = current.for_path(path)
    assert len(canonical_bytes(scoped)) <= 65536
    assert compact_maintenance_summary(scoped)["total"] == len(current.by_path[path])


def test_full_per_path_summary_counts_survive_128_record_projection_limit(project):
    from dataclasses import replace
    from llm_wiki_cli.services.knowledge_storage import canonical_bytes

    guard, state = adopted(project)
    value = report(project, state, guard)
    sample = cast(dict[str, Any], deepcopy(next(iter(value.by_record.values()))))
    sample.update(
        recorded_status="pending", effective_status="pending", reasons=["unreviewed"]
    )
    rows = {
        f"record-{i}": {**deepcopy(sample), "record_id": f"record-{i}"}
        for i in range(150)
    }
    path = sample["target"]["canonical_path"]
    current = replace(value, by_record=rows, by_path={path: tuple(rows)})
    scoped = current.for_path(path)
    summary = compact_maintenance_summary(scoped)
    assert summary["total"] == summary["pending"] == 150
    assert summary["truncated"]
    assert scoped["bounds"]["returned"] <= 128
    assert len(canonical_bytes(scoped)) <= 65536


def test_queue_bounds_long_candidate_targets_and_preserves_complete_counts(project):
    from dataclasses import replace
    from llm_wiki_cli.services.knowledge_storage import canonical_bytes
    from llm_wiki_cli.services.maintenance_queue import compose_queue

    guard, state = adopted(project)
    value = report(project, state, guard)
    sample = cast(dict[str, Any], deepcopy(next(iter(value.by_record.values()))))
    path = sample["target"]["canonical_path"]
    sample.update(recorded_status="pending", effective_status="pending")
    sample["mapping"] = {
        "state": "ambiguous",
        "candidates": [
            {
                "coordinate": sample["coordinate"],
                "target": {
                    "canonical_path": path,
                    "section_locator": "x" * 4000 + str(i),
                },
            }
            for i in range(8)
        ],
    }
    rows = {
        f"record-{i}": {**deepcopy(sample), "record_id": f"record-{i}"}
        for i in range(150)
    }
    current = replace(value, by_record=rows, by_path={path: tuple(rows)})
    queue = compose_queue([], [], None, [], {}, maintenance_report=current)
    item = next(row for row in queue["items"] if row["path"] == path)
    assert item["maintenance"]["total"] == item["maintenance"]["ambiguous"] == 150
    assert item["semantic_target_bounds"]["total"] == 1350
    assert item["semantic_target_bounds"]["returned"] <= 128
    assert item["semantic_target_bounds"]["truncated"]
    projected = {
        key: item[key]
        for key in (
            "record_ids",
            "record_bounds",
            "semantic_targets",
            "semantic_target_bounds",
            "maintenance",
        )
    }
    assert len(canonical_bytes(projected)) <= 65536


def test_long_legal_record_outweighs_unrelated_coverage_in_generic_and_path_reads(
    project,
):
    from dataclasses import replace
    from pathlib import Path
    from llm_wiki_cli.services.implementation_evidence import validate_coordinate
    from llm_wiki_cli.services.knowledge_storage import canonical_bytes
    from llm_wiki_cli.services.maintenance_evidence import MaintenanceCapture, owner_key
    from llm_wiki_cli.services.maintenance_state import maintenance_core

    guard, state = adopted(project)
    record_id = next(iter(state["records"]))
    observation = state["observations"][record_id]
    source = "/".join(["p" * 150] * 5 + ["policy.py"])
    assert 750 < len(source.encode()) < 850
    path = Path("src") / source
    path.parent.mkdir(parents=True)
    path.write_text(SOURCE)
    observation["coordinate"]["source_path"] = source
    observation["implementation"]["coordinate"]["source_path"] = source
    observation["basis"]["coordinate"]["source_path"] = source
    state = maintenance_core().initial_state(guard, {record_id: observation})
    state = acknowledged(state)
    current = MaintenanceCapture(
        {owner_key(observation["coordinate"], observation["target"]): observation},
        captured_paths=frozenset({source}),
        complete_pages=frozenset({observation["target"]["canonical_path"]}),
        source_backed_semantic_total=1,
        tracked_semantic_total=1,
    )
    collected = get_inventory_result(
        "src", deep=True, capture_implementation_observations=True
    )
    value = build_maintenance_status(
        state,
        guard,
        current,
        implementation_observations=collected.implementation_observations,
        analysis_scope="full-inventory",
        analysis_compatibility_hash=analysis_identity(collected.analysis_components),
    )
    assert len(canonical_bytes(value.by_record[record_id])) > 6000
    coverage = deepcopy(value.payload["coverage"])
    coverage["issues"] = [
        {
            "canonical_path": "entities/unrelated.md",
            "coordinate": validate_coordinate(
                {
                    "source_path": source,
                    "qualified_owner": "x" * 3000,
                    "occurrence": i + 1,
                }
            ),
            "reason": "unsupported-producer",
        }
        for i in range(128)
    ]
    crowded = replace(value, payload={**value.payload, "coverage": coverage})
    generic = crowded.to_payload()
    assert generic["records"][0]["record_id"] == record_id
    assert generic["records"][0]["expected_basis"] == observation["basis"]
    assert generic["coverage"]["issue_bounds"]["total"] == 128
    assert generic["coverage"]["issue_bounds"]["truncated"]
    assert len(canonical_bytes(generic)) <= 65536
    scoped = crowded.for_path(observation["target"]["canonical_path"])
    assert scoped["records"][0]["record_id"] == record_id
    assert scoped["records"][0]["expected_basis"] == observation["basis"]
    assert scoped["coverage"]["issues"] == []
    assert scoped["coverage"]["issue_bounds"]["total"] == 0
    assert len(canonical_bytes(scoped)) <= 65536
