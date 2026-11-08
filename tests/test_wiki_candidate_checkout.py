"""Candidate CI binds the source tree, sibling target and PR review records."""

import json
from pathlib import Path
import runpy
import subprocess

import pytest


ACTION = Path(__file__).resolve().parents[1] / "integrations/wiki-candidate"
checkout = runpy.run_path(str(ACTION / "checkout.py"))
verify = checkout["verified_checkout"]
target_revision = checkout["verified_target"]


def git(root, *args):
    return subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            *args,
        ],
        text=True,
    ).strip()


def repository(root):
    root.mkdir()
    git(root, "init", "-q")
    (root / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    (root / "Home.md").write_text("# Home\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-qm", "Initial source")
    return git(root, "rev-parse", "HEAD")


def test_source_and_separate_target_have_independent_verified_revisions(tmp_path):
    root = tmp_path / "consumer"
    head = repository(root)
    target = root / "wiki"
    repository(target)
    (target / "Home.md").write_text("# Target\n", encoding="utf-8")
    git(target, "commit", "-qam", "Wiki target")
    pin = git(target, "rev-parse", "HEAD")
    assert verify(root, head, "wiki", {}) == head
    assert target_revision(root, "wiki", "") == pin
    with pytest.raises(ValueError, match="target-revision"):
        target_revision(root, "wiki", head)
    with pytest.raises(ValueError, match="source-revision"):
        verify(root, pin, "wiki", {})
    (target / "Home.md").write_text("uncommitted", encoding="utf-8")
    with pytest.raises(ValueError, match="checked-out commit"):
        target_revision(root, "wiki", pin)


@pytest.mark.parametrize("kind", ["modified", "staged", "untracked", "ignored"])
def test_dirty_consumer_cannot_be_labelled_with_a_commit_id(tmp_path, kind):
    root = tmp_path / "consumer"
    head = repository(root)
    path = (
        root
        / {
            "modified": "Home.md",
            "staged": "Home.md",
            "untracked": "new.md",
            "ignored": "ignored/Home.md",
        }[kind]
    )
    path.parent.mkdir(exist_ok=True)
    path.write_text("changed", encoding="utf-8")
    if kind == "staged":
        git(root, "add", "Home.md")
    with pytest.raises(ValueError):
        verify(root, head, "", {})


def test_pr_uses_the_accepted_blob_from_the_base_in_a_monorepo(tmp_path, monkeypatch):
    root = tmp_path / "project"
    repository(root)
    consumer = root / "package"
    consumer.mkdir()
    record = consumer / "accepted.json"
    record.write_bytes(b'{"records":[]}\n')
    git(root, "add", "package")
    git(root, "commit", "-qm", "Accepted record")
    base = git(root, "rev-parse", "HEAD")
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps({"pull_request": {"base": {"sha": base}}}), encoding="utf-8"
    )
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    (consumer / "Home.md").write_text("proposal", encoding="utf-8")
    git(root, "add", "package")
    git(root, "commit", "-qm", "PR content")
    record.write_bytes(b'{"records":["proposal"]}\n')
    git(root, "commit", "-qam", "Proposed decision")
    head = git(root, "rev-parse", "HEAD")
    accepted = {"reviews": "accepted.json"}
    assert verify(consumer, "", "", accepted) == head
    runtime = tmp_path / "runtime"
    (runtime / "evidence").mkdir(parents=True)
    read = checkout["accepted_inputs"]
    with pytest.raises(ValueError, match="base commit"):
        read(consumer, accepted, head, runtime)
    paths, pin = read(consumer, accepted, "", runtime)
    assert pin == base
    assert Path(paths["reviews"]).read_bytes() == b'{"records":[]}\n'
    manifest = json.loads((runtime / "evidence/accepted-state.json").read_bytes())
    assert manifest["files"]["reviews"]["path"] == "package/accepted.json"
    missing = tmp_path / "missing"
    missing.mkdir()
    with pytest.raises(ValueError, match="regular file"):
        read(consumer, {"reviews": "Home.md"}, "", missing)


def test_materialized_reviews_still_protect_the_original_public_target(tmp_path):
    root = tmp_path / "consumer"
    repository(root)
    repository(root / "target")
    with pytest.raises(ValueError, match="outside the public target"):
        verify(root, "", "target", {"reviews": "target/records.json"})
