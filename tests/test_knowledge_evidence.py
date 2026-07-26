"""Tests for concept-scoped knowledge evidence normalization."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from llm_wiki_cli.services.knowledge_evidence import (
    ENTITY_OBSERVATION_SCOPE,
    MODULE_OBSERVATION_SCOPE,
    UNKNOWN_ENTITY_NOT_FOUND,
    UNKNOWN_INSUFFICIENT_INVENTORY,
    UNKNOWN_INVALID_INVENTORY,
    UNKNOWN_UNSUPPORTED_LANGUAGE,
    ConceptObservationBasis,
    build_entity_observation_basis,
    build_module_observation_basis,
    entity_observation_hash,
    is_valid_sha256,
    module_observation_hash,
    normalize_entity_observation,
    normalize_module_observation,
    semantic_hash_for_file,
    sha256_bytes,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "knowledge-evidence"
    / "concept-observation-inventories.json"
)
SOURCE_PATH = "src/accounts.py"
EXTRACTOR_REF = "python-ast"
SOURCE_HASH = sha256_bytes(b"class User: pass\n")


def _inventory(language: str) -> dict:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return payload[language]


def _module_hash(file_data, *, complete: bool = True) -> str | None:
    return module_observation_hash(
        file_data,
        inventory_complete=complete,
    )


def _entity_hash(
    file_data,
    entity_name: str,
    occurrence: int = 1,
    *,
    complete: bool = True,
) -> str | None:
    return entity_observation_hash(
        file_data,
        entity_name,
        occurrence,
        inventory_complete=complete,
    )


def _reverse_mapping_order(value):
    if isinstance(value, dict):
        return {
            key: _reverse_mapping_order(item)
            for key, item in reversed(list(value.items()))
        }
    if isinstance(value, list):
        return [_reverse_mapping_order(item) for item in value]
    return value


def _shift_locations(value, amount: int = 100) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"line", "end_line", "decorator_line"}:
                value[key] = item + amount
            else:
                _shift_locations(item, amount)
    elif isinstance(value, list):
        for item in value:
            _shift_locations(item, amount)


def _module_basis(
    file_data,
    *,
    source_hash: str = SOURCE_HASH,
    complete: bool = True,
) -> ConceptObservationBasis:
    return build_module_observation_basis(
        source_path=SOURCE_PATH,
        file_data=file_data,
        source_content_hash=source_hash,
        extractor_ref=EXTRACTOR_REF,
        inventory_complete=complete,
    )


def _entity_basis(
    file_data,
    name: str,
    occurrence: int = 1,
    *,
    source_hash: str = SOURCE_HASH,
    complete: bool = True,
) -> ConceptObservationBasis:
    return build_entity_observation_basis(
        source_path=SOURCE_PATH,
        file_data=file_data,
        entity_name=name,
        occurrence=occurrence,
        source_content_hash=source_hash,
        extractor_ref=EXTRACTOR_REF,
        inventory_complete=complete,
    )


def test_module_normalization_contains_only_module_structural_inputs():
    inventory = _inventory("python")

    normalized = normalize_module_observation(inventory)

    assert normalized == {
        "scope": "module",
        "language": "python",
        "imports": [{"module": "domain", "name": "Service"}],
        "classes": [
            {
                "name": "User",
                "kind": "class",
                "bases": [],
                "occurrence": 1,
            },
            {
                "name": "AccountService",
                "kind": "class",
                "bases": ["Service"],
                "occurrence": 1,
            },
        ],
        "functions": [
            {
                "name": "run",
                "params": [
                    {
                        "kind": "positional_or_keyword",
                        "name": "user_id",
                        "type": "int",
                    }
                ],
                "return_type": "User",
                "is_async": False,
                "decorators": ["command"],
            }
        ],
    }
    assert inventory["module_docstring"] == "Account orchestration."
    assert inventory["classes"][0]["methods"][0]["calls"]


def test_entity_normalization_selects_one_record_and_removes_nonstructural_data():
    inventory = _inventory("python")

    normalized = normalize_entity_observation(inventory, "User", 1)

    assert normalized is not None
    assert normalized["scope"] == "entity"
    assert normalized["language"] == "python"
    assert normalized["name"] == "User"
    assert normalized["occurrence"] == 1
    declaration = normalized["declaration"]
    assert declaration["name"] == "User"
    assert "line" not in declaration
    assert "docstring" not in declaration
    assert declaration["attributes"] == [
        {"name": "id", "required": True, "type": "int"}
    ]
    assert declaration["methods"] == [
        {
            "decorators": [],
            "is_async": False,
            "name": "render",
            "params": [],
            "return_type": "str",
        }
    ]
    assert inventory["classes"][0]["docstring"] == "A user account."


def test_mapping_order_is_canonical_but_array_order_remains_observed():
    inventory = _inventory("python")
    reordered_mappings = _reverse_mapping_order(inventory)

    assert _module_hash(inventory) == _module_hash(reordered_mappings)
    assert _entity_hash(inventory, "User") == _entity_hash(reordered_mappings, "User")

    reordered_functions = deepcopy(inventory)
    reordered_functions["functions"].append(
        {
            "name": "prepare",
            "line": 30,
            "params": [],
            "return_type": "",
            "decorators": [],
            "is_async": False,
        }
    )
    reverse = deepcopy(reordered_functions)
    reverse["functions"].reverse()
    assert _module_hash(reordered_functions) != _module_hash(reverse)


def test_line_only_shift_changes_source_hash_but_not_observation_hash():
    inventory = _inventory("python")
    inventory["functions"][0]["end_line"] = 29
    inventory["classes"][0]["attributes"][0]["decorator_line"] = 7
    shifted = deepcopy(inventory)
    _shift_locations(shifted)

    first_source_hash = sha256_bytes(b"\nclass User:\n    pass\n")
    shifted_source_hash = sha256_bytes(b"\n\n\nclass User:\n    pass\n")
    first_module = _module_basis(inventory, source_hash=first_source_hash)
    shifted_module = _module_basis(shifted, source_hash=shifted_source_hash)
    first_entity = _entity_basis(
        inventory,
        "User",
        source_hash=first_source_hash,
    )
    shifted_entity = _entity_basis(
        shifted,
        "User",
        source_hash=shifted_source_hash,
    )

    assert first_module.source_content_hash != shifted_module.source_content_hash
    assert (
        first_module.concept_observation_hash == shifted_module.concept_observation_hash
    )
    assert (
        first_entity.concept_observation_hash == shifted_entity.concept_observation_hash
    )


def test_entity_changes_are_sibling_scoped_and_module_facing_changes_propagate():
    inventory = _inventory("python")
    user_hash = _entity_hash(inventory, "User")
    service_hash = _entity_hash(inventory, "AccountService")
    module_hash = _module_hash(inventory)

    service_internal_change = deepcopy(inventory)
    service_internal_change["classes"][1]["attributes"][0]["type"] = "Store"
    assert _entity_hash(service_internal_change, "User") == user_hash
    assert _entity_hash(service_internal_change, "AccountService") != service_hash
    assert _module_hash(service_internal_change) == module_hash

    service_summary_change = deepcopy(inventory)
    service_summary_change["classes"][1]["bases"] = ["AsyncService"]
    assert _module_hash(service_summary_change) != module_hash


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data["imports"][0].update(module="domain.models"),
        lambda data: data["functions"][0]["params"][0].update(type="UserId"),
        lambda data: data["functions"][0].update(return_type="Account"),
    ],
)
def test_module_import_or_signature_change_changes_observation(mutate):
    inventory = _inventory("python")
    changed = deepcopy(inventory)
    mutate(changed)

    assert _module_hash(changed) != _module_hash(inventory)


def test_semantic_prose_and_call_details_are_outside_structural_hash_domain():
    inventory = _inventory("python")
    changed = deepcopy(inventory)
    changed["module_docstring"] = "Rewritten module prose."
    changed["classes"][0]["docstring"] = "Rewritten entity prose."
    changed["classes"][0]["attributes"][0]["description"] = "Rewritten field prose."
    changed["classes"][0]["methods"][0]["docstring"] = "Rewritten method prose."
    changed["classes"][0]["methods"][0]["calls"][0]["name"] = "repr"
    changed["functions"][0]["docstring"] = "Rewritten function prose."
    changed["functions"][0]["calls"][0]["name"] = "OtherService"

    assert _module_hash(changed) == _module_hash(inventory)
    assert _entity_hash(changed, "User") == _entity_hash(inventory, "User")


def test_duplicate_entity_occurrences_are_exact_distinct_and_stable():
    declaration = {
        "name": "Parser",
        "kind": "class",
        "line": 4,
        "bases": [],
        "decorators": [],
        "attributes": [],
        "methods": [],
    }
    inventory = {
        "language": "python",
        "module_docstring": "",
        "classes": [declaration, deepcopy(declaration)],
        "functions": [],
        "imports": [],
    }
    inventory["classes"][1]["line"] = 20

    first = _entity_hash(inventory, "Parser", 1)
    second = _entity_hash(inventory, "Parser", 2)
    repeated = _entity_hash(deepcopy(inventory), "Parser", 2)

    assert is_valid_sha256(first)
    assert is_valid_sha256(second)
    assert first != second
    assert second == repeated

    shifted = deepcopy(inventory)
    _shift_locations(shifted)
    assert _entity_hash(shifted, "Parser", 1) == first
    assert _entity_hash(shifted, "Parser", 2) == second


def test_known_basis_has_contract_fields_and_canonical_hash():
    basis = _entity_basis(_inventory("python"), "User")

    assert basis.is_known
    assert basis.scope == ENTITY_OBSERVATION_SCOPE
    assert basis.unknown_reason is None
    assert is_valid_sha256(basis.concept_observation_hash)
    assert basis.to_evidence_payload() == {
        "scope": "entity",
        "source_path": SOURCE_PATH,
        "extractor_ref": EXTRACTOR_REF,
        "source_content_hash": SOURCE_HASH,
        "concept_observation_hash": basis.concept_observation_hash,
    }
    assert (
        basis.concept_observation_hash
        == "sha256:f42114f1508857eadf7f466a21fc228428fc00a044d0f45ef66e0ceb9e57cdd8"
    )


def test_explicit_slim_inventory_returns_unknown_without_hash():
    inventory = _inventory("python")
    basis = _module_basis(inventory, complete=False)

    assert not basis.is_known
    assert basis.scope == MODULE_OBSERVATION_SCOPE
    assert basis.concept_observation_hash is None
    assert basis.unknown_reason == UNKNOWN_INSUFFICIENT_INVENTORY
    assert basis.to_evidence_payload() == {
        "scope": "module",
        "source_path": SOURCE_PATH,
        "extractor_ref": EXTRACTOR_REF,
        "source_content_hash": SOURCE_HASH,
    }
    assert _module_hash(inventory, complete=False) is None
    assert _entity_hash(inventory, "User", complete=False) is None


@pytest.mark.parametrize(
    ("file_data", "reason"),
    [
        (
            {"language": "cobol", "classes": [], "functions": []},
            UNKNOWN_UNSUPPORTED_LANGUAGE,
        ),
        (
            {"language": "python", "classes": ["User"], "functions": []},
            UNKNOWN_INVALID_INVENTORY,
        ),
        (None, UNKNOWN_INVALID_INVENTORY),
    ],
)
def test_unsupported_or_malformed_module_inventory_is_explicit_unknown(
    file_data, reason
):
    basis = _module_basis(file_data)

    assert not basis.is_known
    assert basis.concept_observation_hash is None
    assert basis.unknown_reason == reason


@pytest.mark.parametrize(
    "file_data",
    [
        {
            "language": "python",
            "classes": [{"name": "Client", "bases": "not-an-array"}],
            "functions": [],
            "imports": [],
        },
        {
            "language": "python",
            "classes": [],
            "functions": [{"name": "run", "params": "not-an-array"}],
            "imports": [],
        },
        {
            "language": "python",
            "classes": [],
            "functions": [],
            "imports": [{}],
        },
    ],
)
def test_malformed_module_structural_fields_are_unknown(file_data):
    basis = _module_basis(file_data)

    assert not basis.is_known
    assert basis.unknown_reason == UNKNOWN_INVALID_INVENTORY


def test_malformed_selected_entity_structural_fields_are_unknown():
    inventory = {
        "language": "python",
        "classes": [{"name": "Client", "methods": "not-an-array"}],
        "functions": [],
        "imports": [],
    }

    basis = _entity_basis(inventory, "Client")

    assert not basis.is_known
    assert basis.unknown_reason == UNKNOWN_INVALID_INVENTORY


def test_missing_entity_occurrence_is_explicit_unknown():
    basis = _entity_basis(_inventory("python"), "User", 2)

    assert not basis.is_known
    assert basis.unknown_reason == UNKNOWN_ENTITY_NOT_FOUND


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"source_path": "/tmp/accounts.py"}, "source_path"),
        ({"source_path": "D:secret.py"}, "source_path"),
        ({"source_path": "src/../accounts.py"}, "source_path"),
        ({"source_path": " src/accounts.py"}, "source_path"),
        ({"source_path": "src/accounts.py "}, "source_path"),
        ({"source_path": "src/\x00accounts.py"}, "source_path"),
        ({"source_content_hash": "sha256:nope"}, "source_content_hash"),
        ({"extractor_ref": "python ast"}, "extractor_ref"),
        ({"inventory_complete": "yes"}, "inventory_complete"),
    ],
)
def test_basis_builder_rejects_invalid_caller_coordinates(kwargs, message):
    arguments = {
        "source_path": SOURCE_PATH,
        "file_data": _inventory("python"),
        "source_content_hash": SOURCE_HASH,
        "extractor_ref": EXTRACTOR_REF,
        "inventory_complete": True,
    }
    arguments.update(kwargs)

    with pytest.raises((TypeError, ValueError), match=message):
        build_module_observation_basis(**arguments)


@pytest.mark.parametrize(("name", "occurrence"), [("", 1), ("User", 0), ("User", True)])
def test_entity_builder_rejects_invalid_occurrence_coordinates(name, occurrence):
    with pytest.raises(ValueError):
        _entity_basis(_inventory("python"), name, occurrence)


def test_prepared_haskell_inventory_requires_no_external_helper():
    inventory = _inventory("haskell")
    module_basis = build_module_observation_basis(
        source_path="hls-analysis/src/HLSAnalysis/API.hs",
        file_data=inventory,
        source_content_hash=sha256_bytes(b"module HLSAnalysis.API where\n"),
        extractor_ref="haskell-ghc",
        inventory_complete=True,
    )
    entity_basis = build_entity_observation_basis(
        source_path="hls-analysis/src/HLSAnalysis/API.hs",
        file_data=inventory,
        entity_name="User",
        occurrence=1,
        source_content_hash=sha256_bytes(b"module HLSAnalysis.API where\n"),
        extractor_ref="haskell-ghc",
        inventory_complete=True,
    )

    assert module_basis.is_known
    assert entity_basis.is_known

    signature_change = deepcopy(inventory)
    signature_change["functions"][0]["signature"] = "UserId -> IO (Maybe User)"
    assert _module_hash(signature_change) != (module_basis.concept_observation_hash)

    entity_change = deepcopy(inventory)
    entity_change["classes"][0]["kind"] = "newtype"
    assert _entity_hash(entity_change, "User") != (
        entity_basis.concept_observation_hash
    )


def test_prepared_typescript_module_signals_are_scoped_without_helper():
    inventory = _inventory("typescript")
    normalized = normalize_module_observation(inventory)
    assert normalized is not None
    assert normalized["exports"] == ["Client", "start"]
    assert normalized["constants"] == [{"name": "DEFAULT_PORT"}]
    assert normalized["module_calls"] == [{"name": "createServer", "target": "server"}]

    baseline = _module_hash(inventory)
    shifted = deepcopy(inventory)
    _shift_locations(shifted)
    assert _module_hash(shifted) == baseline

    unrendered_call_detail = deepcopy(inventory)
    unrendered_call_detail["module_calls"][0]["args"] = ["otherCallback"]
    assert _module_hash(unrendered_call_detail) == baseline

    for field, value in (
        ("exports", ["Client", "stop"]),
        ("constants", [{"name": "FALLBACK_PORT", "line": 3}]),
        (
            "module_calls",
            [{"name": "listen", "target": "server", "line": 20}],
        ),
    ):
        changed = deepcopy(inventory)
        changed[field] = value
        assert _module_hash(changed) != baseline

    entity_change = deepcopy(inventory)
    entity_change["classes"][0]["attributes"][0]["type"] = "string"
    assert _entity_hash(entity_change, "Client") != _entity_hash(
        inventory,
        "Client",
    )


def test_go_unnamed_parameter_is_valid_structural_inventory():
    inventory = {
        "language": "go",
        "classes": [],
        "functions": [
            {
                "name": "Parse",
                "params": [{"name": "", "type": "string"}],
                "return_type": "error",
                "is_async": False,
            }
        ],
        "imports": [],
    }

    assert is_valid_sha256(_module_hash(inventory))


def test_manifest_v4_line_filter_remains_unchanged_for_new_location_keys():
    assert semantic_hash_for_file({"line": 1, "value": "same"}) == (
        semantic_hash_for_file({"line": 99, "value": "same"})
    )
    assert semantic_hash_for_file({"end_line": 1}) != semantic_hash_for_file(
        {"end_line": 99}
    )
    assert semantic_hash_for_file({"decorator_line": 1}) != semantic_hash_for_file(
        {"decorator_line": 99}
    )
