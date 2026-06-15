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
        "def caller():\n    return helper()\n\n\ndef helper():\n    return 1\n"
    )

    deep = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"]
    by_name = {fn["name"]: fn for fn in deep}
    assert by_name["caller"].get("calls")  # additive: present when calls exist
    assert "calls" not in by_name["helper"]  # optional: omitted when empty

    slim = get_inventory(str(tmp_path), deep=False)["m.py"]["functions"]
    assert all("calls" not in fn for fn in slim)


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
