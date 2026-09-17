"""Independent expectations for drift, insufficient context and semantic limits."""

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from llm_wiki_cli import api


FIXTURES = Path(__file__).parent / "native_workflow/fixtures"


def materialize(tmp_path, monkeypatch, case):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    for path in (FIXTURES / case / "project").glob("*.py"):
        shutil.copy2(path, source / path.name)
    api.bootstrap_wiki("src", "wiki")
    return source, tmp_path / "wiki"


def request(facet="source-contract", selector="policy.py:limit", **options):
    return {"schema_version": "llm-wiki-task-request/v1", "requirements": [
        {"id": "required-fact", "facet": facet, "selector": selector}], **options}


def test_resume_after_source_and_authored_wiki_drift(tmp_path, monkeypatch):
    source, wiki = materialize(tmp_path, monkeypatch, "T08")
    req = request()
    with api.open_context_session(src_dir="src", wiki_dir="wiki") as session:
        previous = session.read(req)
        assert previous.context is not None
        packet = previous.context.to_payload()["packet"]
        raw_packet = (json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
        (source / "policy.py").write_text("def limit(value: int = 4) -> int:\n    return value\n")
        page = wiki / "modules/policy.md"
        page.write_text(page.read_text() + "\n## Rationale\nThe cap bounds repeated work.\n")
        assert api.validate_context_packet(raw_packet).valid
        current = session.read(req, if_result_id=previous.result_id)
        assert current.state == "full" and current.result_id != previous.result_id
        assert current.context is not None
        assert current.context.to_payload()["basis"] != previous.context.to_payload()["basis"]


def test_missing_required_contract_cannot_be_an_answerability_success(tmp_path, monkeypatch):
    materialize(tmp_path, monkeypatch, "T09")
    result = api.build_task_context(request(options={"read_scope": "snapshot"}), src_dir="src", wiki_dir="wiki")
    payload = result.to_payload()
    assert payload["facts"] == []
    assert not payload["coverage"][0]["satisfied"]
    assert payload["coverage"][0]["reason"] == "broader-scope-required"
    tiny = api.build_task_context(request(options={"budget_tokens": 1}), src_dir="src", wiki_dir="wiki")
    assert not tiny.ok and tiny.rendered == ""


def test_same_named_symbols_in_two_workspaces_keep_distinct_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = FIXTURES / "T10/project"
    for name, default in (("a", "3"), ("b", "9")):
        shutil.copytree(source / name, tmp_path / name)
        with api.open_context_session(src_dir=name, wiki_dir=f"wiki-{name}") as session:
            result = session.read(request())
            assert result.context is not None
            assert result.context.to_payload()["facts"][0]["observation"]["contract"]["params"][0]["default"] == default


def test_false_prose_with_current_structure_is_not_semantic_approval(tmp_path, monkeypatch):
    _, wiki = materialize(tmp_path, monkeypatch, "T11")
    page = wiki / "modules/policy.md"
    note = "The cap bounds repeated work. It also guarantees every remote write succeeds."
    page.write_text(page.read_text().replace("## Description\n", "## Description\n\n" + note + "\n"))
    refreshed = subprocess.run([sys.executable, "-m", "llm_wiki_cli.cli", "sync", "--src-dir", "src",
                               "--wiki-dir", "wiki", "--no-plugins"], capture_output=True, timeout=30)
    assert refreshed.returncode == 0, refreshed.stderr
    req = request("semantic-section", "modules/policy.md")
    payload = api.build_task_context(req, src_dir="src", wiki_dir="wiki").to_payload()
    assert payload["coverage"][0]["satisfied"]
    fact = payload["facts"][0]
    assert note in json.dumps(fact["observation"], ensure_ascii=False)
    assert fact["qualification"]["semantic_review"] == "not-evaluated"
    assert fact["qualification"]["behavior"] == "not-evaluated"
    assert fact["citations"][0]["path"] == "modules/policy.md"


def test_corrupt_required_native_artifact_is_not_repaired_or_an_empty_graph(tmp_path, monkeypatch):
    _, wiki = materialize(tmp_path, monkeypatch, "T12")
    artifact = wiki / ".llm-wiki-knowledge.json"
    artifact.write_text("{broken")
    before = {path.name: path.read_bytes() for path in wiki.glob(".llm-wiki-*.json")}
    req = request(options={"knowledge_mode": "required"})
    with pytest.raises(api.WorkspaceStateError) as error:
        api.build_task_context(req, src_dir="src", wiki_dir="wiki")
    assert error.value.code == "knowledge-required-unavailable"
    assert before == {path.name: path.read_bytes() for path in wiki.glob(".llm-wiki-*.json")}


def test_snapshot_typed_edges_retain_upstream_coverage_and_semantic_qualifiers(tmp_path, monkeypatch):
    source, _ = materialize(tmp_path, monkeypatch, "T11")
    (source / "caller.py").write_text("from policy import limit\n\ndef run():\n    return limit()\n")
    result = subprocess.run([sys.executable, "-m", "llm_wiki_cli.cli", "sync", "--src-dir", "src",
                             "--wiki-dir", "wiki", "--no-plugins"], capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    req = request("typed-relationships", "modules/policy.md")
    result = api.build_task_context(req, src_dir="src", wiki_dir="wiki")
    payload = api.validate_task_context(result.rendered, req)
    assert payload["coverage"][0]["satisfied"]
    observed = payload["facts"][0]["observation"]
    assert {edge["kind"] for edge in observed["edges"]} >= {"calls", "imports"}
    assert observed["typed_graph"]["coverage"]
    assert payload["facts"][0]["qualification"]["negative_claim_supported"] is False
