"""Complete hosted writer recovery, bounded capture and scoped provenance."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
from types import SimpleNamespace

import pytest


SCRIPT = Path(__file__).parents[1] / ".github/scripts/capture-llm-wiki-review-snapshot.py"
spec = importlib.util.spec_from_file_location("review_snapshot", SCRIPT)
assert spec is not None and spec.loader is not None
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


def git(root, *args):
    return snapshot.git(root, *args)


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init")
    git(root, "config", "user.name", "Fixture")
    git(root, "config", "user.email", "fixture@example.invalid")
    wiki = root / "docs/wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_bytes(b"# Authored navigation\n")
    (root / ".gitignore").write_text("docs/wiki/private/\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "fixture")
    (wiki / "new.pack").write_bytes(b"new native object\x00\xff")
    (wiki / "private").mkdir()
    (wiki / "private/notes.md").write_text("private content")
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    return root, wiki, evidence


def evidence_for(root, destination):
    status = ("status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none")
    captures = {
        "wiki-status-before.txt": b"",
        "wiki-status-after.txt": git(root, *status, "--", "docs/wiki"),
        "worktree-status-after.txt": git(root, *status),
        "wiki-diff.patch": git(root, "diff", "--binary", "HEAD", "--", "docs/wiki"),
        "sync.log": b"owning sync succeeded\n",
    }
    sha = git(root, "rev-parse", "HEAD").decode().strip()
    result = {
        "schema_version": "llm-wiki-convergence/v1", "candidate_sha": sha,
        "wiki_dir": "docs/wiki", "decision": "FAIL",
        "sync": {"exit_code": 0, "plugins_enabled": False, "started": True},
        "checks": {key: True for key in (
            "pre_sync_status_available", "pre_sync_wiki_clean", "pre_sync_worktree_clean",
            "post_sync_status_available", "post_sync_diff_available", "worktree_changes_scoped_to_wiki",
        )},
        "evidence": {},
    }
    for name, raw in captures.items():
        (destination / name).write_bytes(raw)
        result["evidence"][name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    (destination / "convergence-result.json").write_text(json.dumps(result))
    return sha, result


def test_complete_snapshot_retains_untracked_packs_without_publishing_private_files(source):
    root, wiki, evidence = source
    sha, result = evidence_for(root, evidence)
    before = git(root, "status", "--porcelain=v1")
    payload = snapshot.capture(root, evidence, sha, 123, 1)
    archive = evidence / payload["archive"]["filename"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == payload["archive"]["sha256"]
    with tarfile.open(archive) as bundle:
        assert set(bundle.getnames()) == {"index.md", "new.pack"}
        for row in payload["entries"]:
            stream = bundle.extractfile(row["path"])
            assert stream is not None
            with stream:
                raw = stream.read()
            assert raw == (wiki / row["path"]).read_bytes()
            assert len(raw) == row["bytes"]
            assert hashlib.sha256(raw).hexdigest() == row["sha256"]
    assert json.loads((evidence / "convergence-result.json").read_text()) == result
    assert git(root, "status", "--porcelain=v1") == before
    assert payload["workflow_run_id"] == 123 and payload["candidate_sha"] == sha


@pytest.mark.parametrize("change", ["none", "descriptor", "path"])
def test_distinct_windows_ctime_semantics_preserve_change_detection(source, monkeypatch, change):
    root, wiki, evidence = source
    sha, _ = evidence_for(root, evidence)
    original_fstat = snapshot.os.fstat
    calls = {}

    def descriptor_stat(fd):
        value = original_fstat(fd)
        key = (value.st_dev, value.st_ino)
        calls[key] = calls.get(key, 0) + 1
        attributes = {name: getattr(value, name) for name in (
            "st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns",
        )}
        # Model Windows descriptor metadata time, distinct from pathname birth
        # time, on every host. A genuine mutation must still be refused.
        attributes["st_ctime_ns"] += 1
        if calls[key] == 2 and change == "descriptor":
            attributes["st_ctime_ns"] += 1
        if calls[key] == 2 and change == "path":
            member = wiki / "index.md"
            member.write_bytes(member.read_bytes() + b"changed")
        return SimpleNamespace(**attributes)

    monkeypatch.setattr(snapshot, "PATH_DESCRIPTOR_CTIME_COMPARABLE", False)
    monkeypatch.setattr(snapshot.os, "fstat", descriptor_stat)
    if change == "none":
        assert snapshot.capture(root, evidence, sha, 123, 1)["entries"]
    else:
        with pytest.raises(ValueError, match="changed during capture"):
            snapshot.capture(root, evidence, sha, 123, 1)
        assert not (evidence / "wiki-review-snapshot.tar").exists()


@pytest.mark.parametrize("fault", ["source-change", "failed-sync", "changed-capture", "occupied", "size", "symlink", "wrong-candidate", "partial-evidence"])
def test_snapshot_refuses_unsafe_or_incomplete_observations(source, monkeypatch, fault):
    root, wiki, evidence = source
    if fault == "source-change":
        (root / "application.py").write_text("unrelated source change")
    if fault == "symlink":
        (wiki / "link").symlink_to(root / ".gitignore")
    sha, result = evidence_for(root, evidence)
    if fault == "wrong-candidate":
        sha = "0" * 40
    if fault == "partial-evidence":
        result["evidence"].pop("sync.log")
        (evidence / "convergence-result.json").write_text(json.dumps(result))
    if fault == "failed-sync":
        result["sync"]["exit_code"] = 1
        (evidence / "convergence-result.json").write_text(json.dumps(result))
    if fault == "changed-capture":
        (evidence / "sync.log").write_text("changed")
    if fault == "occupied":
        (evidence / "wiki-review-snapshot.tar").write_bytes(b"preserve occupied output")
    if fault == "size":
        monkeypatch.setattr(snapshot, "MAX_CONTENT_BYTES", 1)
    with pytest.raises(ValueError):
        snapshot.capture(root, evidence, sha, 123, 1)
    assert not (evidence / "wiki-review-snapshot.json").exists()
    if fault == "occupied":
        assert (evidence / "wiki-review-snapshot.tar").read_bytes() == b"preserve occupied output"
