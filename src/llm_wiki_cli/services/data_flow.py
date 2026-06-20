"""Static data-flow summaries for generated user-flow pages.

The analyzer combines the deep inventory effect metadata, resolved call edges,
and an already-built user flow. It performs no I/O and intentionally reports
bounded static observations rather than runtime guarantees.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass

_STEP_LIMIT = 12
_EFFECT_LIMIT = 8
_TRANSFER_LIMIT = 12
_GAP_LIMIT = 12

_COMMON_STATIC_CALLS = frozenset(
    {
        "bool",
        "dict",
        "float",
        "int",
        "len",
        "list",
        "object",
        "Path",
        "repr",
        "set",
        "str",
        "tuple",
    }
)


def _iter_callables(inventory: dict) -> Iterable[tuple[str, str, dict]]:
    for filepath, data in inventory.items():
        for fn in data.get("functions", []):
            yield filepath, fn["name"], fn
        for cls in data.get("classes", []):
            for method in cls.get("methods", []):
                yield filepath, f"{cls['name']}.{method['name']}", method
        for fn in data.get("nested_functions", []):
            yield filepath, fn["name"], fn


def _callable_index(inventory: dict) -> dict[tuple[str | None, str | None], dict]:
    return {
        (filepath, symbol): fn for filepath, symbol, fn in _iter_callables(inventory)
    }


def _incoming_edge_queues(edges: list[dict]) -> dict[tuple, tuple[dict, ...]]:
    queues: dict[tuple, deque] = defaultdict(deque)
    for edge in edges:
        key = (edge["to"]["file"], edge["to"]["symbol"], edge["kind"])
        queues[key].append(edge)
    return {key: tuple(value) for key, value in queues.items()}


@dataclass(frozen=True)
class DataFlowAnalysisContext:
    """Precomputed indexes shared by all data-flow analyses in one run."""

    callable_index: dict[tuple[str | None, str | None], dict]
    incoming_edges: dict[tuple, tuple[dict, ...]]


def build_data_flow_context(
    inventory: dict, edges: list[dict]
) -> DataFlowAnalysisContext:
    """Build reusable indexes for analyzing one or more user flows."""
    return DataFlowAnalysisContext(
        callable_index=_callable_index(inventory),
        incoming_edges=_incoming_edge_queues(edges),
    )


def _effect_list(effects: dict, key: str) -> list[dict]:
    values = effects.get(key, [])
    return list(values[:_EFFECT_LIMIT])


def _expr_text(expr: dict) -> str:
    return str(expr.get("value") or expr.get("name") or expr.get("kind") or "?")


def _call_args(call: dict | None) -> list[str]:
    if not call:
        return []
    args = [_expr_text(arg) for arg in call.get("args", [])]
    args.extend(
        f"{kw.get('name', '?')}={_expr_text(kw)}" for kw in call.get("kwargs", [])
    )
    return args


def _call_target(call: dict | None, edge: dict) -> str:
    if call:
        return str(call.get("attr") or call.get("name") or edge.get("name") or "?")
    return str(edge.get("name") or edge["to"].get("symbol") or "?")


def _target_matches(call: dict, edge: dict) -> bool:
    target = str(call.get("attr") or call.get("name") or "")
    name = str(call.get("name") or "")
    edge_name = str(edge.get("name") or "")
    edge_symbol = str(edge["to"].get("symbol") or "")
    return (
        target == edge_name
        or name == edge_name
        or name == edge_symbol
        or target.rsplit(".", 1)[-1] == edge_symbol
    )


def _find_call(
    edge: dict, index: dict[tuple[str | None, str | None], dict]
) -> dict | None:
    caller = index.get((edge["from"]["file"], edge["from"]["symbol"]), {})
    for call in caller.get("calls", []):
        if call.get("line") == edge.get("line") and _target_matches(call, edge):
            return call
    return None


def _call_label(edge: dict, call: dict | None) -> tuple[str, list[str]]:
    target = _call_target(call, edge)
    args = _call_args(call)
    if not args:
        return f"{target}(data not statically known)", ["data not statically known"]
    return f"{target}({', '.join(args)})", args


def _step_summary(
    step: dict, index: dict[tuple[str | None, str | None], dict], step_index: int
) -> dict:
    record = index.get((step.get("file"), step.get("symbol")), {})
    effects = record.get("data_effects", {}) or {}
    return {
        "index": step_index,
        "depth": step.get("depth", 0),
        "file": step.get("file"),
        "symbol": step.get("symbol"),
        "kind": step.get("kind"),
        "inputs": _effect_list(effects, "inputs"),
        "reads": _effect_list(effects, "reads"),
        "writes": _effect_list(effects, "writes"),
        "returns": _effect_list(effects, "returns"),
        "boundary_effects": _effect_list(effects, "boundary_effects"),
    }


def _boundary_rows(step_summary: dict) -> list[dict]:
    rows = []
    for effect in step_summary["boundary_effects"]:
        rows.append(
            {
                "step": step_summary["symbol"],
                "step_index": step_summary["index"],
                "kind": effect.get("kind", "unknown"),
                "target": effect.get("target", "?"),
                "line": effect.get("line", 0),
            }
        )
    return rows


def _edge_is_explained_by_boundary(edge: dict, boundaries: list[dict]) -> bool:
    line = edge.get("line")
    caller = edge["from"]["symbol"]
    return any(
        boundary.get("line") == line and boundary.get("step") == caller
        for boundary in boundaries
    )


def _should_report_gap(edge: dict, boundaries: list[dict]) -> bool:
    if edge.get("kind") not in {"external", "unresolved"}:
        return False
    if _edge_is_explained_by_boundary(edge, boundaries):
        return False
    target = str(edge.get("name") or edge["to"].get("symbol") or "")
    return target.rsplit(".", 1)[-1] not in _COMMON_STATIC_CALLS


def _add_gap(gaps: list[dict], *, kind: str, step: str, target: str, line: int) -> None:
    if len(gaps) >= _GAP_LIMIT:
        return
    gap = {"kind": kind, "step": step, "target": target, "line": line}
    if gap not in gaps:
        gaps.append(gap)


def _legacy_edge_for_step(
    step: dict,
    incoming: dict[tuple, tuple[dict, ...]],
    incoming_offsets: dict[tuple, int],
) -> dict | None:
    key = (step.get("file"), step.get("symbol"), step.get("kind"))
    edges_for_step = incoming.get(key, ())
    offset = incoming_offsets[key]
    if offset >= len(edges_for_step):
        return None
    incoming_offsets[key] = offset + 1
    return edges_for_step[offset]


def _parent_step_for_depth(stack: dict[int, int], depth: int) -> int | None:
    if depth <= 0:
        return None
    return stack.get(depth - 1)


def analyze_data_flow(
    inventory: dict,
    flow: dict,
    edges: list[dict],
    *,
    context: DataFlowAnalysisContext | None = None,
) -> dict:
    """Return a bounded static data-flow summary for one built user flow."""
    if context is None:
        context = build_data_flow_context(inventory, edges)
    index = context.callable_index
    incoming = context.incoming_edges
    incoming_offsets: dict[tuple, int] = defaultdict(int)
    steps: list[dict] = []
    transfers: list[dict] = []
    boundaries: list[dict] = []
    gaps: list[dict] = []
    edge_by_step_index: dict[int, tuple[dict, int | None]] = {}
    stack_by_depth: dict[int, int] = {}

    for zero_based_index, step in enumerate(flow.get("steps", [])[:_STEP_LIMIT]):
        step_index = zero_based_index + 1
        depth = int(step.get("depth", 0))
        summary = _step_summary(step, index, step_index)
        steps.append(summary)
        new_boundaries = _boundary_rows(summary)
        boundaries.extend(new_boundaries[: max(0, _EFFECT_LIMIT - len(boundaries))])
        if zero_based_index == 0:
            stack_by_depth[depth] = step_index
            continue
        edge = step.get("edge") or _legacy_edge_for_step(
            step, incoming, incoming_offsets
        )
        parent_step = _parent_step_for_depth(stack_by_depth, depth)
        if edge is not None:
            edge_by_step_index[step_index] = (edge, parent_step)
        stack_by_depth[depth] = step_index
        for deeper in [
            known_depth for known_depth in stack_by_depth if known_depth > depth
        ]:
            del stack_by_depth[deeper]

    for step_index, (edge, parent_step) in edge_by_step_index.items():
        if len(transfers) >= _TRANSFER_LIMIT:
            break
        call = edge if "args" in edge or "kwargs" in edge else _find_call(edge, index)
        call_label, args = _call_label(edge, call)
        transfer = {
            "from": edge["from"]["symbol"],
            "to": edge["to"]["symbol"],
            "from_step": parent_step,
            "to_step": step_index,
            "line": edge.get("line", 0),
            "call": call_label,
            "arguments": args,
            "kind": edge.get("kind", "unknown"),
        }
        transfers.append(transfer)
        if _should_report_gap(edge, boundaries):
            _add_gap(
                gaps,
                kind=f"{edge.get('kind', 'unknown')}_call",
                step=edge["from"]["symbol"],
                target=str(edge.get("name") or edge["to"].get("symbol") or "?"),
                line=edge.get("line", 0),
            )

    if len(flow.get("steps", [])) > _STEP_LIMIT:
        _add_gap(
            gaps,
            kind="step_limit",
            step=flow["entry"]["symbol"],
            target=f"first {_STEP_LIMIT} steps",
            line=0,
        )
    if flow.get("truncated"):
        _add_gap(
            gaps,
            kind="truncated_flow",
            step=flow["entry"]["symbol"],
            target="depth limit",
            line=0,
        )

    return {
        "id": flow["entry"].get("id"),
        "entry": flow["entry"],
        "steps": steps,
        "transfers": transfers,
        "boundaries": boundaries,
        "gaps": gaps,
        "truncated": bool(flow.get("truncated")),
    }
