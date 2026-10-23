"""Closed lexical helpers must gain targets without borrowing uncertain ones."""

from __future__ import annotations

from copy import deepcopy
import importlib
import subprocess

import pytest

from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli import api
from llm_wiki_cli.extractors.python_bindings import valid_python_constructor_facts
from llm_wiki_cli.services.data_flow import analyze_data_flow
from llm_wiki_cli.services.documentation_queries import DocumentationGraphQueryService
from llm_wiki_cli.services.entrypoints import build_flow, get_entry_points
from llm_wiki_cli.services.extraction_service import resolve_call_edges, resolve_call_observations
from llm_wiki_cli.services.extraction_service import get_inventory_result
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions


SCHEMA = "llm-wiki-python-lexical-functions/v1"
POSITIVE = "def run(value):\n    def clean(candidate):\n        return candidate.strip()\n    return clean(value)\n"


def _inventory(tmp_path, body):
    (tmp_path / "app.py").write_text(body, encoding="utf-8")
    return PythonExtractor().extract(str(tmp_path), deep=True, source_files=["app.py"])


def _edges(inventory, owner="run", name="clean"):
    return [
        [row for row in rows if row["from"] == {"file": "app.py", "symbol": owner} and row["name"] == name]
        for rows in (resolve_call_edges(inventory), resolve_call_observations(inventory)["observations"])
    ]


def test_direct_closed_helper_has_a_qualified_target_and_intact_legacy_bindings(tmp_path):
    inventory = _inventory(tmp_path, POSITIVE)
    data = inventory["app.py"]
    assert data["python_lexical_functions"]["schema_version"] == SCHEMA
    assert [fn["name"] for fn in data["functions"]] == ["run"]
    assert [fn["name"] for fn in data["nested_functions"]] == ["run.<locals>.clean"]
    assert valid_python_constructor_facts(data)
    assert data["functions"][0]["call_bindings"][0]["kind"] == "unresolved"
    for rows in _edges(inventory):
        assert len(rows) == 1
        assert rows[0]["kind"] == "internal"
        assert rows[0]["to"] == {"file": "app.py", "symbol": "run.<locals>.clean"}
        assert rows[0]["reason"] == "closed-lexical-function"
        assert rows[0]["location"]["source_path"] == "app.py"


@pytest.mark.parametrize("body", [
    "def run(value):\n    def clean():\n        return value\n    return clean()\n",
    "def run(value):\n    def clean(x):\n        return clean(x)\n    return clean(value)\n",
    "def run(value):\n    @decorate\n    def clean(x):\n        return x\n    return clean(value)\n",
    "def run(value):\n    if condition:\n        def clean(x):\n            return x\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    def clean(x):\n        return 2\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    clean = factory()\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    del clean\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    alias = clean\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    register(clean)\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    clean.__code__ = factory()\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    def mutate():\n        nonlocal clean\n        clean = other\n    mutate()\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    locals()['clean'] = other\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    ns = globals\n    ns().update(clean=other)\n    return clean(value)\n",
    "def run(value):\n    from builtins import locals as ns\n    def clean(x):\n        return x\n    ns()['clean'] = other\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    exec('clean = other')\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    frame = inspect.currentframe()\n    frame.f_locals['clean'] = other\n    return clean(value)\n",
    "def run(value):\n    def clean(x=value):\n        return x\n    return clean(value)\n",
    "def run(clean, value):\n    def clean(x):\n        return x\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    with context() as clean:\n        pass\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    try:\n        work()\n    except Exception as clean:\n        pass\n    return clean(value)\n",
    "def run(value):\n    def clean(x):\n        return x\n    match value:\n        case {'x': clean}:\n            pass\n    return clean(value)\n",
])
def test_unsupported_or_mutable_helpers_remain_unresolved(tmp_path, body):
    inventory = _inventory(tmp_path, body)
    for rows in _edges(inventory):
        assert rows and all(row["kind"] == "unresolved" and row["to"]["file"] is None for row in rows)
    assert "python_lexical_functions" not in inventory["app.py"]


@pytest.mark.parametrize("body", [
    "def run(clean, value):\n    return clean(value)\n",
    "def run(values):\n    def clean(x):\n        return x\n    return [clean(x) for clean in values]\n",
    "def run(value):\n    def clean(x):\n        return x\n    return (lambda clean: clean(value))(other)\n",
])
def test_callbacks_and_scope_shadowing_never_borrow_a_lexical_target(tmp_path, body):
    for rows in _edges(_inventory(tmp_path, body)):
        assert rows and all(row["to"]["file"] is None for row in rows)


def test_old_inventory_without_the_optional_capability_keeps_its_answers(tmp_path):
    inventory = _inventory(tmp_path, POSITIVE)
    assert "python_lexical_functions" in inventory["app.py"]
    inventory["app.py"].pop("python_lexical_functions")
    for rows in _edges(inventory):
        assert rows[0]["kind"] == "unresolved"
        assert rows[0]["reason"] == "receiver-binding-unresolved"


@pytest.mark.parametrize("mutation", ["version", "duplicate-call", "wrong-owner", "wrong-target", "missing-definition", "alignment", "duplicate-declaration", "ambiguous-owner"])
def test_bad_lexical_capabilities_fail_closed(tmp_path, mutation):
    inventory = _inventory(tmp_path, POSITIVE)
    table = inventory["app.py"]["python_lexical_functions"]
    if mutation == "version":
        table["schema_version"] = "unsupported"
    elif mutation == "duplicate-call":
        table["calls"].append(deepcopy(table["calls"][0]))
    elif mutation == "wrong-owner":
        table["functions"][0]["enclosing_symbol"] = "other"
    elif mutation == "wrong-target":
        table["calls"][0]["callee"] = "other"
    elif mutation == "missing-definition":
        table["functions"] = []
    elif mutation in {"duplicate-declaration", "ambiguous-owner"}:
        field = "nested_functions" if mutation == "duplicate-declaration" else "functions"
        duplicate = deepcopy(inventory["app.py"][field][0])
        duplicate["line"] += 10
        inventory["app.py"][field].append(duplicate)
    else:
        inventory["app.py"]["functions"][0]["call_bindings"] = []
    for rows in _edges(inventory):
        assert all(row["kind"] == "unresolved" and row["to"]["file"] is None for row in rows)


def test_two_enclosing_functions_keep_distinct_local_owners(tmp_path):
    inventory = _inventory(tmp_path, POSITIVE + POSITIVE.replace("run(value)", "second(value)"))
    for owner in ["run", "second"]:
        for rows in _edges(inventory, owner):
            assert rows[0]["to"]["symbol"] == owner + ".<locals>.clean"


def test_calls_before_the_definition_do_not_gain_a_target(tmp_path):
    inventory = _inventory(tmp_path, "def run(value):\n    clean(value)\n    def clean(x):\n        return x\n    return clean(value)\n")
    for rows in _edges(inventory):
        assert [row["kind"] for row in sorted(rows, key=lambda r: r["line"])] == ["unresolved", "internal"]


def test_flow_effects_and_caller_callee_queries_share_the_proven_target(tmp_path):
    inventory = _inventory(tmp_path, POSITIVE)
    edges = resolve_call_edges(inventory)
    service = DocumentationGraphQueryService(inventory, call_edges=edges)
    callees = service.callees("app.py:run")
    callers = service.callers("app.py:run.<locals>.clean")
    assert callees["found"] and callers["found"]
    assert any(row.get("file") == "app.py" and row.get("symbol") == "run.<locals>.clean" for row in callees["callees"])
    assert any(row.get("file") == "app.py" and row.get("symbol") == "run" for row in callers["callers"])
    entry = {"id": "api-run", "category": "api", "file": "app.py", "symbol": "run", "label": "run"}
    flow = build_flow(entry, edges)
    details = analyze_data_flow(inventory, flow, edges)
    helper = next(row for row in details["steps"] if row["symbol"] == "run.<locals>.clean")
    assert helper["inputs"][0]["name"] == "candidate"
    assert not any(point["symbol"] == "run.<locals>.clean" for point in get_entry_points(inventory))


def test_extraction_and_resolution_never_execute_project_imports(tmp_path, monkeypatch):
    (tmp_path / "app.py").write_text("raise RuntimeError('never execute')\n" + POSITIVE)
    def forbidden(*args, **kwargs):
        pytest.fail("analysis executed imports or a subprocess")
    monkeypatch.setattr(importlib, "import_module", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    inventory = PythonExtractor().extract(str(tmp_path), deep=True, source_files=["app.py"])
    assert _edges(inventory)[0][0]["kind"] == "internal"


def test_slim_inventory_does_not_add_the_optional_deep_capture(tmp_path):
    (tmp_path / "app.py").write_text(POSITIVE)
    inventory = PythonExtractor().extract(str(tmp_path), source_files=["app.py"])
    assert "python_lexical_functions" not in inventory["app.py"]


def test_normalized_and_warm_inventory_keep_the_same_lexical_target(tmp_path):
    (tmp_path / "app.py").write_text(POSITIVE)
    options = InventoryCacheOptions(enabled=True, cache_dir=str(tmp_path / "cache"))
    cold = get_inventory_result(str(tmp_path), deep=True, include_plugins=False, cache_options=options)
    warm = get_inventory_result(str(tmp_path), deep=True, include_plugins=False, cache_options=options)
    assert cold.inventory == warm.inventory
    for rows in _edges(warm.inventory):
        assert rows[0]["to"] == {"file": "app.py", "symbol": "run.<locals>.clean"}


def test_deferred_definition_headers_do_not_invent_legacy_call_sites(tmp_path):
    inventory = _inventory(tmp_path, "def run(value):\n    def clean(x):\n        return x\n    def other(x=clean(1)):\n        return x\n    return value\n")
    assert "python_lexical_functions" not in inventory["app.py"]


def test_native_fixture_and_public_queries_preserve_the_lexical_source_target(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text(POSITIVE + "__all__ = ['run']\n")
    api.bootstrap_wiki("source", "wiki")
    result = api.callees("app.py:run", src_dir="source", wiki_dir="wiki")
    assert result["found"]
    assert any(row.get("file") == "app.py" and row.get("symbol") == "run.<locals>.clean" for row in result["callees"])
    typed = api.traverse_typed_graph(
        "llm-wiki://modules/app", src_dir="source", wiki_dir="wiki",
        kinds=["calls"], resolutions=["resolved"], include_evidence=True,
    )
    assert typed["found"] and typed["edges"]
    assert any(sample.get("target", {}).get("symbol") == "run.<locals>.clean"
               for edge in typed["edges"] for sample in edge["evidence"].get("samples", []))
