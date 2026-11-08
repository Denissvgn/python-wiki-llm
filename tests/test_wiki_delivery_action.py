"""Verify the privileged handoff from trusted preparation to wiki Git delivery."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest
import yaml

from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from tests.test_publication_candidate import accept_topics
from tests.test_wiki_delivery_transport import commit, git, head, prepare
from tests.test_wiki_delivery_transport import repos as repos


ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT / "integrations/wiki-candidate"
publisher = importlib.import_module("integrations.wiki-candidate.delivery.publish")
retainer = importlib.import_module("integrations.wiki-candidate.run")


def test_workflow_is_opt_in_and_binds_successful_same_run_artifact():
    template = yaml.safe_load((ACTION / "delivery/workflow.yml.example").read_bytes())
    assert set(template.get(True, template.get("on"))) == {"workflow_dispatch"}
    assert template["concurrency"] == {
        "group": "wiki-delivery-${{ github.repository }}.wiki",
        "cancel-in-progress": False,
    }
    prep, write = template["jobs"]["prepare"], template["jobs"]["publisher"]
    assert write["needs"] == "prepare" and write["environment"] == "wiki-publisher"
    assert "needs.prepare.result == 'success'" in write["if"]
    assert "WIKI_GIT_TOKEN" not in json.dumps(prep)
    assert (
        write["steps"][-1]["with"]["artifact-id"]
        == "${{ needs.prepare.outputs.artifact }}"
    )
    assert (
        write["steps"][-1]["with"]["receipt-id"]
        == "${{ needs.prepare.outputs.receipt }}"
    )
    assert template["permissions"] == {"contents": "read"}
    steps = yaml.safe_load((ACTION / "delivery/action.yml").read_bytes())["runs"][
        "steps"
    ]
    download = next(
        step
        for step in steps
        if step.get("uses", "").startswith("actions/download-artifact@")
    )
    assert set(download["with"]) == {"artifact-ids", "path", "digest-mismatch"}
    assert download["with"]["digest-mismatch"] == "error"
    assert [s["id"] for s in steps if "wiki-token" in json.dumps(s)] == ["publish"]


@pytest.mark.parametrize(
    "event,protected",
    [
        ("pull_request", "true"),
        ("pull_request_target", "true"),
        ("workflow_run", "true"),
        ("workflow_dispatch", "false"),
    ],
)
def test_untrusted_workflow_context_is_rejected(monkeypatch, event, protected):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REF_PROTECTED", protected)
    monkeypatch.setenv("GITHUB_EVENT_NAME", event)
    with pytest.raises(ValueError, match="trusted|protected"):
        publisher.hosted_context("deliver")


def test_public_archive_never_accepts_extra_or_replaced_members(tmp_path):
    path = tmp_path / "candidate.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("../outside.md", b"unexpected")
    digest = sha256_bytes(path.read_bytes())
    receipt = {"files": {"Home.md": sha256_bytes(b"owned")}}
    with pytest.raises(ValueError, match="entry"):
        publisher.artifact_files(tmp_path, receipt, digest)
    with pytest.raises(ValueError, match="archive hash"):
        publisher.artifact_files(tmp_path, receipt, sha256_bytes(b"other"))
    assert not (tmp_path.parent / "outside.md").exists()


def test_protected_handoff_reads_source_and_approval_from_separate_commits(
    repos, tmp_path, monkeypatch
):
    source, remotes = repos
    prepared = prepare(source, tmp_path)
    receipt = prepared["receipt"]
    pin = head(source)
    fork = tmp_path / "approval"
    git(tmp_path, "clone", str(source), str(fork))
    approval = receipt["review"]["decision"]
    # Derive the ledger from the original pending report, just as the reviewer did.
    from llm_wiki_cli.services.publication_impact import compare_publication_impact

    pending = {**receipt, "impact": compare_publication_impact(receipt["basis"])}
    (fork / ".llm-wiki/approval.json").write_text(
        json.dumps(approval), encoding="utf-8"
    )
    (fork / ".llm-wiki/reviews.json").write_text(
        json.dumps(accept_topics(pending)), encoding="utf-8"
    )
    accepted = commit(fork)
    git(source, "fetch", str(fork), "HEAD:refs/remotes/origin/wiki-reviews")
    runtime = tmp_path / "publisher"
    incoming = runtime / "incoming"
    incoming.mkdir(parents=True)
    (runtime / "evidence").mkdir()
    retainer.retain(receipt, tmp_path / "candidate", source / "wiki", incoming)
    (incoming / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    provider = {
        "installed": True,
        "action_ref": "f" * 40,
        "action_repository": "owner/provider",
        "provider_revision": "f" * 40,
        "version": receipt["provider"]["version"],
        "parser_version": receipt["provider"]["parser_version"],
        "package_sha256": "b" * 64,
    }
    for destination in (incoming, runtime / "evidence"):
        (destination / "provider.json").write_text(
            json.dumps(provider), encoding="utf-8"
        )
    env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REF_PROTECTED": "true",
        "GITHUB_REPOSITORY": "example/project",
        "GITHUB_REF": "refs/heads/primary",
        "GITHUB_SHA": pin,
        "GITHUB_RUN_ID": "123",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_OUTPUT": str(tmp_path / "outputs"),
        "ACTION_REVISION": "f" * 40,
        "ACTION_REPOSITORY": "owner/provider",
        "WIKI_RUNTIME": str(runtime),
        "WIKI_CONSUMER": str(source),
        "TARGET_REPOSITORY": "self",
        "WIKI_TOKEN": "fixture-only",
        "SOURCE_TOKEN": "",
        "OPERATION": "deliver",
        "CONFIG_PATH": ".llm-wiki/publication.json",
        "APPROVAL_BRANCH": "wiki-reviews",
        "EXPECTED_RECEIPT": receipt["receipt_id"],
        "CANDIDATE_REVIEW_PATH": ".llm-wiki/approval.json",
        "REVIEWS_PATH": ".llm-wiki/reviews.json",
        "PREVIOUS_RECEIPT_PATH": "",
        "BASELINE_PATH": "",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    handoff = {
        **publisher.hosted_context("deliver"),
        "schema_version": "llm-wiki-delivery-handoff/v1",
        "receipt_id": receipt["receipt_id"],
        "accepted_state_revision": accepted,
        "archive_hash": sha256_bytes((incoming / "candidate.zip").read_bytes()),
    }
    path = incoming / "delivery-handoff.json"
    path.write_text(json.dumps({**handoff, "run_attempt": "2"}), encoding="utf-8")
    with pytest.raises(ValueError, match="Handoff"):
        publisher.checked_artifact(
            incoming,
            runtime,
            publisher.hosted_context("deliver"),
            receipt["basis"]["config"],
            receipt["receipt_id"],
            accepted,
        )
    path.write_text(json.dumps(handoff), encoding="utf-8")

    def local_transport(operation):
        def invoke(**options):
            assert (
                options["target_remote"]
                == "https://github.com/example/project.wiki.git"
            )
            assert options["target_token"] == "fixture-only"
            options.update(
                source_remote=remotes["source_remote"],
                target_remote=remotes["target_remote"],
                source_token=None,
                target_token=None,
            )
            return operation(**options)

        return invoke

    for operation in ("deliver", "preview_rollback", "rollback"):
        implementation = getattr(publisher.git_transport, operation)
        monkeypatch.setattr(
            publisher.git_transport, operation, local_transport(implementation)
        )
    publisher.run()
    result = json.loads((runtime / "evidence/delivery-result.json").read_bytes())
    assert result["readback_verified"] and result["source_revision"] == pin
    assert head(remotes["target_remote"]) == result["target_revision"]

    def rollback_step(operation):
        step = tmp_path / operation
        (step / "evidence").mkdir(parents=True)
        monkeypatch.setenv("WIKI_RUNTIME", str(step))
        monkeypatch.setenv("WIKI_TOKEN", "fixture-only")
        monkeypatch.setenv("OPERATION", operation)
        publisher.run()
        return json.loads((step / "evidence/delivery-result.json").read_bytes())

    monkeypatch.setenv("TARGET_REVISION", result["target_revision"])
    monkeypatch.setenv("RESTORE_REVISION", receipt["context"]["target_revision"])
    proposal = rollback_step("plan-rollback")
    assert head(remotes["target_remote"]) == result["target_revision"]
    from llm_wiki_cli.services.publication_delivery import review_rollback

    record = review_rollback(
        proposal, reviewer="editor", reason="Restore reviewed text"
    )
    (fork / ".llm-wiki/rollback-review.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    commit(fork)
    git(source, "fetch", str(fork), "HEAD:refs/remotes/origin/wiki-reviews")
    monkeypatch.setenv("ROLLBACK_REVIEW_PATH", ".llm-wiki/rollback-review.json")
    restored = rollback_step("rollback")
    assert restored["readback_verified"] and restored["status"] == "rolled-back"
    assert head(remotes["target_remote"]) == restored["target_revision"]
    assert (
        git(remotes["target_remote"], "show", "HEAD:Home.md")
        == (source / "wiki/Home.md").read_bytes()
    )
