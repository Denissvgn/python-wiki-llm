"""Callable coverage remains distinct from evaluated static flow assembly."""
from __future__ import annotations

from copy import deepcopy

import pytest

from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services.bootstrap_runtime import _generate_flow_md
from llm_wiki_cli.services.data_flow import analyze_data_flow, analyze_data_flow_detailed, build_data_flow_context
from llm_wiki_cli.services.extraction_service import _data_flow_details_contract, _public_data_flow_coverage, build_extract_payload


def _flow(symbol="server", filepath: str | None = "inline.mjs"):
    entry = {"id": "http-" + symbol, "category": "http", "file": filepath, "symbol": symbol, "label": symbol}
    return {"entry": entry, "steps": [{"depth": 0, "file": filepath, "symbol": symbol, "kind": "entry"}],
            "modules_touched": [filepath], "truncated": False}


def _zero_coverage(filepath, symbols):
    return {"schema_version": "llm-wiki-data-effect-observations/v1", "callables": [
        {"file": filepath, "symbol": symbol, "coverage": {kind: {
            "observed": 0, "emitted": 0, "omitted": 0, "limit": 8, "truncated": False,
        } for kind in ("inputs", "reads", "writes", "returns", "boundary_effects")}}
        for symbol in symbols]}


def test_missing_inline_callable_is_unavailable_even_when_flow_assembly_is_evaluated():
    inventory = {"inline.mjs": {"language": "javascript", "functions": [], "classes": []}}
    flow = _flow()
    detailed = analyze_data_flow_detailed(inventory, flow, [])
    assert detailed["analysis"]["state"] == "unavailable"
    assert detailed["analysis"]["callables"] == {"available": 0, "unavailable": 1}
    assert detailed["steps"][0]["analysis"]["callable_record"] == "unavailable"
    assert "upstream-callable-record-unavailable" in detailed["analysis"]["limitations"]
    assert "upstream-effect-collector-totals-may-be-unavailable" in detailed["coverage"]["effects"]["limitations"]
    public = _data_flow_details_contract(deep=True, inventory=inventory, unsupported_sources={}, flows=[detailed])
    assert public["state"] == "evaluated" and public["flows"][0]["analysis"]["state"] == "unavailable"
    assert "upstream-callable-record-unavailable" in public["coverage"]["upstream_analyzer_limitations"]
    page = _generate_flow_md(flow, data_flow=analyze_data_flow(inventory, flow, []))
    assert "Callable record unavailable" in page
    assert "No static analysis gaps detected" not in page
    assert "No outbound calls were detected" not in page
    assert "No boundary effects detected" not in page


def test_named_declaration_does_not_imply_body_effect_analysis():
    inventory = {"named.mjs": {"language": "javascript", "functions": [
        {"name": "handle", "params": [{"name": "request"}, {"name": "response"}]}
    ], "classes": []}}
    before = deepcopy(inventory)
    flow = _flow("handle", "named.mjs")
    data = analyze_data_flow_detailed(inventory, flow, [])
    assert data["analysis"]["state"] == "unavailable"
    assert data["analysis"]["callables"] == {"available": 1, "unavailable": 0}
    assert data["steps"][0]["analysis"]["effect_analysis"] == "unavailable"
    assert data["steps"][0]["inputs"] == [] and inventory == before
    page = _generate_flow_md(flow, data_flow=data)
    assert "Effect observations unavailable" in page and "Effect collector totals unavailable" in page
    assert "No static analysis gaps detected" not in page


def test_supported_empty_python_handler_has_evaluated_zero_effects(tmp_path):
    (tmp_path / "empty.py").write_text("def empty_handler():\n    pass\n")
    extractor = PythonExtractor()
    inventory = extractor.extract(str(tmp_path), deep=True, capture_data_effect_observations=True)
    flow = _flow("empty_handler", "empty.py")
    detailed = analyze_data_flow_detailed(inventory, flow, [], data_effect_observations=extractor.last_data_effect_observations)
    assert detailed["analysis"]["state"] == "evaluated"
    assert detailed["analysis"]["effects"] == {"evaluated": 1, "partial": 0, "unavailable": 0}
    assert detailed["coverage"]["effects"]["observed"] == 0
    assert detailed["analysis"]["limitations"] == []
    page = _generate_flow_md(flow, data_flow=detailed)
    assert "Effect analysis evaluated" in page
    assert "Effect observations unavailable" not in page and "Callable record unavailable" not in page


def test_omitted_missing_callable_still_qualifies_displayed_coverage():
    names = [f"known_{index}" for index in range(12)]
    inventory = {"svc.py": {"language": "python", "functions": [{"name": name} for name in names]}}
    flow = _flow(names[0], "svc.py")
    flow["steps"] = [{"depth": 0 if index == 0 else 1, "file": "svc.py", "symbol": name,
                      "kind": "entry" if index == 0 else "internal"} for index, name in enumerate([*names, "missing"])]
    data = analyze_data_flow_detailed(inventory, flow, [], data_effect_observations=_zero_coverage("svc.py", names))
    assert len(data["steps"]) == 12 and data["coverage"]["steps"]["omitted"] == 1
    assert data["analysis"]["state"] == "partial"
    assert data["analysis"]["callables"] == {"available": 12, "unavailable": 1}
    assert "upstream-callable-record-unavailable" in data["coverage"]["effects"]["limitations"]
    page = _generate_flow_md(flow, data_flow=data)
    assert "Callable record unavailable" in page and "No static analysis gaps detected" not in page


def test_external_steps_are_outside_callable_effect_collection_scope():
    flow = _flow("external", None)
    flow["steps"][0]["kind"] = "external"
    data = analyze_data_flow_detailed({}, flow, [])
    assert data["analysis"]["state"] == "not_applicable"
    assert data["analysis"]["source_steps"] == 0 and data["analysis"]["non_source_steps"] == 1
    assert data["analysis"]["limitations"] == []
    assert "upstream-effect-collector-totals-may-be-unavailable" not in data["coverage"]["effects"]["limitations"]


def test_captured_effects_without_collector_totals_are_partial():
    inventory = {"svc.py": {"functions": [{"name": "run", "data_effects": {
        "inputs": [{"kind": "param", "name": "value"}]
    }}]}}
    data = analyze_data_flow_detailed(inventory, _flow("run", "svc.py"), [])
    assert data["analysis"]["state"] == "partial"
    assert data["steps"][0]["inputs"] == [{"kind": "param", "name": "value"}]
    assert data["analysis"]["collector_totals"] == {"available": 0, "unavailable": 1}


def test_legacy_markdown_retains_known_collector_qualification():
    flow = _flow("handle", "named.mjs")
    data = {"steps": [], "transfers": [], "boundaries": [], "gaps": [], "truncated": False,
            "coverage": {"effects": {"limitations": ["upstream-effect-collector-totals-may-be-unavailable"]}}}
    page = _generate_flow_md(flow, data_flow=data)
    assert "Effect collector totals unavailable" in page
    assert "No static analysis gaps detected" not in page


@pytest.mark.parametrize(("limits", "expected"), [
    (["upstream-callable-record-unavailable"], "collection-limit"),
    (["upstream-effect-collector-totals-may-be-unavailable", "limit-applies-per-effect-kind-per-emitted-step"], "per-step-collection-limit"),
])
def test_unavailable_analysis_does_not_relabel_collection_truncation(limits, expected):
    public = _public_data_flow_coverage({"observed": 13, "emitted": 12, "omitted": 1,
        "limit": 12, "truncated": True, "limitations": limits})
    assert public["truncation_reason"] == expected
    assert public["upstream_analyzer_limitations"]


def test_flow_limit_does_not_hide_omitted_handler_coverage_limitations():
    inventory = {"svc.py": {"functions": [{"name": "known"}]}}
    supported = analyze_data_flow_detailed(inventory, _flow("known", "svc.py"), [],
        data_effect_observations=_zero_coverage("svc.py", ["known"]))
    unsupported = analyze_data_flow_detailed(inventory, _flow("missing", "svc.py"), [])
    flows = [deepcopy(supported) for _ in range(100)] + [unsupported]
    contract = _data_flow_details_contract(deep=True, inventory=inventory, unsupported_sources={}, flows=flows)
    assert len(contract["flows"]) == 100 and contract["coverage"]["omitted"] == 1
    assert all(flow["analysis"]["state"] == "evaluated" for flow in contract["flows"])
    assert "upstream-callable-record-unavailable" in contract["coverage"]["upstream_analyzer_limitations"]


def test_clipped_collector_observations_are_partial_and_disclosed_in_markdown(tmp_path):
    text = "\n".join(f"CONFIG_{index} = {index}" for index in range(20))
    (tmp_path / "svc.py").write_text(text + "\ndef handle():\n    return ("
        + ", ".join(f"CONFIG_{index}" for index in range(20)) + ")\n")
    extractor = PythonExtractor()
    inventory = extractor.extract(str(tmp_path), deep=True, capture_data_effect_observations=True)
    flow = _flow("handle", "svc.py")
    context = build_data_flow_context(inventory, [], data_effect_observations=extractor.last_data_effect_observations)
    legacy = analyze_data_flow(inventory, flow, [], context=context)
    detailed = analyze_data_flow_detailed(inventory, flow, [], context=context)
    assert legacy["analysis"]["state"] == detailed["analysis"]["state"] == "partial"
    stats = detailed["steps"][0]["analysis"]["collector_counts"]
    assert stats["observed"] - stats["emitted"] == stats["omitted"] == 12
    assert detailed["analysis"]["collector_observations"] == stats
    assert detailed["analysis"]["collector_totals"] == {"available": 1, "unavailable": 0}
    page = _generate_flow_md(flow, data_flow=legacy)
    assert "Effect collector omitted observations" in page and "omitted: 12" in page
    assert len(detailed["steps"][0]["reads"]) == 8


def test_zero_emitted_collector_results_are_not_equivalent_to_known_empty():
    inventory = {"svc.py": {"functions": [{"name": "run"}]}}
    sidecar = _zero_coverage("svc.py", ["run"])
    sidecar["callables"][0]["coverage"]["reads"].update(observed=3, emitted=0, omitted=3, limit=0, truncated=True)
    data = analyze_data_flow_detailed(inventory, _flow("run", "svc.py"), [], data_effect_observations=sidecar)
    assert data["analysis"]["state"] == "partial"
    assert data["steps"][0]["reads"] == []
    assert data["analysis"]["collector_observations"] == {"observed": 3, "emitted": 0, "omitted": 3}
    assert "omitted: 3" in _generate_flow_md(_flow("run", "svc.py"), data_flow=data)


@pytest.mark.parametrize("kind", ["external", "unresolved"])
def test_non_source_steps_do_not_borrow_same_named_local_effects(kind):
    inventory = {"svc.py": {"functions": [{"name": "run", "data_effects": {
        "inputs": [{"kind": "param", "name": "value"}]
    }}]}}
    flow = _flow("run", "svc.py")
    flow["steps"][0]["kind"] = kind
    data = analyze_data_flow_detailed(inventory, flow, [], data_effect_observations=_zero_coverage("svc.py", ["run"]))
    assert data["analysis"]["state"] == "not_applicable"
    assert data["steps"][0]["inputs"] == []
    assert data["coverage"]["effects"]["observed"] == data["coverage"]["effects"]["emitted"] == 0


@pytest.mark.parametrize("kind", ["reads", "boundary_effects"])
def test_public_extract_preserves_upstream_collector_truncation_cause(tmp_path, kind):
    if kind == "reads":
        source = "\n".join(f"CONFIG_{index} = {index}" for index in range(20))
        body = "    return (" + ", ".join(f"CONFIG_{index}" for index in range(20)) + ")\n"
    else:
        source = ""
        body = "".join(f"    print({index})\n" for index in range(20))
    (tmp_path / "svc.py").write_text(source + '\n__all__ = ["handle"]\ndef handle():\n' + body)

    details = build_extract_payload(str(tmp_path), deep=True, allow_external_src=True).payload["data_flow_details"]
    flow = next(flow for flow in details["flows"] if flow["id"] == "api-handle")
    assert flow["analysis"]["state"] == "partial"
    assert flow["analysis"]["collector_observations"]["omitted"] == 12
    collections = [flow["coverage"]["effects"], flow["coverage"]["effects"]["by_kind"][kind]]
    if kind == "boundary_effects":
        collections.append(flow["coverage"]["boundaries"])
    for coverage in collections:
        assert "upstream-effect-collector-limit-reached" in coverage["upstream_analyzer_limitations"]
        assert coverage["truncation_reason"] == "upstream-analyzer-limit"
    assert flow["coverage"]["effects"]["by_kind"]["inputs"]["truncation_reason"] is None


def test_missing_downstream_callable_is_not_described_as_the_entry():
    inventory = {"svc.py": {"functions": [{"name": "run"}]}}
    flow = _flow("run", "svc.py")
    flow["steps"].append({"depth": 1, "file": "svc.py", "symbol": "missing", "kind": "internal"})
    detailed = analyze_data_flow_detailed(inventory, flow, [], data_effect_observations=_zero_coverage("svc.py", ["run"]))
    assert detailed["steps"][0]["analysis"]["effect_analysis"] == "evaluated"
    page = _generate_flow_md(flow, data_flow=detailed)
    assert "Callable record unavailable for one or more source steps" in page
    assert "the selected entry symbol has no represented callable body" not in page
