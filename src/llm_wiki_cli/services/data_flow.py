"""Static data-flow summaries for generated user-flow pages.

The analyzer combines the deep inventory effect metadata, resolved call edges,
and an already-built user flow. It performs no I/O and intentionally reports
bounded static observations rather than runtime guarantees.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

_STEP_LIMIT = 12
_EFFECT_LIMIT = 8
_TRANSFER_LIMIT = 12
_GAP_LIMIT = 12
_DATA_FLOW_OBSERVATIONS_SCHEMA = "llm-wiki-data-flow-observations/v1"
_DATA_EFFECT_OBSERVATIONS_SCHEMA = "llm-wiki-data-effect-observations/v1"
_FLOW_OBSERVATIONS_SCHEMA = "llm-wiki-flow-observations/v1"
_EFFECT_KEYS = (
    "inputs",
    "reads",
    "writes",
    "returns",
    "boundary_effects",
)

DEFAULT_DATA_FLOW_DETAILS_FLOW_LIMIT = 100


def data_flow_effective_limits(
    *,
    flow_depth: int,
    flow_limit: int = DEFAULT_DATA_FLOW_DETAILS_FLOW_LIMIT,
) -> dict[str, int]:
    """Return the public static-analysis limits used by detailed flow output."""
    return {
        "flows_per_extract": flow_limit,
        "flow_depth": flow_depth,
        "steps_per_flow": _STEP_LIMIT,
        "effects_per_kind_per_step": _EFFECT_LIMIT,
        "boundaries_per_flow": _EFFECT_LIMIT,
        "transfers_per_flow": _TRANSFER_LIMIT,
        "gaps_per_flow": _GAP_LIMIT,
    }


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


def _coverage_count(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _data_effect_coverage_index(
    observations: Mapping | None,
) -> dict[tuple[str, str], dict[str, dict]] | None:
    if observations is None:
        return None
    if observations.get("schema_version") != _DATA_EFFECT_OBSERVATIONS_SCHEMA:
        raise ValueError(
            "unsupported data-effect observation schema_version "
            f"{observations.get('schema_version')!r}"
        )
    callables = observations.get("callables")
    if not isinstance(callables, list):
        raise ValueError("data-effect observations callables must be a list")

    result: dict[tuple[str, str], dict[str, dict]] = {}
    for callable_index, observation in enumerate(callables):
        field = f"data-effect observations callables[{callable_index}]"
        if not isinstance(observation, Mapping):
            raise ValueError(f"{field} must be an object")
        filepath = observation.get("file")
        symbol = observation.get("symbol")
        if not isinstance(filepath, str) or not filepath:
            raise ValueError(f"{field}.file must be a non-empty string")
        if not isinstance(symbol, str) or not symbol:
            raise ValueError(f"{field}.symbol must be a non-empty string")
        raw_coverage = observation.get("coverage")
        if not isinstance(raw_coverage, Mapping):
            raise ValueError(f"{field}.coverage must be an object")

        normalized: dict[str, dict] = {}
        for kind in _EFFECT_KEYS:
            raw_record = raw_coverage.get(kind)
            kind_field = f"{field}.coverage.{kind}"
            if not isinstance(raw_record, Mapping):
                raise ValueError(f"{kind_field} must be an object")
            observed = _coverage_count(
                raw_record.get("observed"), f"{kind_field}.observed"
            )
            emitted = _coverage_count(
                raw_record.get("emitted"), f"{kind_field}.emitted"
            )
            omitted = _coverage_count(
                raw_record.get("omitted"), f"{kind_field}.omitted"
            )
            limit = _coverage_count(raw_record.get("limit"), f"{kind_field}.limit")
            truncated = raw_record.get("truncated")
            if emitted > observed or emitted > limit:
                raise ValueError(f"{kind_field} has inconsistent emitted count")
            if omitted != observed - emitted:
                raise ValueError(f"{kind_field} has inconsistent omitted count")
            if not isinstance(truncated, bool) or truncated != (omitted > 0):
                raise ValueError(f"{kind_field} has inconsistent truncated flag")
            normalized[kind] = {
                "observed": observed,
                "emitted": emitted,
                "omitted": omitted,
                "limit": limit,
                "truncated": truncated,
            }
        result[(filepath, symbol)] = normalized
    return result


@dataclass(frozen=True)
class DataFlowAnalysisContext:
    """Precomputed indexes shared by all data-flow analyses in one run."""

    callable_index: dict[tuple[str | None, str | None], dict]
    incoming_edges: dict[tuple, tuple[dict, ...]]
    data_effect_coverage: dict[tuple[str, str], dict[str, dict]] | None = field(
        default=None
    )


def build_data_flow_context(
    inventory: dict,
    edges: list[dict],
    *,
    data_effect_observations: Mapping | None = None,
) -> DataFlowAnalysisContext:
    """Build reusable indexes for analyzing one or more user flows."""
    return DataFlowAnalysisContext(
        callable_index=_callable_index(inventory),
        incoming_edges=_incoming_edge_queues(edges),
        data_effect_coverage=_data_effect_coverage_index(data_effect_observations),
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
                "confidence": effect.get("confidence", "unknown"),
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


def _edge_sort_key(edge: Mapping) -> tuple:
    source = edge.get("from", {}) or {}
    target = edge.get("to", {}) or {}
    line = edge.get("line")
    return (
        str(source.get("file") or ""),
        str(source.get("symbol") or ""),
        str(target.get("file") or ""),
        str(target.get("symbol") or ""),
        str(edge.get("kind") or ""),
        line if isinstance(line, int) and not isinstance(line, bool) else -1,
        str(edge.get("name") or ""),
    )


def _detailed_context(
    inventory: dict,
    edges: list[dict],
    context: DataFlowAnalysisContext | None,
    data_effect_observations: Mapping | None,
) -> DataFlowAnalysisContext:
    callable_index = (
        context.callable_index if context is not None else _callable_index(inventory)
    )
    effect_coverage = (
        _data_effect_coverage_index(data_effect_observations)
        if data_effect_observations is not None
        else context.data_effect_coverage
        if context is not None
        else None
    )
    return DataFlowAnalysisContext(
        callable_index=callable_index,
        incoming_edges=_incoming_edge_queues(sorted(edges, key=_edge_sort_key)),
        data_effect_coverage=effect_coverage,
    )


def _flow_edge_observations(
    flow: Mapping,
    incoming: dict[tuple, tuple[dict, ...]],
) -> list[tuple[int, dict, int | None]]:
    incoming_offsets: dict[tuple, int] = defaultdict(int)
    stack_by_depth: dict[int, int] = {}
    observations: list[tuple[int, dict, int | None]] = []
    for zero_based_index, step in enumerate(flow.get("steps", []) or []):
        step_index = zero_based_index + 1
        depth = int(step.get("depth", 0))
        if zero_based_index == 0:
            stack_by_depth[depth] = step_index
            continue
        edge = step.get("edge") or _legacy_edge_for_step(
            step, incoming, incoming_offsets
        )
        parent_step = _parent_step_for_depth(stack_by_depth, depth)
        if edge is not None:
            observations.append((step_index, edge, parent_step))
        stack_by_depth[depth] = step_index
        for known_depth in [
            known_depth for known_depth in stack_by_depth if known_depth > depth
        ]:
            del stack_by_depth[known_depth]
    return observations


def _raw_effects(
    steps: Iterable[Mapping],
    index: dict[tuple[str | None, str | None], dict],
    effect_coverage: dict[tuple[str, str], dict[str, dict]] | None,
) -> tuple[dict[str, int], bool]:
    counts = {key: 0 for key in _EFFECT_KEYS}
    missing_totals = False
    for step in steps:
        filepath = step.get("file")
        symbol = step.get("symbol")
        record = index.get((filepath, symbol), {})
        if not record:
            continue
        effects = record.get("data_effects", {}) or {}
        if not isinstance(effects, Mapping):
            continue
        callable_coverage = (
            effect_coverage.get((filepath, symbol))
            if effect_coverage is not None
            and isinstance(filepath, str)
            and isinstance(symbol, str)
            else None
        )
        if callable_coverage is None:
            missing_totals = True
        for key in _EFFECT_KEYS:
            values = effects.get(key, [])
            emitted = len(values) if isinstance(values, list) else 0
            coverage = (
                callable_coverage.get(key)
                if callable_coverage is not None
                else None
            )
            if coverage is None:
                counts[key] += emitted
                continue
            if coverage["emitted"] != emitted:
                raise ValueError(
                    "data-effect observation emitted count does not match inventory "
                    f"for {filepath}:{symbol}:{key}"
                )
            counts[key] += coverage["observed"]
    return counts, missing_totals


def _emitted_effects(steps: Iterable[Mapping]) -> dict[str, int]:
    return {
        key: sum(
            len(step.get(key, [])) if isinstance(step.get(key, []), list) else 0
            for step in steps
        )
        for key in _EFFECT_KEYS
    }


def _positive_source_line(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def _normalize_detailed_value(value: object, *, key: str | None = None) -> object:
    if key == "line":
        return _positive_source_line(value)
    if isinstance(value, Mapping):
        return {
            str(child_key): _normalize_detailed_value(
                child_value, key=str(child_key)
            )
            for child_key, child_value in value.items()
        }
    if isinstance(value, list):
        return [_normalize_detailed_value(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_detailed_value(item) for item in value]
    return value


def _coverage_record(
    observed: int,
    emitted: int,
    limit: int | None,
    limitations: Iterable[str],
) -> dict:
    omitted = max(0, observed - emitted)
    if emitted > observed:
        raise ValueError("coverage emitted count cannot exceed observed count")
    if limit is not None and emitted > limit:
        raise ValueError("coverage emitted count cannot exceed its limit")
    return {
        "observed": observed,
        "emitted": emitted,
        "limit": limit,
        "truncated": omitted > 0,
        "omitted": omitted,
        "limitations": sorted(set(limitations)),
    }


def _flow_step_observed_count(flow: Mapping, emitted: int) -> int:
    if flow.get("schema_version") != _FLOW_OBSERVATIONS_SCHEMA:
        return emitted
    coverage = flow.get("coverage")
    if not isinstance(coverage, Mapping):
        raise ValueError("detailed flow coverage must be an object")
    steps = coverage.get("steps")
    if not isinstance(steps, Mapping):
        raise ValueError("detailed flow coverage.steps must be an object")
    observed = _coverage_count(
        steps.get("observed"), "detailed flow coverage.steps.observed"
    )
    upstream_emitted = _coverage_count(
        steps.get("emitted"), "detailed flow coverage.steps.emitted"
    )
    omitted = _coverage_count(
        steps.get("omitted"), "detailed flow coverage.steps.omitted"
    )
    truncated = steps.get("truncated")
    if upstream_emitted != emitted:
        raise ValueError(
            "detailed flow coverage emitted count does not match flow steps"
        )
    if observed < upstream_emitted or omitted != observed - upstream_emitted:
        raise ValueError("detailed flow coverage has inconsistent counts")
    if not isinstance(truncated, bool) or truncated != (omitted > 0):
        raise ValueError("detailed flow coverage has inconsistent truncated flag")
    return observed


def _unbounded_gap_observations(
    flow: Mapping,
    edge_observations: Iterable[tuple[int, dict, int | None]],
    emitted_boundaries: list[dict],
) -> list[dict]:
    gaps: list[dict] = []

    def append(*, kind: str, step: str, target: str, line: object) -> None:
        gap = {
            "kind": kind,
            "step": step,
            "target": target,
            "line": _positive_source_line(line),
        }
        if gap not in gaps:
            gaps.append(gap)

    for _, edge, _ in edge_observations:
        if _should_report_gap(edge, emitted_boundaries):
            append(
                kind=f"{edge.get('kind', 'unknown')}_call",
                step=str(edge["from"].get("symbol") or "?"),
                target=str(edge.get("name") or edge["to"].get("symbol") or "?"),
                line=edge.get("line"),
            )
    raw_steps = flow.get("steps", []) or []
    entry = flow.get("entry", {}) or {}
    if len(raw_steps) > _STEP_LIMIT:
        append(
            kind="step_limit",
            step=str(entry.get("symbol") or "?"),
            target=f"first {_STEP_LIMIT} steps",
            line=None,
        )
    if flow.get("truncated"):
        append(
            kind="truncated_flow",
            step=str(entry.get("symbol") or "?"),
            target="depth limit",
            line=None,
        )
    return gaps


def analyze_data_flow_detailed(
    inventory: dict,
    flow: dict,
    edges: list[dict],
    *,
    context: DataFlowAnalysisContext | None = None,
    data_effect_observations: Mapping | None = None,
) -> dict:
    """Return the legacy bounded analysis plus exact, versioned coverage.

    The observations remain presentation-bounded, but every bound reports how
    many statically observed records were emitted and omitted.  Missing source
    lines in this detailed shape are ``None``; the legacy analyzer continues to
    return its historical line-zero placeholders unchanged.
    """
    detailed_context = _detailed_context(
        inventory,
        edges,
        context,
        data_effect_observations,
    )
    bounded = analyze_data_flow(
        inventory,
        flow,
        edges,
        context=detailed_context,
    )
    normalized = _normalize_detailed_value(bounded)
    assert isinstance(normalized, dict)

    raw_steps = list(flow.get("steps", []) or [])
    observed_flow_steps = _flow_step_observed_count(flow, len(raw_steps))
    edge_observations = _flow_edge_observations(
        flow, detailed_context.incoming_edges
    )
    observed_effects, missing_effect_totals = _raw_effects(
        raw_steps,
        detailed_context.callable_index,
        detailed_context.data_effect_coverage,
    )
    emitted_effects = _emitted_effects(bounded["steps"])
    upstream_truncated = bool(flow.get("truncated"))
    upstream_limitation = (
        ["upstream-flow-depth-limit-reached"] if upstream_truncated else []
    )
    effect_total_limitation = (
        ["upstream-effect-collector-totals-may-be-unavailable"]
        if missing_effect_totals
        else []
    )
    effect_kind_limit = _EFFECT_LIMIT * len(bounded["steps"]) or None
    effect_total_limit = (
        _EFFECT_LIMIT * len(bounded["steps"]) * len(_EFFECT_KEYS) or None
    )

    effect_by_kind = {
        key: _coverage_record(
            observed_effects[key],
            emitted_effects[key],
            effect_kind_limit,
            [
                "limit-applies-per-effect-kind-per-emitted-step",
                "static-effects-do-not-claim-runtime-completeness",
                *effect_total_limitation,
                *upstream_limitation,
            ],
        )
        for key in _EFFECT_KEYS
    }
    observed_effect_total = sum(observed_effects.values())
    emitted_effect_total = sum(emitted_effects.values())
    effect_coverage = _coverage_record(
        observed_effect_total,
        emitted_effect_total,
        effect_total_limit,
        [
            "limit-applies-per-effect-kind-per-emitted-step",
            "static-effects-do-not-claim-runtime-completeness",
            *effect_total_limitation,
            *upstream_limitation,
        ],
    )
    effect_coverage["by_kind"] = effect_by_kind

    observed_gaps = _unbounded_gap_observations(
        flow, edge_observations, bounded["boundaries"]
    )
    normalized["schema_version"] = _DATA_FLOW_OBSERVATIONS_SCHEMA
    normalized["coverage"] = {
        "steps": _coverage_record(
            observed_flow_steps,
            len(bounded["steps"]),
            _STEP_LIMIT,
            [
                "flow-steps-are-statically-inferred",
                *upstream_limitation,
            ],
        ),
        "effects": effect_coverage,
        "transfers": _coverage_record(
            len(edge_observations),
            len(bounded["transfers"]),
            _TRANSFER_LIMIT,
            [
                "transfers-follow-the-bounded-static-flow",
                *upstream_limitation,
            ],
        ),
        "boundaries": _coverage_record(
            observed_effects["boundary_effects"],
            len(bounded["boundaries"]),
            _EFFECT_LIMIT,
            [
                "boundary-detection-is-static",
                *effect_total_limitation,
                *upstream_limitation,
            ],
        ),
        "gaps": _coverage_record(
            len(observed_gaps),
            len(bounded["gaps"]),
            _GAP_LIMIT,
            [
                "absence-of-a-gap-does-not-claim-runtime-completeness",
                *upstream_limitation,
            ],
        ),
    }
    return normalized
