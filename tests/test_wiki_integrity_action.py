from __future__ import annotations

import re
import shlex
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ACTION_PATH = ROOT / "integrations" / "wiki-integrity" / "action.yml"


def _action() -> dict:
    return yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))


def _named_step(action: dict, name: str) -> dict:
    return next(step for step in action["runs"]["steps"] if step.get("name") == name)


def _run_text(action: dict) -> str:
    return "\n".join(str(step.get("run", "")) for step in action["runs"]["steps"])


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
    assert "python -m pip install --no-cache-dir" in install
    assert '"${GITHUB_ACTION_PATH}/../.."' in install

    setup = _named_step(action, "Install the locked routine toolchain")["run"]
    assert shlex.split(setup) == [
        "${GITHUB_ACTION_PATH}/../../.github/scripts/setup-llm-wiki-ci-toolchains.sh",
        "--mode",
        "routine",
        "--install-root",
        "${RUNNER_TEMP}/llm-wiki-toolchains",
        "--lock",
        "${GITHUB_ACTION_PATH}/../../release/toolchain-lock.json",
        "--python",
        "${{ steps.setup-python.outputs.python-path }}",
    ]

    versions = _named_step(action, "Record locked routine toolchain versions")["run"]
    for required in (
        'qualification_helper="${GITHUB_ACTION_PATH}/../../release/qualification.py"',
        'toolchain_lock="${GITHUB_ACTION_PATH}/../../release/toolchain-lock.json"',
        "--key toolchains.node.version_output",
        "--key toolchains.npm.version_output",
        'actual_node="$(node --version)"',
        'actual_npm="$(npm --version)"',
        'tee "${LLM_WIKI_EVIDENCE_DIR}/locked-toolchain-versions.txt"',
        'test "${actual_node}" = "${expected_node}"',
        'test "${actual_npm}" = "${expected_npm}"',
    ):
        assert required in versions


def test_full_integrity_action_preserves_default_selection_and_gate_exit() -> None:
    action = _action()
    run_text = _run_text(action)
    assert "${{ inputs." not in run_text
    assert "--source-selection" not in run_text

    prepare = _named_step(
        action, "Prepare the automatically selected extractor helpers"
    )
    assert prepare["env"]["INPUT_SRC_DIR"] == "${{ inputs.src-dir }}"
    for required in (
        '"${{ steps.setup-python.outputs.python-path }}"',
        "-m llm_wiki_cli.cli prepare-extractors",
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
    assert step_names.index(
        "Prepare the automatically selected extractor helpers"
    ) < step_names.index(
        "Validate committed wiki (native drift diagnostics are advisory)"
    )


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
    assert upload["with"]["name"] == "llm-wiki-ci-${{ github.sha }}"
    assert upload["with"]["retention-days"] == 14
    assert upload["with"]["if-no-files-found"] == "warn"
    assert set(upload["with"]["path"].splitlines()) == {
        "${{ runner.temp }}/llm-wiki-evidence/llm-wiki-ci-report.md",
        "${{ runner.temp }}/llm-wiki-evidence/llm-wiki-ci-report.json",
        "${{ runner.temp }}/llm-wiki-evidence/llm-wiki-ci-report.invalid.txt",
        "${{ runner.temp }}/llm-wiki-evidence/prepare-extractors.log",
        "${{ runner.temp }}/llm-wiki-evidence/locked-toolchain-versions.txt",
    }
