"""Exercise the source-only semantic handoff through the consumer CLI."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from llm_wiki_cli import cli
from tests.test_documentation_native_lifecycle import _agent_result


def test_reviewed_workspace_yields_an_applicable_patch_for_the_authored_page(
    tmp_path, monkeypatch, capsysbinary
):
    consumer = tmp_path / "consumer"
    example = Path(__file__).resolve().parents[1] / "examples" / "sibling-wiki"
    shutil.copytree(example, consumer, ignore=shutil.ignore_patterns("reports"))
    for key in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_ATTR_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    subprocess.run(
        ["git", "init", "-q", "--initial-branch=codex/source-review"],
        cwd=consumer,
        capture_output=True,
        check=True,
        timeout=30,
    )
    monkeypatch.chdir(consumer)
    workspace = tmp_path / "workspace"
    ws = ["--workspace", str(workspace)]
    receipt = tmp_path / "receipt.json"
    candidate = tmp_path / "candidate"
    inputs = ["--target-dir", "sibling-wiki", "--receipt", str(receipt)]
    scoped = [
        *inputs,
        "--candidate-dir",
        str(candidate),
        *ws,
        "--topic",
        "accounts.overview",
    ]
    source_document = "docs/Accounts.md"
    canonical = consumer / source_document
    original = canonical.read_bytes()
    new_text = (
        original
        + b"\nReview the account configuration before changing the account type.\n"
    )

    def invoke(*args):
        capsysbinary.readouterr()
        monkeypatch.setattr(sys, "argv", ["llm-wiki", "docs", *args])
        cli.main()
        return capsysbinary.readouterr().out

    invoke("wiki", "export", *inputs, "--output-dir", str(candidate))
    brief = tmp_path / "brief.md"
    brief.write_text("Maintain the public account guide.", encoding="utf-8")
    invoke(
        "prepare",
        *ws,
        "--baseline",
        "bootstrap-source",
        "--src-dir",
        "project",
        "--site-name",
        "Accounts",
        "--project-brief",
        str(brief),
        "--audience",
        "operator",
        "--audience-intent",
        "operator=manage accounts",
    )
    pending = json.loads(invoke("wiki", "maintain", *scoped))
    assert not pending["ready_for_repository_review"] and pending["next_actions"]
    editable = workspace / "mapped-docs" / source_document
    assert editable.read_bytes() == original
    with pytest.raises(SystemExit) as unavailable:
        invoke("wiki", "patch", *scoped, "--format", "patch")
    assert unavailable.value.code

    def packet(stage):
        return json.loads(invoke("packet", *ws, "--stage", stage, "--format", "json"))

    def record(stage, actor, payload):
        handoff = tmp_path / f"{stage}-handoff.json"
        handoff.write_text(json.dumps(payload), encoding="utf-8")
        invoke("record-result", *ws, "--actor", actor, "--result", str(handoff))

    first = packet("wiki-enrichment")
    run_id = first["run_id"]
    worklist = json.loads((workspace / first["worklist"]["path"]).read_bytes())
    evidence = sorted({item["canonical_path"] for item in worklist["items"]})
    record(
        "wiki-enrichment",
        "native-author",
        _agent_result(
            run_id,
            "wiki-enrichment",
            completed=[item["id"] for item in worklist["items"]],
            claims=evidence,
        ),
    )
    packet("user-docs")
    editable.write_bytes(new_text)
    author = _agent_result(run_id, "user-docs", claims=["modules/app.md"])
    author["changed_document_paths"] = [source_document]
    record("user-docs", "guide-author", author)
    packet("review")
    record(
        "review",
        "independent-editor",
        _agent_result(run_id, "review", claims=["modules/app.md"]),
    )
    assert json.loads(invoke("verify", *ws, "--format", "json"))["ok"]

    patch = invoke("wiki", "patch", *scoped, "--format", "patch")
    proposal = json.loads(invoke("wiki", "patch", *scoped))
    assert proposal["ready_for_repository_review"] and not proposal["delivery_ready"]
    assert proposal["patch"].encode("utf-8") == patch
    assert canonical.read_bytes() == original
    checked = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "--no-pager", "apply", "--check", "--verbose", "-"],
        input=patch, cwd=consumer, capture_output=True, timeout=30,
    )
    assert checked.returncode == 0, checked.stderr.decode("utf-8", errors="replace")
    repository = tmp_path / "review-copy"
    repository.mkdir()
    subprocess.run(
        ["git", "init", "-q", "--initial-branch=codex/monorepo-review"],
        cwd=repository, capture_output=True, check=True, timeout=30,
    )
    copy = repository / "packages" / "accounts"
    shutil.copytree(consumer, copy)
    applied = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "--no-pager", "apply", "--verbose", "--directory=packages/accounts", "-"],
        input=patch, cwd=repository, capture_output=True, timeout=30,
    )
    assert applied.returncode == 0, applied.stderr.decode("utf-8", errors="replace")
    assert (copy / source_document).read_bytes() == new_text

    editable.write_bytes(new_text + b"Changed after review.\n")
    with pytest.raises(SystemExit) as stale:
        invoke("wiki", "patch", *scoped, "--format", "patch")
    assert stale.value.code
    assert not capsysbinary.readouterr().out
    assert canonical.read_bytes() == original
