"""One captured decision owns conservative constructor method resolution."""

from __future__ import annotations

from typing import Any, cast

import pytest

from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services.python_calls import (
    PythonCallContext,
    resolve_python_call,
    resolve_python_call_decision,
)
from llm_wiki_cli.services.imports import build_module_path_resolver
from llm_wiki_cli.services.extraction_service import (
    resolve_call_edges,
    resolve_call_observations,
)
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
    _minimal_oversized_query_result,
)
from llm_wiki_cli.services.knowledge_graph import (
    KnowledgeGraphInputs,
    GraphConcept,
    materialize_typed_graph,
)

CLASS = "class Batch:\n    def cap(self, values):\n        return values[:3]\n"


def collect(tmp_path, sources):
    for name, source in sources.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    return PythonExtractor().extract(
        str(tmp_path), deep=True, source_files=list(sources)
    )


def decision(inventory, filepath="app.py", caller="run", member="cap"):
    data = inventory[filepath]
    fn = next(fn for fn in data["functions"] if fn["name"] == caller)
    index = next(
        index for index, call in enumerate(fn["calls"]) if call["name"] == member
    )
    return resolve_python_call_decision(
        fn["calls"][index],
        filepath,
        data,
        PythonCallContext(fn, index, build_module_path_resolver(inventory)),
    )


@pytest.mark.parametrize(
    "body",
    [
        "return Batch().cap(values)",
        "batch = Batch()\n    return batch.cap(values)",
        "Alias = Batch\n    return Alias().cap(values)",
        "batch = Batch()\n    alias = batch\n    return alias.cap(values)",
    ],
)
def test_actual_direct_assigned_and_alias_class_method_decision_is_immutable(
    tmp_path, body
):
    inventory = collect(
        tmp_path, {"app.py": CLASS + "def run(values):\n    " + body + "\n"}
    )
    value = decision(inventory)
    assert (value.file, value.symbol, value.kind) == ("app.py", "Batch.cap", "internal")
    assert value.reason == "constructed-receiver-resolved"
    assert value.location is not None and value.constructor is not None
    assert value.location["column"] == 11
    with pytest.raises(TypeError):
        cast(dict[str, Any], value.constructor)["line"] = 1
    returned = value.metadata()
    returned["constructor"]["line"] = -1
    assert value.constructor["line"] > 0
    data = inventory["app.py"]
    fn = data["functions"][0]
    index = next(i for i, call in enumerate(fn["calls"]) if call["name"] == "cap")
    assert (
        resolve_python_call(
            fn["calls"][index],
            "app.py",
            data,
            PythonCallContext(fn, index, build_module_path_resolver(inventory)),
        )
        == value.as_tuple()
    )


@pytest.mark.parametrize(
    "prefix,expression",
    [
        ("from policy import Batch as Alias", "Alias"),
        ("import policy as module", "module.Batch"),
        ("from exported import Alias", "Alias"),
    ],
)
def test_imports_and_reexports_require_actual_captured_class_authority(
    tmp_path, prefix, expression
):
    inventory = collect(
        tmp_path,
        {
            "app.py": prefix
            + "\ndef run(values): return "
            + expression
            + "().cap(values)\n",
            "policy.py": CLASS,
            "exported.py": "from policy import Batch as Alias\n__all__ = ['Alias']\n",
        },
    )
    value = decision(inventory)
    assert (
        value.file == "policy.py"
        and value.symbol == "Batch.cap"
        and value.kind == "internal"
    )
    assert (
        value.constructor is not None and value.constructor["source_path"] == "app.py"
    )


@pytest.mark.parametrize(
    "body",
    [
        "batch = factory()\n    return batch.cap(values)",
        "return factory().cap(values)",
        "batch = Batch()\n    batch = other\n    return batch.cap(values)",
        "batch = Batch()\n    batch.cap = other\n    return batch.cap(values)",
        "if flag:\n        batch = Batch()\n    else:\n        batch = other\n    return batch.cap(values)",
        "return getattr(Batch(), name)(values)",
    ],
)
def test_factories_rebindings_and_dynamic_targets_never_invent_method_edges(
    tmp_path, body
):
    inventory = collect(
        tmp_path,
        {
            "app.py": CLASS
            + "def factory(): return Batch()\ndef run(values):\n    "
            + body
            + "\n"
        },
    )
    edges = [
        edge
        for edge in resolve_call_observations(inventory)["observations"]
        if edge["from"]["symbol"] == "run"
    ]
    assert not any(
        edge["to"] == {"file": "app.py", "symbol": "Batch.cap"} for edge in edges
    )
    assert any(
        edge["kind"] == "unresolved" and edge.get("reason") and edge.get("location")
        for edge in edges
    )


@pytest.mark.parametrize(
    "policy,reason",
    [
        ("def Batch(): return other\n", "constructor-not-class"),
        (
            "class Batch(Base):\n    def cap(self, values): return values\n",
            "constructor-dispatch-unsupported",
        ),
        (
            "class Batch(metaclass=Meta):\n    def cap(self, values): return values\n",
            "constructor-dispatch-unsupported",
        ),
        (
            "class Batch:\n    def __new__(cls): return other\n    def cap(self, values): return values\n",
            "constructor-dispatch-unsupported",
        ),
        (
            "class Batch:\n    def __init__(obj): obj.cap = other\n    def cap(self, values): return values\n",
            "constructor-member-replaced",
        ),
        (
            "class Batch:\n    @property\n    def cap(self): return other\n",
            "constructor-member-replaced",
        ),
    ],
)
def test_imported_factories_and_unsupported_dispatch_are_qualified(
    tmp_path, policy, reason
):
    inventory = collect(
        tmp_path,
        {
            "app.py": "from policy import Batch\ndef run(values): return Batch().cap(values)\n",
            "policy.py": policy,
        },
    )
    value = decision(inventory)
    assert value.file is None and value.kind == "unresolved" and value.reason == reason
    assert value.location is not None
    assert value.location["line"] == 2 and value.location["column"] == 24


@pytest.mark.parametrize(
    "policy",
    [
        CLASS + CLASS,
        "class Batch:\n    def cap(self, values): return values\n    def cap(self, values): return other\n",
    ],
)
def test_duplicate_class_or_method_never_selects_first_or_last(tmp_path, policy):
    inventory = collect(
        tmp_path,
        {
            "app.py": "from policy import Batch\ndef run(values): return Batch().cap(values)\n",
            "policy.py": policy,
        },
    )
    value = decision(inventory)
    assert value.file is None and value.kind == "ambiguous"
    assert value.candidates and len(value.candidates) == 2
    assert len({candidate["line"] for candidate in value.candidates}) == 2


@pytest.mark.parametrize(
    "corruption",
    ["missing-marker", "unknown-field", "reasons", "bool-location", "missing-dispatch"],
)
def test_imported_target_metadata_must_validate_before_eligible_true_is_trusted(
    tmp_path, corruption
):
    inventory = collect(
        tmp_path,
        {
            "app.py": "from policy import Batch\ndef run(values): return Batch().cap(values)\n",
            "policy.py": CLASS,
        },
    )
    target = inventory["policy.py"]
    cls = target["classes"][0]
    if corruption == "missing-marker":
        target.pop("python_constructor_facts_version")
    elif corruption == "unknown-field":
        cls["python_constructor_dispatch"]["guessed"] = True
    elif corruption == "reasons":
        cls["python_constructor_dispatch"]["reasons"] = "safe"
    elif corruption == "bool-location":
        target["functions"] = [
            {
                "name": "bad",
                "calls": [{"name": "bad", "line": True}],
                "call_bindings": [{"kind": "unresolved"}],
            }
        ]
    else:
        cls.pop("python_constructor_dispatch")
    value = decision(inventory)
    assert (
        value.kind == "unresolved"
        and value.file is None
        and value.reason == "constructor-dispatch-unavailable"
    )


def test_legacy_constructor_fact_absence_cannot_borrow_new_capability(tmp_path):
    inventory = collect(
        tmp_path, {"app.py": CLASS + "def run(values): return Batch().cap(values)\n"}
    )
    inventory["app.py"]["functions"][0].pop("call_bindings")
    value = decision(inventory)
    assert value.kind == "unresolved" and value.file is None


def test_display_expression_cannot_replace_structured_constructor_authority(tmp_path):
    inventory = collect(
        tmp_path, {"app.py": CLASS + "def run(values): return Batch().cap(values)\n"}
    )
    inventory["app.py"]["functions"][0]["calls"][0]["attr"] = (
        "fabricated.bad().receiver"
    )
    assert decision(inventory).symbol == "Batch.cap"


def test_alignment_failure_preserves_actual_invocation_location(tmp_path):
    inventory = collect(
        tmp_path, {"app.py": CLASS + "def run(values): return Batch().cap(values)\n"}
    )
    inventory["app.py"]["functions"][0]["call_bindings"].pop()
    value = decision(inventory)
    assert (
        value.kind == "unresolved" and value.reason == "call-binding-alignment-invalid"
    )
    assert value.location == {"source_path": "app.py", "line": 4, "column": 24}


def test_all_adapters_preserve_exact_method_and_constructor_locations_and_graph_column(
    tmp_path,
):
    inventory = collect(
        tmp_path,
        {
            "app.py": "from policy import Batch\ndef run(values):\n    batch = Batch()\n    return batch.cap(values)\n",
            "policy.py": CLASS,
        },
    )
    legacy = next(
        edge for edge in resolve_call_edges(inventory) if edge["name"] == "batch.cap"
    )
    observed = next(
        edge
        for edge in resolve_call_observations(inventory)["observations"]
        if edge["name"] == "batch.cap"
    )
    assert legacy == observed
    assert observed["location"] == {"source_path": "app.py", "line": 4, "column": 11}
    assert (
        observed["constructor"]["line"] == 3 and observed["constructor"]["column"] == 12
    )
    service = DocumentationGraphQueryService(
        inventory, call_edges=resolve_call_edges(inventory)
    )
    caller = service.callers("policy.py:Batch.cap")["callers"][0]
    assert (
        caller["location"] == observed["location"]
        and caller["constructor"] == observed["constructor"]
    )
    graph = materialize_typed_graph(
        KnowledgeGraphInputs(
            inventory=inventory,
            call_edges=resolve_call_observations(inventory),
            concepts=[
                GraphConcept(
                    locator="llm-wiki://modules/app",
                    concept_kind="source-module",
                    source_path="app.py",
                    page_id="app",
                ),
                GraphConcept(
                    locator="llm-wiki://entities/Batch",
                    concept_kind="source-entity",
                    source_path="policy.py",
                    page_id="Batch",
                    symbol="Batch",
                    occurrence=1,
                ),
            ],
        )
    )
    samples = [
        sample
        for edge in graph["edges"]
        if edge["kind"] == "calls"
        for sample in edge["evidence"]["samples"]
    ]
    method = next(
        sample
        for sample in samples
        if sample.get("target", {}).get("symbol") == "Batch.cap"
    )
    assert method["location"]["column"] == 12 and method["location"]["line"] == 4
    assert method["attributes"]["constructor"]["column"] == 12


def test_every_empty_ambiguous_and_oversized_selection_retains_static_coverage():
    service = DocumentationGraphQueryService({})
    for operation in (service.callers, service.callees):
        result = operation("missing")
        assert result["coverage"]["analysis_scope"] == "provided-inventory"
        assert result["coverage"]["runtime_completeness"] is False
        fallback = _minimal_oversized_query_result(result, total_bytes=100_000)
        assert fallback["coverage"] == result["coverage"]
        assert fallback["result_omitted"]["records_returned"] == 0


def test_optional_constructor_budget_preserves_essential_callee_records():
    inventory = {
        "app.py": {"language": "python", "classes": [], "functions": [{"name": "run"}]}
    }
    edge = {
        "from": {"file": "app.py", "symbol": "run"},
        "to": {"file": None, "symbol": "cap"},
        "kind": "unresolved",
        "line": 3,
        "name": "receiver.cap",
        "reason": "constructor-source-unavailable",
        "location": {"source_path": "app.py", "line": 3, "column": 11},
        "constructor": {
            "source_path": "app.py",
            "line": 2,
            "column": 12,
            "receiver_origin": "assigned-construction",
            "root_binding": {
                "kind": "import",
                "module": "x" * 100_000,
                "name": "Batch",
            },
            "members": [],
        },
    }
    result = DocumentationGraphQueryService(inventory, call_edges=[edge]).callees(
        "app.py:run"
    )
    assert len(result["callees"]) == 1 and result["callees"][0]["symbol"] == "cap"
    constructor = result["callees"][0]["constructor"]
    assert constructor["truncated"] and constructor["bounds"]["total_bytes"] > 100_000
    assert constructor["line"] == 2 and result["callees"][0]["location"]["line"] == 3
    assert result["coverage"]["runtime_completeness"] is False


def test_legacy_ambiguity_is_explicit_and_preserved_in_both_graph_adapters(tmp_path):
    inventory = collect(
        tmp_path,
        {
            "app.py": "from policy import Batch\ndef run(values): return Batch().cap(values)\n",
            "policy.py": CLASS + CLASS,
        },
    )
    legacy = next(
        edge for edge in resolve_call_edges(inventory) if edge["name"] == "Batch().cap"
    )
    detailed = next(
        edge
        for edge in resolve_call_observations(inventory)["observations"]
        if edge["name"] == "Batch().cap"
    )
    assert legacy["kind"] == "unresolved" and detailed["kind"] == "ambiguous"
    assert legacy["resolution"] == detailed["resolution"] == "ambiguous"
    assert (
        legacy["reason"] == detailed["reason"]
        and legacy["location"] == detailed["location"]
    )
    assert legacy["candidates"] == detailed["candidates"]
    concepts = [
        GraphConcept(
            locator="llm-wiki://modules/app",
            concept_kind="source-module",
            source_path="app.py",
        ),
        GraphConcept(
            locator="llm-wiki://modules/policy",
            concept_kind="source-module",
            source_path="policy.py",
        ),
    ]
    results = [
        materialize_typed_graph(
            KnowledgeGraphInputs(
                inventory=inventory, concepts=concepts, call_edges=[edge]
            )
        )
        for edge in (legacy, detailed)
    ]
    for graph in results:
        assert graph["edges"][0]["resolution"] == "ambiguous"
        sample = graph["edges"][0]["evidence"]["samples"][0]
        assert sample["reason"] == legacy["reason"]
        assert sample["location"]["column"] == legacy["location"]["column"] + 1
        assert sample["attributes"]["candidates"] == legacy["candidates"]


def test_actual_outer_column_capture_remains_optional_and_uses_existing_parse_pass(
    tmp_path, monkeypatch
):
    from llm_wiki_cli.extractors import python_extractor

    (tmp_path / "app.py").write_text(
        CLASS + "def run(values): return Batch().cap(values)\n"
    )
    original = python_extractor.ast.parse
    calls = []

    def observed(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(python_extractor.ast, "parse", observed)
    ordinary = PythonExtractor().extract(str(tmp_path), deep=True)
    count = len(calls)
    calls.clear()
    captured = PythonExtractor().extract(
        str(tmp_path), deep=True, capture_implementation_observations=True
    )
    assert ordinary == captured and len(calls) == count
    location = decision(captured).location
    assert location is not None and location["column"] == 24
    captured["app.py"]["functions"][0]["calls"][0].pop("column")
    legacy_location = decision(captured).location
    assert legacy_location is not None and "column" not in legacy_location


@pytest.mark.parametrize(
    "corruption", ["marker", "binding-missing", "unknown-binding-field", "alignment"]
)
def test_every_intermediate_reexport_authority_requires_constructor_capability(
    tmp_path, corruption
):
    inventory = collect(
        tmp_path,
        {
            "app.py": "from exported import Alias\ndef run(values): return Alias().cap(values)\n",
            "exported.py": "from policy import Batch as Alias\n__all__ = ['Alias']\ndef helper(): return Alias()\n",
            "policy.py": CLASS,
        },
    )
    intermediate = inventory["exported.py"]
    if corruption == "marker":
        intermediate.pop("python_constructor_facts_version")
    elif corruption == "binding-missing":
        intermediate.pop("python_bindings")
    elif corruption == "unknown-binding-field":
        intermediate["python_bindings"]["Alias"]["guessed"] = True
    else:
        intermediate["functions"][0]["call_bindings"].pop()
    value = decision(inventory)
    assert value.kind == "unresolved" and value.file is None
    assert value.reason == "constructor-dispatch-unavailable"


def test_healthy_relative_class_reexports_keep_actual_join(tmp_path):
    inventory = collect(
        tmp_path,
        {
            "app.py": "from pkg import Alias\ndef run(values): return Alias().cap(values)\n",
            "pkg/__init__.py": "from .policy import Batch as Alias\n__all__ = ['Alias']\n",
            "pkg/policy.py": CLASS,
        },
    )
    value = decision(inventory)
    assert (
        value.file == "pkg/policy.py"
        and value.symbol == "Batch.cap"
        and value.kind == "internal"
    )


@pytest.mark.parametrize("field", ["functions", "classes"])
def test_malformed_imported_collections_are_qualified_before_declaration_inspection(
    tmp_path, field
):
    inventory = collect(
        tmp_path,
        {
            "app.py": "from policy import Batch\ndef run(values): return Batch().cap(values)\n",
            "policy.py": CLASS,
        },
    )
    inventory["policy.py"][field] = None
    value = decision(inventory)
    assert value.file is None and value.kind == "unresolved"
    assert value.reason == "constructor-dispatch-unavailable"


def test_empty_supplied_inventory_with_native_view_is_not_snapshot_origin(
    tmp_path, monkeypatch
):
    from llm_wiki_cli import api
    from llm_wiki_cli.services.knowledge_consumption import load_knowledge_read_view
    from llm_wiki_cli.services.documentation_query_builder import (
        build_snapshot_documentation_query_service,
    )

    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text(CLASS)
    api.bootstrap_wiki("src", "wiki")
    view = load_knowledge_read_view(tmp_path / "wiki", snapshot_only=True)
    provided = DocumentationGraphQueryService({}, knowledge_view=view)
    assert (
        provided.callers("missing")["coverage"]["analysis_scope"]
        == "provided-inventory"
    )
    snapshot = build_snapshot_documentation_query_service(
        wiki_root=tmp_path / "wiki", limit=30
    )
    assert snapshot.callees("missing")["coverage"]["analysis_scope"] == "snapshot"
    with pytest.raises(ValueError):
        DocumentationGraphQueryService(
            {"app.py": {}}, knowledge_view=view, snapshot_call_inventory=True
        )
    with pytest.raises(ValueError):
        DocumentationGraphQueryService(
            {},
            knowledge_view=view,
            inventory_result=object(),
            snapshot_call_inventory=True,
        )
    with pytest.raises(ValueError):
        DocumentationGraphQueryService({}, snapshot_call_inventory=cast(Any, "yes"))
