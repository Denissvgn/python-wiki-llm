from __future__ import annotations

import inspect

import pytest

from llm_wiki_cli.extractors.go_extractor import GoExtractor
from llm_wiki_cli.extractors.rust_extractor import RustExtractor
from llm_wiki_cli.extractors.ts_extractor import TypeScriptExtractor


@pytest.mark.parametrize(
    "extractor_cls",
    [GoExtractor, RustExtractor, TypeScriptExtractor],
)
def test_load_inventory_return_annotation_matches_empty_dict_contract(extractor_cls):
    annotation = inspect.signature(extractor_cls._load_inventory).return_annotation

    assert annotation == "dict"


def test_deep_calls_field_is_additive_and_optional(tmp_path):
    """The deep-mode ``calls`` field is optional: present only when a body makes
    calls, absent otherwise, and never present in slim mode."""
    from llm_wiki_cli.commands.extract_cmd import get_inventory

    (tmp_path / "m.py").write_text(
        "def caller(value):\n    return helper(value, mode='fast')\n\n\ndef helper(value, mode='slow'):\n    return value\n"
    )

    deep = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"]
    by_name = {fn["name"]: fn for fn in deep}
    calls = by_name["caller"].get("calls")
    assert calls  # additive: present when calls exist
    assert calls[0]["args"] == [{"kind": "name", "value": "value"}]
    assert calls[0]["kwargs"] == [
        {"name": "mode", "kind": "literal", "value": "'fast'"}
    ]
    assert "calls" not in by_name["helper"]  # optional: omitted when empty

    slim = get_inventory(str(tmp_path), deep=False)["m.py"]["functions"]
    assert all("calls" not in fn for fn in slim)


def test_deep_module_calls_field_is_additive_and_optional(tmp_path):
    """The deep-mode ``module_calls`` field is optional: present only when the
    module has top-level side-effect calls, absent otherwise and in slim mode."""
    from llm_wiki_cli.commands.extract_cmd import get_inventory

    (tmp_path / "wired.py").write_text(
        "app = Flask(__name__)\n\n\ndef run():\n    return app\n"
    )
    (tmp_path / "pure.py").write_text("VALUE = 1\n\n\ndef run():\n    return 1\n")

    deep = get_inventory(str(tmp_path), deep=True)
    assert deep["wired.py"]["module_calls"]  # additive: present when side effects exist
    assert "module_calls" not in deep["pure.py"]  # optional: omitted when empty

    slim = get_inventory(str(tmp_path), deep=False)
    assert "module_calls" not in slim["wired.py"]


def test_deep_data_effects_field_is_additive_and_optional(tmp_path):
    """The deep-mode ``data_effects`` field is optional: present only when a
    function has extractable inputs/effects, absent otherwise and in slim mode."""
    from llm_wiki_cli.commands.extract_cmd import get_inventory

    (tmp_path / "m.py").write_text(
        "def echo(value):\n    print(value)\n    return value\n\n\ndef noop():\n    pass\n"
    )

    deep = {
        fn["name"]: fn
        for fn in get_inventory(str(tmp_path), deep=True)["m.py"]["functions"]
    }
    assert deep["echo"]["data_effects"]["inputs"] == [
        {"kind": "param", "name": "value", "type": ""}
    ]
    assert deep["echo"]["data_effects"]["boundary_effects"] == [
        {"kind": "output", "target": "print", "line": 2}
    ]
    assert "data_effects" not in deep["noop"]

    slim = get_inventory(str(tmp_path), deep=False)["m.py"]["functions"]
    assert all("data_effects" not in fn for fn in slim)


def test_resolver_tolerates_extractor_inventory_without_calls():
    """Extractors that do not emit ``calls`` must not break edge resolution."""
    from llm_wiki_cli.commands.extract_cmd import resolve_call_edges

    inventory = {
        "lib.ts": {
            "language": "typescript",
            "classes": [{"name": "Widget", "methods": [{"name": "render"}]}],
            "functions": [{"name": "mount"}],
        }
    }
    assert resolve_call_edges(inventory) == []


def test_resolver_tolerates_enriched_call_records():
    """Call args are additive metadata and do not alter edge resolution."""
    from llm_wiki_cli.commands.extract_cmd import resolve_call_edges

    inventory = {
        "m.py": {
            "language": "python",
            "classes": [],
            "functions": [
                {
                    "name": "caller",
                    "calls": [
                        {
                            "name": "helper",
                            "line": 2,
                            "args": [{"kind": "name", "value": "value"}],
                            "kwargs": [
                                {
                                    "name": "mode",
                                    "kind": "literal",
                                    "value": "'fast'",
                                }
                            ],
                        }
                    ],
                },
                {"name": "helper"},
            ],
        }
    }

    assert resolve_call_edges(inventory) == [
        {
            "from": {"file": "m.py", "symbol": "caller"},
            "to": {"file": "m.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 2,
        }
    ]
