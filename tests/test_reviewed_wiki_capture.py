"""A preview is never a writer; only an unchanged explicit approval admits one."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import tarfile

import pytest
import yaml


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / ".github/scripts/run-reviewed-wiki-capture.py"
spec = importlib.util.spec_from_file_location("reviewed_wiki_capture", SCRIPT)
assert spec is not None and spec.loader is not None
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
PLAN = b"Sync dry-run plan:\n  generator refresh sources: 53\n  requires --force: yes\nDRY-RUN: no files modified.\n"


@pytest.fixture
def case(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    (root / "docs/llm_wiki").mkdir(parents=True)
    (root / "docs/llm_wiki/index.md").write_text("# Retained navigation\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "commit", "-qm", "fixture"], cwd=root, check=True)
    sha = driver.git(root, "rev-parse", "HEAD").decode().strip()
    observed = {"source_sha": sha, "platform": ["Linux", "x86_64"],
                "python": "fixture Python 3.13.16", "helper": {"status": "ready", "files": "fixture"}}
    calls = []

    def runner(source, evidence, *, dry_run):
        assert source == root
        calls.append(dry_run)
        if not dry_run:
            (root / "docs/llm_wiki/index.md").write_text("# Captured navigation\n")
        return subprocess.CompletedProcess([], 0, PLAN if dry_run else b"owning sync complete\n", b"")

    monkeypatch.setattr(driver, "context", lambda _: observed)
    monkeypatch.setattr(driver, "run_sync", runner)
    approved = driver.digest(driver.canonical(observed) + b"\n" + PLAN)
    return root, tmp_path / "evidence", sha, observed, calls, approved


def invoke(case, *, operation="preview", approved=None):
    root, evidence, sha, *_ = case
    return driver.capture(root, evidence, operation=operation, candidate=sha,
                          approved=approved, run_id=123, attempt=1)


def test_preview_is_clean_and_has_no_owning_or_snapshot_receipt(case):
    result = invoke(case)
    root, evidence, _, _, calls, approved = case
    assert result == {"status": "previewed", "preview_sha256": approved, "writer_succeeded": False}
    assert calls == [True]
    assert not driver.status(root)
    assert (evidence / "preview.stdout").read_bytes() == PLAN
    assert not (evidence / "convergence-result.json").exists()
    assert not (evidence / "wiki-review-snapshot.tar").exists()


@pytest.mark.parametrize("approved", [None, "", "z" * 64])
def test_apply_without_valid_explicit_approval_never_invokes_sync(case, approved):
    with pytest.raises(ValueError, match="requires the reviewed preview"):
        invoke(case, operation="apply", approved=approved)
    assert case[4] == []
    assert not case[1].exists()


def test_different_reviewed_hash_keeps_full_preview_and_never_writes(case):
    with pytest.raises(ValueError, match="differs; no writer"):
        invoke(case, operation="apply", approved="0" * 64)
    assert case[4] == [True]
    assert not driver.status(case[0])
    assert (case[1] / "preview.stdout").read_bytes() == PLAN
    assert not (case[1] / "convergence-result.json").exists()


@pytest.mark.parametrize("field", ["python", "helper", "source_sha"])
def test_changed_binding_during_preview_never_invokes_writer(case, monkeypatch, field):
    observed = case[3]
    values = iter([observed, {**observed, field: "changed"}])
    monkeypatch.setattr(driver, "context", lambda _: next(values))
    with pytest.raises(ValueError, match="changed during preview"):
        invoke(case, operation="apply", approved=case[5])
    assert case[4] == [True]
    assert not driver.status(case[0])


def test_preview_mutation_stops_before_any_writer(case, monkeypatch):
    def mutate(root, evidence, *, dry_run):
        assert dry_run
        case[4].append(dry_run)
        (root / "unexpected.txt").write_text("unexpected preview side effect")
        return subprocess.CompletedProcess([], 0, PLAN, b"")

    monkeypatch.setattr(driver, "run_sync", mutate)
    with pytest.raises(ValueError, match="preview changed"):
        invoke(case, operation="apply", approved=case[5])
    assert case[4] == [True]


def test_explicit_matching_apply_retains_drift_and_complete_native_snapshot(case):
    result = invoke(case, operation="apply", approved=case[5])
    root, evidence, sha, _, calls, approved = case
    assert result == {"status": "drift", "preview_sha256": approved, "writer_succeeded": True}
    assert calls == [True, False]
    record = json.loads((evidence / "convergence-result.json").read_text())
    assert record["decision"] == "FAIL"
    assert record["sync"] == {"exit_code": 0, "plugins_enabled": False, "started": True}
    spec = importlib.util.spec_from_file_location(
        "reviewed_capture_snapshot", ROOT / ".github/scripts/capture-llm-wiki-review-snapshot.py"
    )
    assert spec is not None and spec.loader is not None
    snapshot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(snapshot)
    manifest = snapshot.capture(root, evidence, sha, 123, 1)
    assert [row["path"] for row in manifest["entries"]] == ["index.md"]
    with tarfile.open(evidence / "wiki-review-snapshot.tar") as archive:
        member = archive.extractfile("index.md")
        assert member is not None
        with member:
            assert member.read() == (root / "docs/llm_wiki/index.md").read_bytes()


def test_outside_wiki_write_cannot_report_a_successful_writer(case, monkeypatch):
    def mutate(root, evidence, *, dry_run):
        case[4].append(dry_run)
        if not dry_run:
            (root / "outside.txt").write_text("outside wiki")
        return subprocess.CompletedProcess([], 0, PLAN, b"")

    monkeypatch.setattr(driver, "run_sync", mutate)
    with pytest.raises(ValueError, match="outside the wiki"):
        invoke(case, operation="apply", approved=case[5])
    record = json.loads((case[1] / "convergence-result.json").read_text())
    assert record["checks"]["worktree_changes_scoped_to_wiki"] is False
    assert not (case[1] / "wiki-review-snapshot.tar").exists()


def test_changed_binding_during_writer_retains_logs_but_no_owning_receipt(case, monkeypatch):
    observed = case[3]
    values = iter([observed, observed, {**observed, "helper": "changed during writer"}])
    monkeypatch.setattr(driver, "context", lambda _: next(values))
    with pytest.raises(ValueError, match="writer basis changed"):
        invoke(case, operation="apply", approved=case[5])
    assert case[4] == [True, False]
    assert (case[1] / "sync.stdout").read_bytes() == b"owning sync complete\n"
    assert (case[1] / "wiki-status-after.txt").stat().st_size > 0
    assert not (case[1] / "convergence-result.json").exists()
    assert not (case[1] / "wiki-review-snapshot.tar").exists()


@pytest.mark.parametrize("fault", ["candidate", "dirty", "occupied", "inside-source"])
def test_invalid_start_never_invokes_a_preview_or_writer(case, fault):
    root, evidence, sha, *_ = case
    if fault == "candidate":
        sha = "0" * 40
    elif fault == "dirty":
        (root / "unexpected.txt").write_text("unreviewed source")
    elif fault == "occupied":
        evidence.mkdir()
    else:
        evidence = root / "evidence"
    with pytest.raises(ValueError):
        driver.capture(root, evidence, operation="apply", candidate=sha,
                       approved=case[5], run_id=123, attempt=1)
    assert case[4] == []


def test_failed_or_incomplete_preview_never_invokes_writer(case, monkeypatch):
    monkeypatch.setattr(driver, "run_sync", lambda *a, **k: subprocess.CompletedProcess([], 1, b"refused", b""))
    with pytest.raises(ValueError, match="preview failed"):
        invoke(case, operation="apply", approved=case[5])
    assert not (case[1] / "convergence-result.json").exists()


def test_new_workflow_is_manual_pinned_read_only_and_preview_by_default():
    source = (ROOT / ".github/workflows/reviewed-wiki-capture.yml").read_text()
    workflow = yaml.safe_load(source)
    triggers = workflow.get("on", workflow.get(True))
    assert set(triggers) == {"workflow_dispatch"}
    inputs = triggers["workflow_dispatch"]["inputs"]
    assert inputs["operation"]["default"] == "preview"
    assert inputs["operation"]["options"] == ["preview", "apply"]
    assert inputs["candidate-sha"]["required"] is True
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["cancel-in-progress"] is False
    steps = workflow["jobs"]["capture"]["steps"]
    for step in steps:
        if "uses" in step:
            assert len(step["uses"].split("@", 1)[1]) == 40
    guard = steps[0]["run"]
    assert 'test "${RUN_REF}" = refs/heads/main' in guard
    assert 'test "${CANDIDATE}" = "${RUN_SHA}"' in guard
    assert 'test "${WORKFLOW_SHA}" = "${RUN_SHA}"' in guard
    setup = next(step["run"] for step in steps if step.get("name") == "Prepare the selected locked helper")
    command = shlex.split(next(line for line in setup.splitlines()
                              if "setup-llm-wiki-ci-toolchains.sh" in line))
    install_root = command[command.index("--install-root") + 1]
    assert install_root.startswith("${RUNNER_TEMP}/")
    child = PurePosixPath(install_root.removeprefix("${RUNNER_TEMP}/"))
    assert not child.is_absolute() and ".." not in child.parts and child.parts
    assert "approved-preview-sha256" in source
    assert "writer-succeeded == 'true'" in source
    assert "${{ secrets." not in source
    assert "git push" not in source and "git commit" not in source
    uploaded = steps[-1]["with"]["path"].splitlines()
    assert all(path.startswith("${{ runner.temp }}/reviewed-wiki-capture/") for path in uploaded)
    assert {path.rsplit("/", 1)[1] for path in uploaded} == {
        "preview.json", "preview.stdout", "preview.stderr", "sync.stdout", "sync.stderr",
        "sync.log", "convergence-result.json", "wiki-status-before.txt", "wiki-status-after.txt",
        "worktree-status-after.txt", "wiki-diff.patch", "wiki-review-snapshot.tar",
        "wiki-review-snapshot.json",
    }


@pytest.mark.parametrize("event,ref,repository", [
    ("push", "refs/heads/main", "Denissvgn/python-wiki-llm"),
    ("workflow_dispatch", "refs/heads/other", "Denissvgn/python-wiki-llm"),
    ("workflow_dispatch", "refs/heads/main", "other/fork"),
])
def test_main_rejects_foreign_or_nonmanual_dispatch_before_capture(monkeypatch, event, ref, repository):
    monkeypatch.setattr("sys.argv", [str(SCRIPT), "--operation", "preview", "--candidate-sha", "a" * 40,
                                      "--evidence-dir", "/unused"])
    monkeypatch.setenv("GITHUB_EVENT_NAME", event)
    monkeypatch.setenv("GITHUB_REF", ref)
    monkeypatch.setenv("GITHUB_REPOSITORY", repository)
    monkeypatch.setattr(driver, "capture", lambda *a, **k: pytest.fail("capture must not run"))
    assert driver.main() == 2
