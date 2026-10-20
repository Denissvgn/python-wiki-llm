"""Class import coverage must not change declaration or load-order contracts."""

import pytest

from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services.dependencies import (
    build_dependency_graph,
    build_dependency_observations,
    detect_cycles,
)
from llm_wiki_cli.services.relationships import build_entity_relationship_summaries


SOURCE = """from typing import TYPE_CHECKING as TC
import module_dep
def top():
    import function_dep
    class Local:
        import function_class_dep
        def method(self):
            import local_method_dep
class Outer:
    import class_dep as class_alias
    from .missing import Unknown as unresolved_name
    CONSTANT = 1
    __all__ = ["not_a_module_export"]
    if TC:
        import class_type_dep
    else:
        import class_runtime_dep
    def method(self):
        import method_dep
        if TC:
            import method_type_dep
        def inner():
            import nested_function_dep
        class NestedInMethod:
            import method_class_dep
    async def async_method(self):
        import async_dep
    @staticmethod
    def static_method(value):
        from . import static_dep
    class Nested:
        import nested_class_dep
        def method(self):
            import nested_method_dep
    if __name__ == "__main__":
        pass
if TC:
    class TypeOnly:
        import guarded_class_dep
        def method(self):
            import guarded_method_dep
def factory():
    @decorator
    def wrapper():
        import decorated_dep
    return wrapper
"""

# Independent lexical occurrence, execution-phase and line oracle.
EXPECTED = [
    ("typing", "TYPE_CHECKING", "", 1),
    ("module_dep", "module_dep", "", 2),
    ("function_dep", "function_dep", "deferred", 4),
    ("function_class_dep", "function_class_dep", "deferred", 6),
    ("local_method_dep", "local_method_dep", "deferred", 8),
    ("class_dep", "class_alias", "", 10),
    (".missing", "Unknown", "", 11),
    ("class_type_dep", "class_type_dep", "type_checking", 15),
    ("class_runtime_dep", "class_runtime_dep", "", 17),
    ("method_dep", "method_dep", "deferred", 19),
    ("method_type_dep", "method_type_dep", "type_checking", 21),
    ("nested_function_dep", "nested_function_dep", "deferred", 23),
    ("method_class_dep", "method_class_dep", "deferred", 25),
    ("async_dep", "async_dep", "deferred", 27),
    (".", "static_dep", "deferred", 30),
    ("nested_class_dep", "nested_class_dep", "", 32),
    ("nested_method_dep", "nested_method_dep", "deferred", 34),
    ("guarded_class_dep", "guarded_class_dep", "type_checking", 39),
    ("guarded_method_dep", "guarded_method_dep", "type_checking", 41),
    ("decorated_dep", "decorated_dep", "deferred", 45),
]


def _extract(tmp_path):
    (tmp_path / "app.py").write_bytes(SOURCE.encode())
    extractor = PythonExtractor()
    inventory = extractor.extract(
        str(tmp_path), deep=True, capture_import_observations=True
    )
    return inventory, extractor.last_import_observations


def test_class_import_occurrences_scopes_and_locations_are_complete(tmp_path):
    inventory, sidecar = _extract(tmp_path)
    assert sidecar is not None
    records = inventory["app.py"]["imports"]
    locations = sidecar["observations"]
    assert [
        (r["module"], r["name"], r.get("scope", ""), loc["line"])
        for r, loc in zip(records, locations, strict=True)
    ] == EXPECTED
    assert [loc["import_index"] for loc in locations] == list(range(20))
    assert all(loc["source_path"] == "app.py" for loc in locations)
    assert records[5] == {
        "module": "class_dep", "name": "class_alias", "type": "import"
    }
    assert records[6] == {
        "module": ".missing", "name": "Unknown", "alias": "unresolved_name",
        "type": "from",
    }
    assert (tmp_path / "app.py").read_bytes() == SOURCE.encode()


def test_import_walk_does_not_duplicate_or_promote_declarations(tmp_path):
    inventory, _ = _extract(tmp_path)
    entry = inventory["app.py"]
    assert [c["name"] for c in entry["classes"]] == ["Outer", "TypeOnly"]
    assert [f["name"] for f in entry["functions"]] == ["top", "factory"]
    assert [f["name"] for f in entry["nested_functions"]] == ["wrapper"]
    outer = entry["classes"][0]
    assert [m["name"] for m in outer["methods"]] == [
        "method", "async_method", "static_method"
    ]
    assert outer["methods"][0]["params"] == []
    assert outer["methods"][2]["params"] == [
        {"name": "value", "kind": "positional_or_keyword", "type": ""}
    ]
    assert "constants" not in entry
    assert "has_all" not in entry
    assert "main_block" not in entry


def test_class_dependencies_include_deferred_but_load_only_eager_edges(tmp_path):
    inventory, sidecar = _extract(tmp_path)
    dependencies = {
        module if module != "." else name
        for module, name, _, _ in EXPECTED
        if module not in {"typing", ".missing"}
    }
    for name in dependencies:
        inventory[name + ".py"] = {
            "language": "python", "classes": [], "functions": [], "imports": []
        }
    inventory["class_dep.py"]["imports"] = [{"module": "app", "name": "app"}]
    inventory["method_dep.py"]["imports"] = [{"module": "app", "name": "app"}]
    graph = build_dependency_graph(inventory)
    assert {target for source, target in graph["edges"] if source == "app.py"} == {
        name + ".py" for name in dependencies
    }
    assert {target for source, target in graph["import_time_edges"] if source == "app.py"} == {
        "module_dep.py", "class_dep.py", "class_runtime_dep.py", "nested_class_dep.py"
    }
    assert detect_cycles(graph, import_time_only=True) == [["app.py", "class_dep.py"]]
    observations = build_dependency_observations(inventory, import_observations=sidecar)
    missing = [r for r in observations["observations"] if r["module"] == ".missing"]
    assert len(missing) == 1
    assert missing[0]["resolution"] == "unresolved"
    assert missing[0]["line"] == 11


@pytest.mark.parametrize("guard", ["TC", "typing.TYPE_CHECKING"], ids=["alias", "attribute"])
def test_method_type_guard_else_restores_deferred_and_class_runtime_scope(tmp_path, guard):
    source = f"""from typing import TYPE_CHECKING as TC
class C:
    def method(self):
        if {guard}:
            import only_type
        else:
            import on_call
    import on_load
"""
    (tmp_path / "app.py").write_bytes(source.encode())
    imports = PythonExtractor().extract(str(tmp_path), deep=True)["app.py"]["imports"]
    assert [(r["module"], r.get("scope", "")) for r in imports] == [
        ("typing", ""), ("only_type", "type_checking"),
        ("on_call", "deferred"), ("on_load", ""),
    ]


@pytest.mark.parametrize("model", ["pydantic", "typeddict"])
@pytest.mark.parametrize("scope", ["class", "method", "function"])
def test_local_import_is_dependency_not_module_model_binding(tmp_path, model, scope):
    base = "BaseModel" if model == "pydantic" else "TypedDict"
    package = "pydantic" if model == "pydantic" else "typing"
    (tmp_path / "base.py").write_text(
        f"from {package} import {base}\nclass Model({base}): pass\n"
    )
    source = {
        "class": "class Container:\n    from base import Model\n",
        "method": "class Container:\n    def method(self):\n        from base import Model\n",
        "function": "def factory():\n    from base import Model\n",
    }[scope]
    (tmp_path / "app.py").write_text(source + "class Child(Model): pass\n")
    inventory = PythonExtractor().extract(str(tmp_path), deep=True)
    entry = inventory["app.py"]
    child = next(c for c in entry["classes"] if c["name"] == "Child")
    assert "model_kind" not in child
    assert any(r["module"] == "base" for r in entry["imports"])
    summaries = build_entity_relationship_summaries(inventory)["classes"]
    child_summary = next(c for c in summaries if c["name"] == "Child")
    assert child_summary["bases"][0]["file"] is None
    model_summary = next(c for c in summaries if c["file"] == "base.py")
    assert any(r["file"] == "app.py" and r["kind"] == "import" for r in model_summary["references"])


def test_method_import_cannot_shadow_real_module_model_or_required_alias(tmp_path):
    (tmp_path / "base.py").write_text(
        "from typing import TypedDict\nclass Model(TypedDict): pass\n"
    )
    (tmp_path / "other.py").write_text("class Model: pass\n")
    (tmp_path / "app.py").write_text(
        "from base import Model\nfrom typing import Required as Presence\n"
        "class Container:\n    def method(self):\n"
        "        from other import Model\n"
        "        from typing import NotRequired as Presence\n"
        "class Child(Model, total=False):\n    field: Presence[str]\n"
    )
    entry = PythonExtractor().extract(str(tmp_path), deep=True)["app.py"]
    child = next(c for c in entry["classes"] if c["name"] == "Child")
    assert child["model_kind"] == "typeddict"
    assert child["attributes"][0]["required"] is True


@pytest.mark.parametrize("model", ["pydantic", "typeddict"])
@pytest.mark.parametrize("style", ["alias", "namespace"])
def test_real_module_model_binding_survives_a_shadowing_method_import(tmp_path, model, style):
    base = "BaseModel" if model == "pydantic" else "TypedDict"
    package = "pydantic" if model == "pydantic" else "typing"
    (tmp_path / "base.py").write_text(
        f"from {package} import {base}\nclass Model({base}): pass\n"
    )
    (tmp_path / "other.py").write_text("class Model: pass\n")
    if style == "alias":
        imports, shadow, reference = "from base import Model as Parent", "from other import Model as Parent", "Parent"
    else:
        imports, shadow, reference = "import base as models", "import other as models", "models.Model"
    (tmp_path / "app.py").write_text(
        f"{imports}\nclass Container:\n    def method(self):\n        {shadow}\n"
        f"class Child({reference}): pass\n"
    )
    inventory = PythonExtractor().extract(str(tmp_path), deep=True)
    entry = inventory["app.py"]
    child = next(c for c in entry["classes"] if c["name"] == "Child")
    assert child["model_kind"] == model
    child_summary = next(c for c in build_entity_relationship_summaries(inventory)["classes"] if c["name"] == "Child")
    assert child_summary["bases"][0]["file"] == "base.py"


def test_legacy_inventory_without_binding_facts_retains_model_inference():
    from llm_wiki_cli.extractors.python_contracts import finalize_inventory_model_kinds

    child = {"name": "Child", "bases": ["Parent"], "attributes": []}
    inventory = {
        "base.py": {"classes": [{"name": "Model", "model_kind": "pydantic"}]},
        "child.py": {
            "imports": [{"type": "from", "module": "base", "name": "Model", "alias": "Parent"}],
            "classes": [child],
        },
    }
    finalize_inventory_model_kinds(
        inventory, module_candidates=lambda module, source: {"base.py"} if module == "base" else set()
    )
    assert child["model_kind"] == "pydantic"


def test_method_import_cannot_rewrite_global_response_model_alias(tmp_path):
    from llm_wiki_cli.services.api_contracts import build_static_api_contracts

    (tmp_path / "models.py").write_text("class Result: pass\nclass Wrong: pass\n")
    (tmp_path / "app.py").write_text(
        "from fastapi import FastAPI\nfrom models import Result as PublicResult\n"
        "app = FastAPI()\nclass Container:\n    def method(self):\n"
        "        from models import Wrong as PublicResult\n"
        "@app.get('/item', response_model=PublicResult)\ndef item(): pass\n"
    )
    inventory = PythonExtractor().extract(str(tmp_path), deep=True)
    response = build_static_api_contracts(inventory)["operations"][0]["responses"][0]
    assert response["model"] == "Result"


@pytest.mark.parametrize("module_import", [False, True], ids=["local-only", "module-bound"])
def test_cli_dispatch_requires_module_binding_not_a_method_import(tmp_path, module_import):
    from llm_wiki_cli.services.entrypoints import detect_entry_points

    (tmp_path / "commands").mkdir()
    (tmp_path / "commands/run.py").write_text("def run(): pass\n")
    source = "from commands import run as command\n" if module_import else ""
    (tmp_path / "app.py").write_text(
        source + "class Container:\n    def method(self):\n"
        "        from commands import run as command\n"
        "_COMMAND_MODULES = {'execute': command}\n"
    )
    inventory = PythonExtractor().extract(str(tmp_path), deep=True)
    detected = detect_entry_points(inventory, root=tmp_path, include_plugins=False)
    commands = [e for e in detected.entries if e.get("label") == "execute"]
    assert len(commands) == int(module_import)


def test_local_import_is_not_a_module_function_annotation_binding(tmp_path):
    from llm_wiki_cli.services.bootstrap_runtime import _build_relationships

    (tmp_path / "models.py").write_text("class Item: pass\n")
    (tmp_path / "app.py").write_text(
        "class Container:\n    def method(self):\n        from models import Item\n"
        "def consume(value: Item): pass\n"
    )
    inventory = PythonExtractor().extract(str(tmp_path), deep=True)
    legacy = _build_relationships(inventory)[("Item", "models.py")]
    assert [r["rel"] for r in legacy] == ["imported_by"]
    item = next(c for c in build_entity_relationship_summaries(inventory)["classes"] if c["file"] == "models.py")
    assert [r["kind"] for r in item["references"]] == ["import"]
