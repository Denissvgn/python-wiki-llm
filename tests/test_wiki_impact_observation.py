"""Read-only observations of a separately maintained Git wiki."""

import importlib
import json
from pathlib import Path

import pytest

from tests.test_wiki_delivery_transport import (
    commit,
    create,
    git,
    head,
    prepare,
    refresh_checkout,
    repos as repos,
    transport,
)


observation = importlib.import_module("integrations.wiki-impact.observe")
checkout = importlib.import_module("integrations.wiki-candidate.checkout")
CONFIG = ".llm-wiki/publication.json"


def observe(source):
    return observation.observe(
        source, repository="example/project", config=CONFIG, target_dir="wiki"
    )


def test_observe_delivered_checkpoint_and_manual_edits_without_writing(repos, tmp_path):
    source, options = repos
    target = source / "wiki"
    unmanaged = observe(source)
    assert unmanaged["status"] == "unmanaged"
    assert unmanaged["checkpoint_id"] is None and unmanaged["source_changed"] is None

    candidate = prepare(source, tmp_path)
    delivered = transport.deliver(**options, **candidate)
    refresh_checkout(target, options["target_remote"], "pages")
    current = observe(source)
    assert current["status"] == "unchanged" and current["source_changed"] is False
    assert current["checkpoint_revision"] == delivered["target_revision"]
    assert current["checkpoint_id"] == delivered["checkpoint"]["checkpoint_id"]

    (target / "Notes.md").write_bytes(b"# Manual edit\n")
    (target / "image.bin").write_bytes(b"\x00\x01\xff")
    git(target, "add", "Notes.md", "image.bin")
    git(target, "update-index", "--chmod=-x", "tool.txt")
    git(target, "commit", "-qm", "manual content and mode changes")
    manual = observe(source)
    assert manual["status"] == "unmanaged-edits" and not manual["owned_changes"]
    assert [entry["path"] for entry in manual["unmanaged_changes"]] == [
        "Notes.md",
        "image.bin",
        "tool.txt",
    ]
    assert manual["unmanaged_changes"][1]["before"] is None
    mode_change = manual["unmanaged_changes"][2]
    assert mode_change["before"]["blob"] == mode_change["after"]["blob"]
    assert (mode_change["before"]["mode"], mode_change["after"]["mode"]) == (
        "100755",
        "100644",
    )

    (target / "Home.md").unlink()
    tip = commit(target)
    (source / "project/app.py").write_bytes(b"value = 4\n")
    newer = commit(source)
    conflict = observe(source)
    assert conflict["status"] == "owned-conflict" and conflict["complete"]
    assert conflict["source_changed"] and conflict["source_revision"] == newer
    assert conflict["last_delivered_source"] == current["source_revision"]
    assert conflict["owned_changes"][0]["path"] == "Home.md"
    assert conflict["owned_changes"][0]["after"] is None
    assert conflict["target_revision"] == head(target) == tip
    assert head(options["target_remote"]) == delivered["target_revision"]
    assert git(target, "status", "--porcelain") == b""


def test_observer_keeps_a_deleted_checkpoint_and_shallow_history_indeterminate(
    repos, tmp_path, monkeypatch
):
    source, options = repos
    target = source / "wiki"
    transport.deliver(**options, **prepare(source, tmp_path))
    refresh_checkout(target, options["target_remote"], "pages")
    (target / transport.CHECKPOINT_PATH).unlink()
    tip = commit(target)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    for name, value in {
        "IMPACT_CONSUMER": source,
        "IMPACT_EVIDENCE": evidence,
        "GITHUB_REPOSITORY": "example/project",
        "INPUT_CONFIG": CONFIG,
        "INPUT_TARGET_DIR": "wiki",
        "GITHUB_OUTPUT": tmp_path / "output",
        "GITHUB_STEP_SUMMARY": tmp_path / "summary",
    }.items():
        monkeypatch.setenv(name, str(value))
    assert observation.main() == 1
    report = json.loads((evidence / "drift.json").read_bytes())
    assert report["status"] == "indeterminate" and not report["complete"]
    assert "removed" in report["error"] and head(target) == tip
    git(source, "clone", "--depth=1", target.as_uri(), "shallow")
    with pytest.raises(ValueError, match="full wiki history"):
        observation.observe(
            source, repository="example/project", config=CONFIG, target_dir="shallow"
        )


def test_absolute_impact_inputs_read_exact_blobs_even_with_shallow_pr_checkout(
    tmp_path, monkeypatch
):
    base = tmp_path / "accepted-state"
    create(base, "main")
    record = base / "approved.json"
    record.write_bytes(b'{"records": []}\n')
    accepted = commit(base)
    source = tmp_path / "source"
    create(source, "proposal")
    (source / "README.md").write_bytes(b"proposed content\n")
    commit(source)
    record.write_bytes(b"unaccepted worktree changes")
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps({"pull_request": {"base": {"sha": accepted}}}), encoding="utf-8"
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    runtime = tmp_path / "runtime"
    (runtime / "evidence").mkdir(parents=True)
    paths, pin = checkout.accepted_inputs(
        source, {"reviews": str(record)}, "", runtime, workspace=tmp_path
    )
    assert (
        pin == accepted and Path(paths["reviews"]).read_bytes() == b'{"records": []}\n'
    )
