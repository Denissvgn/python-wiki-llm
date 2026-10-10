"""Independent expectations for the explicitly owned Window workflow fixture.

These pure checks consume supplied bytes and observations. They never import
the product, read files, execute source, or decide whether a runtime is admitted.
Matching syntax or bytes does not establish behavior or semantic acceptance.
"""

from __future__ import annotations

import ast
from collections.abc import Collection, Mapping
from copy import deepcopy
from typing import Any


SOURCE_CALLERS = frozenset({
    ("policy.py", "public_clip"),
    ("client.py", "direct_clip"),
    ("client.py", "assigned_clip"),
})
FORBIDDEN_SOURCE_CALLERS = frozenset({("client.py", "dynamic_clip")})
GAP_STATES = frozenset({"missing", "ambiguous", "unavailable", "unknown", "unsupported", "partial", "omitted", "stale"})
REQUIRED_GAP_STATES = {
    "missing": frozenset({"missing"}),
    "ambiguous": frozenset({"ambiguous"}),
    "behavior": frozenset({"unavailable", "unknown", "unsupported"}),
}
_LIMITS = frozenset({"3", "1", "0", "-1", "9"})


def assert_clip_behavior(observations: Mapping[str, Any], change: str) -> None:
    """Check hand-declared outputs for input [0, 1, 2, 3, 4], not provider facts.

The caller alone may run this known synthetic fixture in its named admitted
oracle phase. ``before`` is first-N/default3; ``body`` is last-N/default3;
``default`` is first-N/default2. Nonpositive limits always produce an empty list.
"""
    assert change in {"before", "body", "default"}, "Unknown owned behavior variant"
    assert isinstance(observations, Mapping) and set(observations) == {"default", "limits"}
    limits = observations["limits"]
    assert isinstance(limits, Mapping) and set(limits) == _LIMITS
    for value in (observations["default"], *limits.values()):
        assert isinstance(value, list) and all(type(item) is int for item in value), "Behavior result must retain integer lists"
    expected_limits = ({"3": [2, 3, 4], "1": [4], "0": [], "-1": [], "9": [0, 1, 2, 3, 4]}
                       if change == "body" else
                       {"3": [0, 1, 2], "1": [0], "0": [], "-1": [], "9": [0, 1, 2, 3, 4]})
    expected_default = {"before": [0, 1, 2], "body": [2, 3, 4], "default": [0, 1]}[change]
    assert dict(limits) == expected_limits, "Owned limit controls disagree with the declared behavior"
    assert observations["default"] == expected_default, "Owned default control disagrees with the declared behavior"


def _clip(tree: ast.Module) -> ast.FunctionDef:
    windows = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Window"]
    assert len(windows) == 1, "Owned source needs one top-level Window"
    methods = [node for node in windows[0].body if isinstance(node, ast.FunctionDef) and node.name == "clip"]
    assert len(methods) == 1, "Owned source needs one Window.clip declaration"
    return methods[0]


def _default(node: ast.FunctionDef) -> ast.Constant:
    positional = [*node.args.posonlyargs, *node.args.args]
    defaults = dict(zip((arg.arg for arg in positional[-len(node.args.defaults):]), node.args.defaults, strict=True)) if node.args.defaults else {}
    defaults.update({arg.arg: value for arg, value in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True) if value is not None})
    value = defaults.get("limit")
    assert isinstance(value, ast.Constant) and type(value.value) is int, "Owned limit default must be an integer literal"
    return value


def _signature(node: ast.FunctionDef) -> tuple[Any, ...]:
    return (node.name, ast.dump(node.args, include_attributes=False),
            ast.dump(node.returns, include_attributes=False) if node.returns is not None else None,
            tuple(ast.dump(decorator, include_attributes=False) for decorator in node.decorator_list))


def _slice(node: ast.FunctionDef, *, last: bool) -> None:
    slices = [item for item in ast.walk(ast.Module(body=node.body, type_ignores=[]))
              if isinstance(item, ast.Subscript) and isinstance(item.value, ast.Name) and item.value.id == "values"]
    assert len(slices) == 1 and isinstance(slices[0].slice, ast.Slice), "Owned clip needs one values slice"
    selected = slices[0].slice
    assert selected.step is None
    if last:
        assert selected.upper is None and selected.lower is not None
        expected = ast.parse("max(0, len(values) - limit)", mode="eval").body
        assert ast.dump(selected.lower, include_attributes=False) == ast.dump(expected, include_attributes=False), "After body change must select the admitted bounded last-N window"
    else:
        assert selected.lower is None and isinstance(selected.upper, ast.Name) and selected.upper.id == "limit", "Before/default change must select the first limit values"


def assert_source_change(before: bytes, after: bytes, change: str) -> None:
    """Check the exact admitted syntax change, independently of fingerprints.

``body`` changes only Window.clip's body, retaining its signature/default3.
``default`` changes only its limit default3 to2, retaining the first-N body.
All other AST declarations remain identical. Separate behavior controls are
required; AST comparison alone is not runtime evidence.
"""
    assert type(before) is bytes and type(after) is bytes and before != after
    assert change in {"body", "default"}, "Unknown owned source mutation"
    old, new = ast.parse(before.decode("utf-8")), ast.parse(after.decode("utf-8"))
    old_clip, new_clip = _clip(old), _clip(new)
    assert _default(old_clip).value == 3
    _slice(old_clip, last=False)
    normalized = deepcopy(new)
    normalized_clip = _clip(normalized)
    if change == "body":
        assert _signature(old_clip) == _signature(new_clip), "Body edit changed the source contract"
        assert _default(new_clip).value == 3
        _slice(new_clip, last=True)
        assert ast.dump(ast.Module(body=old_clip.body, type_ignores=[])) != ast.dump(ast.Module(body=new_clip.body, type_ignores=[]))
        normalized_clip.body = deepcopy(old_clip.body)
    else:
        assert _default(new_clip).value == 2
        _slice(new_clip, last=False)
        assert ast.dump(ast.Module(body=old_clip.body, type_ignores=[])) == ast.dump(ast.Module(body=new_clip.body, type_ignores=[])), "Default edit changed the executable body"
        _default(normalized_clip).value = 3
    assert ast.dump(old, include_attributes=False) == ast.dump(normalized, include_attributes=False), "Mutation changed an unrelated source declaration"


def assert_read_only(before: Mapping[str, bytes], after: Mapping[str, bytes], *,
                     allowed_changes: Collection[str] = ()) -> None:
    """Require supplied artifact bytes/presence to remain exact outside a list.

No filesystem access occurs. Default permission is zero changed paths; callers
must separately authorize and name every owning write phase and allowed path.
"""
    assert isinstance(before, Mapping) and isinstance(after, Mapping)
    assert not isinstance(allowed_changes, (str, bytes))
    assert all(isinstance(path, str) and type(raw) is bytes for path, raw in (*before.items(), *after.items()))
    allowed = set(allowed_changes)
    assert all(isinstance(path, str) for path in allowed)
    changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
    assert changed <= allowed, "Unexpected artifact mutation, creation, or deletion: " + ", ".join(sorted(changed - allowed))


def assert_coverage_gap(payload: Mapping[str, Any], requirement_id: str, *,
                        states: Collection[str] = GAP_STATES) -> None:
    """Unanswered requirements must keep their exact ID and explicit gap.

    An honest unavailable/partial/stale result may pass a gap-preservation control, but
    does not count as a solved behavioral or native requirement.
    Omitted is a bounded-read gap, not proof of absence; callers checking known
    missing or ambiguous controls must narrow ``states`` (see REQUIRED_GAP_STATES).
"""
    assert isinstance(payload, Mapping) and isinstance(requirement_id, str) and requirement_id
    assert not isinstance(states, (str, bytes)) and set(states) <= GAP_STATES and states
    rows = [row for row in payload["coverage"] if row["requirement_id"] == requirement_id]
    assert len(rows) == 1, "Required gap identity was dropped or duplicated"
    row = rows[0]
    assert row["state"] in states and row["satisfied"] is False
    assert isinstance(row["reason"], str) and row["reason"], "Required gap lost its reason"
    assert row in payload["omissions"] and payload["state"] != "covered", "Unanswered requirement became a success"


def assert_coverage_preserved(canonical: Mapping[str, Any], expanded: Mapping[str, Any]) -> None:
    """Require compact expansion to retain exact independently checked facts/gaps."""
    for field in ("facts", "coverage", "omissions", "limitations"):
        assert expanded[field] == canonical[field], "Compact expansion changed " + field
    assert expanded["canonical"]["result_id"] == canonical["result_id"]
