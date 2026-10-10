"""Possible-owner joins retain semantic hazards without duplicating graph paths."""

from __future__ import annotations

import ast
import cProfile
import json
import os
import pstats
import subprocess
import sys

import pytest

from llm_wiki_cli.extractors.python_bindings import (
    UNKNOWN,
    _BindingAnalyzer,
    analyze_python_bindings,
)


def _owner(token, blocked=()):
    return {
        "kind": "constructed-instance",
        "_allocation": token,
        "constructor": {
            "root_binding": {"kind": "local", "symbol": "Batch"},
            "members": [],
            "line": 1,
            "column": 0,
        },
        "blocked_members": list(blocked),
    }


def _collector_calls(profile):
    stats = getattr(pstats.Stats(profile), "stats")
    assert isinstance(stats, dict)
    return sum(
        total
        for (_, _, name), (_, total, _, _, _) in stats.items()
        if name == "collect"
    )


def _graph_work_budget(roots):
    """One collector root call and one call for each unique container slot."""
    seen = set()
    slots = 0

    def walk(value):
        nonlocal slots
        if not isinstance(value, (dict, list, tuple)) or id(value) in seen:
            return
        seen.add(id(value))
        slots += len(value)
        for item in value.values() if isinstance(value, dict) else value:
            walk(item)

    for value in roots:
        walk(value)
    return len(roots) + slots


def test_repeated_rebinding_and_path_join_keep_possible_owner_cardinality():
    analyzer = _BindingAnalyzer(ast.parse(""))
    owner = _owner(1)
    analyzer.state.env = {"batch": owner, "maybe": dict(UNKNOWN)}
    analyzer.state.possible_targets = {"maybe": [owner]}
    name = ast.Name(id="maybe", ctx=ast.Load())

    for _ in range(12):
        value = analyzer.expression(name, analyzer.state.env, set())
        analyzer.bind_value("maybe", value, analyzer.state.env, name)
        analyzer.join_states(
            [analyzer.state.snapshot(), analyzer.state.snapshot()],
            analyzer.state.env,
            [UNKNOWN, UNKNOWN],
        )
        targets = analyzer.state.possible_targets["maybe"]
        assert len(targets) == 1
        assert targets[0] is analyzer.state.env["batch"]


def test_collector_visits_shared_containers_within_graph_slot_budget():
    analyzer = _BindingAnalyzer(ast.parse(""))
    owner = _owner(1)
    namespace = {"kind": "receiver-namespace", "target": owner, "qualified": True}
    effect = {"kind": "namespace-mutator", "namespace": namespace, "method": "update"}
    analyzer.state.env = {f"alias_{i}": owner for i in range(20)}
    analyzer.state.possible_targets = {"write": [effect] * 64}
    states = [analyzer.state.snapshot(), analyzer.state.snapshot()]
    budget = _graph_work_budget([vars(state) for state in states])
    profile = cProfile.Profile()

    profile.enable()
    analyzer.join_states(states, analyzer.state.env)
    profile.disable()

    assert _collector_calls(profile) <= budget
    assert len(analyzer.state.possible_targets["write"]) == 1


def test_join_retains_distinct_allocations_descriptors_and_mutation_aliases():
    analyzer = _BindingAnalyzer(ast.parse(""))
    first, second = _owner(1, ["left"]), _owner(2)
    qualified = {"kind": "receiver-namespace", "target": first, "qualified": True}
    unqualified = {**qualified, "qualified": False}
    analyzer.state.env = {"batch": first, "alias": first, "other": second}
    effects = [
        {"kind": "namespace-mutator", "namespace": qualified, "method": "update"},
        {"kind": "namespace-mutator", "namespace": unqualified, "method": "update"},
        {"kind": "namespace-mutator", "namespace": qualified, "method": "pop"},
        {"kind": "namespace-getter", "target": first},
        {"kind": "namespace-getter", "target": second},
        {"kind": "import", "module": "pkg", "name": "", "target_members": ["one"]},
        {"kind": "import", "module": "pkg", "name": "", "target_members": ["two"]},
    ]
    analyzer.state.possible_targets = {"maybe": [first, second], "helper": effects}
    left, right = analyzer.state.snapshot(), analyzer.state.snapshot()
    right.env["batch"]["blocked_members"] = ["right"]

    analyzer.join_states([left, right], analyzer.state.env)
    owners = analyzer.state.possible_targets["maybe"]
    retained = analyzer.state.possible_targets["helper"]

    assert len(owners) == 2
    assert [value["_allocation"] for value in owners] == [1, 2]
    assert len(retained) == len(effects)
    assert owners[0] is analyzer.state.env["batch"] is analyzer.state.env["alias"]
    assert owners[1] is analyzer.state.env["other"]
    assert set(owners[0]["blocked_members"]) == {"left", "right"}
    assert retained[0]["namespace"]["target"] is owners[0]
    assert retained[4]["target"] is owners[1]

    analyzer.invalidate_target(retained[0]["namespace"]["target"], analyzer.state.env, "cap")
    assert "cap" in analyzer.state.env["alias"]["blocked_members"]
    assert "cap" not in owners[1]["blocked_members"]


def test_repeated_expression_transfers_keep_public_positive_and_negative_facts():
    source = (
        "class Batch:\n"
        "    def cap(self): pass\n"
        "def run(flag):\n"
        "    batch = Batch()\n"
        "    maybe = batch if flag else None\n"
        + "    maybe = maybe\n    0 if flag else 1\n" * 12
        + "    maybe.cap()\n    batch.cap()\n"
    )
    tree = ast.parse(source)
    captured = analyze_python_bindings(tree)
    calls = {
        node.func.value.id: captured.calls[id(node)]
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
    }

    assert calls["maybe"]["kind"] == "unresolved"
    assert calls["maybe"]["reason"] == "receiver-path-conflict"
    assert calls["batch"] == {
        "kind": "constructed-receiver",
        "constructor": {
            "root_binding": {"kind": "local", "symbol": "Batch"},
            "members": [],
            "line": 4,
            "column": 12,
        },
        "member": "cap",
        "receiver_origin": "assigned-construction",
    }


@pytest.mark.parametrize("namespace_first", [True, False])
def test_captured_allocation_mutation_reaches_all_live_variants_in_either_env_order(
    namespace_first,
):
    analyzer = _BindingAnalyzer(ast.parse(""))
    captured = _owner(1, ["captured"])
    stale_namespace_owner = _owner(1, ["namespace"])
    canonical_owner = _owner(1, ["canonical"])
    possible_owner = _owner(1, ["possible"])
    other = _owner(2)
    namespace = {
        "kind": "receiver-namespace",
        "target": stale_namespace_owner,
        "qualified": False,
    }
    entries = [("namespace", namespace), ("original", canonical_owner)]
    if not namespace_first:
        entries.reverse()
    analyzer.state.env = dict([*entries, ("second", other)])
    analyzer.state.possible_targets = {
        "maybe": [{"kind": "unresolved", "_possible_targets": [possible_owner]}],
        "other": [other],
    }

    analyzer.invalidate_target(captured, analyzer.state.env, "cap")

    expected = {"captured", "namespace", "canonical", "possible", "cap"}
    for value in (captured, stale_namespace_owner, canonical_owner, possible_owner):
        assert set(value["blocked_members"]) == expected
    assert other["blocked_members"] == []
    assert analyzer.class_mutations == {}
    assert analyzer.import_mutations == []


@pytest.mark.parametrize("seed", [1, 2, 6])
def test_joined_getter_captured_owner_is_unresolved_and_second_owner_internal(
    tmp_path, seed
):
    # A fresh producer process fixes hash order and uses the actual installed
    # binding analyzer, PythonExtractor, and public observation resolver together.
    probe = r'''
import ast, json, sys
from pathlib import Path
import llm_wiki_cli.extractors.python_bindings as bindings
import llm_wiki_cli.extractors.python_extractor as extractor
from llm_wiki_cli.services.extraction_service import resolve_call_observations

assert extractor.analyze_python_bindings is bindings.analyze_python_bindings
source = (
    "class Batch:\n    def cap(self): pass\n"
    "def run():\n    first=Batch()\n    original=first\n    second=Batch()\n"
    "    namespace=object.__getattribute__(first, (first := second) and '__dict__')\n"
    "    namespace['cap']=replacement\n    original.cap()\n    second.cap()\n"
)
root = Path(sys.argv[1])
(root / "app.py").write_text(source)
tree = ast.parse(source)
facts = bindings.analyze_python_bindings(tree)
direct = {
    node.func.value.id: facts.calls[id(node)]["kind"]
    for node in ast.walk(tree)
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Attribute)
    and node.func.attr == "cap"
}
inventory = extractor.PythonExtractor().extract(
    str(root), deep=True, source_files=["app.py"]
)
rows = {
    row["line"]: row["kind"]
    for row in resolve_call_observations(inventory)["observations"]
    if row["from"]["symbol"] == "run" and row["name"].endswith("cap")
}
print(json.dumps({"direct": direct, "rows": rows}))
'''
    result = subprocess.run(
        [sys.executable, "-c", probe, str(tmp_path)],
        env={**os.environ, "PYTHONHASHSEED": str(seed)},
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    report = json.loads(result.stdout)
    assert report["direct"] == {
        "original": "unresolved",
        "second": "constructed-receiver",
    }
    assert report["rows"] == {"9": "unresolved", "10": "internal"}
