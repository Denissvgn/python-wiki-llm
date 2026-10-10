"""Pure bounded presentation selection over a complete captured call trace."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .immutable import freeze

_INTERACTION_LIMIT = 30
_CALL_KINDS = frozenset({"internal", "external", "unresolved"})


def _coordinate(step: Mapping[str, Any]) -> dict[str, Any]:
    return {"file": step.get("file"), "symbol": step.get("symbol")}


@dataclass(frozen=True)
class FlowOverview:
    """Original occurrence evidence and its separate presentation selection."""

    records: tuple[Mapping[str, Any], ...]
    selected_step_indexes: tuple[int, ...]
    limit: int
    upstream_coverage: Mapping[str, Any] | None
    upstream_truncated: bool

    def __post_init__(self):
        object.__setattr__(self, "records", freeze(tuple(self.records)))
        object.__setattr__(self, "selected_step_indexes", tuple(self.selected_step_indexes))
        object.__setattr__(self, "upstream_coverage", freeze(self.upstream_coverage))

    @property
    def interactions(self) -> tuple[Mapping[str, Any], ...]:
        by_index = {record["step_index"]: record for record in self.records}
        return tuple(by_index[index]["interaction"] for index in self.selected_step_indexes)

    @property
    def counts(self) -> dict[str, Any]:
        selected = set(self.selected_step_indexes)
        boundaries = {}
        for kind in ("external", "unresolved"):
            captured = sum(record["kind"] == kind for record in self.records)
            displayed = sum(record["kind"] == kind and record["step_index"] in selected
                            for record in self.records)
            boundaries[kind] = {"captured": captured, "displayed": displayed, "omitted": captured - displayed}
        parent_gaps = {state: sum(record["parent_state"] == state for record in self.records)
                       for state in ("unknown", "conflicting")}
        return {"captured": len(self.records), "displayed": len(selected),
                "omitted": len(self.records) - len(selected), "boundaries": boundaries,
                "parent_gaps": parent_gaps,
                "conflicting_targets": sum(not record["target_coherent"] for record in self.records),
                "unknown_kinds": sum(record["kind"] not in _CALL_KINDS for record in self.records)}

    @property
    def omission_groups(self) -> tuple[Mapping[str, Any], ...]:
        """Neutral counts, not fabricated aggregate invocations."""
        selected = set(self.selected_step_indexes)
        groups: dict[tuple, dict[str, Any]] = {}
        for record in self.records:
            if record["step_index"] in selected:
                continue
            caller, callee = record["caller"], record["callee"]
            key = (record["parent_step_index"], caller.get("file"), caller.get("symbol"),
                   callee.get("file"), record["kind"], record["parent_state"], record["target_coherent"])
            group = groups.setdefault(key, {"parent_step_index": key[0], "caller": dict(caller),
                "target_module": key[3], "kind": key[4], "parent_state": key[5],
                "target_coherent": key[6], "step_indexes": []})
            group["step_indexes"].append(record["step_index"])
        return tuple(freeze({**group, "count": len(group["step_indexes"])}) for group in groups.values())


def select_flow_overview(
    flow: Mapping[str, Any], interactions: Sequence[Mapping[str, Any]], *, limit: int = 30,
) -> FlowOverview:
    """Balance depth and actual-parent siblings without rewriting call evidence."""
    if type(limit) is not int or not 0 <= limit <= _INTERACTION_LIMIT:
        raise ValueError("overview interaction limit must be an integer between 0 and 30")
    steps = flow.get("steps", [])
    if not isinstance(steps, (list, tuple)) or any(not isinstance(step, Mapping) for step in steps):
        raise ValueError("overview requires a complete captured step sequence")
    if any(type(step.get("depth")) is not int or step["depth"] < 0 for step in steps):
        raise ValueError("overview depths must be nonnegative integers")
    if len(interactions) != sum(step["depth"] > 0 for step in steps):
        raise ValueError("overview interactions must align with every complete nonentry step")
    stack: dict[int, tuple[int, Mapping[str, Any]]] = {}
    siblings: dict[int | None, int] = defaultdict(int)
    records = []
    offset = 0
    for index, step in enumerate(steps, 1):
        depth = step["depth"]
        if depth == 0:
            stack = {0: (index, step)}
            continue
        interaction = interactions[offset]
        offset += 1
        if not isinstance(interaction, Mapping):
            raise ValueError("overview interactions must be mappings")
        edge = step.get("edge") or {}
        if not isinstance(edge, Mapping):
            raise ValueError("overview edge metadata must be an object")
        parent = stack.get(depth - 1)
        parent_index = parent[0] if parent else None
        parent_coordinate = _coordinate(parent[1]) if parent else {}
        captured_caller = edge.get("from")
        captured_callee = edge.get("to")
        if captured_caller is not None and not isinstance(captured_caller, Mapping):
            raise ValueError("overview captured caller must be an object")
        if captured_callee is not None and not isinstance(captured_callee, Mapping):
            raise ValueError("overview captured callee must be an object")
        caller = dict(captured_caller) if captured_caller is not None else parent_coordinate
        callee = dict(captured_callee) if captured_callee is not None else _coordinate(step)
        parent_state = ("unknown" if parent is None or parent[1].get("kind") not in {"entry", "internal"} else "conflicting" if
                        captured_caller is not None and _coordinate(captured_caller) != parent_coordinate else
                        "captured" if captured_caller is not None else "trace")
        siblings[parent_index] += 1
        records.append({"step_index": index, "parent_step_index": parent_index,
            "depth": depth, "sibling_ordinal": siblings[parent_index],
            "kind": step.get("kind", "unknown"), "caller": caller, "callee": callee,
            "edge": edge, "interaction": interaction, "parent_state": parent_state,
            "target_coherent": _coordinate(callee) == _coordinate(step)})
        stack[depth] = (index, step)
        for deeper in [known for known in stack if known > depth]:
            del stack[deeper]
    eligible = [record for record in records if record["parent_state"] in {"captured", "trace"}
                and record["target_coherent"] and record["kind"] in _CALL_KINDS]
    eligible.sort(key=lambda record: (record["depth"], record["sibling_ordinal"], record["step_index"]))
    coverage = flow.get("coverage")
    if coverage is not None and not isinstance(coverage, Mapping):
        raise ValueError("overview upstream coverage must be an object")
    truncated = flow.get("truncated", False)
    if type(truncated) is not bool:
        raise ValueError("overview upstream truncation must be boolean")
    return FlowOverview(tuple(records), tuple(record["step_index"] for record in eligible[:limit]),
                        limit, coverage, truncated)


def trim_flow_overview(overview: FlowOverview, displayed_count: int) -> FlowOverview:
    """Reconcile the actual renderer-admitted prefix against the complete trace."""
    if type(displayed_count) is not int or not 0 <= displayed_count <= len(overview.selected_step_indexes):
        raise ValueError("displayed count must identify a prefix of selected interactions")
    return FlowOverview(overview.records, overview.selected_step_indexes[:displayed_count],
                        overview.limit, overview.upstream_coverage, overview.upstream_truncated)
