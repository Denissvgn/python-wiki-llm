"""Behavioral contracts for the real-sync convergence wrapper."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import pytest


ROOT = Path(__file__).parents[1]
WRAPPER = ROOT / ".github" / "scripts" / "run-llm-wiki-convergence.sh"
PYTHON = Path(sys.executable)
EVIDENCE_NAMES = {
    "convergence-result.json",
    "sync.log",
    "wiki-diff.patch",
    "wiki-status-after.txt",
    "wiki-status-before.txt",
    "worktree-status-after.txt",
}


class ConvergenceCase(TypedDict):
    repo: Path
    candidate_sha: str
    runner_temp: Path
    evidence_dir: Path
    helper_cache: Path
    summary: Path
    invocations: Path
    github_output: Path
    fake_python: Path
    env: dict[str, str]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _fake_python(path: Path) -> Path:
    path.write_text(
        """#!/usr/bin/env bash
set -uo pipefail
{
  printf '%s\n' BEGIN
  printf '<%s>\n' "$@"
  printf '%s\n' END
} >> "${FAKE_INVOCATIONS}"
if [[ "$*" == *"llm-wiki-convergence-python-v1"* ]]; then
  printf '%s' 'llm-wiki-convergence-python-v1'
  exit 0
fi
if [[ "${1:-}" == "-I" && "${2:-}" == "-m" &&
      "${3:-}" == "llm_wiki_cli.cli" && "${4:-}" == "sync" ]]; then
  if [[ "${FAKE_MODIFY_TRACKED:-0}" == "1" ]]; then
    printf '%s\n' changed >> docs/llm_wiki/tracked.md
  fi
  if [[ "${FAKE_STAGE_TRACKED:-0}" == "1" ]]; then
    git add -- docs/llm_wiki/tracked.md
  fi
  untracked_count="${FAKE_UNTRACKED_COUNT:-0}"
  for ((index = 0; index < untracked_count; index++)); do
    printf 'generated %s\n' "${index}" > \
      "docs/llm_wiki/generated-$(printf '%03d' "${index}").md"
  done
  if [[ -n "${FAKE_INJECTION_NAME:-}" ]]; then
    printf '%s\n' generated > "docs/llm_wiki/${FAKE_INJECTION_NAME}"
  fi
  if [[ "${FAKE_CREATE_OUTSIDE:-0}" == "1" ]]; then
    printf '%s\n' outside > outside-sync-change.txt
  fi
  printf 'fake real sync output\n'
  exit "${FAKE_SYNC_EXIT:-0}"
fi
exec "${REAL_PYTHON}" "$@"
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


@pytest.fixture
def convergence_case(tmp_path: Path) -> ConvergenceCase:
    repo = tmp_path / "repo"
    wiki = repo / "docs" / "llm_wiki"
    wiki.mkdir(parents=True)
    (wiki / "tracked.md").write_text("committed\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "docs/llm_wiki/tracked.md")
    _git(
        repo,
        "-c",
        "user.name=Convergence Test",
        "-c",
        "user.email=convergence@example.invalid",
        "commit",
        "-qm",
        "fixture",
    )
    candidate_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    runner_temp = tmp_path / "runner-temp"
    runner_temp.mkdir()
    helper_cache = runner_temp / "helpers"
    helper_cache.mkdir()
    evidence_dir = runner_temp / "llm-wiki-convergence-evidence"
    summary = tmp_path / "summary.md"
    invocations = tmp_path / "invocations.txt"
    github_output = tmp_path / "github-output.txt"
    github_output.write_text("", encoding="utf-8")
    fake_python = _fake_python(tmp_path / "fake-python")
    env = os.environ.copy()
    env.update(
        {
            "FAKE_INVOCATIONS": str(invocations),
            "GITHUB_SHA": candidate_sha,
            "GITHUB_STEP_SUMMARY": str(summary),
            "REAL_PYTHON": str(PYTHON),
            "RUNNER_TEMP": str(runner_temp),
        }
    )
    return {
        "repo": repo,
        "candidate_sha": candidate_sha,
        "runner_temp": runner_temp,
        "evidence_dir": evidence_dir,
        "helper_cache": helper_cache,
        "summary": summary,
        "invocations": invocations,
        "github_output": github_output,
        "fake_python": fake_python,
        "env": env,
    }


def _run(
    case: ConvergenceCase,
    *,
    sync_exit: int = 0,
    modify_tracked: bool = False,
    untracked_count: int = 0,
    create_outside: bool = False,
    injection_name: str = "",
    stage_tracked: bool = False,
) -> subprocess.CompletedProcess[str]:
    env = dict(case["env"])
    env.update(
        {
            "FAKE_CREATE_OUTSIDE": "1" if create_outside else "0",
            "FAKE_INJECTION_NAME": injection_name,
            "FAKE_MODIFY_TRACKED": "1" if modify_tracked else "0",
            "FAKE_SYNC_EXIT": str(sync_exit),
            "FAKE_STAGE_TRACKED": "1" if stage_tracked else "0",
            "FAKE_UNTRACKED_COUNT": str(untracked_count),
        }
    )
    return subprocess.run(
        [
            str(WRAPPER),
            "--python",
            str(case["fake_python"]),
            "--src-dir",
            ".",
            "--wiki-dir",
            "docs/llm_wiki",
            "--helper-cache-dir",
            str(case["helper_cache"]),
            "--evidence-dir",
            str(case["evidence_dir"]),
            "--github-output",
            str(case["github_output"]),
            "--jobs",
            "1",
        ],
        cwd=case["repo"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _payload(case: ConvergenceCase) -> dict:
    return json.loads(
        (case["evidence_dir"] / "convergence-result.json").read_text(
            encoding="utf-8"
        )
    )


def test_clean_real_sync_writes_the_fixed_hashed_evidence(
    convergence_case: ConvergenceCase,
) -> None:
    completed = _run(convergence_case)

    assert completed.returncode == 0, completed.stderr
    assert convergence_case["github_output"].read_text(encoding="utf-8") == (
        "evidence-ready=true\n"
    )
    evidence = convergence_case["evidence_dir"]
    assert {path.name for path in evidence.iterdir()} == EVIDENCE_NAMES
    assert all(path.is_file() and not path.is_symlink() for path in evidence.iterdir())

    invocations = convergence_case["invocations"].read_text(encoding="utf-8")
    assert "<sync>" in invocations
    assert "<--no-plugins>" in invocations
    assert "<--dry-run>" not in invocations
    assert "<--force>" not in invocations

    payload = _payload(convergence_case)
    assert payload["schema_version"] == "llm-wiki-convergence/v1"
    assert payload["candidate_sha"] == convergence_case["candidate_sha"]
    assert payload["decision"] == "PASS"
    assert payload["captures"] == {"wiki_diff": {"exit_code": 0}}
    assert payload["sync"] == {
        "exit_code": 0,
        "plugins_enabled": False,
        "started": True,
    }
    assert payload["checks"] == {
        "post_sync_diff_available": True,
        "post_sync_status_available": True,
        "post_sync_wiki_clean": True,
        "pre_sync_status_available": True,
        "pre_sync_wiki_clean": True,
        "pre_sync_worktree_clean": True,
        "worktree_changes_scoped_to_wiki": True,
    }
    assert set(payload["evidence"]) == EVIDENCE_NAMES - {"convergence-result.json"}
    for filename, record in payload["evidence"].items():
        raw = (evidence / filename).read_bytes()
        assert record == {
            "bytes": len(raw),
            "filename": filename,
            "records": len(raw.splitlines()),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }


def test_status_artifacts_are_complete_while_the_summary_is_bounded(
    convergence_case: ConvergenceCase,
) -> None:
    completed = _run(
        convergence_case,
        modify_tracked=True,
        untracked_count=25,
        injection_name="aaa-status`## forged-heading.md",
        stage_tracked=True,
    )

    assert completed.returncode == 1
    after = (
        convergence_case["evidence_dir"] / "wiki-status-after.txt"
    ).read_text(encoding="utf-8")
    full = (
        convergence_case["evidence_dir"] / "worktree-status-after.txt"
    ).read_text(encoding="utf-8")
    assert after == full
    assert len(after.splitlines()) == 27
    assert "docs/llm_wiki/tracked.md" in after
    assert "docs/llm_wiki/generated-024.md" in after
    assert "aaa-status`## forged-heading.md" in after
    patch = (convergence_case["evidence_dir"] / "wiki-diff.patch").read_text(
        encoding="utf-8"
    )
    assert "diff --git a/docs/llm_wiki/tracked.md" in patch
    assert "generated-024.md" not in patch
    assert "aaa-status" not in patch

    payload = _payload(convergence_case)
    assert payload["decision"] == "FAIL"
    assert payload["evidence"]["wiki-status-after.txt"]["records"] == 27
    assert payload["evidence"]["worktree-status-after.txt"]["records"] == 27
    assert payload["captures"]["wiki_diff"]["exit_code"] == 0
    assert payload["evidence"]["wiki-diff.patch"]["records"] == len(
        patch.splitlines()
    )

    summary = convergence_case["summary"].read_bytes()
    assert len(summary) <= 8192
    assert len(summary.splitlines()) <= 40
    summary_text = summary.decode("utf-8")
    assert "7 additional records omitted" in summary_text
    assert "aaa-status\\x60## forged-heading.md" in summary_text
    for line in summary_text.splitlines():
        if line.startswith("  - `"):
            assert line.count("`") == 2


def test_full_worktree_evidence_detects_changes_outside_the_wiki(
    convergence_case: ConvergenceCase,
) -> None:
    completed = _run(convergence_case, create_outside=True)

    assert completed.returncode == 1
    assert not (
        convergence_case["evidence_dir"] / "wiki-status-after.txt"
    ).read_text(encoding="utf-8")
    full = (
        convergence_case["evidence_dir"] / "worktree-status-after.txt"
    ).read_text(encoding="utf-8")
    assert "outside-sync-change.txt" in full
    assert not (
        convergence_case["evidence_dir"] / "wiki-diff.patch"
    ).read_text(encoding="utf-8")
    payload = _payload(convergence_case)
    assert payload["checks"]["post_sync_wiki_clean"] is True
    assert payload["checks"]["worktree_changes_scoped_to_wiki"] is False


def test_original_nonzero_sync_exit_is_preserved(
    convergence_case: ConvergenceCase,
) -> None:
    completed = _run(convergence_case, sync_exit=37, modify_tracked=True)

    assert completed.returncode == 37
    assert convergence_case["github_output"].read_text(encoding="utf-8") == (
        "evidence-ready=true\n"
    )
    payload = _payload(convergence_case)
    assert payload["decision"] == "FAIL"
    assert payload["sync"]["exit_code"] == 37
    assert payload["sync"]["started"] is True


def test_dirty_pre_sync_worktree_prevents_the_real_sync(
    convergence_case: ConvergenceCase,
) -> None:
    (convergence_case["repo"] / "already-dirty.txt").write_text(
        "dirty\n", encoding="utf-8"
    )

    completed = _run(convergence_case)

    assert completed.returncode == 1
    invocations = convergence_case["invocations"].read_text(encoding="utf-8")
    assert "<sync>" not in invocations
    payload = _payload(convergence_case)
    assert payload["sync"] == {
        "exit_code": None,
        "plugins_enabled": False,
        "started": False,
    }
    assert payload["checks"]["pre_sync_worktree_clean"] is False


def test_occupied_evidence_path_is_rejected_before_sync(
    convergence_case: ConvergenceCase,
    tmp_path: Path,
) -> None:
    target = tmp_path / "evidence-target"
    target.mkdir()
    convergence_case["evidence_dir"].symlink_to(target, target_is_directory=True)

    completed = _run(convergence_case)

    assert completed.returncode == 2
    assert "already occupied" in completed.stderr
    assert not convergence_case["github_output"].read_text(encoding="utf-8")
    invocations = convergence_case["invocations"].read_text(encoding="utf-8")
    assert "<sync>" not in invocations
