"""Verify the read-only Actions candidate against an independent consumer checkout."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

import pytest
import yaml

from llm_wiki_cli import api


ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT / "integrations/wiki-candidate"


def _git(repo, *arguments):
    return subprocess.check_output(["git", "-C", str(repo), *arguments], text=True).strip()


def _run_steps(consumer, env, *, candidate_exit):
    for mode in ("toolchains", "candidate"):
        result = subprocess.run(
            [sys.executable, "-B", "-I", str(ACTION / "run.py"), mode],
            cwd=consumer, env=env, capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == (candidate_exit if mode == "candidate" else 0), result.stderr


def test_action_uses_pinned_dependencies_and_installed_interpreter():
    action = yaml.safe_load((ACTION / "action.yml").read_bytes())
    steps = action["runs"]["steps"]
    assert set(action["outputs"]) == {
        "candidate-dir", "receipt-path", "report-path", "diff-path",
        "provider-receipt", "changed", "ready", "artifact-id", "receipt-id",
    }
    assert steps[0]["uses"].startswith("actions/setup-python@")
    assert len(steps[0]["uses"].split("@")[1]) == 40
    assert steps[-1]["uses"].startswith("actions/upload-artifact@")
    assert len(steps[-1]["uses"].split("@")[1]) == 40
    assert "always()" in steps[-1]["if"]
    for step in steps[1:-1]:
        assert '-I "${GITHUB_ACTION_PATH}/' in step["run"]
        assert "${{" not in step["run"]


@pytest.mark.parametrize("case", ["pending", "required", "broken"])
def test_python_only_foreign_consumer_retains_exact_candidate_for_review(tmp_path, case):
    consumer = tmp_path / "foreign consumer"
    shutil.copytree(ROOT / "examples/sibling-wiki", consumer, ignore=shutil.ignore_patterns("reports", "__pycache__"))
    manual = consumer / "sibling-wiki/.well-known"
    manual.mkdir()
    (manual / "empty").write_bytes(b"")
    # A consumer package sharing the provider's name must never be imported.
    shadow = consumer / "llm_wiki_cli"
    shadow.mkdir()
    (shadow / "__init__.py").write_text("raise RuntimeError('wrong provider')\n", encoding="utf-8")
    if case == "broken":
        with (consumer / "docs/Home.md").open("a", encoding="utf-8") as page:
            page.write("\n[[Absent-page]]\n")
    _git(consumer, "init", "-q")
    _git(consumer, "-c", "core.autocrlf=false", "add", "-A")
    _git(consumer, "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-qm", "consumer")
    revision = _git(consumer, "rev-parse", "HEAD")
    runtime = tmp_path / "action runtime"
    evidence = runtime / "evidence"
    evidence.mkdir(parents=True)
    output = tmp_path / "outputs"
    env = {
        **os.environ, "GITHUB_OUTPUT": str(output), "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
        "GITHUB_EVENT_NAME": "push", "GITHUB_WORKSPACE": str(tmp_path), "GITHUB_SHA": revision,
        "PYTHONPATH": str(consumer), "WIKI_CONSUMER": str(consumer), "WIKI_RUNTIME": str(runtime),
        "INPUT_CONFIG": ".llm-wiki/publication.json", "INPUT_SRC_DIR": ".",
        "INPUT_TARGET_DIR": "sibling-wiki", "INPUT_SOURCE_REVISION": revision,
        "INPUT_FAIL_ON": "review-required" if case == "required" else "error",
    }
    _run_steps(consumer, env, candidate_exit=0 if case == "pending" else 1)
    assert _git(consumer, "status", "--porcelain") == ""
    assert json.loads((evidence / "helper-plan.json").read_bytes())["languages"] == []
    assert json.loads((evidence / "helpers.json").read_bytes()) == {}
    assert output.is_file(), {path.name: path.read_text(encoding="utf-8") for path in evidence.glob("*.log")}
    values = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines())
    receipt = json.loads(Path(values["receipt-path"]).read_bytes())
    assert receipt["context"]["source_revision"] == revision
    assert receipt["checks"]["ok"] is (case != "broken")
    assert receipt["ready"] is False and values["ready"] == "false" and values["changed"] == "true"
    assert json.loads(Path(values["report-path"]).read_bytes()) == receipt["impact"]
    assert "adopt Accounts.md" in Path(values["diff-path"]).read_text(encoding="utf-8")
    with ZipFile(evidence / "candidate.zip") as archive:
        archived = {name: archive.read(name) for name in archive.namelist()}
        assert archived[".well-known/empty"] == b""
        assert {name: "sha256:" + hashlib.sha256(raw).hexdigest()
                for name, raw in archived.items()} == receipt["files"]
        assert all((Path(values["candidate-dir"]) / name).read_bytes() == raw for name, raw in archived.items())
    if case != "pending":
        diagnostic = (evidence / "error.txt").read_text(encoding="utf-8")
        assert ("approval" if case == "required" else "structural") in diagnostic
        return

    # A reviewer accepts the exact earlier source in a later commit. Checking
    # that original source must bind the new records without changing the ID.
    approval = api.review_publication_candidate(receipt, reviewer="alice", reason="Reviewed public diff")
    ledger = None
    for finding in receipt["impact"]["findings"]:
        if finding["kind"] == "topic":
            ledger = api.resolve_publication_finding(
                receipt["impact"], receipt["basis"], finding_id=finding["id"],
                reviewer="alice", reason="Reviewed public topic", reviews=ledger,
            )
    for name, record in (("topics", ledger), ("approval", approval)):
        (consumer / f".llm-wiki/{name}.json").write_text(json.dumps(record), encoding="utf-8")
    _git(consumer, "add", "--", ".llm-wiki/topics.json", ".llm-wiki/approval.json")
    _git(consumer, "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-qm", "accept")
    accepted = _git(consumer, "rev-parse", "HEAD")
    _git(consumer, "switch", "--detach", revision)
    later = tmp_path / "reviewed runtime"
    (later / "evidence").mkdir(parents=True)
    env.update(WIKI_RUNTIME=str(later), INPUT_REVIEWS=".llm-wiki/topics.json",
               INPUT_CANDIDATE_REVIEW=".llm-wiki/approval.json", INPUT_ACCEPTED_STATE_REVISION=accepted,
               INPUT_FAIL_ON="review-required", GITHUB_EVENT_NAME="workflow_dispatch")
    _run_steps(consumer, env, candidate_exit=0)
    checked = json.loads((later / "evidence/receipt.json").read_bytes())
    assert checked["ready"] and checked["candidate_id"] == receipt["candidate_id"]


def test_remote_provider_requires_an_immutable_revision(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("candidate_action_provider", ACTION / "provider.py")
    assert spec is not None and spec.loader is not None
    provider = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(provider)
    monkeypatch.setenv("PROVIDER_ACTION_REF", "main")
    monkeypatch.setenv("PROVIDER_REPOSITORY", "example/provider")
    with pytest.raises(ValueError, match="immutable"):
        provider.build_input(ROOT, tmp_path)


@pytest.mark.parametrize("mutation", ["none", "changed-code", "missing-data"])
def test_provider_attestation_checks_installed_code_and_package_data(tmp_path, mutation):
    from tests.test_wiki_impact_action import _installed_fixture

    python, source, expected, installed, _, consumer = _installed_fixture(tmp_path)
    (source / "pyproject.toml").write_text(
        '[project]\nversion="1.0.0"\n[tool.setuptools.package-data]\nllm_wiki_cli=["py.typed"]\n',
        encoding="utf-8",
    )
    (expected / "py.typed").touch()
    if mutation != "missing-data":
        (installed / "py.typed").touch()
    if mutation == "changed-code":
        (installed / "cli.py").write_text("# Different code at the same version\n", encoding="utf-8")
    parser = installed.parent / "markdown_it_py-4.0.0.dist-info"
    parser.mkdir()
    (parser / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: markdown-it-py\nVersion: 4.0.0\n", encoding="utf-8"
    )
    shadow = consumer / "llm_wiki_cli"
    shadow.mkdir()
    (shadow / "__init__.py").write_text("raise RuntimeError('wrong provider')\n", encoding="utf-8")
    receipt = tmp_path / "provider.json"
    ref = "b" * 40
    result = subprocess.run(
        [str(python), "-I", str(ACTION / "provider.py"), "verify", str(source),
         str(receipt), ref, "example/provider"],
        env={**os.environ, "PYTHONPATH": str(consumer)}, cwd=consumer,
        capture_output=True, text=True, timeout=30,
    )
    if mutation != "none":
        assert result.returncode != 0 and not receipt.exists()
        return
    assert result.returncode == 0, result.stderr
    attestation = json.loads(receipt.read_bytes())
    assert attestation["action_ref"] == attestation["provider_revision"] == ref
    assert attestation["parser_version"] == "4.0.0" and Path(attestation["package_origin"]) == installed
