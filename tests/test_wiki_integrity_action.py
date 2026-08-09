from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
ACTION_PATH = ROOT / "integrations" / "wiki-integrity" / "action.yml"


def _action() -> dict:
    return yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))


def _named_step(action: dict, name: str) -> dict:
    return next(step for step in action["runs"]["steps"] if step.get("name") == name)


def _run_text(action: dict) -> str:
    return "\n".join(str(step.get("run", "")) for step in action["runs"]["steps"])


def _embedded_plan_parser(action: dict) -> str:
    run = _named_step(action, "Plan the automatically selected extractor helpers")[
        "run"
    ]
    marker = "<<'PY'\n"
    start = run.index(marker) + len(marker)
    end = run.index("\nPY\n", start)
    return run[start:end]


def test_full_integrity_action_has_bounded_portable_inputs() -> None:
    action = _action()

    assert action["runs"]["using"] == "composite"
    assert action["inputs"] == {
        "wiki-dir": {
            "description": (
                "Repository-relative path to the committed LLM Wiki directory."
            ),
            "required": False,
            "default": "docs/llm_wiki",
        },
        "src-dir": {
            "description": (
                "Repository-relative source root; its default source-selection "
                "profile is discovered automatically."
            ),
            "required": False,
            "default": ".",
        },
    }

    steps = action["runs"]["steps"]
    assert all(step.get("shell") == "bash" for step in steps if "run" in step)
    assert all("continue-on-error" not in step for step in steps)
    expected_environment = {
        "CI": "true",
        "PIP_NO_INPUT": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    for step in steps:
        if "run" not in step:
            continue
        assert expected_environment.items() <= step["env"].items()


def test_full_integrity_action_is_pinned_credential_free_and_read_only() -> None:
    action = _action()
    steps = action["runs"]["steps"]
    assert [step["uses"] for step in steps if "uses" in step] == [
        "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
        "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    ]

    source = ACTION_PATH.read_text(encoding="utf-8")
    for reviewed_line in (
        "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0",
        "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2",
    ):
        assert source.count(reviewed_line) == 1
    for use in re.findall(r"^\s*uses:\s*(\S+)", source, flags=re.MULTILINE):
        assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", use)

    checkout = _named_step(action, "Check out the candidate without credentials")
    assert checkout["with"] == {"persist-credentials": False}

    serialized = yaml.safe_dump(action).lower()
    for prohibited in (
        "${{ secrets.",
        "github.token",
        "github_token",
        "actions/cache@",
        "git add",
        "git commit",
        "git push",
        "gh pr",
        "llm-wiki bootstrap",
        "llm-wiki sync",
        "knowledge init",
        "hook install",
    ):
        assert prohibited not in serialized


def test_full_integrity_action_uses_its_own_locked_implementation() -> None:
    action = _action()
    setup_python = _named_step(action, "Set up Python 3.13")
    assert setup_python["id"] == "setup-python"
    assert setup_python["with"] == {"python-version": "3.13"}

    install = _named_step(action, "Install the action package")["run"]
    assert shlex.split(install) == [
        "${{ steps.setup-python.outputs.python-path }}",
        "-I",
        "-m",
        "pip",
        "install",
        "--no-cache-dir",
        "${GITHUB_ACTION_PATH}/../..",
    ]

    setup_contracts = (
        (
            "Install the locked TypeScript and JavaScript extractor toolchain",
            "typescript",
            "routine",
        ),
        ("Install the locked Go extractor toolchain", "go", "extractor-go"),
        ("Install the locked Rust extractor toolchain", "rust", "extractor-rust"),
        (
            "Install the locked Haskell extractor toolchain",
            "haskell",
            "extractor-haskell",
        ),
    )
    for name, output, mode in setup_contracts:
        step = _named_step(action, name)
        assert step["if"] == f"steps.extractor-plan.outputs.{output} == 'true'"
        assert shlex.split(step["run"]) == [
            (
                "${GITHUB_ACTION_PATH}/../../.github/scripts/"
                "setup-llm-wiki-ci-toolchains.sh"
            ),
            "--mode",
            mode,
            "--install-root",
            "${RUNNER_TEMP}/llm-wiki-toolchains",
            "--lock",
            "${GITHUB_ACTION_PATH}/../../release/toolchain-lock.json",
            "--python",
            "${{ steps.setup-python.outputs.python-path }}",
        ]

    versions_step = _named_step(
        action, "Record selected locked extractor toolchain versions"
    )
    assert (
        versions_step["env"]
        | {
            "PLAN_TYPESCRIPT": "${{ steps.extractor-plan.outputs.typescript }}",
            "PLAN_GO": "${{ steps.extractor-plan.outputs.go }}",
            "PLAN_RUST": "${{ steps.extractor-plan.outputs.rust }}",
            "PLAN_HASKELL": "${{ steps.extractor-plan.outputs.haskell }}",
        }
        == versions_step["env"]
    )
    versions = versions_step["run"]
    for required in (
        'qualification_helper="${GITHUB_ACTION_PATH}/../../release/qualification.py"',
        'toolchain_lock="${GITHUB_ACTION_PATH}/../../release/toolchain-lock.json"',
        'evidence_path="${LLM_WIKI_EVIDENCE_DIR}/locked-toolchain-versions.txt"',
        'case "${selected}" in',
        "true|false)",
        "record_exact_version()",
        "lock_value toolchains.node.version_output",
        "lock_value toolchains.npm.version_output",
        "lock_value toolchains.go.version_output",
        "lock_value toolchains.rust.version_output",
        "lock_value toolchains.haskell.version_output",
        '"$(node --version)"',
        '"$(npm --version)"',
        'actual_go_full="$("${LLM_WIKI_GO}" version)"',
        '"$(cargo --version)"',
        '"$("${LLM_WIKI_GHC}" --numeric-version)"',
        'test "${actual}" = "${expected}"',
        'tee -a "${evidence_path}"',
    ):
        assert required in versions


def test_full_integrity_action_plans_helpers_with_a_fail_closed_contract() -> None:
    action = _action()
    plan = _named_step(action, "Plan the automatically selected extractor helpers")
    assert plan["id"] == "extractor-plan"
    assert plan["env"]["INPUT_SRC_DIR"] == "${{ inputs.src-dir }}"
    for required in (
        'plan_path="${LLM_WIKI_EVIDENCE_DIR}/extractor-plan.json"',
        "-I -m llm_wiki_cli.cli prepare-extractors",
        '--src-dir "${INPUT_SRC_DIR}"',
        "--plan",
        "--format json",
        '"${plan_path}" "${GITHUB_OUTPUT}"',
        'expected_schema = "llm-wiki-prepare-extractors-plan/v1"',
        'supported = ("typescript", "go", "rust", "haskell")',
        "object_pairs_hook=lambda value: value",
        '["schema", "languages"]',
        "len(raw) > 4096",
        'selected = "true" if language in languages else "false"',
    ):
        assert required in plan["run"]


def test_full_integrity_action_isolates_python_modules_from_candidate_source() -> None:
    run_text = _run_text(_action())

    assert run_text.count("-I -m pip") == 1
    assert run_text.count("-m pip") == 1
    assert run_text.count("-I -m llm_wiki_cli.cli") == 2
    assert run_text.count("-m llm_wiki_cli.cli") == 2
    assert "python -m pip" not in run_text


@pytest.mark.parametrize(
    ("languages", "expected"),
    (
        ([], "typescript=false\ngo=false\nrust=false\nhaskell=false\n"),
        (
            ["typescript", "rust", "haskell"],
            "typescript=true\ngo=false\nrust=true\nhaskell=true\n",
        ),
        (
            ["typescript", "go", "rust", "haskell"],
            "typescript=true\ngo=true\nrust=true\nhaskell=true\n",
        ),
    ),
)
def test_embedded_plan_parser_emits_only_fixed_boolean_outputs(
    tmp_path: Path,
    languages: list[str],
    expected: str,
) -> None:
    plan_path = tmp_path / "plan.json"
    output_path = tmp_path / "outputs"
    plan_path.write_text(
        json.dumps(
            {
                "schema": "llm-wiki-prepare-extractors-plan/v1",
                "languages": languages,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-I", "-", str(plan_path), str(output_path)],
        input=_embedded_plan_parser(_action()),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output_path.read_text(encoding="utf-8") == expected


@pytest.mark.parametrize(
    "payload",
    (
        "[]",
        '{"languages":[],"schema":"llm-wiki-prepare-extractors-plan/v1"}',
        '{"schema":"wrong","languages":[]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":[],"extra":0}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":["go","typescript"]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":["go","go"]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":["python"]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":[true]}',
        (
            '{"schema":"llm-wiki-prepare-extractors-plan/v1",'
            '"schema":"llm-wiki-prepare-extractors-plan/v1","languages":[]}'
        ),
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":[NaN]}',
    ),
)
def test_embedded_plan_parser_rejects_malformed_or_ambiguous_contracts(
    tmp_path: Path,
    payload: str,
) -> None:
    plan_path = tmp_path / "plan.json"
    output_path = tmp_path / "outputs"
    plan_path.write_text(payload, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-I", "-", str(plan_path), str(output_path)],
        input=_embedded_plan_parser(_action()),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "invalid extractor-helper plan:" in result.stderr
    assert not output_path.exists()


def test_full_integrity_action_preserves_default_selection_and_gate_exit() -> None:
    action = _action()
    run_text = _run_text(action)
    assert "${{ inputs." not in run_text
    assert "--source-selection" not in run_text

    plan = _named_step(action, "Plan the automatically selected extractor helpers")
    assert plan["env"]["INPUT_SRC_DIR"] == "${{ inputs.src-dir }}"
    for required in (
        "-I -m llm_wiki_cli.cli prepare-extractors",
        '--src-dir "${INPUT_SRC_DIR}"',
        "--plan",
        "--format json",
    ):
        assert required in plan["run"]

    prepare = _named_step(
        action, "Prepare the automatically selected extractor helpers"
    )
    assert prepare["env"]["INPUT_SRC_DIR"] == "${{ inputs.src-dir }}"
    for required in (
        '"${{ steps.setup-python.outputs.python-path }}"',
        "-I -m llm_wiki_cli.cli prepare-extractors",
        '--src-dir "${INPUT_SRC_DIR}"',
        '--cache-dir "${LLM_WIKI_CACHE_DIR}"',
        'tee "${LLM_WIKI_EVIDENCE_DIR}/prepare-extractors.log"',
    ):
        assert required in prepare["run"]

    validation = _named_step(
        action,
        "Validate committed wiki (native drift diagnostics are advisory)",
    )
    assert validation["env"]["INPUT_SRC_DIR"] == "${{ inputs.src-dir }}"
    assert validation["env"]["INPUT_WIKI_DIR"] == "${{ inputs.wiki-dir }}"
    assert shlex.split(validation["run"]) == [
        "${GITHUB_ACTION_PATH}/../../.github/scripts/run-llm-wiki-ci-check.sh",
        "--python",
        "${{ steps.setup-python.outputs.python-path }}",
        "--src-dir",
        "${INPUT_SRC_DIR}",
        "--wiki-dir",
        "${INPUT_WIKI_DIR}",
        "--helper-cache-dir",
        "${LLM_WIKI_CACHE_DIR}",
        "--report-dir",
        "${LLM_WIKI_EVIDENCE_DIR}",
        "--jobs",
        "1",
        "--knowledge-drift-report",
    ]
    assert "|| true" not in validation["run"]
    assert "set +e" not in validation["run"]

    step_names = [step["name"] for step in action["runs"]["steps"]]
    plan_index = step_names.index("Plan the automatically selected extractor helpers")
    prepare_index = step_names.index(
        "Prepare the automatically selected extractor helpers"
    )
    validation_index = step_names.index(
        "Validate committed wiki (native drift diagnostics are advisory)"
    )
    assert plan_index < prepare_index < validation_index
    for setup_name in (
        "Install the locked TypeScript and JavaScript extractor toolchain",
        "Install the locked Go extractor toolchain",
        "Install the locked Rust extractor toolchain",
        "Install the locked Haskell extractor toolchain",
        "Record selected locked extractor toolchain versions",
    ):
        assert plan_index < step_names.index(setup_name) < prepare_index


def test_full_integrity_action_reserves_and_always_uploads_bounded_evidence() -> None:
    action = _action()
    path_binding = _named_step(action, "Bind runner-temporary wiki paths")["run"]
    for required in (
        'cache_dir="${RUNNER_TEMP}/llm-wiki-cache"',
        'evidence_dir="${RUNNER_TEMP}/llm-wiki-evidence"',
        'for reserved_dir in "${cache_dir}" "${evidence_dir}"',
        '[[ -e "${reserved_dir}" || -L "${reserved_dir}" ]]',
        '/usr/bin/mktemp -d "${RUNNER_TEMP}/llm-wiki-collisions.XXXXXX"',
        '"${reserved_dir}" "${quarantine_dir}/${leaf}"',
        '/bin/rm -rf -- "${reserved_dir}"',
        '[[ ! -e "${reserved_dir}" && ! -L "${reserved_dir}" ]]',
        'mkdir -- "${reserved_dir}"',
        '[[ -d "${reserved_dir}" && ! -L "${reserved_dir}" ]]',
        "LLM_WIKI_CACHE_DIR=%s\\n",
        "LLM_WIKI_EVIDENCE_DIR=%s\\n",
        '} >> "${GITHUB_ENV}"',
    ):
        assert required in path_binding

    steps = action["runs"]["steps"]
    upload = _named_step(action, "Upload bounded wiki integrity evidence")
    assert upload == steps[-1]
    assert upload["if"] == "always()"
    artifact_name = upload["with"]["name"]
    assert artifact_name == (
        "llm-wiki-ci-${{ github.job }}-${{ strategy.job-index || 0 }}-${{ github.sha }}"
    )

    def resolved_artifact_name(*, job: str, matrix_index: int | None) -> str:
        return (
            artifact_name.replace("${{ github.job }}", job)
            .replace(
                "${{ strategy.job-index || 0 }}",
                str(0 if matrix_index is None else matrix_index),
            )
            .replace("${{ github.sha }}", "a" * 40)
        )

    assert resolved_artifact_name(job="integrity", matrix_index=None) == (
        f"llm-wiki-ci-integrity-0-{'a' * 40}"
    )
    matrix_names = {
        resolved_artifact_name(job="integrity", matrix_index=index)
        for index in range(3)
    }
    assert len(matrix_names) == 3
    assert resolved_artifact_name(job="secondary", matrix_index=None) not in (
        matrix_names
    )
    assert upload["with"]["retention-days"] == 14
    assert upload["with"]["if-no-files-found"] == "warn"
    assert set(upload["with"]["path"].splitlines()) == {
        "${{ runner.temp }}/llm-wiki-evidence/llm-wiki-ci-report.md",
        "${{ runner.temp }}/llm-wiki-evidence/llm-wiki-ci-report.json",
        "${{ runner.temp }}/llm-wiki-evidence/llm-wiki-ci-report.invalid.txt",
        "${{ runner.temp }}/llm-wiki-evidence/extractor-plan.json",
        "${{ runner.temp }}/llm-wiki-evidence/prepare-extractors.log",
        "${{ runner.temp }}/llm-wiki-evidence/locked-toolchain-versions.txt",
    }
