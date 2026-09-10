"""Both call representations must respect Python's lexical bindings."""

import pytest

from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services.extraction_service import (
    resolve_call_edges,
    resolve_call_observations,
)
from llm_wiki_cli.services.documentation_queries import DocumentationGraphQueryService
from llm_wiki_cli.services.knowledge_graph import (
    GraphConcept,
    KnowledgeGraphInputs,
    materialize_typed_graph,
)


def _inventory(tmp_path, sources):
    for name, source in sources.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    return PythonExtractor().extract(
        str(tmp_path), deep=True, source_files=list(sources)
    )


def _both(inventory, caller="run", name=None):
    return [
        next(
            edge
            for edge in edges
            if edge["from"] == {"file": "app.py", "symbol": caller}
            and (name is None or edge["name"] == name)
        )
        for edges in (
            resolve_call_edges(inventory),
            resolve_call_observations(inventory)["observations"],
        )
    ]


@pytest.mark.parametrize("name", ["set", "dict", "open", "len", "id", "type", "format"])
def test_builtins_do_not_bind_to_unrelated_definitions(tmp_path, name):
    inventory = _inventory(
        tmp_path,
        {
            "app.py": f"def run():\n    return {name}()\n",
            "other/cache.py": f"def {name}(*args): return None\n",
        },
    )
    for edge in _both(inventory):
        assert edge["to"]["file"] is None
        assert edge["kind"] == "external"


@pytest.mark.parametrize(
    "source,caller",
    [
        ("def run(set):\n    return set()\n", "run"),
        ("def run():\n    set = factory()\n    return set()\n", "run"),
        ("def run():\n    return (lambda set: set())(factory())\n", "run"),
        (
            "def outer(set):\n    @tool\n    def inner():\n        return set()\n",
            "inner",
        ),
        ("def run():\n    return [set() for set in values]\n", "run"),
        ("set = factory()\ndef run():\n    return set()\n", "run"),
        (
            "def run():\n    from cache import set\n    del set\n    return set()\n",
            "run",
        ),
        (
            "def run():\n    from cache import set\n    try:\n        work()\n    except Exception as set:\n        return set()\n",
            "run",
        ),
        (
            "def configure():\n    global set\n    set = factory()\ndef run():\n    return set()\n",
            "run",
        ),
        (
            "def set(): return None\nfrom external_sdk import *\ndef run():\n    return set()\n",
            "run",
        ),
    ],
)
def test_shadowed_or_uncertain_builtins_remain_unresolved(tmp_path, source, caller):
    inventory = _inventory(
        tmp_path, {"app.py": source, "other/cache.py": "def set(): return None\n"}
    )
    for edge in _both(inventory, caller, "set"):
        assert edge["to"]["file"] is None
        assert edge["kind"] == "unresolved"


def test_local_import_does_not_leak_into_other_functions(tmp_path):
    inventory = _inventory(
        tmp_path,
        {
            "app.py": "def local():\n    from cache import set\n    return set()\ndef run():\n    return set()\n",
            "cache.py": "def set(): return None\n",
        },
    )
    for edge in _both(inventory, "local"):
        assert edge["to"] == {"file": "cache.py", "symbol": "set"}
    for edge in _both(inventory):
        assert edge["to"]["file"] is None
        assert edge["kind"] == "external"


def test_aliases_imported_receivers_and_local_shadowing_keep_real_targets(tmp_path):
    inventory = _inventory(
        tmp_path,
        {
            "app.py": "import cache as service\nfrom cache import set as imported\ndef set(): return None\n"
            "alias = set\ndef run():\n    alias()\n    imported()\n    service.set()\n",
            "cache.py": "def set(): return None\n",
        },
    )
    for name, target in (
        ("alias", "app.py"),
        ("imported", "cache.py"),
        ("service.set", "cache.py"),
    ):
        for edge in _both(inventory, name=name):
            assert edge["kind"] == "internal"
            assert edge["to"] == {"file": target, "symbol": "set"}


def test_external_import_and_unbound_name_do_not_borrow_internal_homonyms(tmp_path):
    inventory = _inventory(
        tmp_path,
        {
            "app.py": "from external_sdk import Client\ndef run():\n    Client()\n    missing()\n",
            "other/models.py": "class Client: pass\ndef missing(): return None\n",
        },
    )
    for name in ("Client", "missing"):
        for edge in _both(inventory, name=name):
            assert edge["to"]["file"] is None


def test_recursive_functions_and_methods_keep_real_self_edges(tmp_path):
    inventory = _inventory(
        tmp_path,
        {
            "app.py": "def run():\n    return run()\nclass Service:\n"
            "    def act(self):\n        return self.act()\n"
            "    @classmethod\n    def create(cls):\n        return cls.create()\n",
        },
    )
    for caller in ("run", "Service.act", "Service.create"):
        for edge in _both(inventory, caller):
            assert edge["from"] == edge["to"]
            assert edge["kind"] == "internal"


def test_reexports_and_imported_submodules_keep_qualified_targets(tmp_path):
    inventory = _inventory(
        tmp_path,
        {
            "app.py": "import pkg.child\nfrom pkg import exported\ndef run():\n    pkg.child.work()\n    exported()\n",
            "pkg/__init__.py": "from .child import work as exported\n__all__ = ['exported']\n",
            "pkg/child.py": "def work(): return None\n",
        },
    )
    for name in ("pkg.child.work", "exported"):
        for edge in _both(inventory, name=name):
            assert edge["to"] == {"file": "pkg/child.py", "symbol": "work"}


def test_staticmethod_alias_does_not_make_parameter_a_receiver(tmp_path):
    inventory = _inventory(
        tmp_path,
        {
            "app.py": "from builtins import staticmethod as static\nclass Service:\n"
            "    @static\n    def act(self):\n        return self.act()\n",
        },
    )
    for edge in _both(inventory, "Service.act"):
        assert edge["to"]["file"] is None
        assert edge["kind"] == "unresolved"


def test_package_self_relative_child_reexport_is_resolved(tmp_path):
    inventory = _inventory(tmp_path, {
        "app.py": "from pkg import child\ndef run():\n    return child.work()\n",
        "pkg/__init__.py": "from . import child\n__all__ = ['child']\n",
        "pkg/child.py": "def work(): return None\n",
    })
    for edge in _both(inventory):
        assert edge["to"] == {"file": "pkg/child.py", "symbol": "work"}


def test_queries_and_materialized_graph_do_not_restore_phantom_builtin_hops(tmp_path):
    inventory = _inventory(
        tmp_path,
        {
            "app.py": "def run():\n    return set()\n",
            "other/cache.py": "def set(): return None\n",
        },
    )
    for edges in (
        resolve_call_edges(inventory),
        resolve_call_observations(inventory)["observations"],
    ):
        service = DocumentationGraphQueryService(inventory, call_edges=edges)
        callers = service.callers("other/cache.py:set")
        assert callers["found"] is True
        assert callers["callers"] == []
        callees = service.callees("app.py:run")
        assert all(item.get("file") is None for item in callees["callees"])
        graph = materialize_typed_graph(
            KnowledgeGraphInputs(
                inventory=inventory,
                concepts=[
                    GraphConcept(
                        locator="llm-wiki://modules/app",
                        concept_kind="source-module",
                        source_path="app.py",
                        page_id="app",
                    ),
                    GraphConcept(
                        locator="llm-wiki://modules/cache",
                        concept_kind="source-module",
                        source_path="other/cache.py",
                        page_id="cache",
                    ),
                ],
                call_edges=edges,
            )
        )
        calls = [edge for edge in graph["edges"] if edge["kind"] == "calls"]
        assert calls
        assert all(edge["resolution"] == "external" for edge in calls)
