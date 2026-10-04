"""Constructor candidates are captured syntax, with explicit lexical uncertainty."""

from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli.extractors import python_extractor
from llm_wiki_cli.extractors.python_bindings import (
    analyze_python_bindings,
    valid_python_constructor_facts,
)
from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services.extraction_service import get_inventory_result
from llm_wiki_cli.services.inventory_cache import CACHE_FILENAME, InventoryCacheOptions
from llm_wiki_cli.services.knowledge_evidence import build_entity_observation_basis

CLASS = "class Batch:\n    def cap(self, values):\n        return values[:3]\n"


def inventory(tmp_path, source):
    (tmp_path / "app.py").write_text(source)
    return PythonExtractor().extract(str(tmp_path), deep=True, source_files=["app.py"])[
        "app.py"
    ]


def facts(source, member="cap"):
    tree = ast.parse(source)
    captured = analyze_python_bindings(tree)
    return [
        (node, captured.calls[id(node)])
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == member
    ]


@pytest.mark.parametrize(
    "body,origin",
    [
        ("return Batch().cap(values)", "direct-construction"),
        ("batch = Batch()\n    return batch.cap(values)", "assigned-construction"),
        ("Alias = Batch\n    return Alias().cap(values)", "direct-construction"),
        (
            "batch = Batch()\n    alias = batch\n    return alias.cap(values)",
            "assigned-construction",
        ),
        (
            "first = second = Batch()\n    return second.cap(values)",
            "assigned-construction",
        ),
    ],
)
def test_direct_assigned_and_alias_candidates_preserve_actual_ast_locations(
    body, origin
):
    source = CLASS + "def run(values):\n    " + body + "\n"
    node, fact = facts(source)[0]
    assert fact["kind"] == "constructed-receiver"
    assert fact["member"] == "cap" and fact["receiver_origin"] == origin
    constructor = fact["constructor"]
    assert constructor["root_binding"] == {"kind": "local", "symbol": "Batch"}
    assert constructor["members"] == []
    constructor_node = next(
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id in {"Batch", "Alias"}
    )
    assert (constructor["line"], constructor["column"]) == (
        constructor_node.lineno,
        constructor_node.col_offset,
    )
    assert node.lineno >= constructor["line"]


@pytest.mark.parametrize(
    "prefix,expression,root,members",
    [
        (
            "from models import Batch as B",
            "B",
            {"kind": "import", "module": "models", "name": "Batch"},
            [],
        ),
        (
            "import models as m",
            "m.Batch",
            {"kind": "import", "module": "models", "name": "", "modules": ["models"]},
            ["Batch"],
        ),
        (
            "import pkg.models",
            "pkg.models.Batch",
            {"kind": "import", "module": "pkg", "name": "", "modules": ["pkg.models"]},
            ["models", "Batch"],
        ),
        (
            "from .models import Batch",
            "Batch",
            {"kind": "import", "module": ".models", "name": "Batch"},
            [],
        ),
    ],
)
def test_import_aliases_preserve_unjoined_constructor_candidates(
    prefix, expression, root, members
):
    fact = facts(
        prefix + "\ndef run(values):\n    return " + expression + "().cap(values)\n"
    )[0][1]
    assert fact["kind"] == "constructed-receiver"
    assert fact["constructor"]["root_binding"] == root
    assert fact["constructor"]["members"] == members


@pytest.mark.parametrize(
    "body",
    [
        "batch = Batch()\n    batch = factory()\n    batch.cap(values)",
        "batch = Batch()\n    del batch\n    batch.cap(values)",
        "batch = Batch()\n    batch += other\n    batch.cap(values)",
        "if condition:\n        batch = Batch()\n    else:\n        batch = factory()\n    batch.cap(values)",
        "batch = Batch()\n    for batch in values:\n        pass\n    batch.cap(values)",
        "batch = Batch()\n    with manager() as batch:\n        batch.cap(values)",
        "batch = Batch()\n    try:\n        pass\n    except Exception as batch:\n        batch.cap(values)",
        "batch = Batch()\n    return [batch.cap(values) for batch in values]",
        "return [Batch().cap(values) for Batch in values]",
        "return factory().cap(values)",
        "batch = factory()\n    batch.cap(values)",
        "return values[0].cap(values)",
        "return (Batch if condition else Other)().cap(values)",
        "batch, other = Batch(), Batch()\n    batch.cap(values)",
        "return (batch := Batch()).cap(values)",
        "batch = Batch()\n    batch.cap = other\n    batch.cap(values)",
        "batch = Batch()\n    alias = batch\n    alias.cap = other\n    batch.cap(values)",
        "batch = Batch()\n    setattr(batch, name, other)\n    batch.cap(values)",
    ],
)
def test_rebinding_branches_factories_and_dynamic_receivers_do_not_gain_a_constructor(
    body,
):
    source = (
        CLASS + "def factory(): return Batch()\ndef run(values):\n    " + body + "\n"
    )
    _, fact = facts(source)[-1]
    assert fact["kind"] == "unresolved"
    assert fact["reason"]
    assert type(fact["line"]) is int and type(fact["column"]) is int


@pytest.mark.parametrize(
    "source",
    [
        "def run(Batch, values):\n    return Batch().cap(values)\n",
        "def run(values):\n    Batch().cap(values)\n    Batch = other\n",
        "def run(values):\n    global Batch\n    return Batch().cap(values)\n",
        "def outer(values):\n    batch = Batch()\n    def inner():\n        return batch.cap(values)\n",
        "def outer(values):\n    batch = Batch()\n    def inner():\n        nonlocal batch\n        return batch.cap(values)\n",
        "def run(values):\n    class Batch:\n        def cap(self, values): return values\n    return Batch().cap(values)\n",
    ],
)
def test_parameters_local_class_and_closure_barriers_remain_unresolved(source):
    assert facts(CLASS + source)[-1][1]["kind"] == "unresolved"


def test_known_branch_calls_are_local_but_post_merge_is_unknown():
    source = (
        CLASS
        + "def run(values):\n    if condition:\n        batch = Batch()\n        batch.cap(values)\n    batch.cap(values)\n"
    )
    values = sorted(facts(source), key=lambda pair: pair[0].lineno)
    assert values[0][1]["kind"] == "constructed-receiver"
    assert values[1][1]["kind"] == "unresolved"
    assert values[1][1]["reason"] == "receiver-path-conflict"


@pytest.mark.parametrize(
    "source,reason",
    [
        (
            "class Batch(Base):\n    def cap(self, values): return values\n",
            "unsupported-inheritance",
        ),
        (
            "class Batch(metaclass=Meta):\n    def cap(self, values): return values\n",
            "custom-class-keywords",
        ),
        ("@decorate\n" + CLASS, "decorated-class"),
        (
            "class Batch:\n    def __new__(cls): return other\n    def cap(self, values): return values\n",
            "custom-construction-or-dispatch",
        ),
        (
            "class Batch:\n    __new__ = other\n    def cap(self, values): return values\n",
            "custom-construction-or-dispatch",
        ),
        (
            "class Batch:\n    def __getattribute__(self, name): return other\n    def cap(self, values): return values\n",
            "custom-construction-or-dispatch",
        ),
        (CLASS + CLASS, "duplicate-class"),
        (CLASS + "def Batch(): return other\n", "duplicate-class"),
        (CLASS + "setattr(Batch, name, other)\n", "dynamic-member-mutation"),
        (
            "class Batch:\n    locals()['cap'] = other\n    def cap(self, values): return values\n",
            "dynamic-class-namespace",
        ),
    ],
)
def test_custom_or_ambiguous_class_dispatch_is_explicitly_ineligible(
    tmp_path, source, reason
):
    data = inventory(tmp_path, source)
    assert data["classes"]
    for cls in data["classes"]:
        assert cls["python_constructor_dispatch"]["eligible"] is False
        assert reason in cls["python_constructor_dispatch"]["reasons"]


@pytest.mark.parametrize(
    "source",
    [
        "class Batch:\n    def __init__(self): self.cap = other\n    def cap(self, values): return values\n",
        "class Batch:\n    cap = other\n    def cap(self, values): return values\n",
        "class Batch:\n    def cap(self, values): return values\n    def cap(self, values): return other\n",
        "class Batch:\n    @decorate\n    def cap(self, values): return values\n",
        CLASS + "Batch.cap = other\n",
        CLASS + "def patch():\n    Alias = Batch\n    Alias.cap = other\n",
    ],
)
def test_member_replacement_and_duplicate_methods_are_blocked_without_guess(
    tmp_path, source
):
    data = inventory(tmp_path, source)
    dispatch = data["classes"][0]["python_constructor_dispatch"]
    assert "cap" in dispatch["blocked_members"]


def test_normal_init_and_proven_builtin_object_keep_dispatch_eligible(tmp_path):
    data = inventory(
        tmp_path,
        "class Batch(object):\n    def __init__(self): self.value = 1\n    def cap(self, values): return values\n",
    )
    dispatch = data["classes"][0]["python_constructor_dispatch"]
    assert dispatch["eligible"] and dispatch["reasons"] == []
    assert "cap" not in dispatch["blocked_members"]
    assert valid_python_constructor_facts(data)


def test_calls_are_aligned_including_dynamic_targets_and_no_private_instance_leaks(
    tmp_path,
):
    data = inventory(
        tmp_path,
        CLASS
        + "batch = Batch()\ndef run(values):\n    Batch().cap(values)\n    getattr(batch, name)(values)\n    values[0](values)\n",
    )
    run = data["functions"][0]
    assert len(run["calls"]) == len(run["call_bindings"]) == 5
    dynamic = [
        (call, binding)
        for call, binding in zip(run["calls"], run["call_bindings"])
        if call["name"] == "<dynamic>"
    ]
    assert len(dynamic) == 2
    assert all(binding["reason"] == "unsupported-call-target" for _, binding in dynamic)
    assert data["python_bindings"]["batch"]["kind"] == "unresolved"
    assert "constructed-instance" not in json.dumps(data)
    assert valid_python_constructor_facts(data)


@pytest.mark.parametrize(
    "corruption",
    [
        "marker",
        "alignment",
        "private",
        "bool-location",
        "member",
        "root",
        "dispatch",
        "origin",
        "kind",
    ],
)
def test_malformed_new_facts_fail_closed(tmp_path, corruption):
    data = inventory(tmp_path, CLASS + "def run(values): return Batch().cap(values)\n")
    value = deepcopy(data)
    binding = value["functions"][0]["call_bindings"][0]
    if corruption == "marker":
        value["python_constructor_facts_version"] = True
    elif corruption == "alignment":
        value["functions"][0]["call_bindings"].pop()
    elif corruption == "private":
        value["python_bindings"]["instance"] = {"kind": "constructed-instance"}
    elif corruption == "bool-location":
        binding["constructor"]["line"] = True
    elif corruption == "member":
        binding["member"] = "cap()"
    elif corruption == "root":
        binding["constructor"]["root_binding"] = {"kind": "unresolved"}
    elif corruption == "dispatch":
        value["classes"][0]["python_constructor_dispatch"]["eligible"] = "yes"
    elif corruption == "origin":
        binding["receiver_origin"] = []
    else:
        binding["kind"] = []
    assert not valid_python_constructor_facts(value)


def test_cache_constructor_facts_are_cold_warm_and_capability_checked_without_sidecars(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/app.py").write_text(
        CLASS + "def run(values): return Batch().cap(values)\n"
    )
    Path("src/empty.py").write_text("")
    options = InventoryCacheOptions(enabled=True, cache_dir=str(tmp_path / "cache"))
    parsed = []
    original = python_extractor.ast.parse

    def observe(source, filename="<unknown>", *args, **kwargs):
        if str(filename).endswith(".py") and Path(filename).parent == tmp_path / "src":
            parsed.append(Path(filename).name)
        return original(source, filename, *args, **kwargs)

    monkeypatch.setattr(python_extractor.ast, "parse", observe)
    cold = get_inventory_result("src", deep=True, cache_options=options)
    assert valid_python_constructor_facts(cold.inventory["app.py"])
    assert sorted(parsed) == ["app.py", "empty.py"]
    parsed.clear()
    warm = get_inventory_result("src", deep=True, cache_options=options)
    assert warm.inventory == cold.inventory and parsed == []
    stored = json.loads((tmp_path / "cache" / CACHE_FILENAME).read_text())
    stored["files"]["app.py"]["inventory"].pop("python_constructor_facts_version")
    (tmp_path / "cache" / CACHE_FILENAME).write_text(json.dumps(stored))
    refreshed = get_inventory_result("src", deep=True, cache_options=options)
    assert parsed == ["app.py"]
    assert refreshed.inventory == cold.inventory


def test_dispatch_metadata_is_not_a_native_structural_signature(tmp_path):
    data = inventory(tmp_path, CLASS)
    changed = deepcopy(data)
    changed["classes"][0]["python_constructor_dispatch"]["blocked_members"] = ["cap"]
    options: dict[str, Any] = dict(
        source_path="app.py",
        extractor_ref="python",
        source_content_hash="sha256:" + "a" * 64,
        entity_name="Batch",
        occurrence=1,
        inventory_complete=True,
    )
    before = build_entity_observation_basis(file_data=data, **options)
    after = build_entity_observation_basis(file_data=changed, **options)
    assert before.concept_observation_hash is not None
    assert before.concept_observation_hash == after.concept_observation_hash


@pytest.mark.parametrize(
    "body",
    [
        "Alias.cap = other\n    return Alias().cap(values)",
        "m.Batch.cap = other\n    return m.Batch().cap(values)",
        "return Alias().cap(values)\ndef patch():\n    Alias.cap = other",
    ],
)
def test_captured_imported_class_member_replacement_qualifies_all_constructor_candidates(
    body,
):
    source = (
        "from models import Batch as Alias\nimport models as m\ndef run(values):\n    "
        + body
        + "\n"
    )
    fact = facts(source)[0][1]
    assert fact["kind"] == "unresolved"
    assert fact["reason"] in {"constructor-member-replaced", "receiver-member-replaced"}


def test_global_assignment_and_import_never_remove_constructor_scope_barrier():
    source = (
        CLASS
        + "def run(values):\n    global Batch\n    from other import Batch\n    return Batch().cap(values)\n"
    )
    assert facts(source)[0][1]["kind"] == "unresolved"
    assert facts(source)[0][1]["reason"] == "receiver-outside-lexical-scope"


def test_wildcard_import_cache_shape_is_valid_but_constructor_binding_is_unknown(
    tmp_path,
):
    data = inventory(
        tmp_path,
        CLASS + "from other import *\ndef run(values): return Batch().cap(values)\n",
    )
    assert data["functions"][0]["call_bindings"][0]["kind"] == "unresolved"
    assert valid_python_constructor_facts(data)


def test_cache_shape_validation_covers_nested_and_main_call_alignment(tmp_path):
    source = (
        CLASS
        + "def outer():\n    @tool\n    def nested(values): return Batch().cap(values)\nif __name__ == '__main__':\n    Batch().cap(values)\n"
    )
    data = inventory(tmp_path, source)
    assert data["nested_functions"] and data["main_block_calls"]
    assert valid_python_constructor_facts(data)
    for field in ("nested_functions", "main_block_call_bindings"):
        corrupt = deepcopy(data)
        if field == "nested_functions":
            corrupt[field][0]["call_bindings"].pop()
        else:
            corrupt[field].pop()
        assert not valid_python_constructor_facts(corrupt)
    wrong_member = deepcopy(data)
    wrong_member["nested_functions"][0]["call_bindings"][0]["member"] = "other"
    assert not valid_python_constructor_facts(wrong_member)


def test_constructor_and_implementation_capture_reuse_the_source_parse_pass(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/app.py").write_text(
        CLASS + "def run(values): return Batch().cap(values)\n"
    )
    original = python_extractor.ast.parse
    parsed = []

    def observe(source, filename="<unknown>", *args, **kwargs):
        if str(filename).endswith("app.py"):
            parsed.append(filename)
        return original(source, filename, *args, **kwargs)

    monkeypatch.setattr(python_extractor.ast, "parse", observe)
    ordinary = PythonExtractor().extract("src", deep=True, source_files=["app.py"])
    baseline = list(parsed)
    parsed.clear()
    extractor = PythonExtractor()
    result = extractor.extract(
        "src",
        deep=True,
        source_files=["app.py"],
        capture_implementation_observations=True,
    )
    assert parsed == baseline
    assert sum(Path(filename).is_absolute() for filename in parsed) == 1
    assert extractor.last_implementation_observations is not None
    assert result == ordinary
    data = result["app.py"]
    assert valid_python_constructor_facts(data)
    assert data["functions"][0]["call_bindings"][0]["kind"] == "constructed-receiver"


def test_custom_python_provider_keeps_legacy_inventory_with_a_warm_cache(
    tmp_path, monkeypatch
):
    from llm_wiki_cli.services import extraction_service

    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/app.py").write_text("def run(): return 1\n")
    calls = []

    class Custom:
        def extract(self, **kwargs):
            calls.append(kwargs)
            return {
                "app.py": {
                    "language": "python",
                    "classes": [],
                    "functions": [{"name": "run", "line": 1}],
                }
            }

    monkeypatch.setattr(
        extraction_service,
        "get_extractor_registry",
        lambda **kwargs: {"python": "custom:Extractor"},
    )
    monkeypatch.setattr(extraction_service, "_load_extractor", lambda entry: Custom())
    options = InventoryCacheOptions(enabled=True, cache_dir=str(tmp_path / "cache"))
    first = get_inventory_result("src", deep=True, cache_options=options)
    second = get_inventory_result("src", deep=True, cache_options=options)
    assert first.inventory == second.inventory
    assert first.statuses["python"].state == second.statuses["python"].state == "ok"
    assert len(calls) == 2  # Custom providers retain the existing no-reuse policy.
    assert "python_constructor_facts_version" not in second.inventory["app.py"]


@pytest.mark.parametrize(
    "method",
    [
        "def __init__(self):\n        alias = self\n        alias.cap = other",
        "def __init__(self):\n        self.__dict__['cap'] = other",
        "def __init__(self):\n        setattr(self, name, other)",
    ],
)
def test_captured_receiver_alias_and_dynamic_namespace_replacement_blocks_dispatch(
    tmp_path, method
):
    data = inventory(
        tmp_path,
        "class Batch:\n    " + method + "\n    def cap(self, values): return values\n",
    )
    dispatch = data["classes"][0]["python_constructor_dispatch"]
    assert not dispatch["eligible"] or "cap" in dispatch["blocked_members"]


@pytest.mark.parametrize(
    "extra",
    [
        "if condition:\n        cap = other",
        "if condition:\n        def cap(self, values): return other",
        "if condition:\n        def __new__(cls): return other",
        "exec('cap = other')",
    ],
)
def test_conditional_or_dynamic_class_namespace_is_not_guessed(tmp_path, extra):
    data = inventory(tmp_path, CLASS + "    " + extra + "\n")
    dispatch = data["classes"][0]["python_constructor_dispatch"]
    assert not dispatch["eligible"] or "cap" in dispatch["blocked_members"]


def test_shadowed_class_or_receiver_names_do_not_poison_unrelated_class_dispatch(
    tmp_path,
):
    source = (
        CLASS
        + "def patch(Batch):\n    Batch.cap = other\nclass Other:\n    def __init__(self):\n        def inner(self):\n            self.cap = other\n    def cap(self, values): return values\n"
    )
    data = inventory(tmp_path, source)
    for cls in data["classes"]:
        dispatch = cls["python_constructor_dispatch"]
        assert dispatch["eligible"] and "cap" not in dispatch["blocked_members"]


@pytest.mark.parametrize(
    "source",
    [
        "def run(batch: Batch, values): return batch.cap(values)\n",
        "def factory() -> Batch: return Batch()\ndef run(values):\n    batch = factory()\n    return batch.cap(values)\n",
    ],
)
def test_annotations_and_factory_return_signatures_never_establish_a_receiver(source):
    assert facts(CLASS + source)[-1][1]["kind"] == "unresolved"


def test_display_strings_and_target_module_execution_do_not_supply_constructor_facts(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        python_extractor, "_annotation_to_str", lambda node: "fabricated.display"
    )
    data = inventory(
        tmp_path,
        "raise AssertionError('target executed')\nfrom absent_sdk import Other\n"
        + CLASS
        + "def run(values): return Batch().cap(values)\n",
    )
    run = data["functions"][0]
    assert run["calls"][0]["attr"] == "fabricated.display"
    assert run["call_bindings"][0]["constructor"]["root_binding"] == {
        "kind": "local",
        "symbol": "Batch",
    }
    assert run["call_bindings"][0]["member"] == "cap"


def test_uncaptured_external_constructor_is_only_an_unjoined_import_candidate(tmp_path):
    data = inventory(
        tmp_path,
        "from absent_sdk import Batch\ndef run(values): return Batch().cap(values)\n",
    )
    assert data["classes"] == []
    binding = data["functions"][0]["call_bindings"][0]
    assert binding["constructor"]["root_binding"] == {
        "kind": "import",
        "module": "absent_sdk",
        "name": "Batch",
    }
    assert (
        "eligible" not in binding
    )  # Eligibility requires the later captured class join.


@pytest.mark.parametrize("member", ["__class__", "__dict__"])
def test_instance_identity_or_namespace_replacement_blocks_other_member_candidates(
    member,
):
    source = (
        CLASS
        + "def run(values):\n    batch = Batch()\n    batch."
        + member
        + " = other\n    return batch.cap(values)\n"
    )
    assert facts(source)[0][1]["kind"] == "unresolved"


@pytest.mark.parametrize(
    "replacement",
    ["self.__class__ = Other", "Batch.__bases__ = bases", "Batch.__init__ = factory"],
)
def test_captured_class_construction_or_identity_replacement_is_ineligible(
    tmp_path, replacement
):
    if replacement.startswith("self."):
        source = (
            "class Batch:\n    def __init__(self): "
            + replacement
            + "\n    def cap(self, values): return values\n"
        )
    else:
        source = CLASS + replacement + "\n"
    data = inventory(tmp_path, source)
    assert data["classes"][0]["python_constructor_dispatch"]["eligible"] is False


@pytest.mark.parametrize(
    "receiver,mutation",
    [
        ("obj", "obj.cap = other"),
        ("obj", "target = obj\n        target.cap = other"),
        ("self", "vars(self)['cap'] = other"),
        ("self", "target = self\n        vars(target)['cap'] = other"),
        ("self", "d = vars(self)\n        d['cap'] = other"),
        ("self", "d = self.__dict__\n        alias = d\n        alias['cap'] = other"),
        ("obj", "object.__setattr__(obj, 'cap', other)"),
        ("self", "target = self\n        object.__setattr__(target, 'cap', other)"),
        ("self", "put = object.__setattr__\n        put(self, 'cap', other)"),
        ("self", "put = setattr\n        put(self, 'cap', other)"),
        ("self", "show = vars\n        show(self)['cap'] = other"),
        ("self", "d = vars(self)\n        d[name] = other"),
        ("self", "object.__setattr__(self, name, other)"),
        (
            "self",
            "from builtins import vars as show\n        show(self)['cap'] = other",
        ),
        (
            "self",
            "from builtins import object as Obj\n        Obj.__setattr__(self, 'cap', other)",
        ),
        (
            "self",
            "import builtins as bi\n        bi.object.__setattr__(self, 'cap', other)",
        ),
    ],
)
def test_review_explicit_namespace_and_attribute_mutation_blocks_actual_dispatch(
    tmp_path, receiver, mutation
):
    source = (
        "class Batch:\n    def __init__("
        + receiver
        + "):\n        "
        + mutation
        + "\n    def cap(self, values): return values\n"
    )
    dispatch = inventory(tmp_path, source)["classes"][0]["python_constructor_dispatch"]
    assert not dispatch["eligible"] or "cap" in dispatch["blocked_members"]


@pytest.mark.parametrize(
    "mutation",
    [
        "vars(batch)['cap'] = other",
        "d = vars(batch)\n    d['cap'] = other",
        "object.__setattr__(batch, 'cap', other)",
        "put = object.__setattr__\n    put(batch, 'cap', other)",
        "put = setattr\n    put(batch, 'cap', other)",
        "show = vars\n    show(batch)['cap'] = other",
    ],
)
def test_review_explicit_mutation_of_assigned_instance_remains_unresolved(mutation):
    source = (
        CLASS
        + "def run(values):\n    batch = Batch()\n    "
        + mutation
        + "\n    return batch.cap(values)\n"
    )
    assert facts(source)[0][1]["kind"] == "unresolved"


@pytest.mark.parametrize(
    "shadow,mutation",
    [
        ("vars", "vars(self)['cap'] = other"),
        ("object", "object.__setattr__(self, 'cap', other)"),
    ],
)
def test_review_shadowed_helper_does_not_certify_absence_of_dispatch_mutation(
    tmp_path, shadow, mutation
):
    source = (
        "class Batch:\n    def __init__(self, "
        + shadow
        + "):\n        "
        + mutation
        + "\n    def cap(self, values): return values\n"
    )
    dispatch = inventory(tmp_path, source)["classes"][0]["python_constructor_dispatch"]
    assert dispatch["eligible"] is False
    assert "dynamic-member-mutation" in dispatch["reasons"]


def test_review_unrelated_nested_receiver_attributes_and_shadowed_receivers_do_not_poison_class(
    tmp_path,
):
    source = "class Batch:\n    def __init__(self):\n        vars(self.child)['cap'] = other\n        object.__setattr__(self.child, 'cap', other)\n        def inner(self):\n            vars(self)['cap'] = other\n    def cap(self, values): return values\n"
    dispatch = inventory(tmp_path, source)["classes"][0]["python_constructor_dispatch"]
    assert dispatch["eligible"] and "cap" not in dispatch["blocked_members"]


@pytest.mark.parametrize("alias", ["Alias: TypeAlias = int", "type Alias = int"])
def test_review_type_alias_capability_validation_keeps_cold_warm_parity(
    tmp_path, monkeypatch, alias
):
    if alias.startswith("type ") and not hasattr(ast, "TypeAlias"):
        pytest.skip("Parser lacks type alias statements")
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/app.py").write_text(
        "from typing import TypeAlias\n"
        + alias
        + "\ndef run(values): return Alias().cap(values)\n"
    )
    options = InventoryCacheOptions(enabled=True, cache_dir=str(tmp_path / "cache"))
    first = get_inventory_result("src", deep=True, cache_options=options)
    data = first.inventory["app.py"]
    assert valid_python_constructor_facts(data)
    assert data["classes"][0]["kind"] == "type_alias"
    assert "python_constructor_dispatch" not in data["classes"][0]
    assert data["functions"][0]["call_bindings"][0]["kind"] == "unresolved"
    second = get_inventory_result("src", deep=True, cache_options=options)
    assert first.inventory == second.inventory
    assert second.cache_stats is not None and second.cache_stats.hits == 1
    corrupt = deepcopy(data)
    corrupt["classes"][0]["python_constructor_dispatch"] = {"eligible": True}
    assert not valid_python_constructor_facts(corrupt)


def test_review_private_helpers_do_not_leak_and_constructed_receiver_arguments_are_preserved(
    tmp_path,
):
    source = (
        CLASS
        + "put = object.__setattr__\ndef run(values): return Batch().cap(values)\nclass Other:\n    def __init__(self):\n        child = Batch(self)\n        child.cap(values)\n"
    )
    data = inventory(tmp_path, source)
    assert data["python_bindings"]["put"]["kind"] == "unresolved"
    assert "attribute-mutator" not in json.dumps(data)
    assert "receiver-namespace" not in json.dumps(data)
    assert (
        data["classes"][1]["methods"][0]["call_bindings"][-1]["kind"]
        == "constructed-receiver"
    )
    assert valid_python_constructor_facts(data)


def test_review_module_builtin_mutator_alias_blocks_class_allocation_hook(tmp_path):
    source = CLASS + "put = setattr\nput(Batch, '__new__', factory)\n"
    dispatch = inventory(tmp_path, source)["classes"][0]["python_constructor_dispatch"]
    assert not dispatch["eligible"]
    assert "custom-construction-or-dispatch" in dispatch["reasons"]


@pytest.mark.parametrize(
    "mutation",
    [
        "vars(self).update({'cap': other})",
        "d = vars(self)\n        d.clear()",
        "self.__dict__.__setitem__('cap', other)",
    ],
)
def test_review_explicit_namespace_mutation_calls_remain_unavailable(
    tmp_path, mutation
):
    source = (
        "class Batch:\n    def __init__(self):\n        "
        + mutation
        + "\n    def cap(self, values): return values\n"
    )
    dispatch = inventory(tmp_path, source)["classes"][0]["python_constructor_dispatch"]
    assert dispatch["eligible"] is False
    assert "dynamic-member-mutation" in dispatch["reasons"]


def test_review_read_only_namespace_alias_does_not_block_unrelated_dispatch(tmp_path):
    source = "class Batch:\n    def __init__(self):\n        d = vars(self)\n        d.get('cap')\n    def cap(self, values): return values\n"
    dispatch = inventory(tmp_path, source)["classes"][0]["python_constructor_dispatch"]
    assert dispatch["eligible"] and "cap" not in dispatch["blocked_members"]


@pytest.mark.parametrize(
    "mutation",
    [
        "globals()['Batch'] = factory",
        "locals()['Batch'] = factory",
        "ns = globals()\nns['Batch'] = factory",
        "show = globals\nns = show()\nns['Batch'] = factory",
        "from builtins import globals as show\nshow()['Batch'] = factory",
        "ns = globals()\nns.update({'Batch': factory})",
        "ns = locals()\nns.clear()",
        "globals()[name] = factory",
    ],
)
def test_review_captured_module_namespace_rebinding_blocks_constructor_claims(
    tmp_path, mutation
):
    source = (
        CLASS
        + "def factory(): return other\n"
        + mutation
        + "\ndef run(values): return Batch().cap(values)\n"
    )
    data = inventory(tmp_path, source)
    assert data["functions"][-1]["call_bindings"][0]["kind"] == "unresolved"
    assert '"kind": "module-namespace"' not in json.dumps(data)
    assert valid_python_constructor_facts(data)


def test_review_function_local_locals_write_does_not_rebind_module_class(tmp_path):
    source = (
        CLASS
        + "def run(values):\n    ns = locals()\n    ns['Batch'] = factory\n    return Batch().cap(values)\n"
    )
    data = inventory(tmp_path, source)
    assert data["functions"][0]["call_bindings"][-2]["kind"] == "constructed-receiver"
    assert data["python_bindings"]["Batch"] == {"kind": "local", "symbol": "Batch"}
    assert valid_python_constructor_facts(data)


def test_review_exact_module_namespace_write_preserves_unrelated_constructor(tmp_path):
    source = (
        CLASS
        + "class Other:\n    def cap(self, values): return values\nglobals()['Batch'] = factory\ndef run(values):\n    Batch().cap(values)\n    Other().cap(values)\n"
    )
    data = inventory(tmp_path, source)
    constructed = [
        binding
        for binding in data["functions"][0]["call_bindings"]
        if binding["kind"] == "constructed-receiver"
    ]
    assert (
        len(constructed) == 1
        and constructed[0]["constructor"]["root_binding"]["symbol"] == "Other"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "vars(policy)['Batch'] = factory",
        "policy.__dict__['Batch'] = factory",
        "ns = vars(policy)\nns['Batch'] = factory",
        "ns = policy.__dict__\nns.update({'Batch': factory})",
        "alias = policy\nvars(alias)['Batch'] = factory",
    ],
)
def test_review_imported_module_namespace_replacement_blocks_only_implicated_import(
    tmp_path, mutation
):
    source = (
        "import policy\nimport unrelated\n"
        + mutation
        + "\ndef run(values):\n    policy.Batch().cap(values)\n    unrelated.Other().cap(values)\n"
    )
    data = inventory(tmp_path, source)
    facts = [
        binding
        for binding in data["functions"][0]["call_bindings"]
        if binding["kind"] == "constructed-receiver"
    ]
    assert (
        len(facts) == 1
        and facts[0]["constructor"]["root_binding"]["module"] == "unrelated"
    )
    assert "receiver-namespace" not in json.dumps(data)
    assert valid_python_constructor_facts(data)


def test_review_import_namespace_mutation_also_blocks_later_from_alias_constructor(
    tmp_path,
):
    source = "import policy\nvars(policy)['Batch'] = factory\nfrom policy import Batch as Imported\ndef run(values): return Imported().cap(values)\n"
    data = inventory(tmp_path, source)
    assert data["functions"][0]["call_bindings"][0]["kind"] == "unresolved"
    assert valid_python_constructor_facts(data)
