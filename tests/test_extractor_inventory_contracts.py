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
