"""Presentation selection retains complete occurrence evidence and raw bounds."""

from copy import deepcopy
import json
import re

import pytest

from llm_wiki_cli.services import bootstrap_runtime as runtime
from llm_wiki_cli.services.entrypoints import build_flow, build_flow_detailed, get_entry_points
from llm_wiki_cli.services.extraction_service import get_inventory, resolve_call_edges
from llm_wiki_cli.services.flow_overview import select_flow_overview, trim_flow_overview
from tests.developer_value.fixtures import projects


def entry():
    return {"id": "cli-main", "category": "cli", "file": "app.py", "symbol": "main", "label": "main"}


def edge(caller, callee, *, kind="internal", caller_file="app.py", callee_file: str | None = "app.py", **metadata):
    return {"from": {"file": caller_file, "symbol": caller},
            "to": {"file": callee_file, "symbol": callee},
            "name": callee, "kind": kind, "line": 1, **metadata}


def overview(flow, limit=30):
    return select_flow_overview(flow, runtime._flow_interactions(flow), limit=limit)


def diagram(markdown):
    match = re.search(r"```mermaid\n(sequenceDiagram\n.*?)```", markdown, re.DOTALL)
    return "" if match is None else match[1]


def test_sibling_and_depth_selection_uses_complete_original_parents():
    edges = [edge("main", "deep"), edge("main", "selection"), edge("main", "ranking"), edge("main", "result")]
    edges += [edge("deep" if index == 0 else f"helper_{index-1}", f"helper_{index}") for index in range(40)]
    flow = build_flow_detailed(entry(), edges, max_depth=100)
    original = deepcopy(flow)
    selected = overview(flow)
    names = [record["callee"]["symbol"] for record in selected.records
             if record["step_index"] in selected.selected_step_indexes]
    assert {"selection", "ranking", "result"} <= set(names)
    assert selected.selected_step_indexes[:4] == (2, 43, 44, 45)
    for record in selected.records:
        parent = flow["steps"][record["parent_step_index"] - 1]
        assert record["caller"] == {"file": parent["file"], "symbol": parent["symbol"]}
        assert record["edge"] == flow["steps"][record["step_index"] - 1]["edge"]
    assert selected.counts == {"captured": 44, "displayed": 30, "omitted": 14,
        "boundaries": {kind: {"captured": 0, "displayed": 0, "omitted": 0} for kind in ("external", "unresolved")},
        "parent_gaps": {"unknown": 0, "conflicting": 0}, "conflicting_targets": 0, "unknown_kinds": 0}
    assert selected.upstream_coverage == flow["coverage"] and flow == original
    assert selected == overview(flow)


def test_first_children_are_balanced_across_exact_parent_occurrences():
    edges = [edge("main", "left"), edge("main", "right")]
    edges += [edge("left", f"left_{index}") for index in range(10)]
    edges += [edge("right", f"right_{index}") for index in range(2)]
    selected = overview(build_flow(entry(), edges), limit=4)
    assert [item["to_label"] for item in selected.interactions] == ["left", "right", "left_0", "right_0"]
    assert len(set(selected.selected_step_indexes)) == 4


@pytest.mark.parametrize("damage", ["unknown-parent", "conflicting-parent", "conflicting-target", "unknown-kind", "external-parent"])
def test_unknown_or_conflicting_evidence_is_retained_as_counted_omission(damage):
    flow = build_flow(entry(), [edge("main", "work")])
    step = flow["steps"][1]
    if damage == "unknown-parent":
        step["depth"] = 3
    elif damage == "conflicting-parent":
        step["edge"]["from"]["symbol"] = "other"
    elif damage == "conflicting-target":
        step["edge"]["to"]["symbol"] = "other"
    elif damage == "unknown-kind":
        step["kind"] = "dynamic-unknown"
    else:
        step.update(kind="external", file=None)
        step["edge"].update(kind="external", to={"file": None, "symbol": "work"})
        flow["steps"].append({"depth": 2, "file": "app.py", "symbol": "nested", "kind": "internal"})
    original = deepcopy(flow)
    selected = overview(flow)
    assert selected.counts["omitted"] == 1
    assert len(selected.records) == len(flow["steps"]) - 1
    assert sum(group["count"] for group in selected.omission_groups) == 1
    assert selected.records[-1]["step_index"] not in selected.selected_step_indexes
    assert flow == original
    text = runtime._generate_flow_md(flow)
    assert "No replacement caller or target is inferred" in text


def test_repeated_occurrences_keep_distinct_original_indexes_and_neutral_groups():
    edges = [edge("main", "same", args=[{"kind": "constant", "value": "1"}]),
             edge("main", "same", args=[{"kind": "constant", "value": "2"}])]
    flow = build_flow(entry(), edges)
    selected = overview(flow, limit=0)
    assert [record["step_index"] for record in selected.records] == [2, 3]
    assert [record["edge"]["args"][0]["value"] for record in selected.records] == ["1", "2"]
    assert len(selected.omission_groups) == 1
    assert selected.omission_groups[0]["step_indexes"] == [2, 3]
    assert selected.omission_groups[0]["caller"] == {"file": "app.py", "symbol": "main"}
    assert selected.omission_groups[0]["target_module"] == "app.py"
    assert not any("validation" in str(group) or "security" in str(group) for group in selected.omission_groups)


def test_trim_reconciles_all_boundary_counts_after_actual_prefix_admission():
    flow = build_flow(entry(), [edge("main", "inside"),
        edge("main", "outside", kind="external", callee_file=None),
        edge("main", "unknown", kind="unresolved", callee_file=None)])
    selected = overview(flow)
    trimmed = trim_flow_overview(selected, 1)
    assert trimmed.counts["captured"] == 3 and trimmed.counts["displayed"] == 1
    assert trimmed.counts["boundaries"] == {kind: {"captured": 1, "displayed": 0, "omitted": 1}
                                            for kind in ("external", "unresolved")}
    assert sum(group["count"] for group in trimmed.omission_groups) == 2
    assert selected.counts["displayed"] == 3


@pytest.mark.parametrize("bound,value", [("GENERATED_DIAGRAM_NODE_LIMIT", 3),
                                         ("GENERATED_DIAGRAM_LINE_LIMIT", 8),
                                         ("GENERATED_DIAGRAM_CHAR_LIMIT", 180)])
def test_real_mermaid_ceiling_owner_counts_actual_displayed_prefix(monkeypatch, bound, value):
    flow = build_flow(entry(), [edge("main", f"call_{index}", kind="external", callee_file=None) for index in range(8)])
    monkeypatch.setattr(runtime, bound, value)
    text = runtime._generate_flow_md(flow)
    sequence = diagram(text)
    shown = sequence.count("->>")
    assert shown < 8
    assert f"external {shown} of 8 ({8-shown} omitted)" in text
    if sequence:
        nodes = sum("participant " in line for line in sequence.splitlines())
        assert runtime._generated_diagram_fits("```mermaid\n" + sequence + "```", node_count=nodes)
    assert "Omitted captured detail" in text


def test_metadata_and_selection_are_immutable_and_do_not_mutate_the_trace():
    flow = build_flow(entry(), [edge("main", "outside", kind="external", callee_file=None,
        args=[{"kind": "constant", "value": "'captured'"}], kwargs=[{"name": "limit", "kind": "constant", "value": "3"}])])
    original = deepcopy(flow)
    selected = overview(flow, limit=0)
    row = selected.records[0]
    assert isinstance(row, dict)
    with pytest.raises(TypeError, match="immutable"):
        row["edge"]["args"][0]["value"] = "changed"
    group = selected.omission_groups[0]
    assert isinstance(group, dict)
    with pytest.raises(TypeError, match="immutable"):
        group["step_indexes"].append(99)
    flow["steps"][1]["edge"]["args"][0]["value"] = "caller-mutated"
    assert selected.records[0]["edge"] == original["steps"][1]["edge"]


@pytest.mark.parametrize("invalid", [True, -1, 31, 0.0])
def test_interaction_limit_is_exact_and_never_expands_over_thirty(invalid):
    with pytest.raises(ValueError, match="limit"):
        overview(build_flow(entry(), []), limit=invalid)


def test_incomplete_or_malformed_depth_input_refuses_without_reconstructing_a_trace():
    flow = build_flow(entry(), [edge("main", "work")])
    with pytest.raises(ValueError, match="align"):
        select_flow_overview(flow, [])
    flow["steps"][1]["depth"] = True
    with pytest.raises(ValueError, match="depth"):
        overview(flow)


def test_upstream_bounds_are_separate_and_not_all_attributed_to_depth():
    flow = build_flow_detailed(entry(), [edge("main", "work")])
    assert flow["coverage"]["steps"]["limit"] is None
    # Defensive presentation of a supplied qualified envelope, not a new builder contract.
    flow["coverage"]["steps"].update(observed=9, emitted=2, omitted=7, limit=2, depth_limit=6)
    original = deepcopy(flow)
    text = runtime._generate_flow_md(flow)
    assert "7 omitted under recorded bounds (step limit 2, depth limit 6)" in text
    assert "7 omitted at depth limit" not in text
    assert "These are separate from presentation omissions" in text
    assert overview(flow).upstream_coverage == flow["coverage"] and flow == original


def test_empty_same_file_cycles_and_depth_truncation_keep_original_owner_semantics():
    empty = build_flow_detailed(entry(), [])
    assert overview(empty).counts["captured"] == 0
    assert "No outbound calls were detected by static analysis" in runtime._generate_flow_md(empty)
    edges = [edge("main", "work"), edge("work", "main")]
    cyclic = build_flow_detailed(entry(), edges)
    original = deepcopy(cyclic)
    assert overview(cyclic).counts["captured"] == 2 and cyclic == original
    truncated = build_flow_detailed(entry(), edges, max_depth=0)
    text = runtime._generate_flow_md(truncated)
    assert "No outbound interactions are available in this bounded static trace" in text
    assert "Trace truncated at the depth limit" in text
    assert truncated["coverage"]["steps"]["omitted"] == 2


def test_actual_frozen_large_overview_reaches_stages_and_failure_with_full_parent_evidence(tmp_path):
    for name, source in projects()["large"].items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source)
    inventory = get_inventory(tmp_path, deep=True)
    edges = resolve_call_edges(inventory)
    actual_entry = next(item for item in get_entry_points(inventory, root=tmp_path, include_plugins=False)
                        if item["file"] == "cli.py" and item["symbol"] == "main")
    flow = build_flow_detailed(actual_entry, edges)
    original = deepcopy(flow)
    text = runtime._generate_flow_md(flow)
    sequence = diagram(text)
    assert all(stage in sequence for stage in ("validate_command", "validate_catalog_access", "select_records", "rank_records", "format_results"))
    assert "catalog access denied" in sequence
    assert sequence.count("->>") == 30
    assert "Static overview in presentation order, not runtime execution order" in text
    assert "Call sequence diagram shows 30 of 34 interactions; 4 omitted" in text
    assert flow["coverage"]["steps"] == {"observed": 67, "emitted": 35, "omitted": 32,
        "limit": None, "depth_limit": 6, "truncated": True, "limitations": ["flow-steps-are-statically-inferred"]}
    assert flow == original
    for record in overview(flow).records:
        parent = flow["steps"][record["parent_step_index"] - 1]
        assert record["caller"] == {"file": parent["file"], "symbol": parent["symbol"]}
    assert text == runtime._generate_flow_md(flow)
    for path in flow["modules_touched"]:
        assert f"../modules/{runtime._module_name_from_path(path)}.md" in text


def test_all_shown_interaction_totals_are_disclosed_without_implied_omissions():
    flow = build_flow(entry(), [edge("main", "work")])
    text = runtime._generate_flow_md(flow)
    assert "Call sequence diagram shows 1 of 1 interactions; 0 omitted" in text
    assert "external 0 of 0 (0 omitted); unresolved 0 of 0 (0 omitted)" in text
    assert diagram(text).count("->>") == 1


def test_actual_imported_pipeline_survives_validation_fanout_and_duplicate_targets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sources = {
        "transport.py": """from guard import permit
from adapter import invoke
def start():
    permit()
    result = invoke()
    print(result)
""",
        "guard.py": """def reject():
    raise ValueError('denied')
def permit():
""" + "".join("    reject()\n    getattr(object(), 'missing', None)\n" for _ in range(40)),
        "adapter.py": """from operations import dispatch
def invoke():
    return dispatch()
""",
        "operations.py": """from ordering import arrange
def accept():
    isinstance('input', str)
def collect():
    yield len('row')
def deliver(values):
    return tuple(values)
def dispatch():
    accept()
    values = collect()
    return deliver(arrange(values))
""",
        "ordering.py": """def tokenize(values):
    return str(values)
def arrange(values):
    return sorted(tokenize(values))
""",
        "tripwire.py": """from pathlib import Path
Path('trace-source-executed').write_text('must never execute')
""",
    }
    for name, source in sources.items():
        (tmp_path / name).write_text(source)
    inventory = get_inventory(tmp_path, deep=True)
    edges = resolve_call_edges(inventory)
    flow = build_flow_detailed({**entry(), "file": "transport.py", "symbol": "start"}, edges)
    original = deepcopy(flow)
    selected = overview(flow)
    rendered = runtime._bounded_sequence_diagram([dict(row) for row in selected.interactions])
    admitted = trim_flow_overview(selected, rendered.shown_items)
    required = {
        ("operations.py", "accept"), ("operations.py", "collect"),
        ("operations.py", "dispatch"), ("ordering.py", "arrange"),
        ("operations.py", "deliver"),
    }
    coordinates = {
        (record["callee"]["file"], record["callee"]["symbol"])
        for record in admitted.records if record["step_index"] in admitted.selected_step_indexes
    }
    assert required <= coordinates
    assert all(name in diagram(runtime._generate_flow_md(flow)) for _, name in required)
    assert admitted.counts["displayed"] <= 30
    assert flow["coverage"]["steps"]["depth_limit"] == 6
    assert len((rendered.diagram or "").splitlines()) <= 80
    assert len(rendered.diagram or "") <= 6000
    assert flow == original and not (tmp_path / "trace-source-executed").exists()
    assert runtime._generate_flow_md(flow) == runtime._generate_flow_md(flow)
    # The generator declaration is static evidence, never proof it was consumed.
    assert next(record for record in admitted.records if record["callee"]["symbol"] == "collect")["kind"] == "internal"
    selection = tmp_path / ".llm-wiki/source-selection.json"
    selection.parent.mkdir()
    selection.write_text(json.dumps({
        "schema_version": "llm-wiki-source-selection/v1",
        "include": [name for name in sources if name != "ordering.py"], "exclude": [],
    }))
    excluded = get_inventory(tmp_path, deep=True)
    assert "ordering.py" not in excluded and (tmp_path / "ordering.py").exists()
    excluded_edges = resolve_call_edges(excluded)
    rank_call = next(e for e in excluded_edges if e["from"] == {"file": "operations.py", "symbol": "dispatch"} and e["name"] == "arrange")
    # Existing resolution treats imports outside the captured inventory as external.
    assert rank_call["kind"] == "external" and rank_call["to"]["file"] is None
    assert not any(e["kind"] == "internal" and e["to"]["file"] == "ordering.py" for e in excluded_edges)
    assert not (tmp_path / "trace-source-executed").exists()


def test_repeated_internal_sites_yield_display_space_without_coalescing_raw_occurrences():
    edges = [edge("main", "same", line=i + 1, args=[{"kind": "constant", "value": str(i)}]) for i in range(40)]
    edges += [edge("main", f"distinct_{i}") for i in range(5)]
    edges += [edge("main", "remote", kind="external", callee_file=None),
              edge("main", "dynamic", kind="unresolved", callee_file=None)]
    flow = build_flow_detailed(entry(), edges)
    original = deepcopy(flow)
    selected = overview(flow, limit=8)
    shown = [record for record in selected.records if record["step_index"] in selected.selected_step_indexes]
    assert {"same", *(f"distinct_{i}" for i in range(5)), "remote", "dynamic"} == {record["callee"]["symbol"] for record in shown}
    assert selected.counts["captured"] == 47 and selected.counts["omitted"] == 39
    assert all(selected.counts["boundaries"][kind]["displayed"] == 1 for kind in ("external", "unresolved"))
    duplicates = [record for record in selected.records if record["callee"]["symbol"] == "same"]
    assert len(duplicates) == 40
    assert [record["edge"]["args"][0]["value"] for record in duplicates] == [str(i) for i in range(40)]
    assert sum(group["count"] for group in selected.omission_groups) == 39
    assert flow == original


def test_conflicting_child_does_not_promote_an_invented_internal_continuation():
    flow = build_flow(entry(), [])
    flow["steps"] += [
        {"depth": 1, "file": "app.py", "symbol": "left", "kind": "internal",
         "edge": edge("main", "left")},
        {"depth": 2, "file": "app.py", "symbol": "bad", "kind": "internal",
         "edge": edge("other", "bad")},
        {"depth": 1, "file": "app.py", "symbol": "right", "kind": "internal",
         "edge": edge("main", "right")},
        {"depth": 2, "file": "app.py", "symbol": "good", "kind": "internal",
         "edge": edge("right", "good")},
    ]
    original = deepcopy(flow)
    selected = overview(flow, limit=1)
    assert selected.selected_step_indexes == (4,)
    assert selected.counts["parent_gaps"]["conflicting"] == 1
    assert selected.records[1]["parent_state"] == "conflicting"
    assert flow == original
