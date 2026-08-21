"""Validation for the distributable context-health GitHub Action."""

from __future__ import annotations

import json
import os
import re
import runpy
import shutil
import subprocess
import sys
import types
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from llm_wiki_cli.commands import bootstrap_cmd
from llm_wiki_cli.services import doctor_service


ROOT = Path(__file__).parents[1]
ACTION_PATH = ROOT / "integrations" / "github-action" / "action.yml"
SUMMARY_SCRIPT = ROOT / "integrations" / "github-action" / "render_summary.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "action-selftest.yml"
DASHBOARD_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "llm-wiki-doctor.yml"
SETUP_PYTHON_SHA = "ece7cb06caefa5fff74198d8649806c4678c61a1"
CHECKOUT_SHA = "d23441a48e516b6c34aea4fa41551a30e30af803"
UPLOAD_ARTIFACT_SHA = "ea165f8d65b6e75b540449e92b4886f43607fa02"
FRESHNESS_COUNTS = {
    "unknown": 0,
    "current": 2,
    "nonsemantic-source-change": 0,
    "source-changed": 0,
    "basis-incompatible": 0,
    "source-missing": 0,
}
REQUIRED_REPORT_PATHS = (
    ("schema_version",),
    ("status",),
    ("exit_code",),
    ("strict",),
    ("wiki_dir",),
    ("src_dir",),
    ("availability",),
    ("availability", "state"),
    ("availability", "reason"),
    ("availability", "usable"),
    ("freshness",),
    ("freshness", "evaluated"),
    ("freshness", "disclosure"),
    ("freshness", "concepts"),
    ("freshness", "counts_by_state"),
    ("snapshot_parity",),
    ("snapshot_parity", "state"),
    ("snapshot_parity", "issue_count"),
    ("snapshot_parity", "reasons"),
    ("governance",),
    ("governance", "state"),
    ("governance", "ledger"),
    ("governance", "projection"),
    ("governance", "expired_reviews"),
    ("governance", "issue_count"),
    ("governance", "reasons"),
    ("drift",),
    ("drift", "state"),
    ("drift", "confirmed_stale"),
    ("drift", "indeterminate"),
    ("drift", "nonsemantic_changes"),
    ("drift", "counts_by_state"),
    ("drift", "diagnostic_count"),
    ("drift", "reasons"),
    ("verification_receipt",),
    ("verification_receipt", "state"),
    ("verification_receipt", "reason"),
    ("verification_receipt", "recorded_result"),
    ("verification_receipt", "passed"),
    ("degraded_reasons",),
    ("unhealthy_reasons",),
)
CLOSED_STATE_PATHS = (
    ("status",),
    ("availability", "state"),
    ("snapshot_parity", "state"),
    ("governance", "state"),
    ("governance", "ledger"),
    ("governance", "projection"),
    ("drift", "state"),
    ("verification_receipt", "state"),
)
SUMMARY_RENDERER = runpy.run_path(str(SUMMARY_SCRIPT))


def _yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _doctor_payload(status: str) -> dict:
    severity = {
        "healthy": 0,
        "degraded": 1,
        "unhealthy": 2,
        "absent": 3,
    }[status]
    payload = {
        "schema_version": "llm-wiki-doctor/v1",
        "status": status,
        "exit_code": severity,
        "strict": True,
        "wiki_dir": "docs/llm_wiki",
        "src_dir": ".",
        "availability": {"state": "ready", "reason": "ready", "usable": True},
        "freshness": {
            "evaluated": True,
            "disclosure": "evaluated (2 concepts)",
            "concepts": 2,
            "counts_by_state": dict(FRESHNESS_COUNTS),
        },
        "snapshot_parity": {"state": "valid", "issue_count": 0, "reasons": []},
        "governance": {
            "state": "valid",
            "ledger": "valid",
            "projection": "valid",
            "expired_reviews": 0,
            "issue_count": 0,
            "reasons": [],
        },
        "drift": {
            "state": "current",
            "confirmed_stale": 0,
            "indeterminate": 0,
            "nonsemantic_changes": 0,
            "counts_by_state": dict(FRESHNESS_COUNTS),
            "diagnostic_count": 0,
            "reasons": [],
        },
        "verification_receipt": {
            "state": "absent",
            "reason": "verification-receipt-not-present",
            "recorded_result": None,
            "passed": None,
        },
        "degraded_reasons": [],
        "unhealthy_reasons": [],
    }
    if status == "degraded":
        payload["governance"]["expired_reviews"] = 1
        payload["degraded_reasons"] = ["expired-reviews"]
    elif status == "unhealthy":
        payload["verification_receipt"] = {
            "state": "failed",
            "reason": "verification-recorded-failure",
            "recorded_result": "failed",
            "passed": False,
        }
        payload["unhealthy_reasons"] = ["verification-failed"]
    elif status == "absent":
        payload["availability"] = {
            "state": "absent",
            "reason": "knowledge-projection-not-present",
            "usable": False,
        }
        payload["freshness"] = {
            "evaluated": False,
            "disclosure": "not evaluated (knowledge unavailable)",
            "concepts": 0,
            "counts_by_state": None,
        }
        payload["snapshot_parity"] = {
            "state": "not-available",
            "issue_count": 0,
            "reasons": [],
        }
        payload["governance"] = {
            "state": "not-present",
            "ledger": "not-present",
            "projection": "not-present",
            "expired_reviews": 0,
            "issue_count": 0,
            "reasons": [],
        }
        payload["drift"] = {
            "state": "not-evaluated",
            "confirmed_stale": 0,
            "indeterminate": 0,
            "nonsemantic_changes": 0,
            "counts_by_state": None,
            "diagnostic_count": 0,
            "reasons": [],
        }
    return payload


def _delete_path(payload: dict, path: tuple[str, ...]) -> None:
    target = payload
    for component in path[:-1]:
        target = target[component]
    del target[path[-1]]


def _set_path(payload: dict, path: tuple[str, ...], value: object) -> None:
    target = payload
    for component in path[:-1]:
        target = target[component]
    target[path[-1]] = value


def _load_report(
    tmp_path: Path,
    payload: dict,
    *,
    doctor_exit_code: int = 0,
    expected_strict: bool | None = None,
):
    report = tmp_path / "doctor.json"
    report.write_text(json.dumps(payload), encoding="utf-8")
    return SUMMARY_RENDERER["load_report"](
        report,
        doctor_exit_code=doctor_exit_code,
        expected_strict=expected_strict,
    )


def test_action_metadata_defines_the_public_inputs_and_composite_steps() -> None:
    action = _yaml(ACTION_PATH)

    assert action["runs"]["using"] == "composite"
    assert set(action["inputs"]) == {
        "wiki-dir",
        "src-dir",
        "source-selection",
        "strict",
        "fail-on",
        "evidence-id",
    }
    assert action["inputs"]["source-selection"]["default"] == ""
    assert action["inputs"]["strict"]["default"] == "true"
    assert action["inputs"]["fail-on"]["default"] == "unhealthy"
    assert action["inputs"]["evidence-id"]["default"] == "default"
    steps = action["runs"]["steps"]
    scalar_validation = steps[0]
    assert scalar_validation["name"] == "Validate scalar inputs"
    assert scalar_validation["env"] == {
        "INPUT_EVIDENCE_ID": "${{ inputs.evidence-id }}",
        "INPUT_STRICT": "${{ inputs.strict }}",
        "INPUT_FAIL_ON": "${{ inputs.fail-on }}",
    }
    assert "^[a-z0-9][a-z0-9._-]{0,39}$" in scalar_validation["run"]
    assert "true|false" in scalar_validation["run"]
    assert "unhealthy|degraded" in scalar_validation["run"]
    setup_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("uses") == f"actions/setup-python@{SETUP_PYTHON_SHA}"
    )
    assert setup_index > 0
    assert any(
        step.get("uses") == f"actions/setup-python@{SETUP_PYTHON_SHA}" for step in steps
    )
    remote_uses = [
        str(step["uses"])
        for step in steps
        if isinstance(step.get("uses"), str) and not str(step["uses"]).startswith("./")
    ]
    assert remote_uses
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in remote_uses)
    install = next(
        step for step in steps if step["name"] == "Install the dashboard package"
    )
    assert "-I -m pip install" in install["run"]
    assert "--no-cache-dir" in install["run"]
    assert '"${GITHUB_ACTION_PATH}/../.."' in install["run"]
    assert "agent-wiki-cli==" not in install["run"]


def test_action_couples_to_doctor_json_without_scraping_text() -> None:
    action = _yaml(ACTION_PATH)
    steps = action["runs"]["steps"]
    doctor = next(
        step for step in steps if step["name"] == "Build knowledge health report"
    )
    summary = next(
        step
        for step in steps
        if step["name"] == "Publish strict diagnostic dashboard and apply threshold"
    )

    assert "-I -m llm_wiki_cli.cli doctor" in doctor["run"]
    assert "--format json" in doctor["run"]
    assert doctor["env"]["INPUT_SOURCE_SELECTION"] == ("${{ inputs.source-selection }}")
    assert '--source-selection "${INPUT_SOURCE_SELECTION}"' in doctor["run"]
    assert "render_summary.py" in summary["run"]
    assert summary["env"]["DOCTOR_EXIT_CODE"] == (
        "${{ steps.doctor.outputs.exit-code }}"
    )
    assert '--doctor-exit-code "${DOCTOR_EXIT_CODE}"' in summary["run"]
    assert '--expected-strict "${INPUT_STRICT}"' in summary["run"]
    assert "--receipt" in summary["run"]
    combined = "\n".join(str(step.get("run", "")) for step in steps)
    assert not any(command in combined for command in ("grep ", "sed ", "awk ", "cut "))
    source = SUMMARY_SCRIPT.read_text(encoding="utf-8")
    assert "json.loads" in source
    assert "LLM Wiki Doctor" not in source


def test_action_plans_and_prepares_every_detected_locked_helper() -> None:
    action = _yaml(ACTION_PATH)
    steps = action["runs"]["steps"]
    plan = next(
        step for step in steps if step["name"] == "Plan dashboard extractor helpers"
    )
    prepare = next(
        step for step in steps if step["name"] == "Prepare dashboard extractor helpers"
    )

    assert "--plan" in plan["run"]
    assert "--format json" in plan["run"]
    assert "llm-wiki-prepare-extractors-plan/v1" in plan["run"]
    assert 'supported = ("typescript", "go", "rust", "haskell")' in plan["run"]
    assert "duplicate object key" in plan["run"]
    assert "unknown, duplicated, or out of canonical order" in plan["run"]
    assert '--source-selection "${INPUT_SOURCE_SELECTION}"' in plan["run"]

    modes = {
        "typescript": "routine",
        "go": "extractor-go",
        "rust": "extractor-rust",
        "haskell": "extractor-haskell",
    }
    for language, mode in modes.items():
        install = next(
            step
            for step in steps
            if step.get("if") == f"steps.extractor-plan.outputs.{language} == 'true'"
        )
        assert f"--mode {mode}" in install["run"]
        assert "setup-llm-wiki-ci-toolchains.sh" in install["run"]
        assert "release/toolchain-lock.json" in install["run"]
        assert "steps.setup-python.outputs.python-path" in install["run"]
        assert '--install-root "${LLM_WIKI_DOCTOR_TOOLCHAIN_DIR}"' in install["run"]

    assert '--cache-dir "${LLM_WIKI_DOCTOR_CACHE_DIR}"' in prepare["run"]
    assert '--source-selection "${INPUT_SOURCE_SELECTION}"' in prepare["run"]
    assert "prepare-extractors.log" in prepare["run"]


def test_action_reserves_paths_and_uploads_a_fixed_evidence_set() -> None:
    action = _yaml(ACTION_PATH)
    steps = action["runs"]["steps"]
    reserve = next(step for step in steps if step["name"] == "Reserve dashboard paths")
    upload = next(
        step
        for step in steps
        if step["name"] == "Upload fixed doctor dashboard evidence"
    )

    assert "llm-wiki-doctor-${INPUT_EVIDENCE_ID}-cache" in reserve["run"]
    assert "llm-wiki-doctor-${INPUT_EVIDENCE_ID}-toolchains" in reserve["run"]
    assert "llm-wiki-doctor-${INPUT_EVIDENCE_ID}-evidence" in reserve["run"]
    assert "LLM_WIKI_DOCTOR_TOOLCHAIN_DIR=%s" in reserve["run"]
    assert "^[a-z0-9][a-z0-9._-]{0,39}$" in reserve["run"]
    assert '-L "${reserved_dir}"' in reserve["run"]
    assert "llm-wiki-doctor-collisions" in reserve["run"]
    assert "exit 1" in reserve["run"]

    assert upload["if"] == "always() && steps.reserve.outputs.ready == 'true'"
    assert upload["uses"] == f"actions/upload-artifact@{UPLOAD_ARTIFACT_SHA}"
    assert upload["with"]["retention-days"] == 14
    assert upload["with"]["if-no-files-found"] == "error"
    assert upload["with"]["name"].startswith("llm-wiki-doctor-")
    assert set(upload["with"]["path"].splitlines()) == {
        "${{ runner.temp }}/llm-wiki-doctor-${{ inputs.evidence-id }}-evidence/doctor.json",
        "${{ runner.temp }}/llm-wiki-doctor-${{ inputs.evidence-id }}-evidence/dashboard-receipt.json",
        "${{ runner.temp }}/llm-wiki-doctor-${{ inputs.evidence-id }}-evidence/extractor-plan.json",
        "${{ runner.temp }}/llm-wiki-doctor-${{ inputs.evidence-id }}-evidence/prepare-extractors.log",
    }


def test_action_evidence_ids_isolate_cache_toolchain_and_evidence_paths(
    tmp_path: Path,
) -> None:
    action = _yaml(ACTION_PATH)
    reserve = next(
        step
        for step in action["runs"]["steps"]
        if step["name"] == "Reserve dashboard paths"
    )["run"]
    if os.name == "nt":
        for suffix in ("cache", "toolchains", "evidence"):
            assert f"llm-wiki-doctor-${{INPUT_EVIDENCE_ID}}-{suffix}" in reserve
        assert "LLM_WIKI_DOCTOR_TOOLCHAIN_DIR=%s" in reserve
        return

    runner_temp = tmp_path / "runner-temp"
    runner_temp.mkdir()
    for evidence_id in ("first", "second"):
        github_env = tmp_path / f"{evidence_id}-env"
        github_output = tmp_path / f"{evidence_id}-output"
        completed = subprocess.run(
            ["bash", "-c", reserve],
            cwd=ROOT,
            env={
                "GITHUB_ENV": str(github_env),
                "GITHUB_OUTPUT": str(github_output),
                "INPUT_EVIDENCE_ID": evidence_id,
                "PATH": "/usr/bin:/bin",
                "RUNNER_TEMP": str(runner_temp),
            },
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        expected = {
            "LLM_WIKI_DOCTOR_CACHE_DIR": (
                runner_temp / f"llm-wiki-doctor-{evidence_id}-cache"
            ),
            "LLM_WIKI_DOCTOR_TOOLCHAIN_DIR": (
                runner_temp / f"llm-wiki-doctor-{evidence_id}-toolchains"
            ),
            "LLM_WIKI_DOCTOR_EVIDENCE_DIR": (
                runner_temp / f"llm-wiki-doctor-{evidence_id}-evidence"
            ),
        }
        assert github_output.read_text(encoding="utf-8") == "ready=true\n"
        assert github_env.read_text(encoding="utf-8").splitlines() == [
            f"{name}={path}" for name, path in expected.items()
        ]
        assert all(path.is_dir() and not path.is_symlink() for path in expected.values())


def test_action_is_diagnostic_and_does_not_duplicate_integrity_validation() -> None:
    action = _yaml(ACTION_PATH)
    combined = "\n".join(str(step.get("run", "")) for step in action["runs"]["steps"])

    assert action["name"] == "LLM Wiki context health dashboard"
    assert "diagnostic" in action["description"]
    assert "ci-check" not in combined
    assert "run-llm-wiki-ci-check.sh" not in combined
    assert combined.count(" llm_wiki_cli.cli doctor") == 1


def test_manual_dashboard_workflow_is_separate_and_read_only() -> None:
    workflow = _yaml(DASHBOARD_WORKFLOW_PATH)
    triggers = workflow[True]
    job = workflow["jobs"]["dashboard"]
    steps = job["steps"]

    assert workflow["name"] == "LLM Wiki strict doctor dashboard"
    assert triggers == {"workflow_dispatch": None}
    assert workflow["permissions"] == {"contents": "read"}
    assert job["permissions"] == {"contents": "read"}
    assert job["runs-on"] == "ubuntu-24.04"
    assert job["timeout-minutes"] == 30
    assert job["name"] == "LLM Wiki strict doctor dashboard (diagnostic)"

    checkout = next(
        step for step in steps if step.get("uses") == f"actions/checkout@{CHECKOUT_SHA}"
    )
    assert checkout["with"]["persist-credentials"] is False
    dashboard = next(
        step for step in steps if step.get("uses") == "./integrations/github-action"
    )
    assert dashboard["with"] == {
        "wiki-dir": "docs/llm_wiki",
        "src-dir": ".",
        "strict": "true",
        "fail-on": "degraded",
    }
    raw = DASHBOARD_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "pull_request" not in raw
    assert "push:" not in raw
    assert "secrets" not in raw
    assert "contents: write" not in raw
    assert "LLM Wiki integrity" not in raw


@pytest.mark.parametrize(
    ("status", "fail_on", "expected"),
    [
        ("healthy", "degraded", 0),
        ("healthy", "unhealthy", 0),
        ("degraded", "degraded", 1),
        ("degraded", "unhealthy", 0),
        ("unhealthy", "degraded", 1),
        ("unhealthy", "unhealthy", 1),
        ("absent", "degraded", 1),
        ("absent", "unhealthy", 1),
    ],
)
def test_summary_renderer_applies_the_selected_threshold(
    tmp_path: Path,
    status: str,
    fail_on: str,
    expected: int,
) -> None:
    report = tmp_path / "doctor.json"
    summary = tmp_path / "summary.md"
    output = tmp_path / "output.txt"
    receipt = tmp_path / "receipt.json"
    report.write_text(json.dumps(_doctor_payload(status)), encoding="utf-8")
    environment = {
        **os.environ,
        "GITHUB_STEP_SUMMARY": str(summary),
        "GITHUB_OUTPUT": str(output),
    }

    completed = subprocess.run(
        [
            sys.executable,
            str(SUMMARY_SCRIPT),
            "--report",
            str(report),
            "--fail-on",
            fail_on,
            "--doctor-exit-code",
            str({"healthy": 0, "degraded": 1, "unhealthy": 2, "absent": 3}[status]),
            "--expected-strict",
            "true",
            "--receipt",
            str(receipt),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert completed.returncode == expected
    assert "| Overall |" in summary.read_text(encoding="utf-8")
    assert f"`{status}`" in summary.read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == f"status={status}\n"
    receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert receipt_payload["schema_version"] == "llm-wiki-doctor-dashboard/v1"
    assert receipt_payload["status"] == status
    assert receipt_payload["dashboard_exit_code"] == expected


def test_summary_renderer_rejects_contract_mismatch(tmp_path: Path) -> None:
    report = tmp_path / "doctor.json"
    payload = _doctor_payload("healthy")
    payload["schema_version"] = "llm-wiki-doctor/v2"
    report.write_text(json.dumps(payload), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(SUMMARY_SCRIPT),
            "--report",
            str(report),
            "--fail-on",
            "unhealthy",
            "--doctor-exit-code",
            "0",
            "--expected-strict",
            "true",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "Invalid doctor JSON contract" in completed.stderr


def test_summary_renderer_rejects_requested_strictness_mismatch(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="requested strict mode"):
        _load_report(
            tmp_path,
            _doctor_payload("healthy"),
            expected_strict=False,
        )


def test_summary_renderer_bounds_and_escapes_human_disclosure(
    tmp_path: Path,
) -> None:
    payload = _doctor_payload("healthy")
    hostile = "evil`**spoof**|next\nrow" + ("x" * 10_000)
    payload["freshness"]["disclosure"] = hostile
    report = _load_report(tmp_path, payload, expected_strict=True)

    rendered = SUMMARY_RENDERER["render_summary"](report)

    assert "evil`**spoof**" not in rendered
    assert r"evil\x60**spoof**\|next row" in rendered
    assert len(rendered.splitlines()) <= 40
    assert len(rendered.encode("utf-8")) <= 8192


@pytest.mark.parametrize("path", REQUIRED_REPORT_PATHS)
def test_summary_renderer_requires_every_doctor_v1_field(
    tmp_path: Path,
    path: tuple[str, ...],
) -> None:
    payload = deepcopy(_doctor_payload("healthy"))
    _delete_path(payload, path)

    with pytest.raises(ValueError, match="required"):
        _load_report(tmp_path, payload)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("schema_version",), 1),
        (("status",), 1),
        (("exit_code",), True),
        (("strict",), 1),
        (("wiki_dir",), None),
        (("src_dir",), []),
        (("availability",), []),
        (("availability", "state"), 1),
        (("availability", "reason"), None),
        (("availability", "usable"), 1),
        (("freshness",), []),
        (("freshness", "evaluated"), 1),
        (("freshness", "disclosure"), ""),
        (("freshness", "concepts"), True),
        (("freshness", "counts_by_state"), []),
        (("freshness", "counts_by_state", "current"), True),
        (("snapshot_parity",), []),
        (("snapshot_parity", "state"), 1),
        (("snapshot_parity", "issue_count"), True),
        (("snapshot_parity", "reasons"), "reason"),
        (("governance",), []),
        (("governance", "state"), 1),
        (("governance", "ledger"), 1),
        (("governance", "projection"), 1),
        (("governance", "expired_reviews"), True),
        (("governance", "issue_count"), -1),
        (("governance", "reasons"), [1]),
        (("drift",), []),
        (("drift", "state"), 1),
        (("drift", "confirmed_stale"), True),
        (("drift", "indeterminate"), -1),
        (("drift", "nonsemantic_changes"), 1.5),
        (("drift", "counts_by_state"), []),
        (("drift", "diagnostic_count"), None),
        (("drift", "reasons"), "reason"),
        (("verification_receipt",), []),
        (("verification_receipt", "state"), 1),
        (("verification_receipt", "reason"), None),
        (("verification_receipt", "recorded_result"), 1),
        (("verification_receipt", "passed"), 1),
        (("degraded_reasons",), {}),
        (("unhealthy_reasons",), [""]),
    ],
)
def test_summary_renderer_rejects_wrong_doctor_v1_field_types(
    tmp_path: Path,
    path: tuple[str, ...],
    value: object,
) -> None:
    payload = deepcopy(_doctor_payload("healthy"))
    _set_path(payload, path, value)

    with pytest.raises(ValueError):
        _load_report(tmp_path, payload)


@pytest.mark.parametrize("path", CLOSED_STATE_PATHS)
def test_summary_renderer_rejects_unknown_closed_states(
    tmp_path: Path,
    path: tuple[str, ...],
) -> None:
    payload = deepcopy(_doctor_payload("healthy"))
    _set_path(payload, path, "future-state")

    with pytest.raises(ValueError, match="unsupported"):
        _load_report(tmp_path, payload)


def test_summary_renderer_rejects_unknown_recorded_result_and_count_state(
    tmp_path: Path,
) -> None:
    recorded = deepcopy(_doctor_payload("healthy"))
    recorded["verification_receipt"]["recorded_result"] = "unknown"
    with pytest.raises(ValueError, match="unsupported"):
        _load_report(tmp_path, recorded)

    counts = deepcopy(_doctor_payload("healthy"))
    counts["freshness"]["counts_by_state"]["future-state"] = 0
    with pytest.raises(ValueError, match="not supported"):
        _load_report(tmp_path, counts)


def test_summary_renderer_ignores_additive_same_major_fields(
    tmp_path: Path,
) -> None:
    payload = deepcopy(_doctor_payload("healthy"))
    payload["future"] = {"state": "experimental"}
    payload["availability"]["future"] = "must-not-appear"

    loaded = _load_report(tmp_path, payload)
    rendered = SUMMARY_RENDERER["render_summary"](loaded)

    assert loaded["future"] == {"state": "experimental"}
    assert loaded["availability"]["future"] == "must-not-appear"
    assert "experimental" not in rendered
    assert "must-not-appear" not in rendered


def test_summary_renderer_rejects_inconsistent_v1_values(
    tmp_path: Path,
) -> None:
    usable = deepcopy(_doctor_payload("healthy"))
    usable["availability"]["usable"] = False
    with pytest.raises(ValueError, match="does not match"):
        _load_report(tmp_path, usable)

    concepts = deepcopy(_doctor_payload("healthy"))
    concepts["freshness"]["concepts"] = 3
    with pytest.raises(ValueError, match="does not match"):
        _load_report(tmp_path, concepts)

    drift = deepcopy(_doctor_payload("healthy"))
    drift["drift"]["state"] = "not-evaluated"
    with pytest.raises(ValueError, match="does not match"):
        _load_report(tmp_path, drift)

    forged_degraded = deepcopy(_doctor_payload("healthy"))
    forged_degraded["availability"].update(
        {"state": "degraded", "reason": "degraded-invalid"}
    )
    forged_degraded["snapshot_parity"]["state"] = "invalid"
    with pytest.raises(ValueError, match="status does not match its sections"):
        _load_report(tmp_path, forged_degraded)

    mixed_counts = deepcopy(_doctor_payload("healthy"))
    mixed_counts["drift"]["counts_by_state"].update(
        {"current": 1, "unknown": 1}
    )
    with pytest.raises(ValueError, match="does not match freshness"):
        _load_report(tmp_path, mixed_counts)

    invalid_governance = deepcopy(_doctor_payload("healthy"))
    invalid_governance["governance"].update(
        {
            "state": "invalid",
            "ledger": "invalid",
            "projection": "invalid",
            "issue_count": 1,
            "reasons": ["governance-invalid"],
        }
    )
    with pytest.raises(ValueError, match="status does not match its sections"):
        _load_report(tmp_path, invalid_governance)

    failed_verification = deepcopy(_doctor_payload("healthy"))
    failed_verification["verification_receipt"].update(
        {
            "state": "failed",
            "recorded_result": "passed",
            "passed": True,
        }
    )
    with pytest.raises(ValueError, match="failed state is inconsistent"):
        _load_report(tmp_path, failed_verification)

    absent_mixed = deepcopy(_doctor_payload("absent"))
    absent_mixed["snapshot_parity"]["state"] = "mixed"
    with pytest.raises(ValueError, match="does not match availability"):
        _load_report(tmp_path, absent_mixed, doctor_exit_code=3)


def test_summary_renderer_rejects_captured_process_exit_mismatch_before_writes(
    tmp_path: Path,
) -> None:
    report = tmp_path / "doctor.json"
    summary = tmp_path / "summary.md"
    output = tmp_path / "output.txt"
    report.write_text(json.dumps(_doctor_payload("healthy")), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(SUMMARY_SCRIPT),
            "--report",
            str(report),
            "--fail-on",
            "unhealthy",
            "--doctor-exit-code",
            "1",
            "--expected-strict",
            "true",
        ],
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "GITHUB_STEP_SUMMARY": str(summary),
            "GITHUB_OUTPUT": str(output),
        },
    )

    assert completed.returncode != 0
    assert "captured doctor process exit code" in completed.stderr
    assert not summary.exists()
    assert not output.exists()


def test_summary_renderer_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    report = tmp_path / "doctor.json"
    raw = json.dumps(_doctor_payload("healthy"))
    duplicate = raw.replace(
        '{"schema_version":',
        '{"status":"healthy","schema_version":',
    )
    report.write_text(duplicate, encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(SUMMARY_SCRIPT),
            "--report",
            str(report),
            "--fail-on",
            "unhealthy",
            "--doctor-exit-code",
            "0",
            "--expected-strict",
            "true",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "duplicate object key 'status'" in completed.stderr


def test_selftest_workflow_is_valid_and_dogfoods_the_local_action() -> None:
    workflow = _yaml(WORKFLOW_PATH)
    jobs = workflow["jobs"]
    steps = jobs["repository-fixture"]["steps"]

    triggers = workflow[True]
    assert triggers["push"]["branches"] == ["main"]
    assert triggers["push"]["paths"] == triggers["pull_request"]["paths"]
    assert workflow["concurrency"] == {
        "group": (
            "${{ github.workflow }}-${{ "
            "github.event.pull_request.number || github.ref }}"
        ),
        "cancel-in-progress": "${{ github.event_name == 'pull_request' }}",
    }

    checkout = next(
        step for step in steps if step.get("uses") == f"actions/checkout@{CHECKOUT_SHA}"
    )
    assert checkout["with"]["persist-credentials"] is False
    setup = next(
        step
        for step in steps
        if step.get("uses") == f"actions/setup-python@{SETUP_PYTHON_SHA}"
    )
    assert setup["with"] == {
        "python-version": "3.13",
        "cache": "pip",
        "cache-dependency-path": "pyproject.toml",
    }
    remote_uses = [
        str(step["uses"])
        for step in steps
        if isinstance(step.get("uses"), str) and not str(step["uses"]).startswith("./")
    ]
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in remote_uses)
    action_step = next(
        step for step in steps if step.get("uses") == "./integrations/github-action"
    )
    assert action_step["with"] == {
        "wiki-dir": ".action-selftest/wiki",
        "src-dir": "tests/fixtures/context-health-action/source",
        "strict": "true",
        "fail-on": "unhealthy",
        "evidence-id": "valid",
    }
    invalid_strict = next(step for step in steps if step.get("id") == "invalid-strict")
    invalid_evidence_id = next(
        step for step in steps if step.get("id") == "invalid-evidence-id"
    )
    invalid_fail_on = next(
        step for step in steps if step.get("id") == "invalid-fail-on"
    )
    assert invalid_strict["with"]["evidence-id"] == "invalid-strict"
    assert invalid_evidence_id["with"]["evidence-id"] == "Invalid/evidence"
    assert invalid_fail_on["with"]["evidence-id"] == "invalid-fail-on"
    assert len(
        {
            action_step["with"]["evidence-id"],
            invalid_strict["with"]["evidence-id"],
            invalid_evidence_id["with"]["evidence-id"],
            invalid_fail_on["with"]["evidence-id"],
        }
    ) == 4
    bootstrap = next(
        step
        for step in steps
        if step.get("name") == "Build repository-owned wiki fixture"
    )
    assert 'bin/llm-wiki" bootstrap' in bootstrap["run"]
    assert ".action-selftest/wiki" in bootstrap["run"]
    assert "python -m venv" in bootstrap["run"]
    assert '"${BOOTSTRAP_VENV}/bin/python" -m pip install' in bootstrap["run"]
    clean = next(
        step
        for step in steps
        if step.get("name") == "Verify the action interpreter is clean"
    )
    assert "pip show agent-wiki-cli" in clean["run"]
    combined = "\n".join(str(step.get("run", "")) for step in steps)
    assert "pip install -e" not in combined
    assert "pip install --editable" not in combined
    assert "actions/setup-python@v6" not in WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "actions/checkout@v6" not in WORKFLOW_PATH.read_text(encoding="utf-8")
    public_workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    for dependency in (
        ".github/scripts/setup-llm-wiki-ci-toolchains.sh",
        "release/qualification.py",
        "release/toolchain-lock.json",
    ):
        assert public_workflow.count(dependency) == 2
    assert "knowledge-" + "m1" not in public_workflow.casefold()
    assert "pre-" + "feature-bootstrap" not in public_workflow.casefold()
    assert re.search(r"\b[MP]\d+\b", public_workflow) is None
    assert (
        re.search(
            r"\b(?:phase|milestone|backlog|pilot)\b",
            public_workflow.casefold(),
        )
        is None
    )


def test_action_yaml_and_workflow_pass_available_validation() -> None:
    # PyYAML parsing always validates both files. When actionlint is installed,
    # also apply its workflow-specific checks.
    assert _yaml(ACTION_PATH)["runs"]["using"] == "composite"
    assert "jobs" in _yaml(WORKFLOW_PATH)
    actionlint = shutil.which("actionlint")
    if actionlint is None:
        return

    subprocess.run(
        [actionlint, str(WORKFLOW_PATH)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_readme_documents_the_ci_gate_inputs_and_thresholds() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("### Strict doctor dashboard", 1)[1].split("\n## ", 1)[0]

    assert "integrations/github-action" in section
    assert "wiki-dir:" in section
    assert "src-dir:" in section
    assert "source-selection:" in section
    assert "strict:" in section
    assert "fail-on:" in section
    assert "fail-on: unhealthy" in section
    assert "fail-on: degraded" in section
    assert "llm-wiki-doctor/v1" in section
    assert "same action checkout" in section
    assert "declared exit code" in section
    assert "immutable released commit" in section
    assert "does not replace general" in section
    assert "LLM Wiki integrity" in section
    assert "hash-bound dashboard receipt" in section


def test_repository_fixture_used_by_workflow_is_strictly_healthy(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    source = tmp_path / "source"
    shutil.copytree(
        ROOT / "tests" / "fixtures" / "context-health-action" / "source",
        source,
    )
    monkeypatch.chdir(tmp_path)
    bootstrap_cmd.run(
        types.SimpleNamespace(
            src_dir="source",
            wiki_dir="wiki",
            overwrite=False,
            depth="full",
            skip_workflows=True,
            skip_flows=True,
            skip_dependencies=True,
        )
    )
    capsys.readouterr()

    report = doctor_service.build_doctor_report(
        "wiki",
        "source",
        strict=True,
    )

    assert report.status is doctor_service.DoctorStatus.HEALTHY
    assert report.exit_code == 0
    validated = _load_report(
        tmp_path,
        report.to_payload(),
        doctor_exit_code=report.exit_code,
    )
    assert validated["status"] == "healthy"
