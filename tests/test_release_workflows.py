"""Static release-workflow safety contracts."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from tests import release_artifact_smoke


ROOT = Path(__file__).parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
REMOTE_ACTION = re.compile(r"^[^@]+@[0-9a-f]{40}$")


def _yaml(name: str) -> dict:
    payload = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _remote_uses(workflow: dict) -> list[str]:
    result: list[str] = []
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            value = step.get("uses")
            if isinstance(value, str) and not value.startswith("./"):
                result.append(value)
    return result


def test_all_workflow_actions_are_pinned_to_full_commits() -> None:
    for path in sorted(WORKFLOWS.glob("*.yml")):
        workflow = _yaml(path.name)
        remote = _remote_uses(workflow)
        assert remote, path
        assert all(REMOTE_ACTION.fullmatch(value) for value in remote), (
            path,
            remote,
        )


def test_dispatch_inputs_are_not_interpolated_into_shell_scripts() -> None:
    for path in sorted(WORKFLOWS.glob("*.yml")):
        workflow = _yaml(path.name)
        triggers = workflow.get("on", workflow.get(True, {}))
        if "workflow_dispatch" not in triggers:
            continue
        for job_name, job in workflow["jobs"].items():
            for step in job.get("steps", []):
                script = step.get("run")
                if not isinstance(script, str):
                    continue
                assert "${{ inputs." not in script, (path, job_name, script)
                assert "${{ github.event.inputs." not in script, (
                    path,
                    job_name,
                    script,
                )


def test_action_selftest_uses_step_scoped_runner_temp_and_negative_cases() -> None:
    workflow = _yaml("action-selftest.yml")
    job = workflow["jobs"]["repository-fixture"]
    assert "env" not in job or "BOOTSTRAP_VENV" not in job["env"]
    fixture = next(
        step
        for step in job["steps"]
        if step.get("name") == "Build repository-owned wiki fixture"
    )
    assert fixture["env"]["BOOTSTRAP_VENV"] == (
        "${{ runner.temp }}/agent-wiki-bootstrap"
    )
    text = (WORKFLOWS / "action-selftest.yml").read_text(encoding="utf-8")
    assert "Reject an invalid strict input" in text
    assert "Reject an invalid failure threshold" in text
    assert text.count('test "${STEP_OUTCOME}" = "failure"') == 2


def test_ci_pins_the_package_build_tool() -> None:
    workflow = _yaml("ci.yml")
    package_build = next(
        step
        for step in workflow["jobs"]["test"]["steps"]
        if step.get("name") == "Check package builds"
    )
    assert 'python -m pip install --no-cache-dir "build==1.5.0"' in package_build[
        "run"
    ]


def test_publish_is_dry_run_by_default_and_publisher_cannot_build() -> None:
    workflow = _yaml("publish.yml")
    dispatch = workflow.get("on", workflow.get(True))["workflow_dispatch"]
    assert dispatch["inputs"]["publish"]["default"] is False
    assert dispatch["inputs"]["qualification-ref"]["required"] is True
    verify_job = workflow["jobs"]["verify"]
    verify_steps = verify_job["steps"]
    verify_text = "\n".join(str(step.get("run", "")) for step in verify_steps)
    assert verify_job["env"]["CANDIDATE_SHA"] == "${{ inputs.candidate-sha }}"
    assert verify_job["env"]["QUALIFICATION_RUN_ID"] == (
        "${{ inputs.qualification-run-id }}"
    )
    assert verify_job["env"]["QUALIFICATION_REF"] == (
        "${{ inputs.qualification-ref }}"
    )
    assert verify_job["env"]["WHEEL_SHA256"] == (
        "${{ inputs.wheel-sha256 }}"
    )
    assert verify_job["env"]["SDIST_SHA256"] == (
        "${{ inputs.sdist-sha256 }}"
    )
    assert "--check-registry" in verify_text
    assert "verify-workflow-run" in verify_text
    assert ".github/workflows/release-qualification.yml" in verify_text
    assert '--workflow-ref "${QUALIFICATION_REF}"' in verify_text
    assert '--workflow-revision "${CANDIDATE_SHA}"' in verify_text
    assert "--event workflow_dispatch" in verify_text
    assert "--repository-root candidate-source" in verify_text
    assert verify_text.count("gh attestation verify") == 2
    assert verify_text.count("--source-digest") == 2
    assert verify_text.count("--source-ref") == 2
    assert verify_text.count("--signer-digest") == 2
    assert verify_text.count("--deny-self-hosted-runners") == 2
    assert "https://slsa.dev/provenance/v1" in verify_text
    assert "https://spdx.dev/Document/v2.3" in verify_text
    assert "finalize-promotion" in verify_text
    assert "for number in" not in verify_text
    assert "workflow-run-verification.json" in verify_text
    assert "bundle-verification.json" in verify_text
    tag_step = next(
        step
        for step in verify_steps
        if step.get("name") == "Require the release tag only for a real publication"
    )
    assert tag_step["if"] == "${{ inputs.publish }}"
    assert "--require-tag" in tag_step["run"]

    publish = workflow["jobs"]["publish"]
    assert publish["environment"]["name"] == "pypi"
    assert publish["permissions"] == {"actions": "read", "id-token": "write"}
    uses = [step["uses"] for step in publish["steps"]]
    assert len(uses) == 2
    assert any(value.startswith("actions/download-artifact@") for value in uses)
    assert any(value.startswith("pypa/gh-action-pypi-publish@") for value in uses)
    combined = "\n".join(str(step) for step in publish["steps"])
    assert "checkout" not in combined
    assert "setup-python" not in combined
    assert "pip install" not in combined
    assert "python -m build" not in combined
    assert "skip-existing" not in combined
    dry_run = next(
        step
        for step in verify_steps
        if step.get("name") == "Record dry-run result"
    )
    assert (
        'printf "Verified \\`%s\\` without uploading.\\n"'
        in dry_run["run"]
    )
    assert "printf 'Verified `%s` without uploading." not in dry_run["run"]


def test_publish_uses_trusted_verifier_before_candidate_checkout() -> None:
    workflow = _yaml("publish.yml")
    steps = workflow["jobs"]["verify"]["steps"]
    indexes = {
        step.get("name"): index
        for index, step in enumerate(steps)
        if step.get("name")
    }
    assert indexes[
        "Bind promotion to the protected default-branch workflow"
    ] < indexes["Check out the trusted default-branch verifier"]
    assert indexes[
        "Check out the trusted default-branch verifier"
    ] < indexes["Verify the qualification run before candidate checkout"]
    assert indexes[
        "Verify the qualification run before candidate checkout"
    ] < indexes["Check out the candidate for read-only identity verification"]

    bind = steps[
        indexes["Bind promotion to the protected default-branch workflow"]
    ]
    assert bind["env"]["DEFAULT_BRANCH"] == (
        "${{ github.event.repository.default_branch }}"
    )
    assert bind["env"]["WORKFLOW_REF"] == "${{ github.workflow_ref }}"
    assert bind["env"]["WORKFLOW_SHA"] == "${{ github.workflow_sha }}"
    assert "workflow_dispatch" in bind["run"]
    assert ".github/workflows/publish.yml@${default_ref}" in bind["run"]
    assert 'test "${WORKFLOW_SHA}" = "${RUN_SHA}"' in bind["run"]
    assert "git check-ref-format" in bind["run"]

    trusted_checkout = steps[
        indexes["Check out the trusted default-branch verifier"]
    ]
    assert trusted_checkout["with"]["ref"] == "${{ github.workflow_sha }}"
    assert trusted_checkout["with"]["path"] == "trusted-verifier"
    assert trusted_checkout["with"]["persist-credentials"] is False

    candidate_checkout = steps[
        indexes["Check out the candidate for read-only identity verification"]
    ]
    assert candidate_checkout["with"]["ref"] == "${{ inputs.candidate-sha }}"
    assert candidate_checkout["with"]["path"] == "candidate-source"
    assert candidate_checkout["with"]["persist-credentials"] is False

    shell_scripts = [
        step["run"] for step in steps if isinstance(step.get("run"), str)
    ]
    assert all("${{ inputs." not in script for script in shell_scripts)
    assert all("${{ github.event.inputs." not in script for script in shell_scripts)
    python_commands = "\n".join(
        line
        for script in shell_scripts
        for line in script.splitlines()
        if "qualification.py" in line
    )
    assert "trusted-verifier/release/qualification.py" in python_commands
    assert "python -I release/qualification.py" not in python_commands
    assert "candidate-source/release/qualification.py" not in python_commands


def test_qualification_freezes_one_archive_and_smokes_without_checkout() -> None:
    workflow = _yaml("release-qualification.yml")
    jobs = workflow["jobs"]
    freeze_text = "\n".join(str(step) for step in jobs["freeze"]["steps"])
    assert "freeze-source" in freeze_text
    assert "candidate-source.tar" in freeze_text
    assert "qualification-harnesses.tar" in freeze_text
    assert "git archive --format=tar" in freeze_text
    assert "release/qualification.py" in freeze_text
    assert "tests/release_artifact_smoke.py" in freeze_text
    assert "sha256sum" in freeze_text
    assert jobs["freeze"]["outputs"]["harness-sha256"] == (
        "${{ steps.harness.outputs.harness-sha256 }}"
    )
    harness_upload = next(
        step
        for step in jobs["freeze"]["steps"]
        if step.get("with", {}).get("name") == "qualification-harnesses"
    )
    assert harness_upload["with"]["path"] == (
        "${{ runner.temp }}/frozen/qualification-harnesses.tar"
    )
    assert harness_upload["with"]["compression-level"] == 0

    harness_consumers = 0
    for job_name, job in jobs.items():
        if job_name == "freeze":
            continue
        steps = job.get("steps", [])
        downloads = [
            index
            for index, step in enumerate(steps)
            if step.get("with", {}).get("name") == "qualification-harnesses"
        ]
        if not downloads:
            continue
        harness_consumers += 1
        verifiers = [
            index
            for index, step in enumerate(steps)
            if step.get("name") == "Verify and extract qualification harnesses"
        ]
        assert len(downloads) == len(verifiers) == 1, job_name
        assert downloads[0] < verifiers[0], job_name
        verify_step = steps[verifiers[0]]
        assert verify_step["env"]["EXPECTED_HARNESS_SHA256"] == (
            "${{ needs.freeze.outputs.harness-sha256 }}"
        )
        verify_run = verify_step["run"]
        assert "hashlib.sha256" in verify_run
        assert "qualification harness digest mismatch" in verify_run
        assert "tarfile --extract" in verify_run
        earlier_runs = "\n".join(
            str(step.get("run", "")) for step in steps[:verifiers[0]]
        )
        assert "incoming/tools/release/qualification.py" not in earlier_runs
        assert "incoming/tools/tests/release_artifact_smoke.py" not in earlier_runs
    assert harness_consumers == 17

    for job_name in ("core", "slow", "security-behavior", "product", "mcp"):
        text = "\n".join(str(step) for step in jobs[job_name]["steps"])
        assert "candidate-source" in text
        assert "extract-source" in text
        assert " -e " not in text
    smoke = jobs["artifact-smoke"]
    smoke_uses = [
        step.get("uses", "") for step in smoke["steps"] if "uses" in step
    ]
    assert not any(value.startswith("actions/checkout@") for value in smoke_uses)
    smoke_text = "\n".join(str(step) for step in smoke["steps"])
    assert "release_artifact_smoke.py" in smoke_text
    assert "default-venv" in smoke_text
    assert "mcp-venv" in smoke_text


def test_qualification_binds_workflow_ref_and_revision_before_candidate_code() -> None:
    workflow = _yaml("release-qualification.yml")
    steps = workflow["jobs"]["freeze"]["steps"]
    bind_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Bind the workflow definition to the candidate"
    )
    freeze_index = next(
        index for index, step in enumerate(steps) if "freeze-source" in step.get("run", "")
    )
    assert bind_index < freeze_index
    bind = steps[bind_index]
    assert bind["env"]["WORKFLOW_EVENT"] == "${{ github.event_name }}"
    assert bind["env"]["WORKFLOW_REF"] == "${{ github.workflow_ref }}"
    assert bind["env"]["WORKFLOW_SHA"] == "${{ github.workflow_sha }}"
    assert "workflow_dispatch" in bind["run"]
    assert "refs/heads/*" in bind["run"]
    assert "git check-ref-format" in bind["run"]


def test_artifact_smoke_preserves_virtualenv_interpreter_path(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    def reject_resolution(_path: Path, *, strict: bool = False) -> Path:
        del strict
        raise AssertionError("virtualenv interpreter symlinks must not resolve")

    monkeypatch.setattr(Path, "resolve", reject_resolution)
    relative = Path("default-venv") / "bin" / "python"
    assert release_artifact_smoke._absolute_without_symlink_resolution(
        relative
    ) == (tmp_path / relative)


def test_qualification_has_every_gate_and_fail_closed_discovery() -> None:
    workflow = _yaml("release-qualification.yml")
    text = (WORKFLOWS / "release-qualification.yml").read_text(encoding="utf-8")
    for number in range(14):
        assert f"RD-{number:02d}" in text
    assert "Prevent discovery evidence from qualifying" in text
    assert "--discovery" in text
    assert "--gate \"RD-13=BLOCKED\"" in text
    assert "--allow-non-go-exit-zero" in text
    assert "qualified-release" in text
    assert "compare-builds" in text
    assert "compare-smoke" in text
    assert "actions/attest-build-provenance@" in text
    assert "actions/attest-sbom@" in text
    assert "--gate-decision gate-decision.json" in text
    for gate in range(13):
        assert f'--evidence "RD-{gate:02d}:' in text
    assert "Download all hosted gate evidence" in text
    assert "evidence-rd-10" in text

    discovery = workflow["jobs"]["discovery-allowlist"]
    discovery_text = "\n".join(
        str(step) for step in discovery["steps"]
    )
    assert "discover-allowlist" in discovery_text
    assert "discovered-skip-allowlist" in discovery_text
    assert "pattern" in discovery_text and "evidence-core-*" in discovery_text

    owners = workflow["jobs"]["owner-lanes"]
    owners_text = "\n".join(str(step) for step in owners["steps"])
    assert "verify-owner-lanes" in owners_text
    assert "--identity incoming/source/identity.json" in owners_text
    assert "--owner-junit" in owners_text
    assert "pattern" in owners_text and "evidence-*" in owners_text
    assert "core-windows-3.13.xml" in owners_text
    assert "REVIEW-REQUIRED" not in owners_text
    assert "owner-lanes" in workflow["jobs"]["bundle"]["needs"]
    decision_text = "\n".join(
        str(step) for step in workflow["jobs"]["decision"]["steps"]
    )
    assert '--gate "RD-02=${{ needs.owner-lanes.result }}"' in decision_text

    publish_text = (WORKFLOWS / "publish.yml").read_text(encoding="utf-8")
    assert "--allow-non-go-exit-zero" not in publish_text


def test_locked_toolchain_archives_and_oci_digests_are_the_executed_inputs() -> None:
    workflow = _yaml("release-qualification.yml")
    toolchains = "\n".join(
        str(step) for step in workflow["jobs"]["toolchains"]["steps"]
    )
    assert "actions/setup-node@" not in toolchains
    assert "actions/setup-go@" not in toolchains
    for key in (
        "toolchains.node.artifact",
        "toolchains.npm.artifact",
        "toolchains.go.artifact",
        "toolchains.haskell.artifact",
        "toolchains.rust.artifact",
        "toolchains.rust.clippy_artifact",
    ):
        assert key in toolchains
    assert "locked-node/bin/node" in toolchains
    assert "locked-go/go/bin/go" in toolchains
    assert "locked-rust/install.sh" in toolchains
    assert "locked-clippy/install.sh" in toolchains
    assert "locked-ghc-source" in toolchains
    assert "govulncheck-builder" in toolchains
    assert (
        '-require="golang.org/x/vuln@v${govulncheck_version}"'
        in toolchains
    )
    assert (
        '-replace="golang.org/x/vuln=${RUNNER_TEMP}/govulncheck-source"'
        in toolchains
    )
    assert "go install -mod=readonly" in toolchains
    assert "golang.org/x/vuln/cmd/govulncheck" in toolchains
    assert "go install ./cmd/govulncheck" not in toolchains
    versions = next(
        step["run"]
        for step in workflow["jobs"]["toolchains"]["steps"]
        if step.get("name") == "Record and enforce tool versions"
    )
    assert versions.lstrip().startswith("set -euo pipefail")
    assert "cargo-audit --version | tee evidence/cargo-audit.txt" in versions
    assert "cargo audit --version" not in versions
    assert "cat evidence/cargo-audit.txt" in versions
    assert "qualification_tools.cargo-audit.version_output" in versions
    assert "qualification_tools.govulncheck.version_output" in versions
    assert "grep -c '^Scanner: '" in versions
    assert "Scanner: ${expected_govulncheck}" in versions
    audit = next(
        step["run"]
        for step in workflow["jobs"]["toolchains"]["steps"]
        if step.get("name") == "Audit exact helper dependency trees"
    )
    assert audit.lstrip().startswith("set -euo pipefail")
    assert "govulncheck -json ./..." in audit
    assert "govulncheck-blocking.txt" in audit
    assert audit.index("govulncheck -json ./...") < audit.index(
        "govulncheck ./... 2>&1"
    )
    audit_lines = [line.strip() for line in audit.splitlines() if line.strip()]
    haskell_command = "ghc -Wall -Werror -package ghc -fno-code Main.hs"
    assert [line for line in audit_lines if line.startswith("ghc ")] == [
        haskell_command
    ]
    haskell_audit_index = audit_lines.index(haskell_command)
    assert audit_lines[haskell_audit_index - 2 : haskell_audit_index + 2] == [
        "(",
        "cd candidate/src/llm_wiki_cli/extractors/haskell_scripts",
        haskell_command,
        ")",
    ]

    static = "\n".join(
        str(step) for step in workflow["jobs"]["static"]["steps"]
    )
    assert "qualification_tools.actionlint.version_output" in static
    assert (
        "-X github.com/rhysd/actionlint.version=${actionlint_version}"
        in static
    )
    assert "./cmd/actionlint" in static

    oci = "\n".join(str(step) for step in workflow["jobs"]["oci"]["steps"])
    assert "oci_images.python_base.reference" in oci
    assert "oci_images.registry.reference" in oci
    assert "docker pull python:3.13-alpine" not in oci
    assert "docker pull registry:2" not in oci
    assert "--platform linux/amd64" in oci


def test_toolchain_audits_require_complete_owner_suite_evidence() -> None:
    workflow = _yaml("release-qualification.yml")
    steps = workflow["jobs"]["toolchains"]["steps"]
    names = [step.get("name") for step in steps]
    suite_index = names.index("Run toolchain owner suites")
    verifier_index = names.index("Enforce complete toolchain owner evidence")
    audit_index = names.index("Audit exact helper dependency trees")
    assert suite_index < verifier_index < audit_index

    verifier = steps[verifier_index]
    assert verifier.get("continue-on-error") is None
    assert verifier.get("if") is None
    command = verifier["run"]
    assert "verify-junit" in command
    assert "--junit evidence/toolchains.xml" in command
    assert "--lane toolchains" in command
    assert "--allowlist candidate/release/skip-allowlist.json" in command
    assert "--minimum-collected 488" in command
    assert "--minimum-passed 488" in command
    assert "--output evidence/result-toolchains.json" in command
    assert "--discovery" not in command
    assert "DISCOVERY_MODE" not in str(verifier)

    audit = steps[audit_index]
    assert audit.get("if") is None
    assert audit.get("continue-on-error") is None


def test_release_runners_and_ci_runners_are_explicit() -> None:
    for name in (
        "ci.yml",
        "action-selftest.yml",
        "release-qualification.yml",
        "publish.yml",
    ):
        text = (WORKFLOWS / name).read_text(encoding="utf-8")
        assert "ubuntu-latest" not in text
        assert "windows-latest" not in text
        assert "macos-latest" not in text


def test_core_qualification_preserves_the_supported_cross_platform_contract() -> None:
    ci = _yaml("ci.yml")
    ci_matrix = ci["jobs"]["test"]["strategy"]["matrix"]["include"]
    assert ci_matrix == [
        {"os": "ubuntu-24.04", "python-version": "3.10"},
        {"os": "windows-2025", "python-version": "3.13"},
        {"os": "macos-15", "python-version": "3.14"},
    ]

    qualification = _yaml("release-qualification.yml")
    core = qualification["jobs"]["core"]
    assert core["strategy"]["matrix"]["include"] == [
        {"lane": "core-ubuntu-3.10", "os": "ubuntu-24.04", "python": "3.10"},
        {"lane": "core-windows-3.13", "os": "windows-2025", "python": "3.13"},
        {"lane": "core-macos-3.14", "os": "macos-15", "python": "3.14"},
    ]
    core_text = "\n".join(str(step) for step in core["steps"])
    assert 'python -m pip install --no-cache-dir "./candidate[dev]"' in core_text
    assert " -e " not in core_text
    assert "--strict-config" in core_text
    assert "--strict-markers" in core_text
    assert "-W error" in core_text
    assert "-o xfail_strict=true" in core_text
    assert "--junitxml=" in core_text
    assert "verify-junit" in core_text
    assert "--cov-fail-under=87" in core_text

    source_test_jobs = (
        "core",
        "slow",
        "security-behavior",
        "product",
        "mcp",
        "toolchains",
        "oci",
    )
    for job_name in source_test_jobs:
        pytest_steps = [
            step
            for step in qualification["jobs"][job_name]["steps"]
            if "python -m pytest" in str(step.get("run", ""))
        ]
        assert pytest_steps, job_name
        for step in pytest_steps:
            assert step["working-directory"] == "candidate", job_name
            run = step["run"]
            assert "candidate/tests" not in run, job_name
            assert "--junitxml" in run, job_name
            assert "../evidence/" in run, job_name

    core_suite = next(
        step
        for step in core["steps"]
        if step.get("name") == "Run strict core suite and coverage"
    )
    assert core_suite["env"]["LLM_WIKI_QUALIFICATION_SOURCE_ARCHIVE"] == (
        "${{ github.workspace }}/incoming/source/candidate-source.tar"
    )
    assert "--cov-report=\"xml:../evidence/" in core_suite["run"]
