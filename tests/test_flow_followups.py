"""Independent flow segments and receiving contracts, frozen before implementation."""

from __future__ import annotations

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services.documentation_queries import DocumentationGraphQueryService
from llm_wiki_cli.services.extraction_service import InventoryResult
from llm_wiki_cli.services.source_snapshot import SourceSnapshot
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


def _project(tmp_path, shape="linear", count=10):
    if shape == "linear":
        text = '__all__ = ["f0"]\n' + "\n".join(
            f"def f{i}(value):\n    return "
            + (f"f{i + 1}(value)\n" if i + 1 < count else "value\n")
            for i in range(count)
        )
    elif shape == "wide":
        text = '__all__ = ["root"]\ndef root(value):\n' + "".join(
            f"    leaf{i}(value)\n" for i in range(count)
        ) + "\n".join(f"def leaf{i}(value):\n    return value\n" for i in range(count))
    elif shape == "branch":
        text = (
            '__all__ = ["root"]\ndef root(value):\n    left(value)\n    right(value)\n'
            'def left(value):\n    return shared(value)\n'
            'def right(value):\n    return shared(value)\n'
            'def shared(value):\n    return value\n'
        )
    else:
        text = (
            '__all__ = ["a"]\ndef a(value):\n    return b(value)\n'
            'def b(value):\n    return a(value)\n'
        )
    (tmp_path / "app.py").write_text(text, encoding="utf-8")
    return _service(tmp_path)


def _service(root, *, limit=20, source_selection=None):
    with pytest.MonkeyPatch.context() as patch:
        patch.chdir(root)
        return api.build_documentation_query_service(
            src_dir=".", wiki_dir="wiki", limit=limit,
            source_selection=source_selection,
        )


def _symbols(result):
    return [step["symbol"] for step in result["steps"]]


def test_existing_queries_clip_the_captured_analysis_and_do_not_recover_a_tail(tmp_path):
    service = _project(tmp_path, "wide", 20)
    flow = service.flow_for_entrypoint("root")
    detail = service.data_flow_for_entrypoint("root")
    assert len(flow["flow"]["steps"]) == 20  # response clips 21 existing rows
    assert len(detail["data_flow"]["steps"]) == 12  # upstream analyzer cap
    # The legacy query sorts its delivered records; it still cannot recreate
    # any upstream steps beyond root + leaf0..leaf10.
    assert {row["symbol"] for row in detail["data_flow"]["steps"]} == {
        "root", *[f"leaf{i}" for i in range(11)]
    }
    assert len(service.callees("app.py:root")["callees"]) == 20
    assert service.flow_for_entrypoint("app.py:leaf15")["found"] is False
    assert service.data_flow_for_entrypoint("app.py:leaf15")["found"] is False


def test_linear_depth_followup_recovers_the_exact_omitted_transitions(tmp_path):
    service = _project(tmp_path)
    result = service.flow_segment("app.py:f0")
    assert _symbols(result) == [f"f{i}" for i in range(7)]
    assert result["coverage"] == {
        "observed": 10, "eligible": 7, "returned": 7,
        "omitted_before": 0, "omitted_after": 0, "depth_omitted": 3,
        "depth_limit": 6, "step_limit": 12, "runtime_completeness": False,
    }
    request = result["steps"][-1]["follow_up"]["request"]
    assert request["value"] == "app.py:f6"
    assert request["basis"] == result["basis"]
    tail = service.flow_segment(request["value"], basis=request["basis"])
    assert _symbols(tail) == ["f6", "f7", "f8", "f9"]
    assert [(step["edge"]["from"]["symbol"], step["edge"]["to"]["symbol"])
            for step in tail["steps"][1:]] == [("f6", "f7"), ("f7", "f8"), ("f8", "f9")]
    assert tail["coverage"]["depth_omitted"] == 0
    assert result["truncated"] is True
    assert tail["truncated"] is False


def test_wide_segments_have_exact_order_counts_and_no_duplicate_rows(tmp_path):
    service = _project(tmp_path, "wide", 20)
    first = service.flow_segment("app.py:root")
    assert _symbols(first) == ["root", *[f"leaf{i}" for i in range(11)]]
    request = first["follow_up"]["request"]
    assert request["offset"] == 12
    second = service.flow_segment(request["value"], basis=request["basis"], offset=request["offset"])
    assert _symbols(second) == [f"leaf{i}" for i in range(11, 20)]
    assert first["coverage"]["omitted_after"] == 9
    assert second["coverage"]["omitted_before"] == 12
    assert second["coverage"]["omitted_after"] == 0
    assert first["coverage"]["observed"] == second["coverage"]["observed"] == 21
    assert second["follow_up"] == {"status": "unavailable", "reason": "no-more-rows-at-this-depth"}
    assert first["work"]["traversed_edges"] == second["work"]["traversed_edges"] == 20
    assert json.dumps(first, sort_keys=True) == json.dumps(service.flow_segment("app.py:root"), sort_keys=True)


@pytest.mark.parametrize("shape,owner,expected", [
    ("branch", "root", ["root", "left", "shared", "right", "shared"]),
    ("cycle", "a", ["a", "b", "a"]),
])
def test_branches_and_cycles_retain_the_existing_decycled_preorder(tmp_path, shape, owner, expected):
    service = _project(tmp_path, shape)
    result = service.flow_segment(f"app.py:{owner}")
    assert _symbols(result) == expected
    assert result["coverage"]["observed"] == len(expected)
    assert result["coverage"]["depth_omitted"] == 0
    assert result["truncated"] is False


def test_same_graph_source_edit_rejects_a_followup_on_fresh_capture(tmp_path):
    old = _project(tmp_path)
    first = old.flow_segment("app.py:f0")
    with (tmp_path / "app.py").open("a") as stream:
        stream.write("\n# Same call graph, different selected source bytes.\n")
    fresh = _service(tmp_path)
    assert fresh.call_edges == old.call_edges
    with pytest.raises(ValueError, match="basis"):
        fresh.flow_segment("app.py:f6", basis=first["basis"])
    assert old.flow_segment("app.py:f6", basis=first["basis"])["basis"] == first["basis"]


@pytest.mark.parametrize("change", ["producer", "selection", "generation", "options"])
def test_binding_cannot_cross_producer_selection_generation_or_traversal_options(tmp_path, change):
    old = _project(tmp_path)
    first = old.flow_segment("app.py:f0")
    fresh = _service(tmp_path, limit=1 if change == "options" else 20)
    receipt = fresh.inventory_result
    assert isinstance(receipt, InventoryResult)
    assert isinstance(receipt.source_snapshot, SourceSnapshot)
    if change == "producer":
        fresh.inventory_result = replace(receipt, analysis_components={"different-producer": {"version": "changed"}})
    elif change == "selection":
        fresh.inventory_result = replace(receipt, source_snapshot=replace(receipt.source_snapshot, only_files=frozenset({"app.py"})))
    elif change == "generation":
        fresh.inventory_result = replace(receipt, source_snapshot=replace(receipt.source_snapshot, gitignore_fingerprint="different-generation"))
    with pytest.raises(ValueError, match="basis"):
        fresh.flow_segment("app.py:f6", basis=first["basis"])


@pytest.mark.parametrize("offset,basis", [(1, None), (-1, None), (True, None), (0, "bad")])
def test_invalid_continuation_is_rejected(tmp_path, offset, basis):
    with pytest.raises(ValueError):
        _project(tmp_path).flow_segment("app.py:f0", offset=offset, basis=basis)


def test_missing_ambiguous_and_unbound_owners_do_not_invent_a_flow(tmp_path):
    service = _project(tmp_path)
    assert service.flow_segment("app.py:missing")["found"] is False
    with pytest.raises(ValueError, match="qualified"):
        service.flow_segment("f0")
    (tmp_path / "app.py").write_text("def same():\n    pass\ndef same():\n    pass\n")
    ambiguous = _service(tmp_path).flow_segment("app.py:same")
    assert ambiguous["found"] is False and ambiguous["ambiguous"] is True
    assert ambiguous["steps"] == []
    unbound = DocumentationGraphQueryService({"app.py": {"functions": [{"name": "run"}]}})
    result = unbound.flow_segment("app.py:run")
    assert result["steps"] == []
    assert result["follow_up"]["reason"] == "captured-source-and-producer-binding-unavailable"


def test_unresolved_calls_stay_uncertain_leaves(tmp_path):
    (tmp_path / "app.py").write_text('def run(callback):\n    callback()\n')
    result = _service(tmp_path).flow_segment("app.py:run")
    assert _symbols(result) == ["run", "callback"]
    assert result["steps"][1]["kind"] == "unresolved"
    assert "follow_up" not in result["steps"][1]
    assert result["coverage"]["runtime_completeness"] is False


def test_dispatcher_and_api_share_the_service_contract(tmp_path, monkeypatch):
    service = _project(tmp_path, "wide", 20)
    monkeypatch.setattr(api, "build_documentation_query_service", lambda *a, **k: service)
    direct = dict(api.flow_segment("app.py:root", service=service))
    dispatched = dict(api.query_documentation({"operation": "flow-segment", "value": "app.py:root", "allow_full_inventory": True}))
    assert dispatched["steps"] == direct["steps"]
    assert dispatched["basis"] == direct["basis"]
    assert dispatched["cost"] == {"scope": "full-inventory", "full_inventory_performed": True, "supplied_paths": 0}
    with pytest.raises(api.InvalidRequestError):
        api.query_documentation({"operation": "flow-segment", "value": "app.py:root"})


def test_transport_validation_precedes_workspace_access(monkeypatch):
    monkeypatch.setattr(api, "build_documentation_query_service", lambda *a, **k: pytest.fail("invalid request touched workspace"))
    for request in (
        {"value": "root"}, {"value": "../app.py:root"}, {"value": "app.py:root", "offset": 1},
        {"value": "app.py:root", "basis": "bad"}, {"value": "app.py:root", "offset": True},
        {"value": "app.py:\ud800"},
    ):
        with pytest.raises(api.InvalidRequestError):
            api.query_documentation({"operation": "flow-segment", "allow_full_inventory": True, **request})


def test_paging_and_byte_bounds_do_not_claim_missing_rows_are_complete(tmp_path):
    service = _project(tmp_path, "wide", 20)
    old = json.dumps((service.flows, service.data_flows, service.call_edges), sort_keys=True)
    small = _service(tmp_path, limit=1)
    first = small.flow_segment("app.py:root")
    assert _symbols(first) == ["root"]
    follow = first["follow_up"]["request"]
    second = small.flow_segment(follow["value"], basis=follow["basis"], offset=follow["offset"])
    assert _symbols(second) == ["leaf0"]
    end = small.flow_segment("app.py:root", basis=first["basis"], offset=21)
    assert end["steps"] == [] and end["coverage"]["omitted_before"] == 21
    with pytest.raises(ValueError, match="offset"):
        small.flow_segment("app.py:root", basis=first["basis"], offset=22)
    service.call_edges[0]["args"] = [{"kind": "literal", "value": "x" * 100_000}]
    oversized = service.flow_segment("app.py:root")
    assert _symbols(oversized) == ["root"]
    assert oversized["follow_up"]["reason"] == "step-delivery-byte-limit"
    assert oversized["coverage"]["omitted_after"] == 20
    assert oversized["truncated"] is True
    assert len(json.dumps(oversized).encode()) < 65536
    service.call_edges[0] = json.loads(old)[2][0]
    assert json.dumps((service.flows, service.data_flows, service.call_edges), sort_keys=True) == old


def test_cli_and_mcp_receive_the_same_pinned_graph_without_writes(tmp_path, monkeypatch, capsys):
    from llm_wiki_cli.commands import query_cmd
    from llm_wiki_cli.services.mcp_server import McpWikiService

    _project(tmp_path, "wide", 20)
    monkeypatch.chdir(tmp_path)
    request = {"operation": "flow-segment", "value": "app.py:root", "allow_full_inventory": True}
    (tmp_path / "request.json").write_text(json.dumps(request))
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    query_cmd.run(SimpleNamespace(request="request.json", src_dir=".", wiki_dir="wiki",
                                 helper_cache_dir=None, source_selection=None, allow_external_src=False, output=None))
    cli = json.loads(capsys.readouterr().out)
    mcp = McpWikiService(src_dir=".", wiki_dir="wiki").query_documentation(request)
    assert cli["steps"] == mcp["steps"]
    assert cli["basis"] == mcp["basis"]
    assert cli["cost"]["full_inventory_performed"] is True
    follow = cli["follow_up"]["request"]
    tail = McpWikiService(src_dir=".", wiki_dir="wiki").query_documentation(follow)
    assert _symbols(tail) == [f"leaf{i}" for i in range(11, 20)]
    after = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after


@pytest.mark.parametrize("shape,kind", [("linear", "truncated_flow"), ("wide", "step_limit")])
def test_limit_diagnostics_supply_a_valid_exact_owner_request(tmp_path, monkeypatch, shape, kind):
    from llm_wiki_cli.services import lint_service

    service = _project(tmp_path, shape, 20)
    wiki = tmp_path / "wiki"
    (wiki / "flows").mkdir(parents=True)
    entry = service.flows[0]["entry"]
    (wiki / "flows" / (entry["id"] + ".md")).write_text("# Flow\n")
    monkeypatch.setattr(lint_service, "get_entry_points", lambda *a, **k: [entry])
    report = lint_service.LintReport(str(wiki), str(tmp_path))
    lint_service._check_data_flow_diagnostics(report, wiki, service.inventory, str(tmp_path), include_plugins=False)
    finding = next(row for row in report.diagnostics if f": {kind} " in row.message)
    assert finding.target == entry["id"]
    assert isinstance(finding.hint, str)
    assert f'"value": "app.py:{entry["symbol"]}"' in finding.hint
    assert '"operation": "flow-segment"' in finding.hint
    assert "full inventory" in finding.hint


def test_repeated_queries_do_not_read_source_and_real_selection_changes_reject(tmp_path, monkeypatch):
    from pathlib import Path

    _project(tmp_path)
    profile = tmp_path / "selection.json"
    profile.write_text(json.dumps({"schema_version": "llm-wiki-source-selection/v1", "include": ["app.py"], "exclude": []}))
    old = _service(tmp_path)
    receipt = old.inventory_result
    assert isinstance(receipt, InventoryResult)
    old.inventory_result = replace(receipt, source_snapshot=build_source_snapshot(tmp_path, source_selection="selection.json"))
    first = old.flow_segment("app.py:f0")
    profile.write_text(json.dumps({"schema_version": "llm-wiki-source-selection/v1", "include": ["app.py", "not-present.py"], "exclude": []}))
    fresh = _service(tmp_path)
    receipt = fresh.inventory_result
    assert isinstance(receipt, InventoryResult)
    fresh.inventory_result = replace(receipt, source_snapshot=build_source_snapshot(tmp_path, source_selection="selection.json"))
    assert old.call_edges == fresh.call_edges
    with pytest.raises(ValueError, match="basis"):
        fresh.flow_segment("app.py:f6", basis=first["basis"])
    # The public route independently refuses an explicit selection without a
    # matching wiki manifest. Snapshot-model controls do not relax that guard.
    with pytest.raises(api.InvalidRequestError):
        _service(tmp_path, source_selection="selection.json")
    monkeypatch.setattr(Path, "read_bytes", lambda *a, **k: pytest.fail("query read a file"))
    monkeypatch.setattr(Path, "read_text", lambda *a, **k: pytest.fail("query read a file"))
    assert _symbols(old.flow_segment("app.py:f6", basis=first["basis"])) == ["f6", "f7", "f8", "f9"]


def test_copy_of_a_graph_in_another_source_root_cannot_receive_a_followup(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    old = _project(first)
    fresh = _project(second)
    assert old.call_edges == fresh.call_edges
    with pytest.raises(ValueError, match="basis"):
        fresh.flow_segment("app.py:f6", basis=old.flow_segment("app.py:f0")["basis"])


def test_query_implementation_change_also_rejects_the_old_binding(tmp_path):
    service = _project(tmp_path)
    first = service.flow_segment("app.py:f0")
    service.flow_query_binding = {"implementation": "different-query-producer"}
    with pytest.raises(ValueError, match="basis"):
        service.flow_segment("app.py:f6", basis=first["basis"])


def test_missing_optional_query_binding_preserves_legacy_queries(tmp_path, monkeypatch):
    from pathlib import Path

    _project(tmp_path)
    original = Path.read_bytes

    def unavailable(path):
        if path.name == "flow_followup.py":
            raise OSError("query source is unavailable")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", unavailable)
    service = _service(tmp_path)
    assert service.flow_for_entrypoint("f0")["found"] is True
    result = service.flow_segment("app.py:f0")
    assert result["steps"] == []
    assert result["follow_up"]["reason"] == "captured-source-and-producer-binding-unavailable"


def test_limit_diagnostic_discloses_a_missing_owner(tmp_path, monkeypatch):
    from llm_wiki_cli.services import lint_service

    service = _project(tmp_path, "wide", 20)
    wiki = tmp_path / "wiki"
    (wiki / "flows").mkdir(parents=True)
    entry = dict(service.flows[0]["entry"], file=None)
    (wiki / "flows" / (entry["id"] + ".md")).write_text("# Flow\n")
    monkeypatch.setattr(lint_service, "get_entry_points", lambda *a, **k: [entry])
    monkeypatch.setattr(lint_service, "analyze_data_flow", lambda *a, **k: {
        "gaps": [{"kind": "step_limit", "step": entry["symbol"], "target": "first 12 steps", "line": 0}]
    })
    report = lint_service.LintReport(str(wiki), str(tmp_path))
    lint_service._check_data_flow_diagnostics(report, wiki, service.inventory, str(tmp_path), include_plugins=False)
    assert report.diagnostics[0].target == entry["id"]
    assert "unavailable" in (report.diagnostics[0].hint or "")
