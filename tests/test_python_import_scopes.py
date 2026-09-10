"""Python module candidates need an import root, not a matching leaf name."""

from llm_wiki_cli.services.dependencies import (
    build_dependency_graph,
    build_dependency_observations,
    detect_cycles,
)
from llm_wiki_cli.services.extraction_service import get_inventory_result
from llm_wiki_cli.services.imports import build_module_path_resolver
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions


def _module(*imports, **extra):
    return {
        "language": "python",
        "classes": [],
        "functions": [],
        "imports": [
            {"module": name, "name": name, "type": "import"} for name in imports
        ],
        **extra,
    }


def test_nested_stdlib_names_do_not_create_dependencies_or_cycles():
    inventory = {
        "apps/a/src/api.py": _module("logging", "json", "types"),
        "apps/a/src/utils/logging.py": _module("logging"),
        "apps/b/src/utils/logging.py": _module("logging"),
        "libs/helpers/json.py": _module(),
        "libs/helpers/types.py": _module(),
    }
    resolver = build_module_path_resolver(inventory)
    for name in ("logging", "json", "types"):
        assert resolver.candidates(name, "apps/a/src/api.py") == set()
    graph = build_dependency_graph(inventory)
    assert graph["edges"] == []
    assert detect_cycles(graph, import_time_only=True) == []


def test_nearest_src_root_isolated_and_relative_paths_remain_exact():
    inventory = {
        "apps/a/src/api.py": _module("core.settings"),
        "apps/a/src/core/settings.py": _module(),
        "apps/b/src/core/settings.py": _module(),
        "apps/a/src/core/worker.py": _module(),
    }
    resolver = build_module_path_resolver(inventory)
    assert resolver.candidates("core.settings", "apps/a/src/api.py") == {
        "apps/a/src/core/settings.py"
    }
    assert resolver.candidates(".settings", "apps/a/src/core/worker.py") == {
        "apps/a/src/core/settings.py"
    }
    assert resolver.candidates("settings", "apps/a/src/api.py") == set()
    assert resolver.candidates("core.settings", "unscoped.py") == set()


def test_local_stdlib_shadowing_and_root_packages_remain_resolvable():
    inventory = {
        "app.py": _module("logging"),
        "logging.py": _module(),
        "pkg/__init__.py": _module(),
        "pkg/child.py": _module(),
        "elsewhere/pkg/child.py": _module(),
    }
    resolver = build_module_path_resolver(inventory)
    assert resolver.candidates("logging", "app.py") == {"logging.py"}
    assert resolver.import_candidates("pkg", "child", "app.py", import_type="from") == {
        "pkg/child.py"
    }


def test_declared_custom_roots_and_shared_package_imports(tmp_path):
    sources = {
        "apps/a/pyproject.toml": '[project]\nname="a"\n[tool.setuptools.package-dir]\n""="code"\n',
        "libs/shared/pyproject.toml": '[project]\nname="shared"\n[tool.setuptools.packages.find]\nwhere=["lib"]\n',
        "apps/a/code/app.py": "import local\nfrom shared.client import Client\n",
        "apps/a/code/local.py": "VALUE=1\n",
        "libs/shared/lib/shared/client.py": "class Client: pass\n",
        "libs/shared/lib/shared/__init__.py": "",
        "apps/b/code/local.py": "VALUE=2\n",
    }
    for name, text in sources.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    result = get_inventory_result(str(tmp_path), deep=True, include_empty=True)
    resolver = build_module_path_resolver(result.inventory)
    assert resolver.candidates("local", "apps/a/code/app.py") == {
        "apps/a/code/local.py"
    }
    assert resolver.candidates("shared.client", "apps/a/code/app.py") == {
        "libs/shared/lib/shared/client.py"
    }
    assert resolver.candidates("local", "unscoped.py") == set()


def test_ambiguous_declared_packages_are_not_unconditional_graph_edges():
    inventory = {
        "app.py": _module("shared"),
        "one/shared/__init__.py": _module(
            python_import_scope={"root": "one", "search_roots": ["one"]}
        ),
        "two/shared/__init__.py": _module(
            python_import_scope={"root": "two", "search_roots": ["two"]}
        ),
    }
    observation = build_dependency_observations(inventory)["observations"][0]
    assert observation["resolution"] == "ambiguous"
    assert len(observation["candidates"]) == 2
    graph = build_dependency_graph(inventory)
    assert graph["edges"] == []
    assert graph["unresolved"][0]["kind"] == "ambiguous"


def test_changed_packaging_roots_are_restamped_on_cached_inventory(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    for name in ("one", "two"):
        (project / name).mkdir()
        (project / name / "model.py").write_text(
            "class Model: pass\n", encoding="utf-8"
        )
    (project / "app.py").write_text(
        "from model import Model\ndef use(): return Model()\n", encoding="utf-8"
    )
    marker = project / "pyproject.toml"
    marker.write_text(
        '[project]\nname="example"\n[tool.setuptools.package-dir]\n""="one"\n',
        encoding="utf-8",
    )
    options = InventoryCacheOptions(enabled=True, cache_dir=str(tmp_path / "cache"))
    first = get_inventory_result(str(project), deep=True, cache_options=options)
    assert build_module_path_resolver(first.inventory).candidates(
        "model", "app.py"
    ) == {"one/model.py"}
    marker.write_text(marker.read_text().replace('"one"', '"two"'), encoding="utf-8")
    warm = get_inventory_result(str(project), deep=True, cache_options=options)
    cold = get_inventory_result(str(project), deep=True)
    assert warm.cache_stats is not None
    assert warm.cache_stats.hits > 0
    assert warm.inventory == cold.inventory
    assert build_module_path_resolver(warm.inventory).candidates("model", "app.py") == {
        "two/model.py"
    }


def test_unknown_packaging_roots_do_not_fall_back_to_guesses(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="example"\n[tool.setuptools]\npackage-dir="dynamic"\n',
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text("import helper\n", encoding="utf-8")
    (tmp_path / "helper.py").write_text("VALUE=1\n", encoding="utf-8")
    result = get_inventory_result(str(tmp_path), deep=True, include_empty=True)
    assert result.inventory["app.py"]["python_import_scope"]["search_roots"] == []
    assert (
        build_module_path_resolver(result.inventory).candidates("helper", "app.py")
        == set()
    )
