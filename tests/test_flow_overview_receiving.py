"""Receive bounded presentation using captured source and independent parent facts."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import re

import pytest

from llm_wiki_cli.services import bootstrap_runtime as renderer
from llm_wiki_cli.services.data_flow import analyze_data_flow
from llm_wiki_cli.services.entrypoints import (
    build_flow,
    build_flow_detailed,
    get_entry_points,
)
from llm_wiki_cli.services.extraction_service import (
    InventoryRequest,
    get_inventory,
    get_inventory_result,
    resolve_call_edges,
)
from llm_wiki_cli.services.section_ownership import (
    SectionOwnership,
    observe_page_sections,
)
from llm_wiki_cli.services.wiki_surface import PageKind
from tests.developer_value.fixtures import projects


def sequence(markdown: str) -> str:
    matches = re.findall(
        r"```mermaid\n(sequenceDiagram\n.*?)\n```", markdown, re.DOTALL
    )
    assert len(matches) <= 1
    return matches[0] if matches else ""


def arrows(diagram: str) -> list[str]:
    return [line for line in diagram.splitlines() if "->>" in line or "-->>" in line]


def source_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*.py")
    }


@pytest.fixture
def captured_large(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = projects()["large"]
    root = tmp_path / "src"
    for path, text in source.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))
    before = source_hashes(root)
    captured = get_inventory_result(
        InventoryRequest(root, deep=True, include_plugins=False)
    )
    assert captured.source_snapshot is not None and not captured.failed
    assert captured.inventory == get_inventory(root, deep=True)
    assert source_hashes(root) == before
    assert before == {
        path: sha256(text.encode("utf-8")).hexdigest() for path, text in source.items()
    }
    edges = resolve_call_edges(captured.inventory)
    entry = next(
        row
        for row in get_entry_points(
            captured.inventory, root=root, include_plugins=False
        )
        if row["file"] == "cli.py" and row["symbol"] == "main"
    )
    detailed = build_flow_detailed(entry, edges)
    page_map = {
        path: "owned_" + path.removesuffix(".py").replace("/", "_") for path in source
    }
    return root, captured, edges, entry, detailed, page_map


def test_captured_large_overview_shows_operation_stages_and_real_failure(
    captured_large,
):
    root, captured, edges, entry, detailed, page_map = captured_large
    before = deepcopy((captured.inventory, edges, entry, detailed, page_map))
    raw = build_flow(entry, edges)
    assert all(detailed[key] == value for key, value in raw.items())
    data_flow = analyze_data_flow(captured.inventory, detailed, edges)
    original_data = deepcopy(data_flow)
    markdown = renderer._generate_flow_md(detailed, page_map, data_flow=data_flow)
    diagram = sequence(markdown)
    assert 0 < len(arrows(diagram)) <= 30
    for target in (
        "validate_command",
        "validate_catalog_access",
        "select_records",
        "rank_records",
        "format_results",
    ):
        assert target in diagram
    failure = next(
        step
        for step in detailed["steps"]
        if step.get("edge", {}).get("name") == "PermissionError"
    )
    assert failure["edge"]["args"][0]["value"] == "'catalog access denied'"
    assert "catalog access denied" in diagram
    assert "static overview" in markdown.lower()
    assert "presentation order" in markdown.lower()
    assert "runtime" in markdown.lower()
    assert "## Call sequence" in markdown and "## Call overview" not in markdown
    assert "Trace truncated at the depth limit; deeper calls are omitted" in markdown
    assert detailed["coverage"]["steps"] == {
        "observed": 67,
        "emitted": 35,
        "omitted": 32,
        "limit": None,
        "depth_limit": 6,
        "truncated": True,
        "limitations": ["flow-steps-are-statically-inferred"],
    }
    participants = [
        line for line in diagram.splitlines() if line.strip().startswith("participant ")
    ]
    assert len(participants) <= 40 and len(diagram.splitlines()) <= 80
    assert len(diagram) <= 6000
    assert markdown == renderer._generate_flow_md(
        detailed, page_map, data_flow=data_flow
    )
    assert (captured.inventory, edges, entry, detailed, page_map) == before
    assert data_flow == original_data
    assert build_flow(entry, edges) == raw
    assert source_hashes(root) == {
        path: sha256(text.encode()).hexdigest()
        for path, text in projects()["large"].items()
    }


def test_overview_preserves_complete_module_links_and_authored_behavior(captured_large):
    _, _, edges, entry, detailed, page_map = captured_large
    first = renderer._generate_flow_md(detailed, page_map)
    for module in detailed["modules_touched"]:
        assert f"../modules/{page_map[module]}.md" in first
    for module in detailed["related_modules"]:
        assert f"../modules/{page_map[module]}.md" in first
    semantic = "Reviewed search rationale remains source-grounded; runtime conditions require host verification."
    reviewed = first.split("## Behavior\n", 1)[0] + "## Behavior\n\n" + semantic + "\n"
    changed = build_flow_detailed(entry, edges, max_depth=2)
    regenerated = renderer._generate_flow_md(changed, page_map)
    merged = renderer._preserve_level_two_section(reviewed, regenerated, "Behavior")
    assert semantic in merged
    assert (
        merged.split("## Behavior\n", 1)[0] == regenerated.split("## Behavior\n", 1)[0]
    )
    assert merged.count("## Call sequence") == 1
    sections = observe_page_sections(merged, "flows/owned-search.md", PageKind.FLOWS)
    by_heading = {row.title: row.ownership for row in sections.sections}
    assert by_heading["Call sequence"] is SectionOwnership.GENERATED
    assert by_heading["Behavior"] is SectionOwnership.SEMANTIC


def test_selected_records_bind_actual_full_trace_parents_and_separate_omissions(
    captured_large,
):
    from llm_wiki_cli.services.flow_overview import (
        select_flow_overview,
        trim_flow_overview,
    )

    _, _, _, _, detailed, _ = captured_large
    interactions = renderer._flow_interactions(detailed)
    before = deepcopy((detailed, interactions))
    overview = select_flow_overview(detailed, interactions)
    assert overview.counts["captured"] == 34
    assert overview.counts["displayed"] == 30 and overview.counts["omitted"] == 4
    assert (
        overview.upstream_coverage == detailed["coverage"]
        and overview.upstream_truncated
    )
    assert overview.counts["parent_gaps"] == {"unknown": 0, "conflicting": 0}
    for record in overview.records:
        index = record["step_index"]
        parent_index = record["parent_step_index"]
        assert type(parent_index) is int and 0 < parent_index < index
        step = detailed["steps"][index - 1]
        parent = detailed["steps"][parent_index - 1]
        assert record["depth"] == parent["depth"] + 1
        assert record["caller"] == {"file": parent["file"], "symbol": parent["symbol"]}
        assert record["callee"] == step["edge"]["to"]
        assert record["edge"] == step["edge"]
    selected = set(overview.selected_step_indexes)
    omitted = set(range(2, len(detailed["steps"]) + 1)) - selected
    groups = overview.omission_groups
    assert {index for group in groups for index in group["step_indexes"]} == omitted
    assert sum(group["count"] for group in groups) == len(omitted)
    for kind in ("external", "unresolved"):
        expected = sum(step["kind"] == kind for step in detailed["steps"][1:])
        count = overview.counts["boundaries"][kind]
        assert count["captured"] == expected == count["displayed"] + count["omitted"]
    rendered = renderer._bounded_sequence_diagram(
        [dict(row) for row in overview.interactions]
    )
    trimmed = trim_flow_overview(overview, rendered.shown_items)
    assert trimmed.counts["displayed"] == len(arrows(sequence(rendered.diagram or "")))
    assert trimmed.counts["captured"] == 34
    assert trimmed.upstream_coverage == overview.upstream_coverage
    assert (detailed, interactions) == before
    assert select_flow_overview(detailed, interactions) == overview
    # Changing source-sized nested metadata after capture cannot rewrite the model.
    first = overview.records[0]
    prior_edge = deepcopy(dict(first["edge"]))
    detailed["steps"][first["step_index"] - 1]["edge"]["name"] = (
        "changed-after-selection"
    )
    assert first["edge"] == prior_edge


@pytest.mark.parametrize("limit", [0, 1, 17, 30])
def test_explicit_presentation_limits_retain_all_boundary_and_depth_denominators(
    captured_large, limit
):
    from llm_wiki_cli.services.flow_overview import (
        select_flow_overview,
        trim_flow_overview,
    )

    _, _, _, _, detailed, _ = captured_large
    overview = select_flow_overview(
        detailed, renderer._flow_interactions(detailed), limit=limit
    )
    assert overview.counts["displayed"] == limit
    assert overview.counts["omitted"] == 34 - limit
    none = trim_flow_overview(overview, 0)
    assert none.counts["displayed"] == 0 and none.counts["omitted"] == 34
    assert none.upstream_coverage == detailed["coverage"]
    for kind, counts in none.counts["boundaries"].items():
        assert counts["displayed"] == 0 and counts["omitted"] == counts["captured"]
        assert counts["captured"] == sum(
            step["kind"] == kind for step in detailed["steps"]
        )


@pytest.mark.parametrize(
    "mutation",
    ["caller-conflict", "target-conflict", "disconnected-depth", "unknown-kind"],
)
def test_conflicting_actual_metadata_stays_counted_without_a_certified_arrow(
    captured_large, mutation
):
    from llm_wiki_cli.services.flow_overview import select_flow_overview

    _, _, _, _, detailed, _ = captured_large
    index = next(
        index
        for index, step in enumerate(detailed["steps"])
        if step["kind"] == "external"
    )
    selected_step = detailed["steps"][index]
    if mutation == "caller-conflict":
        selected_step["edge"]["from"] = {"file": "different.py", "symbol": "different"}
    elif mutation == "target-conflict":
        selected_step["edge"]["to"]["symbol"] = "different"
    elif mutation == "disconnected-depth":
        selected_step["depth"] = 50
    else:
        selected_step["kind"] = "new-unsupported-kind"
    interactions = renderer._flow_interactions(detailed)
    before = deepcopy((detailed, interactions))
    overview = select_flow_overview(detailed, interactions)
    assert index + 1 not in overview.selected_step_indexes
    record = next(row for row in overview.records if row["step_index"] == index + 1)
    assert record["edge"] == selected_step["edge"]
    assert overview.counts["captured"] == 34
    assert index + 1 in {
        step for group in overview.omission_groups for step in group["step_indexes"]
    }
    if mutation == "caller-conflict":
        assert record["parent_state"] == "conflicting"
        assert overview.counts["parent_gaps"]["conflicting"] >= 1
    elif mutation == "disconnected-depth":
        assert record["parent_state"] == "unknown"
        assert overview.counts["parent_gaps"]["unknown"] >= 1
    elif mutation == "target-conflict":
        assert (
            not record["target_coherent"]
            and overview.counts["conflicting_targets"] >= 1
        )
    else:
        assert overview.counts["unknown_kinds"] >= 1
    assert (detailed, interactions) == before


def test_bounded_query_traversal_and_presentation_counts_remain_independent(
    captured_large,
):
    from llm_wiki_cli import api
    from llm_wiki_cli.services.documentation_queries import (
        DocumentationGraphQueryService,
    )

    _, captured, edges, entry, detailed, page_map = captured_large
    original = deepcopy(detailed)
    service = DocumentationGraphQueryService(
        captured.inventory,
        call_edges=edges,
        flows=[detailed],
        limit=3,
        inventory_result=captured,
    )
    response = api.flow_for_entrypoint(entry["id"], service=service)
    limited = response["flow"]
    assert isinstance(limited, dict)
    assert len(limited["steps"]) == 3
    assert response["bounds"]["flow.steps"] == {
        "total": 35,
        "returned": 3,
        "truncated": True,
    }
    counts = limited["coverage"]["steps"]
    assert counts == original["coverage"]["steps"]
    assert counts["observed"] == 67 and counts["emitted"] == 35
    assert counts["omitted"] == 32 and counts["limit"] is None
    assert counts["depth_limit"] == 6
    markdown = renderer._generate_flow_md(limited, page_map)
    assert "35 of 67" in markdown and "32 omitted" in markdown
    assert "64 omitted" not in markdown
    assert "depth limit 6" in markdown
    from llm_wiki_cli.services.flow_overview import select_flow_overview

    overview = select_flow_overview(limited, renderer._flow_interactions(limited))
    assert overview.counts["captured"] == 3
    assert overview.counts["parent_gaps"]["unknown"] >= 1
    assert overview.selected_step_indexes == ()
    assert overview.upstream_coverage == original["coverage"]
    assert detailed == original
    assert service.flows[0] == original


def test_actual_long_boundary_capture_reconciles_renderer_pressure(
    tmp_path, monkeypatch
):
    from llm_wiki_cli.services.flow_overview import (
        select_flow_overview,
        trim_flow_overview,
    )

    monkeypatch.chdir(tmp_path)
    root = tmp_path / "src"
    root.mkdir()
    names = [
        "CapturedBoundary" + "LongOwner" * 24 + f"_{index:02}" for index in range(48)
    ]
    argument = "captured detail > not a runtime guarantee " * 12
    source = "def main():\n" + "".join(f"    {name}({argument!r})\n" for name in names)
    source += '\nif __name__ == "__main__":\n    main()\n'
    (root / "pressure.py").write_text(source)
    inventory = get_inventory_result(
        InventoryRequest(root, deep=True, include_plugins=False)
    )
    edges = resolve_call_edges(inventory.inventory)
    entry = next(
        row
        for row in get_entry_points(
            inventory.inventory, root=root, include_plugins=False
        )
        if row["symbol"] == "main"
    )
    flow = build_flow_detailed(entry, edges)
    original = deepcopy(flow)
    interactions = renderer._flow_interactions(flow)
    enriched = renderer._flow_overview_interactions(flow, interactions)
    selected = select_flow_overview(flow, enriched)
    assert selected.counts["captured"] == 48 and selected.counts["displayed"] == 30
    admitted = renderer._bounded_sequence_diagram(
        [dict(row) for row in selected.interactions]
    )
    assert 0 < admitted.shown_items < 30
    displayed = trim_flow_overview(selected, admitted.shown_items)
    markdown = renderer._generate_flow_md(flow)
    diagram = sequence(markdown)
    assert len(arrows(diagram)) == displayed.counts["displayed"]
    assert f"shows {displayed.counts['displayed']} of 48 interactions" in markdown
    assert displayed.counts["boundaries"]["external"]["captured"] == 0
    counts = displayed.counts["boundaries"]["unresolved"]
    assert counts["captured"] == 48 and counts["omitted"] == 48 - counts["displayed"]
    assert (
        f"unresolved {counts['displayed']} of 48 ({counts['omitted']} omitted)"
        in markdown
    )
    assert len(diagram) <= 6000 and len(diagram.splitlines()) <= 80
    assert flow == original and (root / "pressure.py").read_text() == source
