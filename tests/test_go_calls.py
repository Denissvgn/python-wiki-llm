"""Conservative Go resolution across package, receiver, and selection boundaries."""

import pytest

from llm_wiki_cli.services.go_calls import resolve_go_call
from llm_wiki_cli.services.imports import build_module_path_resolver


def _file(package="main", names=()):
    return {"language": "go", "go_package": package,
            "go_import_scope": {"root": "", "module": "example.org/app"},
            "functions": [{"name": name, "exported": True} for name in names], "classes": []}


def _call(kind, **binding):
    return {"name": "Run", "go_binding": {"kind": kind, **binding}}


def test_package_calls_do_not_use_global_name_fallback():
    inventory = {"main.go": _file(), "unrelated/other.go": _file("other", ["Run"])}
    resolver = build_module_path_resolver(inventory)
    assert resolve_go_call(_call("package"), "main.go", resolver)[2] == "unresolved"


def test_ambiguous_package_functions_stay_ambiguous():
    inventory = {"main.go": _file(), "a.go": _file(names=["Run"]), "b.go": _file(names=["Run"])}
    result = resolve_go_call(_call("package"), "main.go", build_module_path_resolver(inventory))
    assert result[0] is None and result[2] == "ambiguous"
    assert [candidate["file"] for candidate in result[3]] == ["a.go", "b.go"]


def test_dynamic_call_does_not_bind_to_same_named_function():
    resolver = build_module_path_resolver({"main.go": _file(names=["Run"])})
    assert resolve_go_call(_call("dynamic"), "main.go", resolver)[2] == "unresolved"


def test_excluded_internal_package_is_not_external():
    resolver = build_module_path_resolver({"main.go": _file()})
    assert resolve_go_call(_call("import", module="example.org/app/excluded"), "main.go", resolver)[2] == "unresolved"
    assert resolve_go_call(_call("import", module="fmt"), "main.go", resolver)[2] == "external"


def test_interface_dispatch_does_not_resolve_to_declaration():
    data = _file()
    data["classes"] = [{"name": "Worker", "kind": "interface", "methods": [{"name": "Run"}]}]
    resolver = build_module_path_resolver({"main.go": data})
    assert resolve_go_call(_call("receiver", receiver="Worker"), "main.go", resolver)[2] == "unresolved"


@pytest.mark.parametrize(("export_fields", "expected_kind"), [
    ({"exported": True}, "internal"),
    ({"exported": False}, "unresolved"),
    ({}, "unresolved"),
    ({"exported": None}, "unresolved"),
    ({"exported": "false"}, "unresolved"),
    ({"exported": "true"}, "unresolved"),
    ({"exported": 1}, "unresolved"),
    ({"exported": 0}, "unresolved"),
], ids=["public", "private", "missing", "null", "string-false", "string-true", "one", "zero"])
def test_imported_functions_require_explicit_export_evidence(export_fields, expected_kind):
    library = _file("lib")
    library["functions"] = [{"name": "Run", **export_fields}]
    resolver = build_module_path_resolver({"main.go": _file(), "lib/api.go": library})

    result = resolve_go_call(
        _call("import", module="example.org/app/lib"), "main.go", resolver
    )

    expected_file = "lib/api.go" if expected_kind == "internal" else None
    assert result == (expected_file, "Run", expected_kind, [])


def test_same_package_private_calls_remain_resolvable():
    helper = _file()
    helper["functions"] = [{"name": "hidden", "exported": False}]
    resolver = build_module_path_resolver({"main.go": _file(), "helper.go": helper})

    result = resolve_go_call(
        {"name": "hidden", "go_binding": {"kind": "package"}}, "main.go", resolver
    )

    assert result == ("helper.go", "hidden", "internal", [])
