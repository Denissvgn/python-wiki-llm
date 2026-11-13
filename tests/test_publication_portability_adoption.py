"""Consumer journeys for a managed native wiki and an independent manual sibling."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tests.test_wiki_delivery_transport import commit, create, git, head


ROOT = Path(__file__).resolve().parents[1]
CONFIG = "policy files/sibling.json"
SOURCE = "packages/service"
NATIVE = "architecture/Team Wiki"
TARGET = "snapshots/Manual Wiki"
CANONICAL = "public docs/Home.md"


@pytest.fixture(autouse=True)
def local_only(monkeypatch):
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    monkeypatch.setenv("PIP_NO_INDEX", "1")


def _provider(directory, *args, ok=True, script=None):
    command = [sys.executable, "-B", "-I"]
    command += [str(script)] if script else ["-m", "llm_wiki_cli.cli"]
    result = subprocess.run(
        [*command, *map(str, args)], cwd=directory, capture_output=True, timeout=120
    )
    if ok:
        assert result.returncode == 0, (result.stderr, result.stdout)
    else:
        assert result.returncode != 0, result.stdout
    return result


def _policy(consumer, *, native, manual):
    topic = {
        "id": "service.home",
        "owner": "service-team",
        "wiki_page": "Home.md",
        "edit_at": "wiki" if manual else "repository",
        "depends_on": [{"architecture_page": "modules/service.md"}],
    }
    policy = {
        "schema_version": "llm-wiki-publication/v1",
        "architecture": {
            "baseline": "existing-wiki" if native else "bootstrap-source",
            "root": NATIVE if native else SOURCE,
        },
        "target": {"kind": "github-wiki", "repository": "self"},
        "enforcement": "advisory",
        "publish": False,
        "topics": [topic],
        "exclusions": [
            {"pattern": "*", "reason": "Only the service homepage participates."}
        ],
    }
    if not manual:
        topic["source_document"] = CANONICAL
        policy["content"] = {"root": "public docs"}
    path = consumer / CONFIG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(policy), encoding="utf-8")
    return policy


def _source(consumer):
    source = consumer / SOURCE / "service.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"class Service:\n    pass\n")
    return source


def _files(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def _bootstrap(consumer, wiki_dir):
    _provider(
        consumer,
        "bootstrap",
        "--src-dir",
        SOURCE,
        "--wiki-dir",
        wiki_dir,
        "--source-adapter",
        "--helper-preparation",
        "never",
    )


@pytest.mark.parametrize("retire_member", [False, True], ids=["modified", "retired"])
def test_managed_native_wiki_custom_paths_stale_evidence_and_recovery(
    tmp_path, retire_member
):
    consumer = tmp_path / "monorepo" / "Service guide"
    source = _source(consumer)
    canonical = consumer / CANONICAL
    canonical.parent.mkdir()
    canonical.write_bytes(b"# Service\n\nOperate the managed service.\n")
    policy = _policy(consumer, native=True, manual=False)
    _bootstrap(consumer, NATIVE)
    evidence = tmp_path / "run evidence"
    evidence.mkdir()
    prepare = ROOT / "integrations/wiki-candidate/prepare.py"
    options = [consumer, CONFIG, SOURCE, evidence, tmp_path / "empty helper cache"]
    native = consumer / NATIVE
    original = _files(native)
    _provider(tmp_path, "toolchains", *options, script=prepare)
    _provider(tmp_path, "check", *options, script=prepare)
    assert json.loads((evidence / "native-freshness.json").read_bytes())["current"]
    output = tmp_path / "outside consumer" / "candidate"
    receipt = tmp_path / "receipt.json"
    inputs = ["--consumer-root", consumer, "--config", CONFIG, "--receipt", receipt]
    first = json.loads(
        _provider(
            tmp_path, "docs", "wiki", "export", *inputs, "--output-dir", output
        ).stdout
    )
    assert first["checks"]["ok"] and not first["delivery_ready"]
    assert (output / "Home.md").read_bytes() == canonical.read_bytes()
    checked = json.loads(
        _provider(
            tmp_path, "docs", "wiki", "check", *inputs, "--candidate-dir", output
        ).stdout
    )
    assert checked == first
    assert _files(native) == original

    source.write_bytes(
        b"class ReplacementService:\n    pass\n"
        if retire_member
        else b"class Service:\n    def start(self):\n        return 'ready'\n"
    )
    failure = _provider(tmp_path, "check", *options, script=prepare, ok=False)
    assert b"Native wiki" in failure.stderr
    assert _files(native) == original
    _provider(
        consumer,
        "sync",
        "--src-dir",
        SOURCE,
        "--wiki-dir",
        NATIVE,
        "--no-cache",
        "--no-plugins",
        "--helper-preparation",
        "never",
    )
    if retire_member:
        history = _files(native)
        health = json.loads(_provider(
            consumer, "doctor", "--strict", "--src-dir", SOURCE,
            "--wiki-dir", NATIVE, "--format", "json", "--report-schema", "v4",
            "--comparison-policy", "analysis-v1", "--helper-preparation", "never",
        ).stdout)
        assert health["status"] == "healthy"
        blocked = _provider(tmp_path, "check", *options, script=prepare, ok=False)
        assert b"retained source history" in blocked.stderr
        freshness = json.loads((evidence / "native-freshness.json").read_bytes())
        assert not freshness["current"]
        assert freshness["retained_source_pages"] == ["entities/Service.md"]

        new_root = "architecture/Current Wiki"
        _bootstrap(consumer, new_root)
        policy["architecture"]["root"] = new_root
        (consumer / CONFIG).write_text(json.dumps(policy), encoding="utf-8")
        _provider(tmp_path, "toolchains", *options, script=prepare)
        assert _files(native) == history
    _provider(tmp_path, "check", *options, script=prepare)
    assert json.loads((evidence / "native-freshness.json").read_bytes())["current"]
    stale = _provider(
        tmp_path, "docs", "wiki", "check", *inputs, "--candidate-dir", output, ok=False
    )
    assert b"changed" in stale.stderr
    refreshed = json.loads(
        _provider(
            tmp_path,
            "docs",
            "wiki",
            "export",
            *inputs,
            "--output-dir",
            tmp_path / "new candidate",
        ).stdout
    )
    assert (
        refreshed["candidate_id"] != first["candidate_id"] and refreshed["checks"]["ok"]
    )


@pytest.mark.parametrize(
    ("source_branch", "wiki_branch"), [("main", "master"), ("master", "main")]
)
def test_manual_wiki_impact_then_explicit_adoption(
    tmp_path, source_branch, wiki_branch
):
    consumer = tmp_path / "consumer checkout"
    create(consumer, source_branch)
    _source(consumer)
    (consumer / ".gitignore").write_bytes(b"/snapshots/\n")
    _policy(consumer, native=False, manual=True)
    commit(consumer)
    wiki = consumer / TARGET
    wiki.parent.mkdir()
    create(wiki, wiki_branch)
    # Retain the byte-exact historical target across native checkout policies.
    (wiki / ".gitattributes").write_bytes(b"* -text\n")
    (wiki / "Home.md").write_bytes(b"# Service\r\n\r\nSee [[Notes]].\r\n")
    notes = "# Notes\r\n\r\nRésumé and handwritten guidance.\r\n".encode()
    (wiki / "Notes.md").write_bytes(notes)
    (wiki / "_Sidebar.md").write_bytes(b"[[Home]] | [[Notes]]\r\n")
    (wiki / "assets").mkdir()
    (wiki / "assets/manual.bin").write_bytes(b"\x00\xff\x0d\x0a")
    wiki_head = commit(wiki)
    source_head = head(consumer)
    bare_source = tmp_path / "pinned-source.git"
    bare_wiki = tmp_path / "pinned-wiki.git"
    for work, remote in ((consumer, bare_source), (wiki, bare_wiki)):
        git(
            tmp_path, "clone", "--quiet", "--bare", "--no-local", str(work), str(remote)
        )
    policy = json.loads((consumer / CONFIG).read_bytes())
    transport = importlib.import_module(
        "integrations.wiki-candidate.delivery.git_transport"
    )
    result = transport.qualify(
        policy=policy,
        source_repository="example/service",
        target_repository="example/service",
        source_revision=source_head,
        source_ref="refs/heads/" + source_branch,
        source_remote=bare_source,
        target_remote=bare_wiki,
    )
    assert (
        result["target_branch"] == wiki_branch
        and result["target_revision"] == wiki_head
    )
    assert result["write_verified"] is False

    original = _files(wiki)
    inputs = ["--consumer-root", consumer, "--config", CONFIG, "--target-dir", TARGET]
    report_file = tmp_path / "initial-impact.json"
    report = json.loads(
        _provider(tmp_path, "docs", "impact", *inputs, "--output", report_file).stdout
    )
    assert report["complete"] and report["review_required"]
    finding = next(f for f in report["findings"] if f["kind"] == "topic")
    ledger = tmp_path / "manual-ledger.json"
    _provider(
        tmp_path,
        "docs",
        "impact",
        "resolve",
        *inputs,
        "--report",
        report_file,
        "--finding",
        finding["id"],
        "--decision",
        "still-current",
        "--reviewer",
        "manual-maintainer",
        "--reason",
        "Checked the handwritten service page.",
        "--output",
        ledger,
    )
    reviewed = json.loads(
        _provider(tmp_path, "docs", "impact", *inputs, "--reviews", ledger).stdout
    )
    assert reviewed["ready"] and not reviewed["review_required"]
    assert _files(wiki) == original

    canonical = consumer / CANONICAL
    canonical.parent.mkdir()
    canonical.write_bytes(b"# Service\n\nCanonical service guide. See [[Notes]].\n")
    policy = _policy(consumer, native=False, manual=False)
    output = tmp_path / "public candidate"
    receipt = tmp_path / "candidate-receipt.json"
    export = [
        "docs",
        "wiki",
        "export",
        *inputs,
        "--output-dir",
        output,
        "--receipt",
        receipt,
    ]
    denied = _provider(tmp_path, *export, ok=False)
    assert b"adoption" in denied.stderr
    assert not output.exists() and not receipt.exists()
    policy["content"]["adoptions"] = [
        {
            "path": "Home.md",
            "expected_hash": "sha256:" + original["Home.md"],
            "reason": "Move the reviewed homepage into canonical documentation.",
        }
    ]
    (consumer / CONFIG).write_text(json.dumps(policy), encoding="utf-8")
    checked = json.loads(_provider(tmp_path, *export).stdout)
    assert checked["checks"]["ok"] and not checked["delivery_ready"]
    assert [(op["kind"], op["path"]) for op in checked["operations"]] == [
        ("adopt", "Home.md")
    ]
    expected = {
        **original,
        "Home.md": hashlib.sha256(canonical.read_bytes()).hexdigest(),
    }
    assert _files(output) == expected
    assert _files(wiki) == original
    assert head(wiki) == wiki_head == head(bare_wiki)
    assert head(bare_source) == source_head
