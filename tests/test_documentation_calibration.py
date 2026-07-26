"""Fail-closed contracts for standalone-documentation P0 calibration evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_wiki_cli.services import contracts
from llm_wiki_cli.services import documentation_calibration as calibration
from llm_wiki_cli.services.documentation_calibration import (
    DocumentationCalibrationError,
    build_flow_evidence_census,
    build_p0_calibration_shadow,
    canonical_json_sha256,
    evaluate_calibration_preflight,
    mechanical_calibration_verdict,
    validate_flow_evidence_census,
    validate_source_citation,
)


def test_calibration_schema_constants_are_centralized_and_reexported():
    expected = {
        "P0_FLOW_CENSUS_SCHEMA_VERSION": "llm-wiki-p0-flow-census/v1",
        "P0_CALIBRATION_SHADOW_SCHEMA_VERSION": ("llm-wiki-p0-calibration-shadow/v1"),
        "P0_CALIBRATION_PREFLIGHT_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-preflight/v1"
        ),
        "P0_CALIBRATION_VERDICT_SCHEMA_VERSION": ("llm-wiki-p0-calibration-verdict/v1"),
    }

    for name, value in expected.items():
        assert getattr(contracts, name) == value
        assert getattr(calibration, name) == value


def test_new_calibration_contract_versions_and_decision_scope_are_stable():
    expected_versions = {
        "P0_CALIBRATION_RUN_SCHEMA_VERSION": "llm-wiki-p0-calibration-run/v1",
        "P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-execution-manifest/v1"
        ),
        "P0_CALIBRATION_CONTROL_RECORD_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-control-record/v1"
        ),
        "P0_CALIBRATION_ADMISSION_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-admission/v1"
        ),
        "P0_CALIBRATION_EVIDENCE_BUNDLE_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-evidence-bundle/v1"
        ),
        "P0_CALIBRATION_AUTHORITY_GRANT_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-authority-grant/v1"
        ),
        "P0_CALIBRATION_ISOLATION_ATTESTATION_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-isolation-attestation/v1"
        ),
        "P0_CALIBRATION_ROLE_CAPABILITY_MATRIX_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-role-capability-matrix/v1"
        ),
        "P0_CALIBRATION_ISOLATION_PROBE_RESULT_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-isolation-probe-result/v1"
        ),
        "P0_CALIBRATION_AGENT_PACKET_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-agent-packet/v1"
        ),
        "P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-agent-result/v1"
        ),
        "P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-dispatch-receipt/v1"
        ),
        "P0_CALIBRATION_ACCESS_EVENT_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-access-event/v1"
        ),
        "P0_CALIBRATION_TRANSITION_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-transition/v1"
        ),
        "P0_CALIBRATION_VERIFICATION_REPORT_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-verification-report/v1"
        ),
        "P0_CALIBRATION_FROZEN_INTAKE_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-frozen-intake/v1"
        ),
        "P0_CALIBRATION_TASK_ORACLE_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-task-oracle/v1"
        ),
        "P0_CALIBRATION_LABEL_FIELD_CONTRACT_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-label-field-contract/v1"
        ),
        "P0_CALIBRATION_OPTIMIZER_SEARCH_CONTRACT_SCHEMA_VERSION": (
            "llm-wiki-p0-calibration-optimizer-search-contract/v1"
        ),
    }

    assert {
        name: getattr(contracts, name) for name in expected_versions
    } == expected_versions
    assert contracts.P0_CALIBRATION_DECISION_SCOPE == "p0_policy_default"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _surface(wiki: Path, flows: list[dict]) -> None:
    _write(
        wiki / ".llm-wiki-surface.json",
        json.dumps(
            {
                "schema_version": "llm-wiki-surface-index/v1",
                "flows": flows,
                "pages": [],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
    )


def _rich_flows() -> list[dict]:
    return [
        {
            "id": "http-create-user",
            "category": "http",
            "detector": "builtin",
            "language": "Python",
            "entry_point": {
                "source_path": "src/server.py",
                "symbol": "create_user",
                "label": "Create User",
            },
            "routes": [{"method": "POST", "path": "/users"}],
            "evidence": {
                "flow": {
                    "step_count": 3,
                    "truncated": False,
                    "modules_touched": ["src/server.py", "src/store.py"],
                },
                "data_flow": {
                    "generated": True,
                    "step_count": 3,
                    "transfer_count": 2,
                    "truncated": False,
                    "boundary_effects": [
                        {
                            "kind": "database_write",
                            "target": "users",
                            "confidence": "high",
                        }
                    ],
                    "gaps": [],
                },
            },
        },
        {
            "id": "process-create-user",
            "category": "process",
            "detector": "builtin",
            "language": "python",
            "entry_point": {
                "source_path": "tests/test_worker.py",
                "symbol": "create_user",
                "label": "Create User",
            },
            "evidence": {
                "flow": {
                    "step_count": 5,
                    "truncated": True,
                    "modules_touched": ["tests/test_worker.py"],
                },
                "data_flow": {
                    "generated": True,
                    "step_count": 5,
                    "transfer_count": 0,
                    "truncated": True,
                    "boundary_effects": [],
                    "gaps": [{"kind": "unresolved", "confidence": "low"}],
                },
            },
        },
    ]


def test_census_is_priority_blind_deterministic_and_source_backed(tmp_path: Path):
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    _write(
        source / "src" / "server.py",
        "def create_user(name):\n    return {'name': name}\n",
    )
    _write(
        source / "tests" / "test_worker.py",
        "def create_user():\n    raise NotImplementedError\n",
    )
    for flow in _rich_flows():
        _write(wiki / "flows" / f"{flow['id']}.md", f"# {flow['id']}\n")
    _surface(wiki, list(reversed(_rich_flows())))

    first = build_flow_evidence_census(
        str(wiki),
        source_root=str(source),
        source_revision="a" * 40,
        source_fingerprint="sha256:" + "b" * 64,
        dependency_evidence={
            "metrics": {
                "metrics": {
                    "src/server.py": {"fan_in": 4, "fan_out": 2},
                    "tests/test_worker.py": {"fan_in": 0, "fan_out": 1},
                }
            }
        },
        tool_revision="test",
    )
    reordered = _rich_flows()
    for flow in reordered:
        flow["routes"] = list(reversed(flow.get("routes", [])))
        flow["evidence"]["flow"]["modules_touched"].reverse()
        data_flow = flow["evidence"]["data_flow"]
        data_flow["boundary_effects"].reverse()
        data_flow["gaps"].reverse()
    _surface(wiki, reordered)
    second = build_flow_evidence_census(
        str(wiki),
        source_root=str(source),
        source_revision="a" * 40,
        source_fingerprint="sha256:" + "b" * 64,
        dependency_evidence={
            "metrics": {
                "metrics": {
                    "tests/test_worker.py": {"fan_in": 0, "fan_out": 1},
                    "src/server.py": {"fan_in": 4, "fan_out": 2},
                }
            }
        },
        tool_revision="test",
    )

    assert first == second
    assert canonical_json_sha256(first) == canonical_json_sha256(second)
    assert first["priority_blind"] is True
    assert '"priority"' not in json.dumps(first, sort_keys=True)
    assert first["counts"]["by_source_provenance"] == {
        "production": 1,
        "test": 1,
    }
    assert len(first["critical_review_inventory"]) == 2
    assert all(
        family["semantic_equivalence"] == "unadjudicated"
        for family in first["preliminary_families"]
    )

    production = first["capsules"][0]
    assert production["flow_id"] == "http-create-user"
    assert production["language"] == "python"
    assert production["dependency"] == {"cycle": 0, "fan_in": 4, "fan_out": 2}
    assert validate_source_citation(production["source_citation"], str(source))

    truncated = first["capsules"][1]
    assert truncated["data_flow"]["truncated"] is True
    assert "boundary_effect_absence_under_truncation" in truncated["unknown_fields"]
    assert truncated["evidence_completeness"]["data_flow"] == "partial"

    duplicate_inventory = json.loads(json.dumps(first))
    duplicate_inventory["critical_review_inventory"].append(
        dict(duplicate_inventory["critical_review_inventory"][0])
    )
    with pytest.raises(DocumentationCalibrationError, match="exactly by id"):
        validate_flow_evidence_census(duplicate_inventory)


def test_census_preserves_the_full_381_flow_population(tmp_path: Path):
    wiki = tmp_path / "wiki"
    flows = []
    for category, count in (("http", 240), ("cli", 122), ("process", 19)):
        flows.extend(
            {
                "id": f"{category}-{index:03d}",
                "category": category,
                "entry_point": {"label": f"{category} {index:03d}"},
            }
            for index in range(count)
        )
    _surface(wiki, list(reversed(flows)))

    census = build_flow_evidence_census(str(wiki), source_revision="frozen")

    assert census["counts"]["total"] == 381
    assert census["counts"]["by_category"] == {
        "cli": 122,
        "http": 240,
        "process": 19,
    }
    assert len(census["capsules"]) == 381
    assert len(census["critical_review_inventory"]) == 381
    assert [item["flow_id"] for item in census["capsules"]] == sorted(
        item["id"] for item in flows
    )


def test_shadow_is_evidence_only_until_a_complete_candidate_is_supplied(
    tmp_path: Path,
):
    wiki = tmp_path / "wiki"
    _surface(wiki, _rich_flows())
    census = build_flow_evidence_census(str(wiki), source_revision="frozen")
    worklist = {
        "schema_version": "llm-wiki-documentation-worklist/v1",
        "items": [
            {
                "id": "flow-http",
                "canonical_path": "flows/http-create-user.md",
                "category": "flow_behavior",
                "priority": "P0",
                "signals": ["missing_or_placeholder_flow_behavior"],
            },
            {
                "id": "landing",
                "canonical_path": "index.md",
                "category": "landing_context",
                "priority": "P0",
                "signals": ["generic_landing_context"],
            },
        ],
    }
    original = json.loads(json.dumps(worklist))

    shadow = build_p0_calibration_shadow(worklist, census)

    assert worklist == original
    assert list(shadow) == [
        "schema_version",
        "mode",
        "policy_version",
        "candidate_evaluated",
        "current_worklist_schema",
        "census_schema",
        "counts",
        "structural_controls",
        "items",
        "limitations",
    ]
    assert shadow["mode"] == "evidence_only"
    assert shadow["candidate_evaluated"] is False
    assert shadow["counts"]["inventory_visible"] == 2
    assert shadow["structural_controls"][0]["candidate_change_allowed"] is False
    assert all(item["candidate"]["priority"] is None for item in shadow["items"])

    with pytest.raises(DocumentationCalibrationError, match="every census flow"):
        build_p0_calibration_shadow(
            worklist,
            census,
            candidate_records=[
                {
                    "flow_id": "http-create-user",
                    "candidate_priority": "P1",
                }
            ],
        )

    candidate = build_p0_calibration_shadow(
        worklist,
        census,
        candidate_records=[
            {"flow_id": flow["id"], "candidate_priority": "P1", "score": 3}
            for flow in _rich_flows()
        ],
        policy_version="candidate/v1",
    )
    assert candidate["mode"] == "candidate_shadow"
    assert all(
        item["candidate"]["status"] == "evaluated" for item in candidate["items"]
    )


def test_preflight_fails_closed_and_requires_explicit_boolean_checks():
    checks = {
        "source_revision_matches": True,
        "source_fingerprint_matches": True,
        "source_read_only": True,
        "control_repetitions_match": True,
        "role_isolation_enforced": False,
        "holdout_access_enforced": True,
        "agent_runtime_available": True,
        "budget_enforced": True,
    }

    result = evaluate_calibration_preflight(checks)

    assert result == {
        "schema_version": "llm-wiki-p0-calibration-preflight/v1",
        "checks": checks,
        "gate_result": "fail_closed",
        "failed_checks": ["role_isolation_enforced"],
        "next_state": "BLOCKED_NO_SHIP",
    }
    assert json.dumps(result, separators=(",", ":")) == (
        '{"schema_version":"llm-wiki-p0-calibration-preflight/v1",'
        '"checks":{"source_revision_matches":true,'
        '"source_fingerprint_matches":true,"source_read_only":true,'
        '"control_repetitions_match":true,"role_isolation_enforced":false,'
        '"holdout_access_enforced":true,"agent_runtime_available":true,'
        '"budget_enforced":true},"gate_result":"fail_closed",'
        '"failed_checks":["role_isolation_enforced"],'
        '"next_state":"BLOCKED_NO_SHIP"}'
    )
    with pytest.raises(DocumentationCalibrationError, match="explicit boolean"):
        evaluate_calibration_preflight({**checks, "budget_enforced": 1})


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {
                "reject_reasons": ["regression"],
                "blocked_reasons": ["missing_runtime"],
                "revision_reasons": ["unstable"],
                "mandatory_gates_complete": False,
                "diversity_complete": False,
            },
            "REJECT",
        ),
        (
            {
                "blocked_reasons": ["missing_runtime"],
                "revision_reasons": ["unstable"],
                "mandatory_gates_complete": False,
                "diversity_complete": False,
            },
            "BLOCKED_NO_SHIP",
        ),
        (
            {
                "revision_reasons": ["unstable"],
                "mandatory_gates_complete": True,
                "diversity_complete": False,
            },
            "REVISE_NEW_COHORT",
        ),
        (
            {"mandatory_gates_complete": True, "diversity_complete": False},
            "OPT_IN_ONLY",
        ),
        (
            {"mandatory_gates_complete": True, "diversity_complete": True},
            "ADOPT_DEFAULT",
        ),
    ],
)
def test_mechanical_verdict_precedence(kwargs: dict, expected: str):
    assert mechanical_calibration_verdict(**kwargs)["outcome"] == expected


def test_incomplete_mandatory_authority_or_isolation_cannot_be_opt_in_only():
    verdict = mechanical_calibration_verdict(
        mandatory_gates_complete=False,
        diversity_complete=False,
    )

    assert verdict["outcome"] == "BLOCKED_NO_SHIP"
    assert verdict["decisive_reasons"] == ["mandatory_gates_incomplete"]
