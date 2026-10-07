"""Captured rebinding and mutation paths cannot invent constructor callers."""

from textwrap import indent
from pathlib import Path
import json
from tests.test_python_constructor_bindings import (
    test_namespace_effects_preserve_exact_call_authority as _check_exact_probe,
)


import pytest

from tests.test_python_constructor_resolution import CLASS, collect, decision
from llm_wiki_cli.extractors.python_bindings import valid_python_constructor_facts
from llm_wiki_cli.services.extraction_service import resolve_call_observations
from llm_wiki_cli import api


@pytest.mark.parametrize(
    "body",
    [
        "batch = Batch()\nfor _ in values:\n    batch.cap(values)\n    batch = other",
        "batch = Batch()\nwhile values:\n    batch.cap(values)\n    batch = other",
        "batch = Batch()\nwhile batch.cap(values):\n    batch = other",
        "batch = Batch()\nfor _ in values:\n    batch.cap(values)\n    batch.cap = other",
        'batch = Batch()\nfor _ in values:\n    batch.cap(values)\n    patch = batch.__setattr__\n    patch("cap", other)',
        "batch = Batch()\ntry:\n    batch = other\nfinally:\n    batch.cap(values)",
        "batch = Batch()\ntry:\n    batch = other\n    raise ValueError()\nexcept ValueError:\n    batch.cap(values)",
        "batch = Batch()\ntry:\n    batch = other\nexcept ValueError:\n    pass\nelse:\n    batch.cap(values)",
        "batch = Batch()\n[(batch := other) for _ in values]\nbatch.cap(values)",
        "batch = Batch()\n{(batch := other) for _ in values}\nbatch.cap(values)",
        "batch = Batch()\n{key: (batch := other) for key in values}\nbatch.cap(values)",
        "batch = Batch()\nchanges = ((batch := other) for _ in values)\nbatch.cap(values)",
        'batch = Batch()\nbatch.__setattr__("cap", other)\nbatch.cap(values)',
        'batch = Batch()\npatch = batch.__setattr__\npatch("cap", other)\nbatch.cap(values)',
        'batch = Batch()\npatch = batch.__delattr__\npatch("cap")\nbatch.cap(values)',
        'batch = Batch()\nwhile batch.cap(setattr(batch, "cap", other)):\n    pass',
        'batch = Batch()\nwhile batch.cap(batch.__setattr__("cap", other)):\n    pass',
        'batch = Batch()\npatch = batch.__setattr__\nif values:\n    patch = batch.__setattr__\npatch("cap", other)\nbatch.cap(values)',
        'batch = Batch()\nif values:\n    patch = batch.__setattr__\nelse:\n    patch = other\npatch("cap", other)\nbatch.cap(values)',
        'batch = Batch()\nnamespace = vars(batch)\nif values:\n    namespace = vars(batch)\nnamespace["cap"] = other\nbatch.cap(values)',
        'batch = Batch()\npatch = batch.__setattr__\nfor _ in values:\n    batch.cap(values)\n    patch("cap", other)\n    patch = batch.__setattr__',
        "batch = Batch()\n[(lambda x=(batch := other): x) for _ in values]\nbatch.cap(values)",
        "batch = Batch()\n[(lambda *, x=(batch := other): x) for _ in values]\nbatch.cap(values)",
        "batch = Batch()\ndef nested(x=(batch := other)):\n    pass\nbatch.cap(values)",
        "batch = Batch()\nclass Nested:\n    batch.cap = other\nbatch.cap(values)",
        'batch = Batch()\nfor _ in values:\n    batch.cap(values)\n    if setattr(batch, "cap", other):\n        pass',
        'batch = Batch()\nfor _ in values:\n    batch.cap(values)\n    for item in (setattr(batch, "cap", other) or values):\n        pass',
        'batch = Batch()\nfor _ in values:\n    batch.cap(values)\n    with batch.__setattr__("cap", other):\n        pass',
        'batch = Batch()\nfor _ in values:\n    batch.cap(values)\n    match setattr(batch, "cap", other):\n        case _: pass',
        'batch = Batch()\nfor _ in values:\n    batch.cap(values)\n    match values:\n        case _ if setattr(batch, "cap", other): pass',
        "batch = Batch()\nclass Nested:\n    nonlocal batch\n    batch = other\nbatch.cap(values)",
        'batch = Batch()\ntry:\n    raise ValueError()\nexcept (setattr(batch, "cap", other) or ValueError):\n    batch.cap(values)',
        'batch = Batch()\npatch = getattr(batch, "__setattr__")\npatch("cap", other)\nbatch.cap(values)',
        'batch = Batch()\npatch = batch.__getattribute__("__setattr__")\npatch("cap", other)\nbatch.cap(values)',
        'batch = Batch()\npatch = batch.__setattr__\nmatch values:\n    case []:\n        patch = batch.__setattr__\npatch("cap", other)\nbatch.cap(values)',
    ],
)
def test_control_flow_and_bound_mutation_emit_located_uncertainty(tmp_path, body):
    source = CLASS + "def run(values, other):\n" + indent(body, "    ") + "\n"
    inventory = collect(tmp_path, {"app.py": source})
    value = decision(inventory)
    assert value.kind == "unresolved" and value.file is None
    assert value.reason and value.location and value.location["source_path"] == "app.py"
    assert valid_python_constructor_facts(inventory["app.py"])
    edges = resolve_call_observations(inventory)["observations"]
    assert not any(
        edge["from"]["symbol"] == "run"
        and edge["to"] == {"file": "app.py", "symbol": "Batch.cap"}
        for edge in edges
    )


@pytest.mark.parametrize(
    "body",
    [
        "batch = Batch()\nfor _ in values:\n    batch.cap(values)",
        "batch = Batch()\nwhile values:\n    batch.cap(values)",
        "for _ in values:\n    batch = Batch()\n    batch.cap(values)\n    batch = other",
        "batch = Batch()\ntry:\n    pass\nfinally:\n    batch.cap(values)",
        "batch = Batch()\ntry:\n    batch = other\nfinally:\n    batch = Batch()\n    batch.cap(values)",
        "batch = Batch()\n[(lambda: (batch := other)) for _ in values]\nbatch.cap(values)",
        'batch = Batch()\nbatch.__setattr__("extra", other)\nbatch.cap(values)',
        'batch = Batch()\npatch = batch.__setattr__\npatch("extra", other)\nbatch.cap(values)',
    ],
)
def test_unmodified_or_freshly_constructed_receivers_still_resolve(tmp_path, body):
    inventory = collect(
        tmp_path,
        {"app.py": CLASS + "def run(values, other):\n" + indent(body, "    ") + "\n"},
    )
    value = decision(inventory)
    assert (value.kind, value.file, value.symbol) == ("internal", "app.py", "Batch.cap")
    assert valid_python_constructor_facts(inventory["app.py"])


def test_bound_constructor_mutation_matches_owned_runtime_and_public_callers(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    source = (
        "class Batch:\n"
        "    def __init__(self):\n"
        "        patch = self.__setattr__\n"
        '        patch("cap", lambda values: "patched")\n'
        '    def cap(self, values): return "original"\n'
        "def run(values): return Batch().cap(values)\n"
    )
    inventory = collect(tmp_path, {"app.py": source})
    value = decision(inventory)
    assert value.kind == "unresolved" and value.reason == "constructor-member-replaced"
    # Execute only this deliberately owned, in-memory fixture.
    namespace = {}
    exec(compile(source, "owned-bound-mutation", "exec"), namespace)
    assert namespace["run"]([]) == "patched"
    result = api.callers(
        "app.py:Batch.cap",
        src_dir=str(tmp_path),
        wiki_dir=str(tmp_path / "absent-wiki"),
        read_only=True,
    )
    assert result["callers"] == []
    coverage = result.get("coverage")
    assert coverage is not None and coverage["runtime_completeness"] is False


def test_eager_module_default_updates_constructor_alias_before_function_capture(
    tmp_path,
):
    source = (
        CLASS
        + "class Other:\n    def cap(self, values): return values\n"
        + "def nested(x=(Batch := Other)): pass\n"
        + "def run(values): return Batch().cap(values)\n"
    )
    inventory = collect(tmp_path, {"app.py": source})
    value = decision(inventory)
    assert (value.kind, value.file, value.symbol) == ("internal", "app.py", "Other.cap")
    assert valid_python_constructor_facts(inventory["app.py"])


def test_eager_class_global_rebinding_never_borrows_original_class(tmp_path):
    source = (
        CLASS
        + "class Other:\n    def cap(self, values): return values\n"
        + "class Nested:\n    global Batch\n    Batch = Other\n"
        + "def run(values): return Batch().cap(values)\n"
    )
    inventory = collect(tmp_path, {"app.py": source})
    value = decision(inventory)
    assert value.kind == "unresolved" and value.file is None
    assert valid_python_constructor_facts(inventory["app.py"])


_EXPRESSION_CONTROLS = json.loads(
    (Path(__file__).parent / "fixtures/python_constructor_expressions.json").read_text()
)


@pytest.mark.parametrize("case", _EXPRESSION_CONTROLS, ids=lambda case: case["id"])
def test_expression_transfers_preserve_exact_call_authority(tmp_path, case):
    _check_exact_probe(tmp_path, case)


_PAIR = (
    "class Batch:\n    def cap(self, *args, **kwargs): return 'original'\n"
    "class Other:\n    def cap(self, *args, **kwargs): return 'other'\n"
)


def _cap_observations(tmp_path, body):
    captured = collect(
        tmp_path,
        {"app.py": _PAIR + "def run(condition):\n" + indent(body, "    ") + "\n"},
    )
    assert valid_python_constructor_facts(captured["app.py"])
    return [
        row
        for row in resolve_call_observations(captured)["observations"]
        if row["from"] == {"file": "app.py", "symbol": "run"}
        and row["name"].rsplit(".", 1)[-1] == "cap"
    ]


@pytest.mark.parametrize(
    "choice",
    [
        "target = first if condition else second\ntarget.cap = replacement",
        "patch = first.__setattr__ if condition else second.__setattr__\npatch('cap', replacement)",
        "namespace = vars(first) if condition else vars(second)\nnamespace['cap'] = replacement",
    ],
)
def test_possible_receiver_and_mutator_aliases_survive_unknown_joins(tmp_path, choice):
    rows = _cap_observations(
        tmp_path,
        "first = Batch()\nsecond = Other()\nreplacement = lambda *args: 'replacement'\n"
        + choice
        + "\nreturn first.cap()",
    )
    assert rows[-1]["kind"] == "unresolved" and rows[-1]["reason"]


def test_identical_receiver_alias_join_keeps_required_dispatch(tmp_path):
    rows = _cap_observations(
        tmp_path,
        "batch = Batch()\nalias = batch\ncondition and (batch := alias)\nreturn batch.cap()",
    )
    assert rows[-1]["to"] == {"file": "app.py", "symbol": "Batch.cap"}


def test_a_captured_bound_method_precedes_its_argument_member_mutation(tmp_path):
    rows = _cap_observations(
        tmp_path,
        "batch = Batch()\nfirst = batch.cap(setattr(batch, 'cap', lambda *args: 'replacement'))\nreturn [first, batch.cap()]",
    )
    assert rows[0]["to"] == {"file": "app.py", "symbol": "Batch.cap"}
    assert rows[1]["kind"] == "unresolved"


def test_class_argument_mutation_qualifies_later_calls_and_other_entrypoints(tmp_path):
    sources = {
        "app.py": _PAIR
        + "def run(condition):\n    batch = Batch()\n    first = batch.cap(setattr(Batch, 'cap', lambda *args: 'replacement'))\n    return [first, batch.cap()]\ndef later(): return Batch().cap()\n"
    }
    captured = collect(tmp_path, sources)
    rows = [
        row
        for row in resolve_call_observations(captured)["observations"]
        if row["name"].rsplit(".", 1)[-1] == "cap"
    ]
    earlier = next(
        row for row in rows if row["from"]["symbol"] == "run" and row["line"] == 7
    )
    assert earlier["to"] == {"file": "app.py", "symbol": "Batch.cap"}
    assert all(row["kind"] == "unresolved" for row in rows if row is not earlier)


@pytest.mark.parametrize(
    "deferred",
    [
        "later = lambda: setattr(batch, 'cap', replacement)",
        "later = (setattr(batch, 'cap', replacement) for _ in values)",
    ],
)
def test_deferred_expression_body_does_not_mutate_the_outer_receiver(
    tmp_path, deferred
):
    rows = _cap_observations(
        tmp_path,
        "batch = Batch()\nreplacement = lambda *args: 'replacement'\nvalues = ()\n"
        + deferred
        + "\nreturn batch.cap()",
    )
    outer = next(row for row in rows if row["line"] == 10)
    assert outer["to"] == {"file": "app.py", "symbol": "Batch.cap"}


def test_positional_starred_arguments_precede_keywords_even_when_written_later(
    tmp_path,
):
    rows = _cap_observations(
        tmp_path,
        "batch = Other()\nalias = Batch()\ndef accept(*args, **kwargs): pass\naccept(keyword=(batch := alias), *(batch.cap(),))\nreturn batch.cap()",
    )
    assert rows[0]["to"] == {"file": "app.py", "symbol": "Other.cap"}
    assert rows[1]["to"] == {"file": "app.py", "symbol": "Batch.cap"}


@pytest.mark.parametrize(
    "effect",
    [
        "setattr(batch, 'cap', replacement if condition else replacement)",
        "patch = batch.__setattr__\npatch('cap', replacement if condition else replacement)",
    ],
)
def test_argument_branch_join_retains_the_original_mutation_target(tmp_path, effect):
    rows = _cap_observations(
        tmp_path,
        "batch = Batch()\nreplacement = lambda *args: 'replacement'\n"
        + effect
        + "\nreturn batch.cap()",
    )
    assert rows[-1]["kind"] == "unresolved" and rows[-1]["reason"]


def test_unknown_receiver_argument_retains_possible_original_targets(tmp_path):
    rows = _cap_observations(
        tmp_path,
        "first = Batch()\nsecond = Other()\ntarget = first if condition else second\nsetattr(target, 'cap', lambda *args: 'replacement')\nreturn first.cap()",
    )
    assert rows[-1]["kind"] == "unresolved"


def test_generator_scope_restoration_keeps_unknown_alias_owner_links(tmp_path):
    rows = _cap_observations(
        tmp_path,
        "first = Batch()\ntarget = first\nlater = ((target := Other()) for _ in ())\ntarget.cap = lambda *args: 'replacement'\nreturn first.cap()",
    )
    assert rows[-1]["kind"] == "unresolved"


def test_joined_namespace_unrelated_key_does_not_poison_required_member(tmp_path):
    rows = _cap_observations(
        tmp_path,
        "first = Batch()\nsecond = Other()\nnamespace = vars(first) if condition else vars(second)\nnamespace['extra'] = 1\nreturn first.cap()",
    )
    assert rows[-1]["to"] == {"file": "app.py", "symbol": "Batch.cap"}


def test_bound_namespace_operation_is_frozen_before_argument_rebinding(tmp_path):
    rows = _cap_observations(
        tmp_path,
        "first = Batch()\nsecond = Other()\nnamespace = vars(first)\nreplacement = lambda *args: 'replacement'\npayload = {'cap': replacement}\nnamespace.update((namespace := vars(second)) or payload)\nreturn first.cap()",
    )
    assert rows[-1]["kind"] == "unresolved"


def test_conditional_namespace_argument_keeps_possible_receivers(tmp_path):
    rows = _cap_observations(
        tmp_path,
        "first = Batch()\nsecond = Other()\nnamespace = vars(first if condition else second)\nnamespace['cap'] = lambda *args: 'replacement'\nreturn first.cap()",
    )
    assert rows[-1]["kind"] == "unresolved"


def test_conditional_getattr_argument_keeps_possible_bound_mutation_targets(tmp_path):
    rows = _cap_observations(
        tmp_path,
        "first = Batch()\nsecond = Other()\npatch = getattr(first if condition else second, '__setattr__')\npatch('cap', lambda *args: 'replacement')\nreturn first.cap()",
    )
    assert rows[-1]["kind"] == "unresolved"


def test_lazy_or_future_annotations_do_not_execute_a_namespace_mutation(tmp_path):
    import sys

    annotation = "setattr(Batch, 'cap', None)"
    prefix = (
        "from __future__ import annotations\n" if sys.version_info < (3, 14) else ""
    )
    captured = collect(
        tmp_path,
        {
            "app.py": prefix
            + _PAIR
            + "def helper(value: "
            + annotation
            + "): pass\ndef run(): return Batch().cap()\n"
        },
    )
    rows = resolve_call_observations(captured)["observations"]
    method = next(row for row in rows if row["name"] == "Batch().cap")
    assert method["to"] == {"file": "app.py", "symbol": "Batch.cap"}


@pytest.mark.parametrize("case_id", ["EXP-001", "EXP-015", "EXP-020"])
def test_expression_snapshot_facts_survive_cold_warm_and_disabled_cache(
    tmp_path, case_id
):
    from llm_wiki_cli.services.extraction_service import get_inventory_result
    from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions

    case = next(row for row in _EXPRESSION_CONTROLS if row["id"] == case_id)
    source = tmp_path / "source"
    source.mkdir()
    for name, content in case["sources"].items():
        (source / name).write_text(content)
    options = InventoryCacheOptions(enabled=True, cache_dir=str(tmp_path / "cache"))
    cold = get_inventory_result(str(source), deep=True, cache_options=options)
    warm = get_inventory_result(str(source), deep=True, cache_options=options)
    disabled = get_inventory_result(str(source), deep=True)
    assert cold.inventory == warm.inventory == disabled.inventory
    assert warm.cache_stats is not None and warm.cache_stats.hits == len(
        case["sources"]
    )
    assert all(
        valid_python_constructor_facts(value) for value in warm.inventory.values()
    )
    wire = json.dumps(warm.inventory)
    assert '"_allocation"' not in wire and '"_possible_targets"' not in wire
