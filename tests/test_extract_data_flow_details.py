from __future__ import annotations

from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.services.knowledge_graph import (
    GraphConcept,
    KnowledgeGraphInputs,
    materialize_typed_graph,
)


def test_shallow_deep_empty_and_unsupported_states_are_distinct(tmp_path):
    (tmp_path / "model.py").write_text(
        "class Value:\n    pass\n",
        encoding="utf-8",
    )

    shallow = extract_cmd.build_extract_payload(
        str(tmp_path),
        deep=False,
        allow_external_src=True,
    ).payload["data_flow_details"]
    evaluated = extract_cmd.build_extract_payload(
        str(tmp_path),
        deep=True,
        allow_external_src=True,
    ).payload["data_flow_details"]

    assert (shallow["state"], shallow["reason"], shallow["flows"]) == (
        "not_evaluated",
        "deep-analysis-disabled",
        [],
    )
    assert (evaluated["state"], evaluated["reason"], evaluated["flows"]) == (
        "evaluated",
        None,
        [],
    )
    assert evaluated["coverage"]["observed"] == 0

    unsupported_root = tmp_path / "unsupported"
    unsupported_root.mkdir()
    (unsupported_root / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    unsupported = extract_cmd.build_extract_payload(
        str(unsupported_root),
        deep=True,
        allow_external_src=True,
    ).payload["data_flow_details"]

    assert unsupported["state"] == "unsupported"
    assert unsupported["reason"] == "no-supported-language-analyzer"
    assert unsupported["coverage"]["upstream_analyzer_limitations"] == [
        "unsupported-source-language:shell"
    ]


def test_deep_public_extract_requests_data_effect_analyzer_coverage(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "api.py").write_text(
        '__all__ = ["run"]\n\n'
        "def run(value):\n"
        "    print(value)\n"
        "    return value\n",
        encoding="utf-8",
    )
    original = extract_cmd.get_inventory_result
    captured = {}

    def wrapped(request):
        captured["capture_data_effect_observations"] = (
            request.capture_data_effect_observations
        )
        return original(request)

    monkeypatch.setattr(extract_cmd, "get_inventory_result", wrapped)

    details = extract_cmd.build_extract_payload(
        str(tmp_path),
        deep=True,
        allow_external_src=True,
    ).payload["data_flow_details"]

    assert captured == {"capture_data_effect_observations": True}
    assert details["flows"][0]["coverage"]["effects"]["observed"] >= 1


def test_public_directional_effect_totals_match_typed_graph_materialization(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "api.py").write_text(
        'TOTAL = 0\n'
        '__all__ = ["run"]\n\n'
        "def run(state, value):\n"
        "    global TOTAL\n"
        "    current = state.input\n"
        "    state.output = current\n"
        "    TOTAL = value\n"
        "    return state.output\n",
        encoding="utf-8",
    )
    analyzed_flows = []
    original = extract_cmd.analyze_data_flow_detailed

    def capture_analyzed_flow(*args, **kwargs):
        flow = original(*args, **kwargs)
        analyzed_flows.append(flow)
        return flow

    monkeypatch.setattr(
        extract_cmd,
        "analyze_data_flow_detailed",
        capture_analyzed_flow,
    )

    payload = extract_cmd.build_extract_payload(
        str(tmp_path),
        deep=True,
        allow_external_src=True,
    ).payload
    public_flows = payload["data_flow_details"]["flows"]
    concepts = [
        GraphConcept(
            "llm-wiki://modules/api",
            "source-module",
            source_path="api.py",
            page_id="api",
        ),
        *[
            GraphConcept(
                f"llm-wiki://flows/{flow['id']}",
                "user-flow",
                page_id=flow["id"],
            )
            for flow in analyzed_flows
        ],
    ]
    graph = materialize_typed_graph(
        KnowledgeGraphInputs(
            inventory=payload["inventory"],
            concepts=concepts,
            data_flows=analyzed_flows,
        )
    )

    public_directional_coverage = {
        field: sum(
            flow["coverage"]["effects"]["by_kind"][kind][field]
            for flow in public_flows
            for kind in ("reads", "writes")
        )
        for field in ("observed", "emitted", "omitted")
    }
    graph_coverage = next(
        record
        for record in graph["coverage"]
        if record["analyzer"] == "data-flows"
    )
    materialized_observations = sum(
        edge["evidence"]["observed"]
        for edge in graph["edges"]
        if edge["kind"] in {"reads", "writes"}
    )

    assert public_directional_coverage["observed"] > 0
    assert graph_coverage["observed"] == public_directional_coverage["observed"]
    assert graph_coverage["emitted"] == public_directional_coverage["emitted"]
    assert graph_coverage["omitted"] == public_directional_coverage["omitted"]
    assert materialized_observations == public_directional_coverage["emitted"]


def test_public_detailed_flow_reports_large_fanout_bounds_and_keeps_legacy_shape(
    tmp_path,
):
    calls = "\n".join(f"    client.publish_{index}(value)" for index in range(16))
    (tmp_path / "api.py").write_text(
        '__all__ = ["run"]\n\n\ndef run(client, value):\n'
        f"{calls}\n"
        "    return value\n",
        encoding="utf-8",
    )

    payload = extract_cmd.build_extract_payload(
        str(tmp_path),
        deep=True,
        allow_external_src=True,
    ).payload
    legacy = next(flow for flow in payload["data_flows"] if flow["id"] == "api-run")
    detailed_contract = payload["data_flow_details"]
    detailed = next(
        flow for flow in detailed_contract["flows"] if flow["id"] == "api-run"
    )

    assert set(legacy) == {
        "id",
        "entry",
        "steps",
        "transfers",
        "boundaries",
        "gaps",
        "truncated",
    }
    assert detailed_contract["schema_version"] == (
        "llm-wiki-extract-data-flow-details/v1"
    )
    assert detailed_contract["state"] == "evaluated"
    assert detailed["coverage"]["steps"]["observed"] == 17
    assert detailed["coverage"]["steps"]["emitted"] == 12
    assert detailed["coverage"]["steps"]["omitted"] == 5
    assert detailed["coverage"]["steps"]["truncation_reason"] == (
        "collection-limit"
    )
    assert detailed["coverage"]["transfers"]["observed"] == 16
    assert detailed["coverage"]["transfers"]["emitted"] == 11
    assert detailed["coverage"]["transfers"]["omitted"] == 5
    assert detailed["coverage"]["gaps"]["observed"] >= 12
    assert detailed["coverage"]["gaps"]["emitted"] == 12
    assert detailed["coverage"]["gaps"]["truncation_reason"] == "collection-limit"
    assert detailed_contract["effective_limits"] == {
        "flows_per_extract": 100,
        "flow_depth": 6,
        "steps_per_flow": 12,
        "effects_per_kind_per_step": 8,
        "boundaries_per_flow": 8,
        "transfers_per_flow": 12,
        "gaps_per_flow": 12,
    }


def test_detailed_flow_collection_is_bounded_without_changing_legacy_flows(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        extract_cmd,
        "DEFAULT_DATA_FLOW_DETAILS_FLOW_LIMIT",
        2,
    )
    (tmp_path / "api.py").write_text(
        '__all__ = ["a", "b", "c"]\n\n'
        "def a():\n    return 1\n\n"
        "def b():\n    return 2\n\n"
        "def c():\n    return 3\n",
        encoding="utf-8",
    )

    payload = extract_cmd.build_extract_payload(
        str(tmp_path),
        deep=True,
        allow_external_src=True,
    ).payload
    coverage = payload["data_flow_details"]["coverage"]

    assert len(payload["data_flows"]) == 3
    assert len(payload["data_flow_details"]["flows"]) == 2
    assert coverage == {
        "observed": 3,
        "emitted": 2,
        "omitted": 1,
        "limit": 2,
        "truncated": True,
        "truncation_reason": "collection-limit",
        "upstream_analyzer_limitations": [],
    }


def test_public_coverage_names_upstream_and_per_step_truncation_causes():
    flow = {
        "schema_version": "llm-wiki-data-flow-observations/v1",
        "coverage": {
            "steps": {
                "observed": 4,
                "emitted": 1,
                "omitted": 3,
                "limit": 12,
                "truncated": True,
                "limitations": ["upstream-flow-depth-limit-reached"],
            },
            "effects": {
                "observed": 10,
                "emitted": 8,
                "omitted": 2,
                "limit": 40,
                "truncated": True,
                "limitations": [
                    "limit-applies-per-effect-kind-per-emitted-step"
                ],
                "by_kind": {
                    "reads": {
                        "observed": 10,
                        "emitted": 8,
                        "omitted": 2,
                        "limit": 8,
                        "truncated": True,
                        "limitations": [
                            "limit-applies-per-effect-kind-per-emitted-step"
                        ],
                    }
                },
            },
        },
    }

    public = extract_cmd._public_detailed_data_flow(flow)

    assert public["coverage"]["steps"]["truncation_reason"] == (
        "upstream-analyzer-limit"
    )
    assert public["coverage"]["steps"]["upstream_analyzer_limitations"] == [
        "upstream-flow-depth-limit-reached"
    ]
    assert public["coverage"]["effects"]["truncation_reason"] == (
        "per-step-collection-limit"
    )
    assert public["coverage"]["effects"]["by_kind"]["reads"][
        "effective_limit"
    ] == 8
