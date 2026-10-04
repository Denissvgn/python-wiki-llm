"""Current adapters exercise immutable source and scope transition inputs."""

from __future__ import annotations

import json
import sys
from unittest.mock import patch

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.implementation_evidence import select_implementation_comparison
from tests.developer_value.fixtures import materialize
from tests.developer_value.oracles import (
    apply_prose_mutation,
    apply_source_mutation,
    verify_corpus,
)


def _case(identity):
    return next(row for row in verify_corpus()["cases"] if row["id"] == identity)


def _prepare(tmp_path, monkeypatch, case):
    root = tmp_path / "owned"
    materialize(case["project"], root)
    monkeypatch.chdir(root)
    return root


def _tree(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and not p.name.endswith(".lock")
    }


def _sync(capsys):
    with patch.object(sys, "argv", [
        "llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki",
        "--jobs", "1", "--no-plugins", "--progress", "never",
    ]):
        cli.main()
    capsys.readouterr()


def _selected_default(selector):
    request = {
        "schema_version": "llm-wiki-task-request/v2",
        "requirements": [{"id": "contract", "facet": "source-contract", "selector": selector}],
        "options": {"knowledge_mode": "off"},
    }
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    assert result.ok
    payload = api.validate_task_context(result.rendered, request)
    contract = payload["facts"][0]["observation"]["contract"]
    return next(param["default"] for param in contract["params"] if param["name"] == "limit")


@pytest.mark.parametrize("identity", ["L01", "L02", "L03", "L04", "L05", "S04"])
def test_frozen_mutation_uses_current_independent_implementation_comparison(
    tmp_path, monkeypatch, capsys, identity
):
    case = _case(identity)
    root = _prepare(tmp_path, monkeypatch, case)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    before_service = api.build_documentation_query_service("src", wiki_dir="wiki")
    assert before_service.knowledge_view is not None
    before_report = before_service.knowledge_view.implementation_report
    assert before_report is not None
    assert select_implementation_comparison(before_report, case["selector"]).state == "unchanged"
    if identity == "L02":
        assert _selected_default(case["selector"]) == case["expected"]["before"]["default"]
    apply_source_mutation(case, root / "src")
    bytes_before = _tree(root / "src"), _tree(root / "wiki")
    service = api.build_documentation_query_service("src", wiki_dir="wiki")
    assert service.knowledge_view is not None
    report = service.knowledge_view.implementation_report
    assert report is not None
    selected = select_implementation_comparison(report, case["selector"])
    expected = case["expected"]["after"]
    assert selected.state == expected.get("implementation", expected.get("selected_implementation"))
    assert selected.live_comparison_performed and selected.source_changed is True
    assert "dependencies-and-runtime-behavior-not-evaluated" in selected.limitations
    if "documentation" in expected:
        assert selected.documentation_changed is True
    if identity == "L02":
        assert _selected_default(case["selector"]) == expected["default"]
        inspected = api.inspect_concept("entities/Batch.md", src_dir="src", wiki_dir="wiki", live=True)
        concept = inspected["concept"]["concept"]
        assert concept is not None
        assert concept["freshness"]["state"] == "source-changed"
    if identity == "L04":
        assert select_implementation_comparison(report, "scope.py:Repeated.touch#2").state == "changed"
    if identity == "S04":
        assert select_implementation_comparison(report, "llm-wiki://modules/store").state == "changed"
    assert (_tree(root / "src"), _tree(root / "wiki")) == bytes_before


def test_frozen_source_only_request_keeps_behavior_gap_and_truthful_budget_failure(
    tmp_path, monkeypatch
):
    case = _case("L08")
    root = _prepare(tmp_path, monkeypatch, case)
    before = _tree(root)
    request = case["request"]
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    assert result.ok
    payload = api.validate_task_context(result.rendered, request)
    assert payload["basis"]["paths"] == case["expected"]["before"]["paths"]
    assert payload["storage"]["status"] == "off"
    rows = {row["requirement_id"]: row for row in payload["coverage"]}
    assert rows["contract"]["state"] == "present"
    assert rows["behavior"]["state"] == "unsupported" and not rows["behavior"]["satisfied"]
    limited = api.build_task_context(case["observation_steps"][1]["request"], src_dir="src", wiki_dir="wiki")
    assert not limited.ok and limited.error == "cannot-fit" and limited.rendered == ""
    assert "facts" not in limited.to_payload()
    assert not (root / "wiki").exists() and _tree(root) == before


def test_frozen_large_selected_and_bounded_reads_do_not_claim_runtime_completeness(
    tmp_path, monkeypatch
):
    case = _case("G01")
    root = _prepare(tmp_path, monkeypatch, case)
    before = _tree(root)
    selected = api.build_task_context(case["request"], src_dir="src", wiki_dir="wiki")
    assert selected.ok
    payload = api.validate_task_context(selected.rendered, case["request"])
    assert payload["work"]["source_files"] == 1
    assert payload["basis"]["paths"] == ["parts/part_005.py"]
    policy = api.WorkflowPolicy(**case["host_policy"])
    bounded = api.build_task_context(case["bounded_request"], src_dir="src", wiki_dir="wiki", policy=policy)
    assert bounded.ok
    current = api.validate_task_context(bounded.rendered, case["bounded_request"], policy=policy)
    assert current["work"]["source_files"] == 102
    assert current["basis"]["scope"] == "full-inventory"
    assert current["coverage"][0]["state"] == "partial" and not current["coverage"][0]["satisfied"]
    fact = next(row for row in current["facts"] if row["facet"] == "callees")
    assert fact["qualification"]["negative_claim_supported"] is False
    assert fact["qualification"]["graph_completeness"] == "static-observations-only"
    assert fact["observation"]["bounds"]["callees"] == {
        "total": 3, "returned": 1, "truncated": True,
    }
    assert fact["observation"]["bounds"]["matches"] == {
        "total": 1, "returned": 1, "truncated": False,
    }
    assert fact["observation"]["truncated"] is True
    assert fact["observation"]["coverage"]["runtime_completeness"] is False
    assert _tree(root) == before


def test_frozen_session_source_edit_matches_cold_result_without_stale_render_reuse(
    tmp_path, monkeypatch
):
    case = _case("G02")
    root = _prepare(tmp_path, monkeypatch, case)
    request = case["observation_steps"][0]["request"]
    session = api.open_context_session(src_dir="src", wiki_dir="wiki")
    try:
        first = session.read(request)
        assert first.state == "full" and first.context is not None
        apply_source_mutation(case, root / "src")
        before = _tree(root)
        second = session.read(request, if_result_id=first.result_id)
        cold = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
        assert second.context is not None and second.context.ok and cold.ok
        assert first.result_id != second.result_id
        assert second.context.to_payload() == cold.to_payload()
        assert second.metadata()["reuse"]["rendering"] is False
        assert _tree(root) == before
    finally:
        session.close()


def test_frozen_authored_noop_keeps_complete_committed_generation_idempotent(
    tmp_path, monkeypatch, capsys
):
    case = _case("G03")
    root = _prepare(tmp_path, monkeypatch, case)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    _sync(capsys)
    apply_prose_mutation(case, root / "wiki")
    _sync(capsys)
    first = _tree(root / "wiki")
    inspected = api.inspect_concept(case["selector"], src_dir="src", wiki_dir="wiki", live=True)
    assert inspected["coverage"]["availability"] == "ready"
    assert inspected["concept"]["found"]
    _sync(capsys)
    assert _tree(root / "wiki") == first
    assert case["mutation"]["after"].strip() in (root / "wiki" / case["mutation"]["path"]).read_text()
    assert json.loads((root / "wiki/.llm-wiki-manifest.json").read_bytes())["version"] >= 5
