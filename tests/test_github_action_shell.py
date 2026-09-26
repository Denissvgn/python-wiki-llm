"""Execute the POSIX composite Action boundary with the installed CLI.

Windows retains shared CLI and static Action contracts; conftest collects these
Bash executions on the same Ubuntu/Darwin hosts as the other shell boundaries.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import types

import pytest

from llm_wiki_cli.commands import bootstrap_cmd
from tests.test_github_action import ACTION_PATH, ROOT, _yaml


@pytest.fixture
def action_shell(tmp_path):
    action = _yaml(ACTION_PATH)
    inputs = {name: row["default"] for name, row in action["inputs"].items()}
    inputs.update({"src-dir": "source", "wiki-dir": "wiki"})
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (tmp_path / ".git").write_text("gitdir: absent\n", encoding="utf-8")
    state = {
        **{
            key: value
            for key, value in os.environ.items()
            if not key.startswith("INPUT_")
        },
        "GITHUB_ACTION_PATH": str(ACTION_PATH.parent),
        "GITHUB_STEP_SUMMARY": str(evidence / "summary.md"),
        "LLM_WIKI_DOCTOR_EVIDENCE_DIR": str(evidence),
        "LLM_WIKI_DOCTOR_CACHE_DIR": str(tmp_path / "cache"),
    }
    outputs = {}

    def expand(value):
        if value == "${{ steps.setup-python.outputs.python-path }}":
            return sys.executable
        if value.startswith("${{ inputs."):
            return inputs[value.removeprefix("${{ inputs.").removesuffix(" }}")]
        if value == "${{ steps.doctor.outputs.exit-code }}":
            return outputs["doctor"]["exit-code"]
        if "${{" in value:
            assert value.startswith("llm-wiki-doctor-"), value
            return "llm-wiki-doctor-shell-fixture"
        return value

    def run(name):
        step = next(
            s for s in action["runs"]["steps"] if s.get("id", s["name"]) == name
        )
        output = evidence / (name.replace(" ", "-") + ".outputs")
        env = {**state, "GITHUB_OUTPUT": str(output)}
        env.update({key: expand(value) for key, value in step.get("env", {}).items()})
        script = step["run"].replace(
            "${{ steps.setup-python.outputs.python-path }}", sys.executable
        )
        completed = subprocess.run(
            ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail"],
            input=script,
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        outputs[name] = (
            dict(line.split("=", 1) for line in output.read_text().splitlines())
            if output.exists()
            else {}
        )
        return completed

    return run, inputs, evidence


@pytest.mark.parametrize("schema", [None, "v1", "v3"], ids=["default", "v1", "v3"])
@pytest.mark.parametrize("scenario", ["clean", "drift", "corrupt"])
def test_actual_action_commands_preserve_schema_scope_and_failure_receipts(
    tmp_path,
    monkeypatch,
    action_shell,
    schema,
    scenario,
):
    from tests.provider_conformance.action_fixture import hashes

    run, inputs, evidence = action_shell
    if schema is not None:
        inputs["report-schema"] = schema
    shutil.copytree(
        ROOT / "tests/fixtures/context-health-action/source", tmp_path / "source"
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
    if scenario == "drift":
        path = tmp_path / "source/models.py"
        path.write_text(
            path.read_text().replace('name: str = ""', "name: int = 0"),
            encoding="utf-8",
        )
    elif scenario == "corrupt":
        (tmp_path / "wiki/.llm-wiki-surface.json").write_text(
            "{broken", encoding="utf-8"
        )
    before = hashes(tmp_path)
    for step in (
        "Validate scalar inputs",
        "extractor-plan",
        "Prepare dashboard extractor helpers",
        "doctor",
    ):
        result = run(step)
        assert result.returncode == 0, (step, result.stdout, result.stderr)
    assert json.loads((evidence / "extractor-plan.json").read_text()) == {
        "schema": "llm-wiki-prepare-extractors-plan/v1",
        "languages": [],
    }
    rendered = run("summary")
    assert rendered.returncode == (0 if scenario == "clean" else 1), rendered.stderr
    report = json.loads((evidence / "doctor.json").read_text())
    receipt = json.loads((evidence / "dashboard-receipt.json").read_text())
    assert report["schema_version"] == "llm-wiki-doctor/" + (schema or "v1")
    assert report["src_dir"] == "source" and report["wiki_dir"] == "wiki"
    assert report["status"] == ("healthy" if scenario == "clean" else "unhealthy")
    if scenario == "drift":
        assert report["drift"]["confirmed_stale"] >= 1
    if scenario == "corrupt":
        assert report["availability"]["state"] == "unsupported"
        assert report["snapshot_parity"]["state"] == "not-available"
    assert receipt["report_schema_version"] == report["schema_version"]
    assert receipt["schema_version"] == "llm-wiki-doctor-dashboard/" + (
        "v2" if schema == "v3" else "v1"
    )
    assert receipt["doctor_exit_code"] == report["exit_code"]
    assert receipt["dashboard_exit_code"] == rendered.returncode
    assert (
        receipt["report_sha256"]
        == hashlib.sha256((evidence / "doctor.json").read_bytes()).hexdigest()
    )
    assert hashes(tmp_path) == before


@pytest.mark.parametrize("schema", ["v2", "unknown", ""])
def test_actual_action_rejects_invalid_schema_before_creating_evidence(
    action_shell, schema
):
    run, inputs, evidence = action_shell
    inputs["report-schema"] = schema
    result = run("Validate scalar inputs")
    assert result.returncode == 2 and "report-schema must be v1 or v3" in result.stderr
    assert not list(evidence.iterdir())
