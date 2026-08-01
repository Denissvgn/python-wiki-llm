from __future__ import annotations

import inspect
import textwrap

import pytest

from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.extractors.go_extractor import GoExtractor
from llm_wiki_cli.extractors.rust_extractor import RustExtractor
from llm_wiki_cli.extractors.ts_extractor import TypeScriptExtractor
from llm_wiki_cli.services import contracts


HASKELL_MINIMUM_INVENTORY = {
    "hls-analysis/src/HLSAnalysis/API.hs": {
        "language": "haskell",
        "module": "HLSAnalysis.API",
        "imports": [
            {
                "module": "Data.Text",
                "qualified": False,
                "alias": None,
                "line": 4,
            }
        ],
        "classes": [
            {"name": "User", "kind": "data", "line": 8},
            {
                "name": "instance Renderable User",
                "kind": "instance",
                "line": 14,
            },
        ],
        "functions": [
            {
                "name": "loadUser",
                "kind": "signature",
                "signature": "UserId -> Maybe User",
                "line": 18,
            },
            {"name": "loadUser", "kind": "function", "line": 19},
        ],
    }
}

HASKELL_OPTIONAL_FIELD_INVENTORY = {
    "hls-analysis/src/HLSAnalysis/API.hs": {
        **HASKELL_MINIMUM_INVENTORY["hls-analysis/src/HLSAnalysis/API.hs"],
        "language_pragmas": ["FlexibleInstances"],
        "exports": ["User", "loadUser"],
        "classes": [
            {
                "name": "User",
                "kind": "data",
                "line": 8,
                "deriving": ["Show", "Eq"],
            },
            {
                "name": "Token",
                "kind": "newtype",
                "line": 12,
                "deriving": ["Show"],
            },
            {"name": "UserId", "kind": "type", "line": 16},
            {"name": "Renderable", "kind": "class", "line": 20},
            {
                "name": "instance Renderable User",
                "kind": "instance",
                "line": 24,
            },
        ],
        "functions": [
            {
                "name": "loadUser",
                "kind": "signature",
                "signature": "UserId -> Maybe User",
                "line": 28,
            },
            {"name": "loadUser", "kind": "function", "line": 29},
            {"name": "apiName", "kind": "value", "line": 32},
        ],
    }
}


def test_extract_v1_data_flow_fields_are_additive_contract():
    assert contracts.EXTRACT_SCHEMA_VERSION == "llm-wiki-extract/v1"
    assert getattr(contracts, "EXTRACT_ADDITIVE_FIELDS", None) == {
        "calls[].args",
        "calls[].kwargs",
        "classes[].attributes[].alias",
        "classes[].attributes[].annotated_metadata",
        "classes[].attributes[].constraints",
        "classes[].attributes[].default_factory",
        "classes[].attributes[].description",
        "classes[].attributes[].examples",
        "classes[].attributes[].line",
        "classes[].attributes[].literal_values",
        "classes[].attributes[].nullable",
        "classes[].attributes[].required",
        "classes[].attributes[].serialization_alias",
        "classes[].attributes[].unknowns",
        "classes[].attributes[].validation_alias",
        "classes[].attributes[].value",
        "classes[].inferred",
        "classes[].kind",
        "classes[].literal_values",
        "classes[].methods[].validator",
        "classes[].model_config",
        "classes[].model_config[].unknowns",
        "classes[].model_kind",
        "classes[].target",
        "classes[].type_params",
        "data_effects",
        "data_effects.inputs[].parameter_kind",
        "data_flow_details",
        "data_flows",
        "dependencies.version_details",
        "entrypoints[].routes",
        "frameworks.fastapi",
        "main_block_calls",
        "params[].kind",
        "api_contracts",
    }


def test_deep_extract_m4_top_level_fields_are_additive_for_old_clients(
    tmp_path, monkeypatch
):
    (tmp_path / "api.py").write_text(
        textwrap.dedent(
            """\
            from repo import save

            __all__ = ["run"]

            def run(payload):
                return save(payload)
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "repo.py").write_text(
        "def save(payload):\n    return payload\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    payload = extract_cmd.build_extract_payload(".", deep=True).payload
    old_client_payload = {
        "schema_version": payload["schema_version"],
        "inventory": payload["inventory"],
    }

    assert payload["schema_version"] == "llm-wiki-extract/v1"
    assert {"entrypoints", "data_flows", "dependencies"} <= set(payload)
    assert set(old_client_payload) == {"schema_version", "inventory"}
    assert old_client_payload["inventory"] == payload["inventory"]
    assert "api.py" in old_client_payload["inventory"]


def test_non_deep_extract_keeps_m4_top_level_fields_optional(tmp_path, monkeypatch):
    (tmp_path / "api.py").write_text(
        '__all__ = ["run"]\n\n\ndef run():\n    return 1\n', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    payload = extract_cmd.build_extract_payload(".", deep=False).payload

    assert payload["schema_version"] == "llm-wiki-extract/v1"
    assert "inventory" in payload
    assert "entrypoints" not in payload
    assert "data_flows" not in payload
    assert "dependencies" not in payload


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
        {
            "kind": "param",
            "parameter_kind": "positional_or_keyword",
            "name": "value",
            "type": "",
        }
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
            "args": [{"kind": "name", "value": "value"}],
            "kwargs": [
                {
                    "name": "mode",
                    "kind": "literal",
                    "value": "'fast'",
                }
            ],
        }
    ]


def test_consumers_tolerate_minimum_haskell_inventory_shape():
    """Haskell syntax inventory remains additive under llm-wiki-extract/v1."""
    from llm_wiki_cli.commands.extract_cmd import resolve_call_edges
    from llm_wiki_cli.services.dependencies import build_dependency_graph

    assert contracts.EXTRACT_SCHEMA_VERSION == "llm-wiki-extract/v1"
    assert resolve_call_edges(HASKELL_MINIMUM_INVENTORY) == []
    assert build_dependency_graph(HASKELL_MINIMUM_INVENTORY)["unresolved"] == [
        {
            "file": "hls-analysis/src/HLSAnalysis/API.hs",
            "module": "Data.Text",
            "name": "",
        }
    ]


def test_consumers_tolerate_optional_haskell_specific_fields():
    """Optional Haskell metadata must not require an extract schema bump."""
    from llm_wiki_cli.commands.extract_cmd import resolve_call_edges
    from llm_wiki_cli.services.dependencies import build_dependency_graph
    from llm_wiki_cli.services.relationships import build_entity_relationship_summaries

    inventory = HASKELL_OPTIONAL_FIELD_INVENTORY

    assert contracts.EXTRACT_SCHEMA_VERSION == "llm-wiki-extract/v1"
    assert resolve_call_edges(inventory) == []
    assert build_dependency_graph(inventory)["unresolved"] == [
        {
            "file": "hls-analysis/src/HLSAnalysis/API.hs",
            "module": "Data.Text",
            "name": "",
        }
    ]
    summaries = build_entity_relationship_summaries(inventory, [])
    class_kinds = {
        summary["name"]: summary.get("kind") for summary in summaries["classes"]
    }
    assert class_kinds == {
        "Renderable": "class",
        "Token": "newtype",
        "User": "data",
        "UserId": "type",
        "instance Renderable User": "instance",
    }


def test_haskell_declaration_kind_values_are_contract_fields():
    """Removing Haskell ``kind`` fields must break focused contract coverage."""
    class_kinds = {
        declaration["kind"]
        for declaration in HASKELL_OPTIONAL_FIELD_INVENTORY[
            "hls-analysis/src/HLSAnalysis/API.hs"
        ]["classes"]
    }
    function_kinds = {
        declaration["kind"]
        for declaration in HASKELL_OPTIONAL_FIELD_INVENTORY[
            "hls-analysis/src/HLSAnalysis/API.hs"
        ]["functions"]
    }

    assert class_kinds == {"data", "newtype", "type", "class", "instance"}
    assert function_kinds == {"signature", "function", "value"}
