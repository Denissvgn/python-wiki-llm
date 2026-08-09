"""Behavioral contracts for the dedicated wiki-integrity wrapper."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import pytest


ROOT = Path(__file__).parents[1]
WRAPPER = ROOT / ".github" / "scripts" / "run-llm-wiki-ci-check.sh"
PYTHON = Path(sys.executable).resolve()

pytestmark = pytest.mark.skipif(
    os.name == "nt",
    reason="The dedicated wrapper and its behavioral harness require POSIX Bash",
)


class WrapperCase(TypedDict):
    repo: Path
    report_dir: Path
    summary: Path
    invocations: Path
    stdout_file: Path
    fake: Path
    env: dict[str, str]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _fake_python(path: Path) -> Path:
    path.write_text(
        """#!/usr/bin/env bash
set -uo pipefail
printf '%s\\n' "$*" >> "${FAKE_INVOCATIONS}"
if [[ "$*" == *"llm-wiki-ci-python-v1"* ]]; then
  printf '%s' 'llm-wiki-ci-python-v1'
  exit 0
fi
if [[ "$*" == *"MAX_LINES = int"* && "${FAKE_SUMMARY_FAIL:-0}" == "1" ]]; then
  exit 88
fi
if [[ "${1:-}" == "-m" ]]; then
  if [[ "${FAKE_DELETE_RAW:-0}" == "1" ]]; then
    find "${FAKE_REPORT_DIR}" -name '.llm-wiki-ci-report.raw.*' -delete
  elif [[ -n "${FAKE_STDOUT_FILE:-}" ]]; then
    /bin/cat -- "${FAKE_STDOUT_FILE}"
  fi
  if [[ -n "${FAKE_RAW_REPLACEMENT_KIND:-}" ]]; then
    raw_path="$(find "${FAKE_REPORT_DIR}" -name '.llm-wiki-ci-report.raw.*' -print -quit)"
    rm -f -- "${raw_path}"
    case "${FAKE_RAW_REPLACEMENT_KIND}" in
      directory) mkdir -p -- "${raw_path}" ;;
      symlink)
        printf '%s\\n' '{"forged": true}' > "${FAKE_REPORT_DIR}/.raw-target"
        ln -s -- "${FAKE_REPORT_DIR}/.raw-target" "${raw_path}"
        ;;
      *) exit 90 ;;
    esac
  fi
  if [[ "${FAKE_CREATE_MARKDOWN:-0}" == "1" ]]; then
    while (($#)); do
      if [[ "$1" == "--report" ]]; then
        printf '%s\\n' '# CI report' > "$2"
        break
      fi
      shift
    done
  fi
  if [[ -n "${FAKE_CREATE_PATH:-}" ]]; then
    printf '%s\\n' dirty > "${FAKE_CREATE_PATH}"
  fi
  if [[ -n "${FAKE_CREATE_EVIDENCE_NAME:-}" ]]; then
    evidence_path="${FAKE_REPORT_DIR}/${FAKE_CREATE_EVIDENCE_NAME}"
    case "${FAKE_CREATE_EVIDENCE_KIND:-}" in
      regular) printf '%s\\n' collision > "${evidence_path}" ;;
      directory) mkdir -p -- "${evidence_path}" ;;
      symlink)
        printf '%s\\n' collision > "${FAKE_REPORT_DIR}/.collision-target"
        ln -s -- "${FAKE_REPORT_DIR}/.collision-target" "${evidence_path}"
        ;;
      *) exit 89 ;;
    esac
  fi
  exit "${FAKE_CLI_EXIT:-0}"
fi
exec "${REAL_PYTHON}" "$@"
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


@pytest.fixture
def wrapper_case(tmp_path: Path) -> WrapperCase:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "tracked.txt").write_text("clean\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(
        repo,
        "-c",
        "user.name=CI Test",
        "-c",
        "user.email=ci@example.invalid",
        "commit",
        "-qm",
        "fixture",
    )

    report_dir = tmp_path / "evidence"
    summary = tmp_path / "summary.md"
    invocations = tmp_path / "invocations.txt"
    stdout_file = tmp_path / "stdout.txt"
    fake = _fake_python(tmp_path / "fake-python")
    env = os.environ.copy()
    env.update(
        {
            "FAKE_INVOCATIONS": str(invocations),
            "FAKE_REPORT_DIR": str(report_dir),
            "FAKE_STDOUT_FILE": str(stdout_file),
            "GITHUB_STEP_SUMMARY": str(summary),
            "REAL_PYTHON": str(PYTHON),
        }
    )
    return {
        "repo": repo,
        "report_dir": report_dir,
        "summary": summary,
        "invocations": invocations,
        "stdout_file": stdout_file,
        "fake": fake,
        "env": env,
    }


def _run(
    case: WrapperCase,
    *,
    cli_exit: int = 0,
    output: str | None = '{"ok": true}\n',
    create_markdown: bool = True,
    create_path: Path | None = None,
    create_evidence_name: str | None = None,
    create_evidence_kind: str = "directory",
    raw_replacement_kind: str | None = None,
    delete_raw: bool = False,
    python: Path | None = None,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = dict(case["env"])
    env["FAKE_CLI_EXIT"] = str(cli_exit)
    env["FAKE_CREATE_MARKDOWN"] = "1" if create_markdown else "0"
    env["FAKE_DELETE_RAW"] = "1" if delete_raw else "0"
    if create_path is not None:
        env["FAKE_CREATE_PATH"] = str(create_path)
    else:
        env.pop("FAKE_CREATE_PATH", None)
    if create_evidence_name is not None:
        env["FAKE_CREATE_EVIDENCE_NAME"] = create_evidence_name
        env["FAKE_CREATE_EVIDENCE_KIND"] = create_evidence_kind
    else:
        env.pop("FAKE_CREATE_EVIDENCE_NAME", None)
        env.pop("FAKE_CREATE_EVIDENCE_KIND", None)
    if raw_replacement_kind is not None:
        env["FAKE_RAW_REPLACEMENT_KIND"] = raw_replacement_kind
    else:
        env.pop("FAKE_RAW_REPLACEMENT_KIND", None)
    if environment is not None:
        env.update(environment)
    stdout_file = Path(case["stdout_file"])
    if output is None:
        env["FAKE_STDOUT_FILE"] = ""
    else:
        stdout_file.write_text(output, encoding="utf-8")

    command = [
        str(WRAPPER),
        "--python",
        str(python or case["fake"]),
        "--src-dir",
        ".",
        "--wiki-dir",
        "docs/llm_wiki",
        "--helper-cache-dir",
        str(Path(case["report_dir"]) / "cache"),
        "--report-dir",
        str(case["report_dir"]),
        "--jobs",
        "1",
        "--knowledge-drift-report",
    ]
    return subprocess.run(
        command,
        cwd=case["repo"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize("python", [Path("python"), Path("/missing/python")])
def test_missing_or_invalid_interpreter_fails_closed(
    wrapper_case: WrapperCase, python: Path
) -> None:
    result = _run(wrapper_case, python=python)

    assert result.returncode != 0
    assert "--python" in result.stderr


def test_omitted_interpreter_argument_fails_before_candidate_execution(
    wrapper_case: WrapperCase,
) -> None:
    command = [
        str(WRAPPER),
        "--src-dir",
        ".",
        "--wiki-dir",
        "docs/llm_wiki",
        "--helper-cache-dir",
        str(wrapper_case["report_dir"] / "cache"),
        "--report-dir",
        str(wrapper_case["report_dir"]),
        "--jobs",
        "1",
        "--knowledge-drift-report",
    ]

    result = subprocess.run(
        command,
        cwd=wrapper_case["repo"],
        env=wrapper_case["env"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--python is required" in result.stderr
    assert not wrapper_case["invocations"].exists()


def test_explicit_interpreter_runs_cli_and_parses_json(
    wrapper_case: WrapperCase,
) -> None:
    result = _run(wrapper_case)

    assert result.returncode == 0, result.stderr
    invocations = Path(wrapper_case["invocations"]).read_text(encoding="utf-8")
    assert "-m llm_wiki_cli.cli ci-check" in invocations
    assert "json.loads" in invocations
    assert "--jobs 1 --knowledge-drift-report --format json" in invocations


def test_explicit_interpreter_path_with_spaces_is_used_consistently(
    wrapper_case: WrapperCase,
) -> None:
    fake_with_spaces = _fake_python(
        Path(wrapper_case["fake"]).with_name("selected python")
    )

    result = _run(wrapper_case, python=fake_with_spaces)

    assert result.returncode == 0, result.stderr
    invocations = Path(wrapper_case["invocations"]).read_text(encoding="utf-8")
    assert "llm-wiki-ci-python-v1" in invocations
    assert "-m llm_wiki_cli.cli ci-check" in invocations
    assert "json.loads" in invocations


def test_success_preserves_only_valid_json_and_reports_clean_tree(
    wrapper_case: WrapperCase,
) -> None:
    result = _run(wrapper_case)
    report_dir = Path(wrapper_case["report_dir"])

    assert result.returncode == 0, result.stderr
    assert json.loads(
        (report_dir / "llm-wiki-ci-report.json").read_text(encoding="utf-8")
    ) == {"ok": True}
    assert (report_dir / "llm-wiki-ci-report.md").is_file()
    assert not (report_dir / "llm-wiki-ci-report.invalid.txt").exists()
    summary = Path(wrapper_case["summary"]).read_text(encoding="utf-8")
    assert "Result: **PASS**" in summary
    assert "Worktree: clean" in summary
    assert "Native drift diagnostics are advisory" in summary


@pytest.mark.parametrize(
    ("destination", "kind"),
    [
        ("llm-wiki-ci-report.md", "directory"),
        ("llm-wiki-ci-report.json", "symlink"),
        ("llm-wiki-ci-report.invalid.txt", "directory"),
    ],
)
def test_preexisting_artifact_path_is_cleared_before_validation(
    wrapper_case: WrapperCase,
    destination: str,
    kind: str,
) -> None:
    report_dir = wrapper_case["report_dir"]
    report_dir.mkdir()
    stale_path = report_dir / destination
    if kind == "directory":
        stale_path.mkdir()
        (stale_path / "forged.txt").write_text("forged\n", encoding="utf-8")
    else:
        target = report_dir / ".stale-target"
        target.write_text("forged\n", encoding="utf-8")
        stale_path.symlink_to(target)

    result = _run(wrapper_case)

    assert result.returncode == 0, result.stderr
    assert (report_dir / "llm-wiki-ci-report.md").is_file()
    assert not (report_dir / "llm-wiki-ci-report.md").is_symlink()
    assert (report_dir / "llm-wiki-ci-report.json").is_file()
    assert not (report_dir / "llm-wiki-ci-report.json").is_symlink()
    assert not (report_dir / "llm-wiki-ci-report.invalid.txt").exists()
    assert not (report_dir / "llm-wiki-ci-report.invalid.txt").is_symlink()


def test_symlinked_report_directory_fails_before_candidate_execution(
    wrapper_case: WrapperCase,
) -> None:
    real_report_dir = wrapper_case["report_dir"].with_name("real-evidence")
    real_report_dir.mkdir()
    wrapper_case["report_dir"].symlink_to(real_report_dir, target_is_directory=True)

    result = _run(wrapper_case)

    assert result.returncode != 0
    assert "report directory must be a real directory" in result.stderr
    invocations = wrapper_case["invocations"].read_text(encoding="utf-8")
    assert "-m llm_wiki_cli.cli ci-check" not in invocations


@pytest.mark.parametrize("output", ['{"ok": true}\n', "not json\n", "", None])
def test_nonzero_cli_exit_is_preserved_for_every_evidence_state(
    wrapper_case: WrapperCase, output: str | None
) -> None:
    result = _run(wrapper_case, cli_exit=37, output=output)

    assert result.returncode == 37
    summary = Path(wrapper_case["summary"]).read_text(encoding="utf-8")
    assert "Result: **FAIL**" in summary
    assert "Original `ci-check` exit: `37`" in summary


def test_nonzero_cli_exit_is_preserved_when_raw_output_is_absent(
    wrapper_case: WrapperCase,
) -> None:
    result = _run(
        wrapper_case,
        cli_exit=29,
        output=None,
        delete_raw=True,
    )

    assert result.returncode == 29
    summary = Path(wrapper_case["summary"]).read_text(encoding="utf-8")
    assert "Original `ci-check` exit: `29`" in summary
    assert "no output" in summary


@pytest.mark.parametrize(
    ("output", "delete_raw", "expected"),
    [
        ("invalid output\n", False, "invalid output"),
        ("", False, "empty output"),
        (None, True, "no output"),
    ],
)
def test_successful_cli_fails_closed_without_parseable_json(
    wrapper_case: WrapperCase,
    output: str | None,
    delete_raw: bool,
    expected: str,
) -> None:
    result = _run(wrapper_case, output=output, delete_raw=delete_raw)

    assert result.returncode != 0
    assert expected in (result.stderr + Path(wrapper_case["summary"]).read_text())
    assert not (
        Path(wrapper_case["report_dir"]) / "llm-wiki-ci-report.json"
    ).exists()


def test_invalid_raw_output_never_uses_json_name(
    wrapper_case: WrapperCase,
) -> None:
    result = _run(wrapper_case, cli_exit=19, output="{broken\n")
    report_dir = Path(wrapper_case["report_dir"])

    assert result.returncode == 19
    assert not (report_dir / "llm-wiki-ci-report.json").exists()
    assert (report_dir / "llm-wiki-ci-report.invalid.txt").read_text(
        encoding="utf-8"
    ) == "{broken\n"


@pytest.mark.parametrize(
    ("output", "destination", "kind"),
    [
        ('{"ok": true}\n', "llm-wiki-ci-report.invalid.txt", "directory"),
        ("not json\n", "llm-wiki-ci-report.json", "regular"),
        ('{"ok": true}\n', "llm-wiki-ci-report.json", "symlink"),
    ],
)
def test_cli_created_evidence_collision_is_quarantined_and_fails_closed(
    wrapper_case: WrapperCase,
    output: str,
    destination: str,
    kind: str,
) -> None:
    result = _run(
        wrapper_case,
        output=output,
        create_evidence_name=destination,
        create_evidence_kind=kind,
    )

    assert result.returncode != 0
    assert not (wrapper_case["report_dir"] / destination).exists()
    assert not (wrapper_case["report_dir"] / destination).is_symlink()
    summary = Path(wrapper_case["summary"]).read_text(encoding="utf-8")
    assert "JSON evidence: unavailable" in summary


def test_evidence_collision_never_hides_the_primary_cli_exit(
    wrapper_case: WrapperCase,
) -> None:
    result = _run(
        wrapper_case,
        cli_exit=43,
        create_evidence_name="llm-wiki-ci-report.invalid.txt",
        create_evidence_kind="regular",
    )

    assert result.returncode == 43
    assert not (wrapper_case["report_dir"] / "llm-wiki-ci-report.json").exists()
    assert not (
        wrapper_case["report_dir"] / "llm-wiki-ci-report.invalid.txt"
    ).exists()


@pytest.mark.parametrize("kind", ["directory", "symlink"])
def test_non_file_raw_output_is_quarantined_and_never_promoted(
    wrapper_case: WrapperCase,
    kind: str,
) -> None:
    result = _run(wrapper_case, raw_replacement_kind=kind)

    assert result.returncode != 0
    assert not (wrapper_case["report_dir"] / "llm-wiki-ci-report.json").exists()
    assert not (
        wrapper_case["report_dir"] / "llm-wiki-ci-report.invalid.txt"
    ).exists()
    summary = wrapper_case["summary"].read_text(encoding="utf-8")
    assert "JSON evidence: unavailable" in summary


@pytest.mark.parametrize("kind", ["directory", "symlink"])
def test_non_file_markdown_is_quarantined_and_fails_closed(
    wrapper_case: WrapperCase,
    kind: str,
) -> None:
    result = _run(
        wrapper_case,
        create_markdown=False,
        create_evidence_name="llm-wiki-ci-report.md",
        create_evidence_kind=kind,
    )

    assert result.returncode != 0
    markdown_report = wrapper_case["report_dir"] / "llm-wiki-ci-report.md"
    assert not markdown_report.exists()
    assert not markdown_report.is_symlink()
    summary = wrapper_case["summary"].read_text(encoding="utf-8")
    assert "Markdown report: unavailable" in summary


def test_dirty_worktree_strengthens_success_and_bounds_sorted_diagnostics(
    wrapper_case: WrapperCase,
) -> None:
    repo = Path(wrapper_case["repo"])
    for index in range(25, 0, -1):
        (repo / f"dirty-{index:02d}.txt").write_text("dirty\n", encoding="utf-8")

    result = _run(wrapper_case)
    summary_path = Path(wrapper_case["summary"])
    summary_bytes = summary_path.read_bytes()
    summary = summary_bytes.decode("utf-8")

    assert result.returncode != 0
    assert "Result: **FAIL**" in summary
    diagnostics = [line for line in summary.splitlines() if line.startswith("  - `")]
    assert len(diagnostics) == 20
    assert diagnostics == sorted(diagnostics)
    assert "5 additional status records omitted" in summary
    assert len(summary.splitlines()) <= 40
    assert len(summary_bytes) <= 8192


def test_cli_created_nonignored_path_strengthens_success(
    wrapper_case: WrapperCase,
) -> None:
    created = Path(wrapper_case["repo"]) / "created-by-candidate.txt"
    result = _run(wrapper_case, create_path=created)

    assert result.returncode != 0
    assert "?? created-by-candidate.txt" in result.stderr


def test_missing_markdown_never_hides_primary_exit(
    wrapper_case: WrapperCase,
) -> None:
    result = _run(wrapper_case, cli_exit=23, create_markdown=False)

    assert result.returncode == 23
    summary = Path(wrapper_case["summary"]).read_text(encoding="utf-8")
    assert "Markdown report: unavailable" in summary
    assert "Original `ci-check` exit: `23`" in summary


def test_missing_markdown_strengthens_an_otherwise_successful_result(
    wrapper_case: WrapperCase,
) -> None:
    result = _run(wrapper_case, create_markdown=False)

    assert result.returncode != 0
    assert "Markdown report: unavailable" in Path(
        wrapper_case["summary"]
    ).read_text(encoding="utf-8")


def test_post_validation_support_failure_preserves_original_cli_exit(
    wrapper_case: WrapperCase,
) -> None:
    repo = Path(wrapper_case["repo"])
    (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    fake_bin = Path(wrapper_case["report_dir"]).parent / "fake-bin"
    fake_bin.mkdir()
    fake_sort = fake_bin / "sort"
    fake_sort.write_text("#!/usr/bin/env bash\nexit 73\n", encoding="utf-8")
    fake_sort.chmod(0o755)
    path = os.pathsep.join([str(fake_bin), os.environ["PATH"]])

    result = _run(
        wrapper_case,
        cli_exit=41,
        environment={"PATH": path, "FAKE_SUMMARY_FAIL": "1"},
    )

    assert result.returncode == 41
    assert "Could not sort complete worktree status diagnostics" in result.stderr
    assert "Could not write the bounded CI summary" in result.stderr


def test_git_status_failure_strengthens_success_and_is_summarized(
    wrapper_case: WrapperCase,
) -> None:
    fake_bin = Path(wrapper_case["report_dir"]).parent / "fake-git-bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text("#!/usr/bin/env bash\nexit 57\n", encoding="utf-8")
    fake_git.chmod(0o755)
    path = os.pathsep.join([str(fake_bin), os.environ["PATH"]])

    result = _run(wrapper_case, environment={"PATH": path})

    assert result.returncode != 0
    assert "Could not inspect the complete worktree status" in result.stderr
    summary = Path(wrapper_case["summary"]).read_text(encoding="utf-8")
    assert "Worktree: unavailable" in summary


def test_summary_is_utf8_and_within_frozen_line_and_byte_bounds(
    wrapper_case: WrapperCase,
) -> None:
    repo = Path(wrapper_case["repo"])
    for index in range(24):
        name = f"{index:02d}-" + ("é" * 100)
        (repo / name).write_text("dirty\n", encoding="utf-8")

    result = _run(wrapper_case)
    summary_bytes = Path(wrapper_case["summary"]).read_bytes()

    assert result.returncode != 0
    summary = summary_bytes.decode("utf-8")
    assert len(summary.splitlines()) <= 40
    assert len(summary_bytes) <= 8192
    assert "additional status records omitted" in summary


def test_summary_encodes_filename_backticks_without_markdown_injection(
    wrapper_case: WrapperCase,
) -> None:
    dangerous_name = "evil`**SPOOF**.txt"
    (wrapper_case["repo"] / dangerous_name).write_text("dirty\n", encoding="utf-8")

    result = _run(wrapper_case)

    assert result.returncode != 0
    summary = wrapper_case["summary"].read_text(encoding="utf-8")
    assert dangerous_name not in summary
    assert "?? evil\\x60**SPOOF**.txt" in summary
