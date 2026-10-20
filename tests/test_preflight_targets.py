"""Repository proof declarations and local readiness cannot conceal capture gaps."""

from pathlib import Path

import pytest
from release import preflight, preflight_targets as adapter

ROOT = Path(__file__).parents[1]


def declaration_files(*, runner: object = "ubuntu-24.04", python="3.13"):
    import yaml

    return {
        ".github/workflows/release-qualification.yml": yaml.safe_dump(
            {
                "jobs": {
                    "proof": {
                        "runs-on": runner,
                        "steps": [
                            {
                                "uses": "./candidate/project-action",
                                "with": {
                                    "src-dir": "candidate",
                                    "maintenance-candidate-sha": "${{ needs.freeze.outputs.sha }}",
                                },
                            }
                        ],
                    }
                }
            }
        ).encode(),
        "project-action/action.yml": yaml.safe_dump(
            {
                "runs": {
                    "steps": [
                        {
                            "uses": "actions/setup-python@" + "a" * 40,
                            "with": {"python-version": python},
                        }
                    ]
                }
            }
        ).encode(),
    }


def test_adapter_derives_runtime_from_maintained_declarations_not_current_host():
    files = declaration_files()
    targets, inputs = adapter.declarations(ROOT, files.__getitem__)
    assert targets[0]["platform"] == "linux" and targets[0]["python"] == "3.13"
    assert targets[0]["machine"] is None
    assert set(inputs) == set(files)
    altered = declaration_files(
        runner="${{ matrix.runner }}", python="${{ inputs.python }}"
    )
    targets, _ = adapter.declarations(ROOT, altered.__getitem__)
    assert targets[0]["platform"] is None and targets[0]["python"] is None


def test_own_repository_proof_owner_includes_composite_runtime():
    rows, inputs = adapter.declarations(ROOT, lambda name: (ROOT / name).read_bytes())
    assert len(rows) == 1
    assert "#action/step-" in rows[0]["owner"] and rows[0]["platform"] == "linux"
    assert rows[0]["python"] == "3.13"
    assert "integrations/wiki-integrity/action.yml" in inputs


def test_unavailable_or_unsupported_owner_remains_unknown(tmp_path):
    def missing(name):
        raise FileNotFoundError(name)

    assert adapter.inspect(tmp_path, "wiki", missing)["status"] == "unknown"
    assert (
        adapter.inspect(
            tmp_path, "wiki", declaration_files(runner={"group": "custom"}).__getitem__
        )["status"]
        == "unknown"
    )


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("capture-required", "target-capture-required"),
        ("unknown", "target-runtime-unknown"),
        ("requirements-match", "local-ready-hosted-required"),
    ],
)
def test_completed_local_stages_cannot_obscure_target_capture_requirement(
    state, expected
):
    plan = {
        "binding": {
            "dirty": "",
            "maintenance": {"mode": "required", "target_runtime": {"status": state}},
        },
        "readiness": {
            "status": "eligible",
            "review": {"status": "recorded"},
            "build_residue": [],
        },
    }
    attempts = [{"stage": s, "status": "passed"} for s in preflight.STAGES]
    assert preflight._outcome(plan, "run", list(preflight.STAGES), attempts) == expected
    assert (
        preflight._outcome(plan, "rehearse", list(preflight.STAGES), attempts)
        == "blocked"
    )
    assert all(row["status"] == "passed" for row in attempts)


def test_old_plans_without_target_requirements_are_not_backfilled_as_verified():
    plan = {
        "binding": {"dirty": "", "maintenance": {"status": "hosted-proof-required"}},
        "readiness": {
            "status": "eligible",
            "review": {"status": "recorded"},
            "build_residue": [],
        },
    }
    attempts = [{"stage": s, "status": "passed"} for s in preflight.STAGES]
    assert (
        preflight._outcome(plan, "run", list(preflight.STAGES), attempts)
        == "target-runtime-unknown"
    )


def test_advisory_target_does_not_become_a_new_required_gate():
    plan = {
        "binding": {
            "dirty": "",
            "maintenance": {
                "mode": "advisory",
                "target_runtime": {"status": "capture-required"},
            },
        },
        "readiness": {
            "status": "eligible",
            "review": {"status": "recorded"},
            "build_residue": [],
        },
    }
    attempts = [{"stage": s, "status": "passed"} for s in preflight.STAGES]
    assert (
        preflight._outcome(plan, "run", list(preflight.STAGES), attempts)
        == "local-ready-hosted-required"
    )


def test_plan_summary_exposes_capture_requirement_before_any_stage():
    binding = {
        "maintenance": {
            "mode": "required",
            "target_runtime": {
                "status": "capture-required",
                "counts": {"capture-required": 1},
                "next_action": "review target capture",
            },
        }
    }
    summary = preflight._target_readiness(binding)
    assert (
        summary["status"] == "capture-required"
        and summary["required_for_hosted_proof"] is True
    )
    assert (
        summary["counts"] == {"capture-required": 1}
        and summary["target_execution_verified"] is False
    )


def test_activation_refusal_does_not_hide_independent_target_requirement(
    monkeypatch, tmp_path
):
    from release import knowledge_maintenance as maintenance

    (tmp_path / "release").mkdir()
    (tmp_path / "release/knowledge-maintenance.json").write_text(
        '{"mode":"required","wiki_dir":"wiki"}'
    )
    monkeypatch.setattr(maintenance, "composite_policy_digest", lambda read: "current")

    def blocked(*args, **kwargs):
        raise maintenance.ActivationMismatch(
            {"implementation_sha256": "previous"}, "current"
        )

    monkeypatch.setattr(maintenance, "policy", blocked)
    monkeypatch.setattr(
        adapter,
        "inspect",
        lambda *args: {
            "status": "capture-required",
            "target_execution_verified": False,
        },
    )
    result = preflight._maintenance(tmp_path)
    assert result["status"] == "blocked" and "health policy changed" in result["reason"]
    assert result["target_runtime"]["status"] == "capture-required"
    assert not result["target_runtime"]["target_execution_verified"]


@pytest.mark.parametrize(
    "raw", [b"[]", b"jobs: []", b"jobs: {proof: []}", b"jobs: {proof: {steps: [text]}}"]
)
def test_malformed_owner_declarations_return_unknown_not_an_inferred_target(
    tmp_path, raw
):
    result = adapter.inspect(tmp_path, "wiki", lambda name: raw)
    assert (
        result["status"] == "unknown" and result["target_execution_verified"] is False
    )


def test_matching_runtime_cannot_clear_an_independent_policy_refusal():
    plan = {
        "binding": {
            "dirty": "",
            "maintenance": {
                "status": "blocked",
                "mode": "required",
                "target_runtime": {"status": "requirements-match"},
            },
        },
        "readiness": {
            "status": "eligible",
            "review": {"status": "recorded"},
            "build_residue": [],
        },
    }
    attempts = [{"stage": s, "status": "passed"} for s in preflight.STAGES]
    assert (
        preflight._outcome(plan, "run", list(preflight.STAGES), attempts) == "blocked"
    )


@pytest.mark.parametrize(
    "raw",
    [
        b"jobs: {}\njobs: {}",
        b"jobs: {}\n---\njobs: {}",
        b"jobs: !application-code {}",
        b"jobs: &recursive {proof: *recursive}",
    ],
)
def test_ambiguous_or_executable_yaml_cannot_supply_runtime_authority(tmp_path, raw):
    result = adapter.inspect(tmp_path, "wiki", lambda name: raw)
    assert result["status"] == "unknown" and not result["target_execution_verified"]
