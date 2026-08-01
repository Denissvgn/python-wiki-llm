"""Focused scale checks for bounded typed-graph materialization and reads."""

from __future__ import annotations

import json
import re

from tests.knowledge_m3_scale_gate import (
    M3_SCALE_GATE_RECORD_PATH,
    build_m3_scale_gate_record,
    build_stress_graph,
    build_stress_service,
)
from tests.test_knowledge_queries import (
    MODULE_LOCATOR,
    _ready_view,
)

_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def test_high_fanout_graph_keeps_evidence_and_query_output_bounded(tmp_path):
    view = _ready_view(tmp_path)
    ordered_graph = build_stress_graph(view, reverse=False)
    reversed_graph = build_stress_graph(view, reverse=True)

    assert ordered_graph == reversed_graph

    ordered = build_stress_service(view, ordered_graph, limit=7)
    reversed_service = build_stress_service(view, reversed_graph, limit=7)
    outgoing = ordered.traverse_typed_graph(
        MODULE_LOCATOR,
        direction="outgoing",
        kinds=["depends_on"],
    )
    shuffled_outgoing = reversed_service.traverse_typed_graph(
        MODULE_LOCATOR,
        direction="outgoing",
        kinds=["depends_on"],
    )

    assert outgoing == shuffled_outgoing
    assert outgoing["bounds"]["edges"] == {
        "total": 300,
        "returned": 7,
        "truncated": True,
    }
    assert len(json.dumps(outgoing, sort_keys=True).encode("utf-8")) < 20_000

    calls = ordered.traverse_typed_graph(
        "llm-wiki://entities/AccountService",
        direction="outgoing",
        kinds=["calls"],
        include_evidence=True,
    )
    evidence = calls["edges"][0]["evidence"]
    assert calls["bounds"]["edges"] == {
        "total": 1,
        "returned": 1,
        "truncated": False,
    }
    assert evidence["observed"] == 200
    assert evidence["unique"] == 200
    assert evidence["emitted"] == 3
    assert evidence["omitted"] == 197
    assert len(evidence["samples"]) == 3
    assert len(json.dumps(calls, sort_keys=True).encode("utf-8")) < 20_000


def test_recorded_scale_gate_is_reproducible_current_and_sanitized(tmp_path):
    ordered = build_m3_scale_gate_record(tmp_path / "ordered")
    reversed_inputs = build_m3_scale_gate_record(
        tmp_path / "reversed",
        reverse=True,
    )
    recorded = json.loads(M3_SCALE_GATE_RECORD_PATH.read_text(encoding="utf-8"))

    assert ordered == reversed_inputs == recorded
    assert recorded["result"] == "pass"
    assert all(check["passed"] for check in recorded["budgets"].values())
    assert recorded["measurements"]["sections"] == {
        "pages": 1,
        "total": 6,
        "by_ownership": {
            "generated": 1,
            "mixed": 1,
            "semantic": 1,
            "unknown": 3,
        },
    }
    assert recorded["measurements"]["evidence"] == {
        "observed": 502,
        "unique": 502,
        "emitted": 305,
        "omitted": 197,
        "by_kind": {
            "calls": {
                "edges": 1,
                "observed": 200,
                "unique": 200,
                "emitted": 3,
                "omitted": 197,
            },
            "contains": {
                "edges": 2,
                "observed": 2,
                "unique": 2,
                "emitted": 2,
                "omitted": 0,
            },
            "depends_on": {
                "edges": 300,
                "observed": 300,
                "unique": 300,
                "emitted": 300,
                "omitted": 0,
            },
        },
    }

    encoded = json.dumps(recorded, sort_keys=True)
    assert str(tmp_path) not in encoded
    assert set(recorded["environment"]) == {
        "execution",
        "filesystem",
        "network",
        "python",
        "serialization",
        "tool",
    }

    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for key, item in value.items():
                yield from strings(key)
                yield from strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from strings(item)

    assert not any(
        value.startswith(("/", "\\\\"))
        or _WINDOWS_ABSOLUTE_RE.match(value)
        or value.casefold().startswith("file:")
        for value in strings(recorded)
    )
