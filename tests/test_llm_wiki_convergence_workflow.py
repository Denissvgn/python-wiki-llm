"""Static safety contracts for scheduled LLM Wiki convergence."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "llm-wiki-convergence.yml"
WRAPPER_PATH = ROOT / ".github" / "scripts" / "run-llm-wiki-convergence.sh"
REMOTE_ACTION = re.compile(r"^[^@]+@[0-9a-f]{40}$")
EXPECTED_EVIDENCE = [
    "${{ runner.temp }}/llm-wiki-convergence-evidence/wiki-status-before.txt",
    "${{ runner.temp }}/llm-wiki-convergence-evidence/wiki-status-after.txt",
    "${{ runner.temp }}/llm-wiki-convergence-evidence/worktree-status-after.txt",
    "${{ runner.temp }}/llm-wiki-convergence-evidence/wiki-diff.patch",
    "${{ runner.temp }}/llm-wiki-convergence-evidence/sync.log",
    "${{ runner.temp }}/llm-wiki-convergence-evidence/convergence-result.json",
]


def _workflow() -> dict:
    payload = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _embedded_plan_parser() -> str:
    job = _workflow()["jobs"]["convergence"]
    run = next(
        step["run"]
        for step in job["steps"]
        if step["name"] == "Plan the selected extractor helpers"
    )
    marker = "<<'PY'\n"
    start = run.index(marker) + len(marker)
    end = run.index("\nPY\n", start)
    return run[start:end]


def _convergence_wrapper_mode() -> int:
    source_archive = os.environ.get("LLM_WIKI_QUALIFICATION_SOURCE_ARCHIVE")
    if source_archive:
        member_name = WRAPPER_PATH.relative_to(ROOT).as_posix()
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
                WRAPPER_PATH.relative_to(ROOT).as_posix(),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        assert index_entry.split(maxsplit=1)[0] == "100755"
        return 0o755
    return WRAPPER_PATH.stat().st_mode


def test_convergence_is_a_read_only_scheduled_and_manual_workflow() -> None:
    workflow = _workflow()
    triggers = workflow.get("on", workflow.get(True))
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    assert triggers["schedule"] == [{"cron": "17 3 * * 1"}]
    assert triggers["workflow_dispatch"] is None
    assert workflow["permissions"] == {"contents": "read"}

    assert set(workflow["jobs"]) == {"convergence"}
    job = workflow["jobs"]["convergence"]
    assert job["permissions"] == {"contents": "read"}
    assert job["runs-on"] == "ubuntu-24.04"
    assert job["timeout-minutes"] == 45

    remote_actions = [
        step["uses"]
        for step in job["steps"]
        if isinstance(step.get("uses"), str) and not step["uses"].startswith("./")
    ]
    assert remote_actions
    assert all(REMOTE_ACTION.fullmatch(action) for action in remote_actions)

    checkout = next(
        step
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    )
    assert checkout["with"] == {
        "fetch-depth": 1,
        "persist-credentials": False,
        "ref": "${{ github.sha }}",
    }

    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "${{ secrets." not in source
    assert "contents: write" not in source
    assert "pull-requests: write" not in source
    assert "id-token: write" not in source
    assert "git push" not in source
    assert "git commit" not in source
    assert "ci-check" not in source
    assert "--dry-run" not in source
    assert "--force" not in source

    preflight = next(
        step
        for step in job["steps"]
        if step["name"] == "Reject and quarantine an occupied evidence root"
    )
    install = next(
        step
        for step in job["steps"]
        if step["name"] == "Install the checked-out package"
    )
    assert job["steps"].index(preflight) < job["steps"].index(install)
    assert "llm-wiki-convergence-evidence" in preflight["run"]
    assert "/bin/mv --" in preflight["run"]
    assert "exit 1" in preflight["run"]


def test_convergence_prepares_locked_helpers_then_runs_one_normal_sync() -> None:
    job = _workflow()["jobs"]["convergence"]
    names = [step["name"] for step in job["steps"]]
    assert names.index("Plan the selected extractor helpers") < names.index(
        "Prepare the selected extractor helpers"
    )
    assert names.index("Prepare the selected extractor helpers") < names.index(
        "Run one real LLM Wiki convergence sync"
    )

    setup_steps = [
        step for step in job["steps"] if step["name"].startswith("Install the locked ")
    ]
    assert {step["name"] for step in setup_steps} == {
        "Install the locked TypeScript extractor toolchain",
        "Install the locked Go extractor toolchain",
        "Install the locked Rust extractor toolchain",
        "Install the locked Haskell extractor toolchain",
    }
    assert all("release/toolchain-lock.json" in step["run"] for step in setup_steps)
    assert all(
        ".github/scripts/setup-llm-wiki-ci-toolchains.sh" in step["run"]
        for step in setup_steps
    )

    plan = next(
        step
        for step in job["steps"]
        if step["name"] == "Plan the selected extractor helpers"
    )["run"]
    for required in (
        "object_pairs_hook=lambda value: value",
        "parse_constant=lambda value: fail(",
        '["schema", "languages"]',
        "languages are unknown, duplicated, or unordered",
    ):
        assert required in plan

    run_step = next(
        step
        for step in job["steps"]
        if step["name"] == "Run one real LLM Wiki convergence sync"
    )
    tokens = shlex.split(run_step["run"])
    assert tokens[0] == ".github/scripts/run-llm-wiki-convergence.sh"
    assert tokens[tokens.index("--src-dir") + 1] == "."
    assert tokens[tokens.index("--wiki-dir") + 1] == "docs/llm_wiki"
    assert tokens[tokens.index("--jobs") + 1] == "1"
    assert tokens[tokens.index("--evidence-dir") + 1] == (
        "${RUNNER_TEMP}/llm-wiki-convergence-evidence"
    )
    assert tokens[tokens.index("--github-output") + 1] == "${GITHUB_OUTPUT}"
    assert "--dry-run" not in tokens
    assert "--force" not in tokens


def test_convergence_plan_parser_emits_only_fixed_boolean_outputs(
    tmp_path: Path,
) -> None:
    plan = tmp_path / "plan.json"
    output = tmp_path / "output"
    plan.write_text(
        json.dumps(
            {
                "schema": "llm-wiki-prepare-extractors-plan/v1",
                "languages": ["typescript", "rust"],
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, "-I", "-", str(plan), str(output)],
        input=_embedded_plan_parser(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_text(encoding="utf-8") == (
        "typescript=true\ngo=false\nrust=true\nhaskell=false\n"
    )


@pytest.mark.parametrize(
    "payload",
    (
        "",
        "[]",
        '{"languages":[],"schema":"llm-wiki-prepare-extractors-plan/v1"}',
        (
            '{"schema":"llm-wiki-prepare-extractors-plan/v1",'
            '"schema":"llm-wiki-prepare-extractors-plan/v1","languages":[]}'
        ),
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":["go","go"]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":["go","typescript"]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":["python"]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":[true]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":[NaN]}',
        "x" * 4097,
    ),
)
def test_convergence_plan_parser_rejects_ambiguous_or_noncanonical_json(
    tmp_path: Path,
    payload: str,
) -> None:
    plan = tmp_path / "plan.json"
    output = tmp_path / "output"
    plan.write_text(payload, encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "-I", "-", str(plan), str(output)],
        input=_embedded_plan_parser(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert not output.exists()


def test_convergence_plan_parser_rejects_a_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text(
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":[]}',
        encoding="utf-8",
    )
    plan = tmp_path / "plan.json"
    try:
        plan.symlink_to(target)
    except OSError:
        assert "plan_path.is_symlink()" in _embedded_plan_parser()
        return
    output = tmp_path / "output"

    completed = subprocess.run(
        [sys.executable, "-I", "-", str(plan), str(output)],
        input=_embedded_plan_parser(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert not output.exists()


def test_convergence_upload_is_always_a_pinned_fixed_allowlist() -> None:
    job = _workflow()["jobs"]["convergence"]
    upload = job["steps"][-1]

    assert upload["name"] == "Upload fixed convergence evidence"
    assert upload["if"] == (
        "always() && steps.convergence.outputs.evidence-ready == 'true'"
    )
    assert REMOTE_ACTION.fullmatch(upload["uses"])
    assert upload["uses"].startswith("actions/upload-artifact@")
    assert upload["with"]["path"].splitlines() == EXPECTED_EVIDENCE
    assert upload["with"]["if-no-files-found"] == "error"
    assert upload["with"]["retention-days"] == 14
    assert "*" not in upload["with"]["path"]
    assert "?" not in upload["with"]["path"]


def test_convergence_wrapper_mode_prefers_the_frozen_archive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "candidate-source.tar"
    member_name = WRAPPER_PATH.relative_to(ROOT).as_posix()

    def set_distinct_archive_mode(member: tarfile.TarInfo) -> tarfile.TarInfo:
        member.mode = 0o711
        return member

    with tarfile.open(archive_path, mode="w:") as archive:
        archive.add(
            WRAPPER_PATH,
            arcname=member_name,
            recursive=False,
            filter=set_distinct_archive_mode,
        )
    monkeypatch.setenv(
        "LLM_WIKI_QUALIFICATION_SOURCE_ARCHIVE",
        str(archive_path),
    )

    assert _convergence_wrapper_mode() == 0o711


def test_convergence_wrapper_uses_complete_status_not_diff_as_authority() -> None:
    source = WRAPPER_PATH.read_text(encoding="utf-8")

    assert _convergence_wrapper_mode() & 0o111
    assert 'readonly RESULT_SCHEMA="llm-wiki-convergence/v1"' in source
    assert "git -c core.quotePath=true status" in source
    assert source.count("--porcelain=v1") == 2
    assert source.count("--untracked-files=all") == 2
    assert source.count("--ignore-submodules=none") == 2
    assert "git -c core.quotePath=true diff" in source
    for flag in (
        "--no-ext-diff",
        "--no-textconv",
        "--binary",
        "--full-index",
        "--no-color",
    ):
        assert flag in source
    assert 'HEAD -- "${wiki_dir}"' in source
    assert "readonly SUMMARY_MAX_LINES=40" in source
    assert "readonly SUMMARY_MAX_BYTES=8192" in source
    assert "readonly STATUS_SUMMARY_LIMIT=20" in source

    command = re.search(
        r'(?ms)^  "\$\{python_executable\}" -I -m llm_wiki_cli\.cli sync \\\n'
        r'(?P<body>.*?) > "\$\{SYNC_LOG\}" 2>&1$',
        source,
    )
    assert command is not None
    body = command.group("body")
    assert "--no-plugins" in body
    assert "--dry-run" not in body
    assert "--force" not in body
    assert '--jobs "${jobs}"' in body

    for filename in (
        "wiki-status-before.txt",
        "wiki-status-after.txt",
        "worktree-status-after.txt",
        "wiki-diff.patch",
        "sync.log",
        "convergence-result.json",
    ):
        assert filename in source
    assert '"sha256": hashlib.sha256(raw).hexdigest()' in source
    assert '"records": len(raw.splitlines())' in source
    assert '"wiki_diff": {"exit_code": after_diff_exit}' in source
    assert "evidence-ready=true" in source
    assert 'exit "${final_exit}"' in source
