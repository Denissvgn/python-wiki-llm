"""Static release-workflow safety contracts."""

from __future__ import annotations

import ast
import json
import os
import re
import shlex
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath

import yaml

from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests import release_artifact_smoke


ROOT = Path(__file__).parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
WIKI_CI_WRAPPER = ROOT / ".github" / "scripts" / "run-llm-wiki-ci-check.sh"
REMOTE_ACTION = re.compile(r"^[^@]+@[0-9a-f]{40}$")


def _test_definitions(relative_path: str) -> set[tuple[str | None, str]]:
    tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
    definitions: set[tuple[str | None, str]] = set()
    function_types = (ast.FunctionDef, ast.AsyncFunctionDef)
    for node in tree.body:
        if isinstance(node, function_types) and node.name.startswith("test_"):
            definitions.add((None, node.name))
        elif isinstance(node, ast.ClassDef):
            definitions.update(
                (node.name, member.name)
                for member in node.body
                if isinstance(member, function_types)
                and member.name.startswith("test_")
            )
    return definitions


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


def test_routine_ci_checks_the_full_release_typing_surface() -> None:
    job = _yaml("ci.yml")["jobs"]["typecheck"]
    assert job["runs-on"] == "ubuntu-24.04"
    assert not job.get("continue-on-error")
    install = next(step for step in job["steps"] if step.get("name") == "Install release typing dependencies")
    assert '".[dev,mcp,tokens]"' in install["run"]
    assert "--require-hashes -r release/requirements.txt" in install["run"]
    assert "examples/fastapi-contracts/requirements-ci.txt" in install["run"]
    check = next(step for step in job["steps"] if step.get("name") == "Check the complete project type surface")
    assert check["shell"] == "bash"  # GitHub's bash invocation enables pipefail.
    assert check["run"].split() == [
        '"${{', 'steps.python.outputs.python-path', '}}"', '-m', 'pyright',
        '--pythonpath', '"${{', 'steps.python.outputs.python-path', '}}"',
        '|', 'tee', 'pyright.log',
    ]
    assert not check.get("continue-on-error")


def test_selected_sources_and_committed_wiki_use_lf_checkout_semantics() -> None:
    attribute_lines = [
        line.split()
        for line in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert attribute_lines[0] == ["*", "text=auto", "eol=lf"]

    conflicts: list[tuple[str, str]] = []
    for pattern, *assignments in attribute_lines[1:]:
        for assignment in assignments:
            attribute = assignment.lstrip("-!").split("=", 1)[0]
            compatible = (
                attribute == "text"
                and assignment in {"text", "text=auto"}
            ) or (attribute == "eol" and assignment == "eol=lf")
            if attribute in {"text", "eol", "binary", "crlf"} and not compatible:
                conflicts.append((pattern, assignment))
    assert conflicts == []

    manifest = SyncManifest.load(ROOT / "docs" / "llm_wiki")
    selected_sources = set(manifest.sources)
    selection = manifest.generation_inputs["source_selection_inputs"]
    assert isinstance(selection, dict) and isinstance(selection["inputs"], list)
    selection_inputs = set()
    for item in selection["inputs"]:
        assert isinstance(item, dict) and isinstance(item["path"], str)
        selection_inputs.add(item["path"])
    wiki_files = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "docs" / "llm_wiki").rglob("*")
        if path.is_file()
    }
    censuses = {
        "manifest selected sources": selected_sources,
        "source-selection inputs": selection_inputs,
        "committed wiki files": wiki_files,
    }
    assert all(censuses.values())

    invalid_paths: list[tuple[str, str]] = []
    missing_paths: list[tuple[str, str]] = []
    unmatched_paths: list[tuple[str, str]] = []
    for census, paths in censuses.items():
        for relative_path in sorted(paths):
            path = PurePosixPath(relative_path)
            if (
                path.is_absolute()
                or "\\" in relative_path
                or any(part in {"", ".", ".."} for part in path.parts)
            ):
                invalid_paths.append((census, relative_path))
                continue
            if not path.match(attribute_lines[0][0]):
                unmatched_paths.append((census, relative_path))
            if not ROOT.joinpath(*path.parts).is_file():
                missing_paths.append((census, relative_path))

    assert invalid_paths == []
    assert unmatched_paths == []
    assert missing_paths == []


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
    assert "Reject an invalid evidence ID" in text
    assert "Reject an invalid failure threshold" in text
    assert text.count('test "${STEP_OUTCOME}" = "failure"') == 3
    triggers = workflow.get("on", workflow.get(True))
    assert triggers is not None
    assert triggers["push"]["branches"] == ["main"]
    assert triggers["push"]["paths"] == triggers["pull_request"]["paths"]
    assert workflow["concurrency"]["cancel-in-progress"] == (
        "${{ github.event_name == 'pull_request' }}"
    )


def test_ci_pins_the_package_build_tool() -> None:
    workflow = _yaml("ci.yml")
    package_build = next(
        step
        for step in workflow["jobs"]["test"]["steps"]
        if step.get("name") == "Check package builds"
    )
    assert package_build["if"] == "${{ matrix.package }}"
    assert 'python -m pip install "build==1.5.0"' in package_build["run"]
    assert "--no-cache-dir" not in package_build["run"]


def test_windows_provider_acceptance_uses_installed_artifacts_and_preserves_evidence():
    job = _yaml("ci.yml")["jobs"]["test"]
    check = _named_step(job, "Verify installed provider artifacts on native Windows")
    assert check["id"] == "provider-artifacts"
    assert check["if"] == "${{ matrix.lane == 'core-windows-3.13' }}"
    assert "tests/run_provider_artifact_checks.py" in check["run"]
    assert '"pyright==1.1.411"' in check["run"]
    upload = _named_step(job, "Upload native Windows provider evidence")
    assert " ".join(upload["if"].split()) == (
        "${{ always() && matrix.lane == 'core-windows-3.13' && "
        "(steps.provider-artifacts.outcome == 'success' || "
        "steps.provider-artifacts.outcome == 'failure') }}"
    )
    assert upload["with"]["if-no-files-found"] == "error"


def test_foreign_action_matrix_keeps_provider_separate_and_checks_negative_evidence():
    job = _yaml("action-selftest.yml")["jobs"]["foreign-caller"]
    assert job["strategy"]["matrix"] == {
        "integration": ["context", "integrity"],
        "state": ["clean", "drift", "corrupt"],
    }
    checkout = _named_step(job, "Check out provider separately from caller sources")
    assert checkout["with"]["path"] == ".provider"
    assert checkout["with"]["persist-credentials"] is False
    assert "head.sha" in checkout["with"]["ref"]
    for name in (
        "Run context health against caller",
        "Run full integrity against caller",
    ):
        step = _named_step(job, name)
        assert step["uses"].startswith("./.provider/integrations/")
        assert step["with"]["src-dir"] == "source"
        assert step["with"]["wiki-dir"] == "wiki"
    check = _named_step(job, "Verify actual action outcome and unchanged caller")
    assert check["if"] == "always()"
    assert "--action-evidence" in check["run"]
    assert "--outcome" in check["run"]


def test_language_oracle_controls_have_a_mandatory_locked_owner():
    workflow = _yaml("release-qualification.yml")
    owners = [
        step
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if step.get("name") == "Verify independent provider parser controls"
    ]
    assert len(owners) == 1
    assert "tests.provider_conformance.owner_controls" in owners[0]["run"]
    assert "continue-on-error" not in owners[0]
    assert "if" not in owners[0]


def _wiki_integrity_job() -> tuple[dict, dict]:
    workflow = _yaml("ci.yml")
    return workflow, workflow["jobs"]["wiki-integrity"]


def _named_step(job: dict, name: str) -> dict:
    return next(step for step in job["steps"] if step.get("name") == name)


def _wiki_integrity_source() -> str:
    source = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^  wiki-integrity:\n(?P<body>.*?)(?=^  [a-z0-9-]+:\n|\Z)",
        source,
    )
    assert match is not None
    return match.group(0)


def test_wiki_integrity_has_stable_identity_capacity_and_independence() -> None:
    workflow, job = _wiki_integrity_job()
    assert job["name"] == "LLM Wiki integrity"
    assert job["runs-on"] == "ubuntu-24.04"
    assert job["timeout-minutes"] == 15
    assert "needs" not in job
    assert "strategy" not in job
    assert "if" not in job
    assert "environment" not in job
    assert "continue-on-error" not in job
    assert all("continue-on-error" not in step for step in job["steps"])
    assert (
        sum(
            candidate.get("name") == "LLM Wiki integrity"
            for candidate in workflow["jobs"].values()
        )
        == 1
    )

    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict)
    assert set(triggers) == {"push", "pull_request"}
    for event in triggers.values():
        assert event["branches"] == ["main"]
        assert "paths" not in event
        assert "paths-ignore" not in event


def test_wiki_integrity_is_secretless_read_only_and_credential_free() -> None:
    _workflow, job = _wiki_integrity_job()
    assert job["permissions"] == {"contents": "read"}
    assert job["env"] == {
        "CI": "true",
        "PIP_NO_INPUT": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    }

    checkout = _named_step(job, "Check out the candidate without credentials")
    assert checkout["with"] == {"persist-credentials": False}

    serialized = yaml.safe_dump(job).lower()
    for prohibited in (
        "${{ secrets.",
        "github.token",
        "github_token",
        "pull-requests:",
        "id-token:",
        "actions/cache@",
        "git add",
        "git commit",
        "git push",
        "gh pr",
    ):
        assert prohibited not in serialized


def test_wiki_integrity_uses_only_the_exact_reviewed_actions() -> None:
    _workflow, job = _wiki_integrity_job()
    assert [step["uses"] for step in job["steps"] if "uses" in step] == [
        "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
        "./integrations/wiki-integrity",
    ]

    source = _wiki_integrity_source()
    assert source.count(
        "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0"
    ) == 1


def test_wiki_integrity_delegates_to_the_candidate_composite_contract() -> None:
    _workflow, job = _wiki_integrity_job()
    gate = _named_step(job, "Check LLM Wiki integrity")
    assert gate == {
        "name": "Check LLM Wiki integrity",
        "uses": "./integrations/wiki-integrity",
        "with": {"src-dir": ".", "wiki-dir": "docs/llm_wiki"},
    }
    assert [step.get("name") for step in job["steps"]] == [
        "Check out the candidate without credentials",
        "Check LLM Wiki integrity",
    ]


def test_isolated_wiki_integrity_python_rejects_candidate_module_shadows(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    marker = tmp_path / "candidate-shadow-executed"
    hostile_source = (
        "import os\n"
        "from pathlib import Path\n"
        'Path(os.environ["SHADOW_MARKER"]).write_text("executed\\n")\n'
        'raise RuntimeError("candidate module shadow executed")\n'
    )
    (candidate / "pip.py").write_text(hostile_source, encoding="utf-8")
    (candidate / "sitecustomize.py").write_text(hostile_source, encoding="utf-8")
    candidate_cli = candidate / "llm_wiki_cli"
    candidate_cli.mkdir()
    (candidate_cli / "__init__.py").write_text(hostile_source, encoding="utf-8")
    (candidate_cli / "cli.py").write_text(hostile_source, encoding="utf-8")

    environment = os.environ.copy()
    environment["SHADOW_MARKER"] = str(marker)
    commands = (
        [sys.executable, "-I", "-m", "pip", "--version"],
        [sys.executable, "-I", "-m", "llm_wiki_cli.cli", "--help"],
    )
    for command in commands:
        result = subprocess.run(
            command,
            cwd=candidate,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert not marker.exists()


def _wiki_ci_wrapper_mode() -> int:
    source_archive = os.environ.get("LLM_WIKI_QUALIFICATION_SOURCE_ARCHIVE")
    if source_archive:
        member_name = WIKI_CI_WRAPPER.relative_to(ROOT).as_posix()
        with tarfile.open(source_archive, mode="r:") as archive:
            member = archive.getmember(member_name)
        assert member.isfile()
        return member.mode
    if os.name == "nt":
        index_entry = subprocess.run(
            [
                "git",
                "ls-files",
                "--stage",
                "--",
                WIKI_CI_WRAPPER.relative_to(ROOT).as_posix(),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        assert index_entry.split(maxsplit=1)[0] == "100755"
        return 0o755
    return WIKI_CI_WRAPPER.stat().st_mode


def test_wiki_integrity_wrapper_mode_prefers_the_frozen_archive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "candidate-source.tar"
    member_name = WIKI_CI_WRAPPER.relative_to(ROOT).as_posix()

    def set_distinct_archive_mode(member: tarfile.TarInfo) -> tarfile.TarInfo:
        member.mode = 0o711
        return member

    with tarfile.open(archive_path, mode="w:") as archive:
        archive.add(
            WIKI_CI_WRAPPER,
            arcname=member_name,
            recursive=False,
            filter=set_distinct_archive_mode,
        )
    monkeypatch.setenv(
        "LLM_WIKI_QUALIFICATION_SOURCE_ARCHIVE",
        str(archive_path),
    )

    assert _wiki_ci_wrapper_mode() == 0o711


def test_wiki_integrity_wrapper_executes_the_direct_candidate_gate() -> None:
    assert _wiki_ci_wrapper_mode() & 0o111
    wrapper = WIKI_CI_WRAPPER.read_text(encoding="utf-8")
    assert (
        wrapper.count('"${python_executable}" -I -m llm_wiki_cli.cli ci-check')
        == 1
    )
    for required in (
        '--src-dir "${src_dir}"',
        '--wiki-dir "${wiki_dir}"',
        '--helper-cache-dir "${helper_cache_dir}"',
        '--jobs "${jobs}"',
        "--knowledge-drift-report",
        "--no-plugins",
        "--format json",
        '--report "${MARKDOWN_REPORT}"',
    ):
        assert required in wrapper
    assert "--source-selection" not in wrapper
    assert "--include-tests" not in wrapper


def test_wiki_integrity_wrapper_preserves_exit_evidence_and_cleanliness() -> None:
    wrapper = WIKI_CI_WRAPPER.read_text(encoding="utf-8")
    for required in (
        "cli_exit=$?",
        "ci_completed=true",
        "final_exit=${cli_exit}",
        "if [[ ${cli_exit} -eq 0 ]]; then",
        'exit "${final_exit}"',
        "local returned_exit=\"${command_exit}\"",
        "if ${ci_completed} && [[ ${cli_exit} -ne 0 ]]; then",
        'returned_exit="${cli_exit}"',
        (
            '"${python_executable}" -I -m '
            "llm_wiki_cli.services.ci_report validate"
        ),
        '--report "${raw_output}"',
        '--cli-exit "${cli_exit}"',
        'JSON_REPORT="${report_dir}/llm-wiki-ci-report.json"',
        'INVALID_REPORT="${report_dir}/llm-wiki-ci-report.invalid.txt"',
        "git status --porcelain=v1 --untracked-files=all",
        'sed -n "1,${STATUS_RECORD_LIMIT}p" "${sorted_status}"',
    ):
        assert required in wrapper
    assert "json.loads(" not in wrapper
    assert "git diff --exit-code" not in wrapper


def test_wiki_integrity_wrapper_summary_is_bounded_and_labels_drift_advisory() -> None:
    wrapper = WIKI_CI_WRAPPER.read_text(encoding="utf-8")
    for required in (
        "readonly SUMMARY_MAX_LINES=40",
        "readonly SUMMARY_MAX_BYTES=8192",
        "readonly STATUS_RECORD_LIMIT=20",
        "GITHUB_STEP_SUMMARY",
        "llm_wiki_cli.services.ci_report render-summary",
        '--status-limit "${STATUS_RECORD_LIMIT}"',
        '--max-lines "${SUMMARY_MAX_LINES}"',
        '--max-bytes "${SUMMARY_MAX_BYTES}"',
        "if ${json_valid}; then",
        'summary_args+=(--report "${JSON_REPORT}")',
        "Native drift diagnostics are advisory",
        "integrity validation remains blocking",
    ):
        assert required in wrapper
    assert "summary_program=" not in wrapper


def test_readme_links_the_public_wiki_automation_contract() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/automation.md#install-the-full-integrity-gate" in readme
    automation = " ".join(
        (ROOT / "docs/automation.md").read_text(encoding="utf-8").split()
    )
    for required in (
        ".llm-wiki/source-selection.json",
        "llm-wiki install-ci --action-ref",
        "strict `ci-check` gate",
        "read-only permissions",
        "project worktree stayed clean",
        "up to 50 warning/notice annotations",
        "Reporting failures do not replace the integrity result",
        "Installation does not bootstrap or synchronize the wiki",
    ):
        assert required in automation


def test_publish_is_dry_run_by_default_and_publisher_cannot_build() -> None:
    workflow = _yaml("publish.yml")
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict)
    dispatch = triggers["workflow_dispatch"]
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
    bundle_verifiers = [
        step
        for step in verify_steps
        if "verify-bundle" in str(step.get("run", ""))
    ]
    assert len(bundle_verifiers) == 1
    verifier = bundle_verifiers[0]
    assert verifier["id"] == "verify"
    assert 'if [[ "${PUBLISH_REQUESTED}" == "true" ]]' in verifier["run"]
    assert 'tag_requirement=(--require-tag)' in verifier["run"]
    assert '"${tag_requirement[@]}"' in verifier["run"]

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
    assert "tests/artifact_fixture_clock.py" in freeze_text
    assert "tests/mcp_probe.py" in freeze_text
    assert "tests/fixtures/packet-artifact-parity.py" in freeze_text
    assert "tests/fixtures/native-artifact-consumer.py" in freeze_text
    assert "tests/verify_installed_provider.py" in freeze_text
    assert "tests/fixtures/provider-typing-valid.py" in freeze_text
    assert "tests/fixtures/provider-typing-invalid.txt" in freeze_text
    assert "tests/fixtures/provider-artifact-consumer.py" in freeze_text
    assert "examples/native-knowledge" in freeze_text
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
    assert harness_consumers == 20

    for job_name in ("core", "ubuntu-suites", "security-behavior", "mcp"):
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
    producer = _named_step(smoke, "Run without a source checkout")
    assert producer["id"] == "artifact-smoke"
    diagnostics = _named_step(smoke, "Upload MCP probe diagnostics")
    assert "always()" in diagnostics["if"]
    assert "steps.artifact-smoke.outcome == 'failure'" in diagnostics["if"]
    assert "steps.artifact-smoke.outcome == 'success'" in diagnostics["if"]
    assert diagnostics["with"]["path"] == "smoke-${{ matrix.kind }}-mcp-probes/"
    assert diagnostics["with"]["if-no-files-found"] == "warn"
    canonical = _named_step(smoke, "Upload canonical smoke result")
    assert canonical["with"]["if-no-files-found"] == "error"


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
    attestations = [step for step in workflow["jobs"]["bundle"]["steps"]
                    if step.get("uses", "").startswith("actions/attest@")]
    assert len(attestations) == 2
    assert all(step["with"]["subject-path"] == "qualified-release/dist/*" for step in attestations)
    assert "sbom-path" not in attestations[0]["with"]
    assert attestations[1]["with"]["sbom-path"] == "qualified-release/sbom.spdx.json"
    assert attestations[1]["env"]["NODE_OPTIONS"] == "--max-http-header-size=32768"
    assert all(not any(key.startswith("predicate") for key in step["with"]) for step in attestations)
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


def test_rd10_qualifies_both_composite_actions_from_the_frozen_candidate() -> None:
    workflow = _yaml("release-qualification.yml")
    job = workflow["jobs"]["action"]
    assert job["name"] == "RD-10 hosted composite Action"
    assert job["needs"] == "freeze"
    assert job["timeout-minutes"] == 60
    assert "env" not in job

    bind_paths = _named_step(job, "Bind RD-10 runner-temporary paths")["run"]
    assert '"${RUNNER_TEMP}/rd-10-evidence"' in bind_paths
    assert '"${RUNNER_TEMP}/full-integrity-plugin-executed"' in bind_paths
    assert '} >> "${GITHUB_ENV}"' in bind_paths

    context = _named_step(job, "Run context health gate")
    assert context["uses"] == "./candidate/integrations/github-action"
    assert context["with"] == {
        "wiki-dir": "candidate/.action-selftest/wiki",
        "src-dir": "candidate/tests/fixtures/context-health-action/source",
        "evidence-id": "valid",
        "strict": "true",
        "fail-on": "unhealthy",
    }
    invalid_ids = {
        "Reject invalid strict": "invalid-strict",
        "Reject invalid fail-on": "invalid-fail-on",
    }
    for name, evidence_id in invalid_ids.items():
        invalid = _named_step(job, name)
        assert invalid["uses"] == "./candidate/integrations/github-action"
        assert invalid["continue-on-error"] is True
        assert invalid["with"]["evidence-id"] == evidence_id
    invalid_assertion = _named_step(
        job, "Assert both invalid inputs failed closed"
    )["run"]
    assert 'test "${STRICT_OUTCOME}" = failure' in invalid_assertion
    assert 'test "${FAIL_ON_OUTCOME}" = failure' in invalid_assertion
    assert '"${RD10_EVIDENCE_DIR}/action-result.json"' in invalid_assertion

    fixture = _named_step(
        job, "Create a clean frozen-source full-integrity fixture"
    )["run"]
    for required in (
        "candidate/.llm-wiki/plugins/hostile-rd10-plugin",
        "candidate/.llm-wiki/plugins.lock.json",
        'Path(os.environ["TARGET_PLUGIN_EXECUTION_MARKER"])',
        'mv -- incoming "${RUNNER_TEMP}/rd-10-frozen-inputs"',
        "git init --quiet",
        "git add --all -- candidate",
        'git commit --quiet -m "Create frozen-source RD-10 fixture"',
        'test -z "$(git status --porcelain=v1 --untracked-files=all)"',
    ):
        assert required in fixture

    full_integrity = _named_step(
        job, "Run full integrity gate from the frozen candidate"
    )
    assert full_integrity == {
        "name": "Run full integrity gate from the frozen candidate",
        "uses": "./candidate/integrations/wiki-integrity",
        "env": {
            "TARGET_PLUGIN_EXECUTION_MARKER": (
                "${{ runner.temp }}/full-integrity-plugin-executed"
            )
        },
        "with": {
            "src-dir": "candidate",
            "wiki-dir": "candidate/docs/llm_wiki",
        },
    }

    validation = _named_step(job, "Validate fixed full-integrity evidence")[
        "run"
    ]
    for required in (
        'test ! -e "${FULL_INTEGRITY_PLUGIN_MARKER}"',
        'test -z "$(git status --porcelain=v1 --untracked-files=all)"',
        '"${RD10_EVIDENCE_DIR}/full-integrity-action-result.json"',
        '"extractor-plan.json"',
        '"helper-cache-metrics.json"',
        '"llm-wiki-ci-report.json"',
        '"llm-wiki-ci-report.md"',
        '"locked-toolchain-versions.txt"',
        '"prepare-extractors.log"',
        '"schema": "llm-wiki-prepare-extractors-plan/v1"',
        '"languages": ["typescript"]',
        '"schema": "llm-wiki-helper-cache-metrics/v1"',
        '"cache_key_schema": "llm-wiki-helpers-v1"',
        '"cache_attempted": True',
        "0 < len(cache_metrics_raw) <= 1024",
        "object_pairs_hook=strict_object",
        "parse_constant=reject_nonfinite",
        "duplicate object key",
        "set(cache_metrics) != expected_cache_metric_keys",
        "unexpected helper-cache metric keys",
        'type(cache_metrics.get("cache_hit")) is not bool',
        'prepare_elapsed_ms > 3_600_000',
        '"knowledge_drift_gate": False',
        '"knowledge_drift_report": True',
        '"ok": True',
        '"typescript selected": "true"',
        '"go selected": "false"',
        '"rust selected": "false"',
        '"haskell selected": "false"',
        '"plugin_disabled": "PASS"',
        '"worktree": "clean"',
    ):
        assert required in validation
    validator = validation.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    compile(validator, "release-qualification-rd10-validator", "exec")

    upload = _named_step(job, "Upload gate evidence")
    assert upload["if"] == "always()"
    assert upload["with"] == {
        "archive": True,
        "name": "evidence-rd-10",
        "path": "${{ runner.temp }}/rd-10-evidence/",
        "if-no-files-found": "error",
        "retention-days": 14,
    }
    assert "action" in workflow["jobs"]["bundle"]["needs"]
    assert "action" in workflow["jobs"]["decision"]["needs"]
    bundle = _named_step(
        job=workflow["jobs"]["bundle"], name="Build versioned release bundle"
    )
    assert '--evidence "RD-10:action=incoming/gates/evidence-rd-10"' in bundle[
        "run"
    ]


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


def test_static_qualification_installs_analyzed_extras_and_uses_blocking_runner():
    steps = _yaml("release-qualification.yml")["jobs"]["static"]["steps"]
    install = _named_step({"steps": steps}, "Install source and hash-locked release tools")
    assert '"./candidate[dev,mcp,tokens]"' in install["run"]
    tutorial_install = next(
        line for line in install["run"].splitlines()
        if "candidate/examples/fastapi-contracts/" in line
    )
    assert "--require-hashes" in tutorial_install
    assert "-r candidate/examples/fastapi-contracts/requirements-ci.txt" in tutorial_install
    check = _named_step({"steps": steps}, "Run static checks")
    assert "python -I release/static_checks.py --evidence ../evidence/security" in check["run"]
    assert not check.get("continue-on-error", False)
    assert "|| true" not in check["run"]
    assert _named_step({"steps": steps}, "Upload gate evidence")["if"] == "always()"
    config = json.loads((ROOT / "pyrightconfig.json").read_text())
    assert "venv" not in config and "venvPath" not in config
    assert config["reportUnsupportedDunderAll"] == "error"
    assert "examples" in config["include"]


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
    assert "--minimum-collected 489" in command
    assert "--minimum-passed 489" in command
    assert "--output evidence/result-toolchains.json" in command
    assert "--discovery" not in command
    assert "DISCOVERY_MODE" not in str(verifier)

    audit = steps[audit_index]
    assert audit.get("if") is None
    assert audit.get("continue-on-error") is None


def test_javascript_migration_skips_have_executable_toolchain_ownership() -> None:
    workflow = _yaml("release-qualification.yml")
    selector = (
        "tests/test_verified_bug_migrations.py::"
        "test_javascript_health_refresh_and_first_sync_converge"
    )
    entries = json.loads(
        (ROOT / "release" / "skip-allowlist.json").read_text(encoding="utf-8")
    )["entries"]
    actual = {
        (entry["lane"], entry["node_id"], entry["owner_lane"], entry["reason"])
        for entry in entries
        if entry["node_id"].startswith(selector)
    }
    lanes = {
        lane["lane"]
        for lane in workflow["jobs"]["core"]["strategy"]["matrix"]["include"]
    } | {"core-windows-3.13"}
    assert actual == {
        (
            lane,
            f"{selector}[{legacy}]",
            "toolchains",
            "requires an already prepared TypeScript helper",
        )
        for lane in lanes
        for legacy in (False, True)
    }
    suites = _named_step(workflow["jobs"]["toolchains"], "Run toolchain owner suites")
    assert selector in shlex.split(suites["run"])
    assert suites["env"]["LLM_WIKI_CACHE_DIR"] == "${{ runner.temp }}/extractor-cache"


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
        {
            "lane": "core-ubuntu-3.10",
            "os": "ubuntu-24.04",
            "python-version": "3.10",
            "coverage": True,
            "package": True,
        },
        {
            "lane": "core-windows-3.13",
            "os": "windows-2025",
            "python-version": "3.13",
            "coverage": False,
            "package": False,
        },
        {
            "lane": "core-macos-3.14",
            "os": "macos-15",
            "python-version": "3.14",
            "coverage": False,
            "package": False,
        },
    ]

    qualification = _yaml("release-qualification.yml")
    core = qualification["jobs"]["core"]
    assert core["strategy"]["matrix"]["include"] == [
        {
            "lane": "core-ubuntu-3.10",
            "os": "ubuntu-24.04",
            "python": "3.10",
            "coverage": True,
        },
        {
            "lane": "core-macos-3.14",
            "os": "macos-15",
            "python": "3.14",
            "coverage": False,
        },
    ]
    core_text = "\n".join(str(step) for step in core["steps"])
    assert 'python -m pip install --no-cache-dir "./candidate[dev,tokens]"' in core_text
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
        "core-windows",
        "security-behavior",
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
        if step.get("name") == "Run strict core suite with canonical coverage"
    )
    assert core_suite["env"]["LLM_WIKI_QUALIFICATION_SOURCE_ARCHIVE"] == (
        "${{ github.workspace }}/incoming/source/candidate-source.tar"
    )
    assert "--cov-report=\"xml:../evidence/" in core_suite["run"]
    assert core_suite["if"] == "${{ matrix.coverage && !inputs.discovery-mode }}"
    uninstrumented = _named_step(
        core, "Run strict core suite without coverage instrumentation"
    )
    assert uninstrumented["if"] == (
        "${{ !matrix.coverage || inputs.discovery-mode }}"
    )
    assert "--cov" not in uninstrumented["run"]


def test_routine_ci_reuses_only_instrumentation_and_expensive_packaging() -> None:
    workflow = _yaml("ci.yml")
    assert workflow["concurrency"] == {
        "group": (
            "${{ github.workflow }}-${{ "
            "github.event.pull_request.number || github.ref }}"
        ),
        "cancel-in-progress": "${{ github.event_name == 'pull_request' }}",
    }
    job = workflow["jobs"]["test"]
    assert job["name"] == (
        "test (${{ matrix.os }}, ${{ matrix.python-version }})"
    )
    setup = next(
        step
        for step in job["steps"]
        if str(step.get("uses", "")).startswith("actions/setup-python@")
    )
    assert setup["with"]["cache"] == "pip"
    assert setup["with"]["cache-dependency-path"] == "pyproject.toml"
    install = _named_step(job, "Install dependencies")
    assert 'pip install -e ".[dev,tokens]"' in install["run"]
    assert "--no-cache-dir" not in install["run"]

    coverage = _named_step(job, "Run strict suite with coverage")
    plain = _named_step(job, "Run strict suite")
    assert coverage["if"] == "${{ matrix.coverage }}"
    assert plain["if"] == "${{ !matrix.coverage }}"
    for step in (coverage, plain):
        command = step["run"]
        for flag in (
            "--strict-config",
            "--strict-markers",
            "-W error",
            "-o xfail_strict=true",
            "--junitxml=",
        ):
            assert flag in command
    assert "--cov-fail-under=87" in coverage["run"]
    assert "--cov" not in plain["run"]

    verifier = _named_step(job, "Enforce exact skips and minimum inventory")
    for required in (
        "verify-junit",
        '--lane "${{ matrix.lane }}"',
        "--minimum-collected 5322",
        "--minimum-passed 5070",
    ):
        assert required in verifier["run"]
    package = _named_step(job, "Check package builds")
    assert package["if"] == "${{ matrix.package }}"
    assert "verify_installed_knowledge_schema.py" in package["run"]
    diagnostics = _named_step(job, "Upload failed lane diagnostics")
    assert diagnostics["if"] == "failure()"

    for job_name in ("test", "mcp-sdk", "p0-oci-integration"):
        cached_job = workflow["jobs"][job_name]
        cached_setup = next(
            step
            for step in cached_job["steps"]
            if str(step.get("uses", "")).startswith("actions/setup-python@")
        )
        assert cached_setup["with"]["cache"] == "pip"
        assert cached_setup["with"]["cache-dependency-path"] == (
            "pyproject.toml"
        )
        assert "--no-cache-dir" not in "\n".join(
            str(step.get("run", "")) for step in cached_job["steps"]
        )

    mcp = workflow["jobs"]["mcp-sdk"]
    assert mcp["strategy"]["matrix"]["include"] == [
        {"lane": "mcp-3.10", "python-version": "3.10"},
        {"lane": "mcp-3.13", "python-version": "3.13"},
    ]
    mcp_command = _named_step(
        mcp, "Run MCP SDK registration contract"
    )["run"]
    assert "tests/test_mcp_sdk.py" in mcp_command
    assert "tests/test_mcp.py" not in mcp_command
    mcp_verifier = _named_step(
        mcp, "Enforce MCP SDK registration and canonical delivery"
    )["run"]
    assert "--minimum-collected 2" in mcp_verifier
    assert "--minimum-passed 2" in mcp_verifier


def test_bandit_parity_is_opt_in_and_uses_current_static_evidence() -> None:
    workflow = _yaml("release-qualification.yml")
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict)
    option = triggers["workflow_dispatch"]["inputs"]["bandit-parity-verification"]
    assert option["type"] == "boolean" and option["default"] is False
    job = workflow["jobs"]["static"]
    names = [step.get("name") for step in job["steps"]]
    name = "Verify Bandit decision parity on owned controls and candidate source"
    assert names.index("Run static checks") < names.index(name) < names.index("Upload gate evidence")
    check = _named_step(job, name)
    assert check["if"] == "${{ inputs.bandit-parity-verification }}"
    assert check["working-directory"] == "candidate"
    assert "--project-evidence ../evidence/security" in check["run"]
    assert "--output ../evidence/bandit-parity" in check["run"] and "--pipeline" in check["run"]
    assert "continue-on-error" not in check
    assert _named_step(job, "Upload gate evidence")["if"] == "always()"
    for job_name, candidate_job in workflow["jobs"].items():
        if job_name not in {"freeze", "static", "decision"}:
            assert "!inputs.bandit-parity-verification" in candidate_job["if"], job_name
    assert workflow["jobs"]["static"]["if"] == "${{ !inputs.discovery-mode }}"
    assert "always()" in workflow["jobs"]["decision"]["if"]
    binding = _named_step(workflow["jobs"]["freeze"], "Bind the workflow definition to the candidate")
    assert "mutually exclusive" in binding["run"]


def test_release_discovery_runs_only_core_and_reconciles_complete_evidence() -> None:
    workflow = _yaml("release-qualification.yml")
    assert workflow["concurrency"] == {
        "group": (
            "${{ github.workflow }}-${{ inputs.candidate-sha }}-"
            "${{ inputs.discovery-mode }}-${{ inputs.bandit-parity-verification }}-${{ inputs.ubuntu-suite-shadow }}-${{ inputs.windows-core-shards }}"
        ),
        "cancel-in-progress": True,
    }
    jobs = workflow["jobs"]
    for job_name in (
        "ubuntu-suites",
        "security-behavior",
        "mcp",
        "toolchains",
        "oci",
        "static",
        "action",
        "build",
        "reproducible",
        "artifact-smoke",
        "smoke-parity",
    ):
        expected = "${{ !inputs.discovery-mode }}" if job_name == "static" else "${{ !inputs.discovery-mode && !inputs.bandit-parity-verification }}"
        if job_name == "ubuntu-suites":
            expected = "${{ !inputs.discovery-mode && !inputs.bandit-parity-verification && !inputs.ubuntu-suite-shadow }}"
        assert jobs[job_name]["if"] == expected
    assert "!inputs.discovery-mode" in jobs["owner-lanes"]["if"]
    assert jobs["decision"]["if"] == (
        "${{ always() && !inputs.discovery-mode && !inputs.ubuntu-suite-shadow }}"
    )
    for mode in ["discovery-mode", "bandit-parity-verification", "ubuntu-suite-shadow"]:
        assert f"!inputs.{mode}" in jobs["bundle"]["if"]

    discovery = jobs["discovery-allowlist"]
    assert "inputs.discovery-mode" in discovery["if"]
    assert "needs.core.result == 'failure'" in discovery["if"]
    evidence_download = next(
        step
        for step in discovery["steps"]
        if step.get("with", {}).get("pattern") == "evidence-core-*"
    )
    assert evidence_download["continue-on-error"] is True
    reconcile = _named_step(
        discovery, "Reconcile observed tuples with reviewed ownership"
    )["run"]
    assert "--baseline candidate/release/skip-allowlist.json" in reconcile
    assert reconcile.count("--expected-lane") == 3
    assert "--diagnostic skip-discovery-diagnostic.json" in reconcile
    upload = _named_step(
        discovery, "Upload non-qualifying skip diagnostics for owner review"
    )
    assert "skip-discovery-diagnostic.json" in upload["with"]["path"]
    assert "discovered-skip-allowlist.json" in upload["with"]["path"]


def test_windows_core_projects_candidate_bound_rd04_and_rd05_evidence() -> None:
    workflow = _yaml("release-qualification.yml")
    jobs = workflow["jobs"]
    assert jobs["security-behavior"]["strategy"]["matrix"]["os"] == ["macos-15"]
    assert "product" not in jobs

    core = jobs["core-windows"]
    security_projection = _named_step(
        core, "Project Windows core evidence for RD-04"
    )
    product_projection = _named_step(
        core, "Project Windows core evidence for RD-05"
    )
    expected_selectors = {
        "security-windows-2025": {
            "tests/test_lockfile.py",
            "tests/test_circuit_breaker.py",
            "tests/test_redaction.py",
            "tests/test_metrics.py",
            "tests/test_config.py",
            "tests/test_io.py",
            "tests/test_protected_artifacts.py",
            "tests/test_documentation_adversarial.py",
            "tests/test_documentation_control_integrity.py",
            "tests/test_documentation_input_recheck.py",
            "tests/test_documentation_native_lifecycle.py",
            "tests/test_resource_diagnostics.py",
            "tests/test_api_exception_taxonomy.py",
        },
        "product-windows-2025": {
            "tests/test_knowledge_*.py",
            "tests/test_documentation_*.py",
            "tests/test_doctor.py",
            "tests/test_context_packet.py",
            "tests/test_eval_lite.py",
            "tests/test_github_action.py",
            "tests/test_site_*.py",
            "tests/test_obsidian.py",
        },
    }
    for target, step in (
        ("security-windows-2025", security_projection),
        ("product-windows-2025", product_projection),
    ):
        command = step["run"]
        assert step["if"] == "${{ !inputs.discovery-mode }}"
        assert "project-junit" in command
        assert "--identity incoming/source/identity.json" in command
        assert "--source-junit evidence/core-windows-3.13.xml" in command
        assert "--source-lane core-windows-3.13" in command
        assert f"--target-lane {target}" in command
        assert "--projected-junit" in command
        assert "--receipt" in command
        tokens = shlex.split(command)
        selectors = {
            tokens[index + 1]
            for index, token in enumerate(tokens)
            if token == "--selector"
        }
        assert selectors == expected_selectors[target]

    for gate in ("04", "05"):
        upload = _named_step(
            core, f"Upload projected Windows RD-{gate} evidence"
        )
        assert upload["with"]["name"] == (
            f"evidence-rd-{gate}-windows-2025"
        )
        assert "-projection.json" in upload["with"]["path"]

    core_upload = _named_step(core, "Upload lane evidence")
    assert "evidence/core-windows-3.13.xml" in core_upload["with"]["path"]
    assert "evidence/result-core-windows-3.13.json" in core_upload["with"]["path"]
    assert "-projection.json" not in core_upload["with"]["path"]

    owner_command = _named_step(
        jobs["owner-lanes"],
        "Verify reviewed owners against hosted lane results",
    )["run"]
    assert (
        '--owner-result "security-windows-2025=${{ needs.core-windows.result }}"'
        in owner_command
    )
    assert (
        '--owner-result "product-windows-2025=${{ needs.core-windows.result }}"'
        in owner_command
    )
    bundle_command = _named_step(
        jobs["bundle"], "Build versioned release bundle"
    )["run"]
    assert (
        '--evidence "RD-04:windows=incoming/gates/'
        'evidence-rd-04-windows-2025"' in bundle_command
    )
    assert (
        '--evidence "RD-05:windows=incoming/gates/'
        'evidence-rd-05-windows-2025"' in bundle_command
    )


def test_release_mcp_and_build_jobs_avoid_identical_revalidation() -> None:
    workflow = _yaml("release-qualification.yml")
    mcp = workflow["jobs"]["mcp"]
    mcp_command = _named_step(mcp, "Run MCP contract")["run"]
    assert "tests/test_mcp_sdk.py" in mcp_command
    assert "tests/test_mcp.py" not in mcp_command
    mcp_verifier = _named_step(
        mcp, "Enforce the dedicated MCP SDK contract"
    )["run"]
    assert "--minimum-collected 2" in mcp_verifier
    assert "--minimum-passed 2" in mcp_verifier

    build = workflow["jobs"]["build"]
    assert build["strategy"]["matrix"]["include"] == [
        {"copy": "a", "validate": True},
        {"copy": "b", "validate": False},
    ]
    build_command = _named_step(
        build, "Build both independent distributions"
    )["run"]
    assert "python -m build" in build_command
    assert "twine check" not in build_command
    validation = _named_step(build, "Validate the first independent build")
    assert validation["if"] == "${{ matrix.validate }}"
    assert "twine check" in validation["run"]
    assert "verify_installed_knowledge_schema.py" in validation["run"]


def test_committed_skip_contract_nodes_resolve_to_test_definitions() -> None:
    payload = json.loads(
        (ROOT / "release" / "skip-allowlist.json").read_text(encoding="utf-8")
    )
    definitions_by_path: dict[str, set[tuple[str | None, str]]] = {}
    unresolved: list[str] = []
    for entry in payload["entries"]:
        node_id = entry["node_id"]
        components = node_id.split("::")
        assert len(components) in {2, 3}, node_id
        relative_path = components[0]
        definitions = definitions_by_path.get(relative_path)
        if definitions is None:
            definitions = _test_definitions(relative_path)
            definitions_by_path[relative_path] = definitions
        owner = components[1] if len(components) == 3 else None
        test_name = components[-1].split("[", 1)[0]
        if (owner, test_name) not in definitions:
            unresolved.append(node_id)

    assert unresolved == []


def test_packed_range_link_skips_match_their_parameterized_contract() -> None:
    from tests.test_knowledge_packs import test_ranges_never_follow_untrusted_links

    test = test_ranges_never_follow_untrusted_links
    marks = {mark.name: mark for mark in test.pytestmark}
    parameters = marks["parametrize"]
    assert parameters.args[0] == "link"
    selector = f"tests/test_knowledge_packs.py::{test.__name__}"
    entries = json.loads(
        (ROOT / "release" / "skip-allowlist.json").read_text(encoding="utf-8")
    )["entries"]
    actual = [entry for entry in entries if entry["node_id"].startswith(selector)]
    assert actual == [
        {
            "lane": "core-windows-3.13",
            "node_id": f"{selector}[{link}]",
            "owner_lane": "core-ubuntu-3.10",
            "reason": marks["skipif"].kwargs["reason"],
        }
        for link in sorted(parameters.args[1])
    ]
    for workflow, job in (("ci.yml", "test"), ("release-qualification.yml", "core")):
        lanes = _yaml(workflow)["jobs"][job]["strategy"]["matrix"]["include"]
        assert any(lane["lane"] == "core-ubuntu-3.10" for lane in lanes)


def test_committed_skip_contract_covers_platform_and_optional_owners_exactly() -> None:
    payload = json.loads(
        (ROOT / "release" / "skip-allowlist.json").read_text(encoding="utf-8")
    )
    entries = payload["entries"]
    assert entries == sorted(
        entries,
        key=lambda item: (
            item["lane"],
            item["node_id"],
            item["reason"],
            item["owner_lane"],
        ),
    )

    windows_native = [
        entry
        for entry in entries
        if entry["node_id"].startswith(
            "tests/test_filesystem_guard_windows.py::"
        )
    ]
    assert len(windows_native) == 22
    assert {entry["lane"] for entry in windows_native} == {
        "core-ubuntu-3.10",
        "core-macos-3.14",
    }
    assert {entry["owner_lane"] for entry in windows_native} == {
        "core-windows-3.13"
    }
    assert {entry["reason"] for entry in windows_native} == {
        "native Windows contracts"
    }

    posix = [
        entry
        for entry in entries
        if entry["node_id"].startswith("tests/test_filesystem_guard.py::")
    ]
    assert len(posix) == 8
    assert {entry["lane"] for entry in posix} == {"core-windows-3.13"}
    assert {entry["owner_lane"] for entry in posix} == {
        "core-ubuntu-3.10"
    }
    assert any("[absent]" in entry["node_id"] for entry in posix)
    assert any("[present]" in entry["node_id"] for entry in posix)

    dogfood = [
        entry
        for entry in entries
        if entry["node_id"].startswith(
            "tests/test_documentation_dogfood.py::"
        )
    ]
    assert len(dogfood) == 6
    assert {entry["reason"] for entry in dogfood} == {
        "prepared multi-language helper cache is required for documentation dogfood"
    }
    assert all("bootstrap_sync_and_site_export" not in entry["node_id"] for entry in entries)
    assert sum(
        entry["node_id"]
        == "tests/test_mcp_sdk.py::test_optional_sdk_registration_when_installed"
        for entry in entries
    ) == 3

    haskell = [
        entry
        for entry in entries
        if entry["node_id"].startswith("tests/test_haskell_extract.py::")
    ]
    assert len(haskell) == 18
    assert {entry["lane"] for entry in haskell} == {
        "core-macos-3.14",
        "core-ubuntu-3.10",
        "core-windows-3.13",
    }
    assert {entry["owner_lane"] for entry in haskell} == {"toolchains"}
    assert {entry["reason"] for entry in haskell} == {
        "Prepared Haskell helper not available — "
        "Haskell extractor integration tests skipped"
    }

    multilanguage = [
        entry
        for entry in entries
        if entry["node_id"]
        == (
            "tests/test_multilanguage_wiki.py::"
            "test_migrate_reconciles_legacy_go_page_with_rust_name_collision"
        )
    ]
    assert not multilanguage

    case_aliases = [
        entry
        for entry in entries
        if entry["node_id"].startswith(
            "tests/test_uninstall.py::TestUninstallRemovesHooks::"
            "test_remove_wiki_rejects_case_aliases_of_protected_roots["
        )
    ]
    assert {
        (entry["lane"], entry["node_id"], entry["owner_lane"], entry["reason"])
        for entry in case_aliases
    } == {
        (
            "core-ubuntu-3.10",
            "tests/test_uninstall.py::TestUninstallRemovesHooks::"
            "test_remove_wiki_rejects_case_aliases_of_protected_roots["
            ".claude/skills-.CLAUDE/SKILLS]",
            "core-windows-3.13",
            "filesystem is case-sensitive; no case alias exists",
        ),
        (
            "core-ubuntu-3.10",
            "tests/test_uninstall.py::TestUninstallRemovesHooks::"
            "test_remove_wiki_rejects_case_aliases_of_protected_roots[.git-.GIT]",
            "core-windows-3.13",
            "filesystem is case-sensitive; no case alias exists",
        ),
        (
            "core-ubuntu-3.10",
            "tests/test_uninstall.py::TestUninstallRemovesHooks::"
            "test_remove_wiki_rejects_case_aliases_of_protected_roots["
            ".llm-wiki/skills-.LLM-WIKI/SKILLS]",
            "core-windows-3.13",
            "filesystem is case-sensitive; no case alias exists",
        ),
    }

    platform_alias = [
        entry
        for entry in entries
        if entry["node_id"]
        == (
            "tests/test_wiki_reference_skill.py::TestReferenceSkillProvisioning::"
            "test_root_owned_platform_alias_preserves_install_and_export"
        )
    ]
    assert {
        (entry["lane"], entry["owner_lane"], entry["reason"])
        for entry in platform_alias
    } == {
        (
            "core-ubuntu-3.10",
            "core-macos-3.14",
            "root-owned /var alias contract is macOS-only",
        ),
        (
            "core-windows-3.13",
            "core-macos-3.14",
            "root-owned /var alias contract is macOS-only",
        ),
    }

    windows_posix = [
        entry
        for entry in entries
        if entry["node_id"]
        in {
            "tests/test_provisioning_failures.py::"
            "test_fifo_schema_is_rejected_by_stat_without_opening",
            "tests/test_provisioning_failures.py::"
            "test_init_revalidates_schema_after_reference_provision[fifo]",
            "tests/test_status.py::TestStatusHooks::"
            "test_exact_managed_hook_without_execute_bit_still_needs_cleanup",
        }
    ]
    assert {
        (entry["lane"], entry["node_id"], entry["owner_lane"], entry["reason"])
        for entry in windows_posix
    } == {
        (
            "core-windows-3.13",
            "tests/test_provisioning_failures.py::"
            "test_fifo_schema_is_rejected_by_stat_without_opening",
            "core-ubuntu-3.10",
            "FIFOs are unavailable on this platform",
        ),
        (
            "core-windows-3.13",
            "tests/test_provisioning_failures.py::"
            "test_init_revalidates_schema_after_reference_provision[fifo]",
            "core-ubuntu-3.10",
            "FIFOs are unavailable on this platform",
        ),
        (
            "core-windows-3.13",
            "tests/test_status.py::TestStatusHooks::"
            "test_exact_managed_hook_without_execute_bit_still_needs_cleanup",
            "core-ubuntu-3.10",
            "Windows does not expose a POSIX hook execute-bit contract",
        ),
    }


def test_windows_pr_ci_covers_the_noneditable_venv_probe_topology() -> None:
    job = _yaml("ci.yml")["jobs"]["test"]
    probe = _named_step(job, "Verify stdin harness inside a native Windows venv")
    assert probe["if"] == "${{ matrix.lane == 'core-windows-3.13' }}"
    assert "python -m venv" in probe["run"]
    assert 'stdio-venv/Scripts/python.exe" -m pip install ".[dev]"' in probe["run"]
    assert "tests/test_readonly_subprocess_stdin.py" in probe["run"]
    assert "--strict-config" in probe["run"] and "--strict-markers" in probe["run"]
    assert "-W error -o xfail_strict=true" in probe["run"]
    assert "GITHUB_PATH" not in probe["run"]
    assert "continue-on-error" not in probe
    upload = _named_step(job, "Upload native Windows venv probe evidence")
    assert "always()" in upload["if"]
    assert "stdio-venv.log" in upload["with"]["path"] and "stdio-venv.xml" in upload["with"]["path"]


def test_qualification_binds_hosted_artifacts_at_build_and_promotion() -> None:
    workflow = _yaml("release-qualification.yml")
    freeze = _named_step(workflow["jobs"]["freeze"], "Freeze and digest tracked qualification harnesses")["run"]
    assert "release/hosted_evidence.py" in freeze
    bundle = workflow["jobs"]["bundle"]
    assert bundle["permissions"]["actions"] == "read"
    for name in ["Build versioned release bundle", "Self-verify the completed bundle"]:
        step = _named_step(bundle, name)
        assert step["env"]["GITHUB_TOKEN"] == "${{ github.token }}"
    command = _named_step(bundle, "Build versioned release bundle")["run"]
    assert "--workflow-run-attempt" in command and "--harness-sha256" in command
    assert "--suite-layout" in command
    promotion = _yaml("publish.yml")["jobs"]["verify"]
    verifier = next(step for step in promotion["steps"] if step.get("id") == "verify")
    assert verifier["env"]["GITHUB_TOKEN"] == "${{ github.token }}"


def test_normal_union_producer_artifacts_and_consumers_are_integrated() -> None:
    from release import hosted_evidence, optimization_evidence, ubuntu_suites

    workflow = _yaml("release-qualification.yml")
    jobs = workflow["jobs"]
    expanded = [
        optimization_evidence.resolve(job, row)
        for job in jobs.values()
        for row in optimization_evidence.matrix_rows(job)
    ]
    # Names here are an external REST contract, including matrix expansion.
    for artifact, producer, _required in hosted_evidence.artifact_contract(
        "union"
    ).values():
        matches = [job for job in expanded if job["name"] == producer]
        assert len(matches) == 1, producer
        uploads = [
            step
            for step in matches[0]["steps"]
            if step.get("uses", "").startswith("actions/upload-artifact@")
            and step["with"]["name"] == artifact
        ]
        assert len(uploads) == 1, artifact
        assert uploads[0]["with"]["if-no-files-found"] == "error"
    assert hosted_evidence.REQUIRED_JOBS <= {job["name"] for job in expanded}

    union = jobs["ubuntu-suites"]
    run = _named_step(union, "Run the qualifying Ubuntu union once")["run"]
    assert "--mode union --purpose qualification" in run
    assert "--root candidate" in run
    assert "--harness-sha256" in run
    assert (
        len(
            [
                step
                for step in union["steps"]
                if "ubuntu_suites.py run" in step.get("run", "")
            ]
        )
        == 1
    )
    assert (
        "always()"
        in _named_step(union, "Upload complete Ubuntu execution and lineage")["if"]
    )
    for artifact in [
        "evidence-rd-03",
        "evidence-rd-04-ubuntu-24.04",
        "evidence-rd-05-ubuntu-24.04",
    ]:
        upload = _named_step(union, f"Upload {artifact} logical gate view")
        assert "steps.suites.outcome == 'success'" in upload["if"]
        assert "projection.json" in upload["with"]["path"]

    owners = _named_step(
        jobs["owner-lanes"], "Verify reviewed owners against hosted lane results"
    )["run"]
    assert "--ubuntu-purpose qualification" in owners
    for lane in ubuntu_suites.LANES:
        assert (
            f'--owner-junit "{lane}=incoming/owner-evidence/evidence-ubuntu-suites/{lane}.xml"'
            in owners
        )
        assert (
            f'--owner-result "{lane}=${{{{ needs.ubuntu-suites.result }}}}"' in owners
        )
    builder = _named_step(jobs["bundle"], "Build versioned release bundle")["run"]
    assert '--evidence "RD-03:union=incoming/gates/evidence-ubuntu-suites"' in builder
    assert "--suite-layout union" in builder

    for name in ["owner-lanes", "bundle", "decision"]:
        assert {"ubuntu-suites", "core", "security-behavior"} <= set(
            jobs[name]["needs"]
        )
    for name in ["bundle", "decision"]:
        commands = "\n".join(step.get("run", "") for step in jobs[name]["steps"])
        assert '--gate "RD-04=${{ needs.security-behavior.result }}"' in commands
        assert '--gate-dependency "RD-04=${{ needs.core.result }}"' in commands
        assert '--gate-dependency "RD-04=${{ needs.ubuntu-suites.result }}"' in commands
    serialized = json.dumps(workflow)
    for removed in ["slow", "product", "shadow-security-macos"]:
        assert removed not in jobs
        assert f"needs.{removed}." not in serialized
        assert not any(removed in job.get("needs", []) for job in jobs.values())


def test_bundle_overrides_skipped_ancestors_but_requires_every_producer() -> None:
    jobs = _yaml("release-qualification.yml")["jobs"]
    bundle = jobs["bundle"]
    assert "ubuntu-shadow" in jobs["owner-lanes"]["needs"]
    assert "ubuntu-shadow" not in bundle["needs"]
    # A status function is essential: GitHub otherwise injects success() and
    # propagates the intentionally skipped shadow ancestor to this normal job.
    condition = bundle["if"].removeprefix("${{").removesuffix("}}")
    clauses = [term.strip() for term in condition.split("&&")]
    expected = {
        "!cancelled()",
        "!inputs.discovery-mode",
        "!inputs.bandit-parity-verification",
        "!inputs.ubuntu-suite-shadow",
        *(f"needs.{name}.result == 'success'" for name in bundle["needs"]),
    }
    assert set(clauses) == expected and len(clauses) == len(expected)
    assert "continue-on-error" not in bundle


def test_final_decision_requires_bundle_success_without_qualifying_diagnostics() -> (
    None
):
    jobs = _yaml("release-qualification.yml")["jobs"]
    job = jobs["decision"]
    assert "bundle" in job["needs"]
    step = _named_step(job, "Require complete pre-promotion qualification")
    assert step["if"] == (
        "${{ always() && !inputs.bandit-parity-verification && needs.freeze.result == 'success' }}"
    )
    assert "verify-qualification-completion" in step["run"]
    assert '--bundle-result "${{ needs.bundle.result }}"' in step["run"]
    assert '--candidate-sha "${{ needs.freeze.outputs.sha }}"' in step["run"]
    assert '--candidate-version "${{ needs.freeze.outputs.version }}"' in step["run"]
    assert "--decision decision.json" in step["run"]
    assert "continue-on-error" not in step
    names = [s.get("name") for s in job["steps"]]
    assert names.index("Emit deterministic aggregate") < names.index(step["name"])
    assert names.index(step["name"]) < names.index("Upload pre-promotion decision")
    assert "always()" in _named_step(job, "Upload pre-promotion decision")["if"]
