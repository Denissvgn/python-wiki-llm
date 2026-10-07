"""Captured rebinding and mutation paths cannot invent constructor callers."""

from textwrap import indent

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
