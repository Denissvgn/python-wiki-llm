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
SETUP_PYTHON_SHA = "ece7cb06caefa5fff74198d8649806c4678c61a1"
CHECKOUT_SHA = "d23441a48e516b6c34aea4fa41551a30e30af803"
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
    return {
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
):
    report = tmp_path / "doctor.json"
    report.write_text(json.dumps(payload), encoding="utf-8")
    return SUMMARY_RENDERER["load_report"](
        report,
        doctor_exit_code=doctor_exit_code,
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
    }
    assert action["inputs"]["source-selection"]["default"] == ""
    assert action["inputs"]["strict"]["default"] == "true"
    assert action["inputs"]["fail-on"]["default"] == "unhealthy"
    steps = action["runs"]["steps"]
    assert any(
        step.get("uses") == f"actions/setup-python@{SETUP_PYTHON_SHA}"
        for step in steps
    )
    remote_uses = [
        str(step["uses"])
        for step in steps
        if isinstance(step.get("uses"), str)
        and not str(step["uses"]).startswith("./")
    ]
    assert remote_uses
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in remote_uses)
    install = next(step for step in steps if step["name"] == "Install LLM Wiki CLI")
    assert "--disable-pip-version-check" in install["run"]
    assert "--no-input" in install["run"]
    assert '"${GITHUB_ACTION_PATH}/../.."' in install["run"]
    assert "agent-wiki-cli==" not in install["run"]


def test_action_couples_to_doctor_json_without_scraping_text() -> None:
    action = _yaml(ACTION_PATH)
    steps = action["runs"]["steps"]
    doctor = next(step for step in steps if step["name"] == "Build knowledge health report")
    summary = next(
        step
        for step in steps
        if step["name"] == "Publish health summary and apply threshold"
    )

    assert "llm-wiki doctor" in doctor["run"]
    assert "--format json" in doctor["run"]
    assert doctor["env"]["INPUT_SOURCE_SELECTION"] == (
        "${{ inputs.source-selection }}"
    )
    assert '--source-selection "${INPUT_SOURCE_SELECTION}"' in doctor["run"]
    assert "render_summary.py" in summary["run"]
    assert summary["env"]["DOCTOR_EXIT_CODE"] == (
        "${{ steps.doctor.outputs.exit-code }}"
    )
    assert '--doctor-exit-code "${DOCTOR_EXIT_CODE}"' in summary["run"]
    combined = "\n".join(str(step.get("run", "")) for step in steps)
    assert not any(
        command in combined
        for command in ("grep ", "sed ", "awk ", "cut ")
    )
    source = SUMMARY_SCRIPT.read_text(encoding="utf-8")
    assert "json.loads" in source
    assert "LLM Wiki Doctor" not in source


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
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "Invalid doctor JSON contract" in completed.stderr


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

    assert any(
        step.get("uses") == f"actions/checkout@{CHECKOUT_SHA}" for step in steps
    )
    assert any(
        step.get("uses") == f"actions/setup-python@{SETUP_PYTHON_SHA}"
        for step in steps
    )
    remote_uses = [
        str(step["uses"])
        for step in steps
        if isinstance(step.get("uses"), str)
        and not str(step["uses"]).startswith("./")
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
    }
    bootstrap = next(
        step for step in steps if step.get("name") == "Build repository-owned wiki fixture"
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
    assert "knowledge-m1" not in public_workflow.casefold()
    assert "pre-feature-bootstrap" not in public_workflow.casefold()
    assert re.search(r"\b[MP]\d+\b", public_workflow) is None
    assert re.search(
        r"\b(?:phase|milestone|backlog|pilot)\b",
        public_workflow.casefold(),
    ) is None


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
    section = readme.split("### CI gate", 1)[1].split("\n## ", 1)[0]

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
