"""Contract tests for the native knowledge model."""

from __future__ import annotations

import json
import re
from collections import UserDict
from copy import deepcopy
from dataclasses import replace
from typing import Any, Callable

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from llm_wiki_cli.services.contracts import (
    KNOWLEDGE_SCHEMA_VERSION,
    SECTION_OWNERSHIP_EXTENSION_KEY,
)
from llm_wiki_cli.services.knowledge_model import (
    EVALUATED_REVISION_PATTERN,
    LIMITATION_CODE_PATTERN,
    PAGE_KIND_TO_CONCEPT_KIND,
    REPOSITORY_IDENTITY_PATTERN,
    REPOSITORY_IDENTITY_SOURCE_EXTENSION,
    ActorKind,
    ComputedFreshness,
    ConceptKind,
    EvidenceState,
    KnowledgeModelError,
    KnowledgeProjectionProfile,
    Lifecycle,
    Origin,
    RepositoryIdentitySource,
    Resolution,
    TargetClass,
    Verification,
    concept_kind_for_page_kind,
    knowledge_index_to_payload,
    load_knowledge_schema,
    parse_knowledge_index,
    repository_identities_match,
    serialize_knowledge_index,
)
from llm_wiki_cli.services.section_ownership import (
    observe_page_sections,
    section_ownership_extension,
)
from llm_wiki_cli.services.wiki_surface import PageKind


def _hash(character: str) -> str:
    return f"sha256:{character * 64}"


def _minimum_payload() -> dict[str, Any]:
    """Return the smallest useful source-module knowledge record."""
    return {
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "bundle": {
            "repository": {
                "identity": "unknown",
            },
            "snapshot": {
                "source_snapshot_hash": _hash("1"),
                "markdown_snapshot_hash": _hash("2"),
                "surface_index_hash": _hash("3"),
                "generation_options_hash": _hash("4"),
            },
            "producer": {
                "tool": {
                    "id": "agent-wiki-cli",
                    "version": "1.4.0",
                },
            },
        },
        "concepts": [
            {
                "locator": "llm-wiki://modules/sync_cmd",
                "concept_kind": "source-module",
                "title": "sync_cmd",
                "document": {
                    "page_kind": "modules",
                    "page_id": "sync_cmd",
                    "canonical_path": "modules/sync_cmd.md",
                    "role": "semantic",
                },
                "facets": {
                    "structure": {},
                    "semantics": {
                        "ownership": "semantic",
                        "page_hash": _hash("5"),
                    },
                },
            }
        ],
        "relationships": [],
    }


def test_section_extension_model_validation_is_intrinsic_not_snapshot_parity():
    payload = _minimum_payload()
    observed = observe_page_sections(
        "# sync_cmd\n## Description\nForeign snapshot.\n",
        "llm-wiki://modules/sync_cmd",
        PageKind.MODULES,
    )
    payload["extensions"] = section_ownership_extension([observed])
    assert observed.source_hash != payload["concepts"][0]["facets"]["semantics"][
        "page_hash"
    ]

    model = parse_knowledge_index(payload)
    assert SECTION_OWNERSHIP_EXTENSION_KEY in model.extensions

    malformed = deepcopy(payload)
    malformed["extensions"][SECTION_OWNERSHIP_EXTENSION_KEY]["pages"][0][
        "sections"
    ][0]["occurrence"] = 0
    with pytest.raises(KnowledgeModelError):
        parse_knowledge_index(malformed)


def _full_payload() -> dict[str, Any]:
    payload = _minimum_payload()
    payload["bundle"]["repository"] = {
        "identity": "github.com/example/project",
        "evaluated_revision": f"git:{'a' * 40}",
        "working_tree": "clean",
        "extensions": {
            REPOSITORY_IDENTITY_SOURCE_EXTENSION: "configured-public",
        },
    }
    payload["bundle"]["producer"] = {
        "tool": {
            "id": "agent-wiki-cli",
            "version": "1.4.0",
        },
        "extractors": [
            {
                "id": "python-ast",
                "version": "builtin",
                "configuration_hash": _hash("6"),
                "limitations": ["syntax-only"],
            }
        ],
        "plugins": [],
    }

    concept = payload["concepts"][0]
    concept["lifecycle"] = "active"
    concept["facets"]["structure"] = {
        "origin": "extracted",
        "evidence": "present",
        "basis": {
            "scope": "module",
            "source_path": "src/llm_wiki_cli/commands/sync_cmd.py",
            "extractor_ref": "python-ast",
            "source_content_hash": _hash("7"),
            "concept_observation_hash": _hash("8"),
        },
    }
    concept["facets"]["semantics"].update(
        {
            "authorship": {
                "kind": "agent",
                "id": "docs-agent",
                "version": "2026.07",
                "model": "example-model",
                "organization": "Example",
            },
            "verification": "unverified",
        }
    )

    payload["relationships"] = [
        {
            "kind": "derived_from",
            "from": concept["locator"],
            "target": {
                "target_class": "source",
                "source_path": "src/llm_wiki_cli/commands/sync_cmd.py",
            },
            "origin": "extracted",
            "evidence": {
                "state": "present",
                "concept_observation_hash": _hash("8"),
            },
            "resolution": "resolved",
        },
        {
            "kind": "links_to",
            "from": concept["locator"],
            "target": {
                "target_class": "concept",
                "canonical_path": "modules/sync_cmd.md",
                "raw_target": "sync_cmd.md",
                "normalized_target": "sync_cmd.md",
                "label": "sync_cmd",
                "location": {"start": 10, "end": 34},
            },
            "origin": "markdown",
            "evidence": {
                "state": "present",
                "page_hash": _hash("5"),
            },
            "resolution": "resolved",
        },
    ]
    return payload


def _assert_model_error(payload: object, field: str) -> KnowledgeModelError:
    with pytest.raises(KnowledgeModelError) as exc_info:
        parse_knowledge_index(payload)
    assert exc_info.value.field == field
    assert field in str(exc_info.value)
    return exc_info.value


def _schema_enum_sets(value: object) -> set[frozenset[str]]:
    enum_sets: set[frozenset[str]] = set()
    if isinstance(value, dict):
        enum = value.get("enum")
        if isinstance(enum, list) and all(isinstance(item, str) for item in enum):
            enum_sets.add(frozenset(enum))
        for child in value.values():
            enum_sets.update(_schema_enum_sets(child))
    elif isinstance(value, list):
        for child in value:
            enum_sets.update(_schema_enum_sets(child))
    return enum_sets


def _schema_property_names(value: object) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict):
            names.update(str(name) for name in properties)
        for child in value.values():
            names.update(_schema_property_names(child))
    elif isinstance(value, list):
        for child in value:
            names.update(_schema_property_names(child))
    return names


def test_contract_enums_have_exact_v1_vocabularies():
    assert {kind.value for kind in ConceptKind} == {
        "source-module",
        "code-entity",
        "workflow",
        "guide",
        "user-flow",
        "infrastructure-resource",
        "api-contract",
        "dependency-view",
        "navigation-document",
        "change-log-document",
    }
    assert {origin.value for origin in Origin} == {
        "unknown",
        "extracted",
        "authored",
        "inferred",
        "imported",
        "markdown",
        "governance",
    }
    assert {state.value for state in EvidenceState} == {
        "unknown",
        "present",
        "missing",
        "invalid",
        "not-applicable",
    }
    assert {state.value for state in Resolution} == {
        "resolved",
        "ambiguous",
        "external",
        "unresolved",
    }
    assert {target_class.value for target_class in TargetClass} == {
        "unknown",
        "concept",
        "source",
        "external",
        "mail",
        "anchor",
        "asset",
        "malformed",
    }
    assert {state.value for state in Verification} == {
        "untracked",
        "unverified",
        "machine-checked",
        "human-reviewed",
        "failed",
        "expired",
    }
    assert {state.value for state in Lifecycle} == {
        "unknown",
        "draft",
        "active",
        "deprecated",
        "superseded",
    }
    assert {state.value for state in ComputedFreshness} == {
        "unknown",
        "current",
        "nonsemantic-source-change",
        "source-changed",
        "basis-incompatible",
        "source-missing",
    }
    assert {kind.value for kind in ActorKind} == {
        "unknown",
        "tool",
        "agent",
        "human",
        "process",
    }
    assert {source.value for source in RepositoryIdentitySource} == {
        "configured-public",
        "normalized-vcs",
        "unknown",
    }
    assert {profile.value for profile in KnowledgeProjectionProfile} == {
        "internal",
        "public-portable",
    }


@pytest.mark.parametrize(
    ("page_kind", "concept_kind"),
    [
        (PageKind.INDEX, ConceptKind.NAVIGATION_DOCUMENT),
        (PageKind.LOG, ConceptKind.CHANGE_LOG_DOCUMENT),
        (PageKind.ENTITIES, ConceptKind.CODE_ENTITY),
        (PageKind.MODULES, ConceptKind.SOURCE_MODULE),
        (PageKind.WORKFLOWS, ConceptKind.WORKFLOW),
        (PageKind.GUIDES, ConceptKind.GUIDE),
        (PageKind.FLOWS, ConceptKind.USER_FLOW),
        (PageKind.INFRASTRUCTURE, ConceptKind.INFRASTRUCTURE_RESOURCE),
        (PageKind.API_CONTRACTS, ConceptKind.API_CONTRACT),
        (PageKind.DEPENDENCIES, ConceptKind.DEPENDENCY_VIEW),
        (PageKind.LOAD_ORDER, ConceptKind.DEPENDENCY_VIEW),
    ],
)
def test_page_kinds_map_to_domain_or_explicit_document_kinds(
    page_kind: PageKind, concept_kind: ConceptKind
):
    assert concept_kind_for_page_kind(page_kind) is concept_kind
    assert concept_kind_for_page_kind(page_kind.value) is concept_kind


def test_minimum_record_deserializes_missing_facts_conservatively():
    model = parse_knowledge_index(_minimum_payload())
    concept = model.concepts[0]

    assert model.schema_version == KNOWLEDGE_SCHEMA_VERSION
    assert concept.concept_kind is ConceptKind.SOURCE_MODULE
    assert concept.lifecycle is Lifecycle.UNKNOWN
    assert concept.facets.structure.origin is Origin.UNKNOWN
    assert concept.facets.structure.evidence is EvidenceState.UNKNOWN
    assert concept.facets.structure.basis is None
    assert concept.facets.semantics.authorship.kind is ActorKind.UNKNOWN
    assert concept.facets.semantics.authorship.actor_id is None
    assert concept.facets.semantics.verification is Verification.UNTRACKED
    assert model.bundle.repository.identity_source is RepositoryIdentitySource.UNKNOWN

    normalized = knowledge_index_to_payload(model)
    assert normalized["bundle"]["repository"] == {
        "identity": "unknown",
        "evaluated_revision": "unknown",
        "working_tree": "unknown",
    }
    assert normalized["bundle"]["producer"]["extractors"] == []
    assert normalized["bundle"]["producer"]["plugins"] == []
    normalized_concept = normalized["concepts"][0]
    assert normalized_concept["lifecycle"] == "unknown"
    assert normalized_concept["facets"]["structure"] == {
        "origin": "unknown",
        "evidence": "unknown",
    }
    assert normalized_concept["facets"]["semantics"]["authorship"] == {
        "kind": "unknown"
    }
    assert normalized_concept["facets"]["semantics"]["verification"] == "untracked"


def test_full_record_round_trips_all_supported_shapes():
    payload = _full_payload()
    model = parse_knowledge_index(payload)
    normalized = knowledge_index_to_payload(model)

    assert normalized == payload
    assert model.bundle.repository.identity_source is (
        RepositoryIdentitySource.CONFIGURED_PUBLIC
    )
    assert model.concepts[0].lifecycle is Lifecycle.ACTIVE
    assert model.concepts[0].facets.structure.origin is Origin.EXTRACTED
    assert model.concepts[0].facets.structure.evidence is EvidenceState.PRESENT
    assert model.concepts[0].facets.semantics.verification is (Verification.UNVERIFIED)
    assert [relationship.kind for relationship in model.relationships] == [
        "derived_from",
        "links_to",
    ]
    assert [relationship.resolution for relationship in model.relationships] == [
        Resolution.RESOLVED,
        Resolution.RESOLVED,
    ]


def test_present_aggregate_observation_carries_aggregate_input_commitment():
    payload = _minimum_payload()
    payload["concepts"][0]["facets"]["structure"] = {
        "origin": "extracted",
        "evidence": "present",
        "basis": {
            "scope": "aggregate",
            "aggregate_input_hash": _hash("7"),
        },
    }

    model = parse_knowledge_index(payload)

    basis = model.concepts[0].facets.structure.basis
    assert basis is not None
    assert basis.aggregate_input_hash == _hash("7")
    assert list(_knowledge_schema_validator().iter_errors(payload)) == []


def test_repository_identity_matches_only_equal_nonunknown_identities():
    unknown_left = parse_knowledge_index(_minimum_payload()).bundle.repository
    unknown_right = parse_knowledge_index(_minimum_payload()).bundle.repository
    explicit_left = parse_knowledge_index(_full_payload()).bundle.repository
    explicit_right = parse_knowledge_index(_full_payload()).bundle.repository
    different_payload = _full_payload()
    different_payload["bundle"]["repository"]["identity"] = (
        "github.com/example/other-project"
    )
    explicit_different = parse_knowledge_index(different_payload).bundle.repository

    assert not repository_identities_match(unknown_left, unknown_right)
    assert repository_identities_match(explicit_left, explicit_right)
    assert not repository_identities_match(explicit_left, explicit_different)
    assert not repository_identities_match(
        replace(explicit_left, extensions={}),
        explicit_right,
    )
    with pytest.raises(TypeError):
        repository_identities_match("unknown", unknown_right)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "identity",
    [
        "https://user:token@private.example/repo.git?access_token=secret",
        "file:///Users/alice/private/repo",
        "sha256:" + ("a" * 64),
        "checkout",
        "GitHub.com/example/repo",
        "github.com/example/repo.git",
        "github.com/example/repo.GIT",
        r"github.com\example\repo",
        "github.com/example/repo\n",
        "unknown\n",
    ],
)
def test_repository_identity_rejects_raw_remotes_paths_and_opaque_hashes(
    identity: str,
):
    payload = _full_payload()
    payload["bundle"]["repository"]["identity"] = identity

    _assert_model_error(payload, "bundle.repository.identity")
    assert list(_knowledge_schema_validator().iter_errors(payload))


@pytest.mark.parametrize(
    "revision",
    [
        "main",
        "git:abc123",
        f"git:{'A' * 40}",
        f"git:{'a' * 39}",
        f"git:{'a' * 40}\n",
        "2026-07-25T12:00:00Z",
    ],
)
def test_evaluated_revision_is_unknown_or_a_full_lowercase_git_oid(revision: str):
    payload = _full_payload()
    payload["bundle"]["repository"]["evaluated_revision"] = revision

    _assert_model_error(payload, "bundle.repository.evaluated_revision")
    assert list(_knowledge_schema_validator().iter_errors(payload))


@pytest.mark.parametrize(
    ("identity", "source"),
    [
        ("unknown", "configured-public"),
        ("unknown", "normalized-vcs"),
        ("github.com/example/project", "unknown"),
        ("github.com/example/project", "other"),
    ],
)
def test_repository_identity_source_matches_identity_state(
    identity: str,
    source: str,
):
    payload = _full_payload()
    repository = payload["bundle"]["repository"]
    repository["identity"] = identity
    repository["extensions"][REPOSITORY_IDENTITY_SOURCE_EXTENSION] = source

    _assert_model_error(
        payload,
        (f"bundle.repository.extensions.{REPOSITORY_IDENTITY_SOURCE_EXTENSION}"),
    )
    assert list(_knowledge_schema_validator().iter_errors(payload))


def test_nonunknown_repository_identity_requires_selection_provenance():
    payload = _full_payload()
    payload["bundle"]["repository"].pop("extensions")

    _assert_model_error(
        payload,
        (f"bundle.repository.extensions.{REPOSITORY_IDENTITY_SOURCE_EXTENSION}"),
    )
    assert list(_knowledge_schema_validator().iter_errors(payload))


def test_explicit_unknown_identity_source_canonicalizes_to_omission():
    omitted_payload = _minimum_payload()
    explicit_payload = deepcopy(omitted_payload)
    explicit_payload["bundle"]["repository"]["extensions"] = {
        REPOSITORY_IDENTITY_SOURCE_EXTENSION: "unknown"
    }

    omitted = parse_knowledge_index(omitted_payload)
    explicit = parse_knowledge_index(explicit_payload)

    assert knowledge_index_to_payload(explicit) == knowledge_index_to_payload(omitted)
    assert serialize_knowledge_index(explicit) == serialize_knowledge_index(omitted)
    assert (
        "extensions" not in knowledge_index_to_payload(explicit)["bundle"]["repository"]
    )


@pytest.mark.parametrize(
    ("limitations", "drop_configuration", "field", "schema_rejects"),
    [
        (
            ["syntax-only", "syntax-only"],
            False,
            "bundle.producer.extractors[0].limitations",
            True,
        ),
        (
            ["syntax-only", "alpha"],
            False,
            "bundle.producer.extractors[0].limitations",
            False,
        ),
        (
            ["human readable diagnostic"],
            False,
            "bundle.producer.extractors[0].limitations[0]",
            True,
        ),
        (
            ["syntax-only"],
            True,
            "bundle.producer.extractors[0].configuration_hash",
            True,
        ),
        (
            ["configuration-basis-unknown", "syntax-only"],
            False,
            "bundle.producer.extractors[0].limitations",
            True,
        ),
    ],
)
def test_analyzer_configuration_and_limitation_basis_is_canonical(
    limitations: list[str],
    drop_configuration: bool,
    field: str,
    schema_rejects: bool,
):
    payload = _full_payload()
    extractor = payload["bundle"]["producer"]["extractors"][0]
    extractor["limitations"] = limitations
    if drop_configuration:
        extractor.pop("configuration_hash")

    _assert_model_error(payload, field)
    assert bool(list(_knowledge_schema_validator().iter_errors(payload))) is (
        schema_rejects
    )


def test_unknown_analyzer_configuration_basis_is_explicit_and_valid():
    payload = _full_payload()
    extractor = payload["bundle"]["producer"]["extractors"][0]
    extractor.pop("configuration_hash")
    extractor["limitations"] = [
        "configuration-basis-unknown",
        "syntax-only",
    ]

    model = parse_knowledge_index(payload)

    assert model.bundle.producer.extractors[0].configuration_hash is None
    assert model.bundle.producer.extractors[0].limitations == (
        "configuration-basis-unknown",
        "syntax-only",
    )
    assert list(_knowledge_schema_validator().iter_errors(payload)) == []


def test_qualified_unknown_concept_kind_and_extensions_round_trip_losslessly():
    payload = _full_payload()
    concept = payload["concepts"][0]
    concept["concept_kind"] = "example.com/custom"
    concept["extensions"] = {
        "example.com/custom": {
            "enabled": True,
            "labels": ["one", "two"],
            "nested": {"value": None},
        }
    }

    normalized = knowledge_index_to_payload(parse_knowledge_index(payload))

    assert normalized["concepts"][0]["concept_kind"] == "example.com/custom"
    assert normalized["concepts"][0]["extensions"] == concept["extensions"]


def test_extension_mappings_are_normalized_to_plain_json_objects():
    payload = _minimum_payload()
    payload["extensions"] = {
        "example.com/custom": UserDict(
            {"nested": UserDict({"enabled": True}), "labels": ["one", "two"]}
        )
    }

    model = parse_knowledge_index(payload)
    normalized = knowledge_index_to_payload(model)

    value = normalized["extensions"]["example.com/custom"]
    assert type(value) is dict
    assert type(value["nested"]) is dict
    assert (
        json.loads(serialize_knowledge_index(model))["extensions"]["example.com/custom"]
        == value
    )


def test_cyclic_extension_values_fail_with_a_field_specific_error():
    payload = _minimum_payload()
    cycle: list[object] = []
    cycle.append(cycle)
    payload["extensions"] = {"example.com/cycle": cycle}

    _assert_model_error(payload, "extensions.example.com/cycle[0]")


def test_deep_extension_values_fail_with_a_field_specific_error():
    payload = _minimum_payload()
    nested: list[object] = []
    for _ in range(2000):
        nested = [nested]
    payload["extensions"] = {"example.com/deep": nested}

    _assert_model_error(payload, "extensions.example.com/deep")


def test_unserializable_large_extension_integer_is_wrapped_as_model_error():
    payload = _minimum_payload()
    payload["extensions"] = {"example.com/large": 10**5000}
    model = parse_knowledge_index(payload)

    with pytest.raises(KnowledgeModelError) as exc_info:
        serialize_knowledge_index(model)

    assert exc_info.value.field == "model"


def test_qualified_unknown_relationship_kind_round_trips_losslessly():
    payload = _full_payload()
    relationship = payload["relationships"][0]
    relationship["kind"] = "example.com/custom-edge"
    relationship["origin"] = "authored"
    relationship["extensions"] = {"example.com/custom-edge": {"coverage": "partial"}}

    normalized = knowledge_index_to_payload(parse_knowledge_index(payload))

    assert normalized["relationships"][0]["kind"] == "example.com/custom-edge"
    assert normalized["relationships"][0]["extensions"] == (relationship["extensions"])


def test_page_kind_mapping_is_immutable_process_wide():
    with pytest.raises(TypeError):
        PAGE_KIND_TO_CONCEPT_KIND[PageKind.MODULES] = (  # type: ignore[index]
            ConceptKind.GUIDE
        )


@pytest.mark.parametrize(
    ("mutate", "field"),
    [
        (
            lambda payload: payload["concepts"][0].__setitem__(
                "concept_kind", "future-kind"
            ),
            "concepts[0].concept_kind",
        ),
        (
            lambda payload: payload["concepts"][0].__setitem__("unexpected", "value"),
            "concepts[0].unexpected",
        ),
        (
            lambda payload: payload["concepts"][0].__setitem__(
                "extensions", {"custom": True}
            ),
            "concepts[0].extensions.custom",
        ),
    ],
)
def test_unknown_unnamespaced_kinds_fields_and_extensions_are_rejected(
    mutate: Callable[[dict[str, Any]], None], field: str
):
    payload = _minimum_payload()
    mutate(payload)
    _assert_model_error(payload, field)


@pytest.mark.parametrize(
    ("mutate", "field"),
    [
        (
            lambda payload: payload["concepts"][0]["facets"]["semantics"].__setitem__(
                "authorship",
                {
                    "kind": "robot",
                    "id": "example",
                },
            ),
            "concepts[0].facets.semantics.authorship.kind",
        ),
        (
            lambda payload: payload["concepts"][0]["facets"]["semantics"].__setitem__(
                "authorship",
                {
                    "kind": "human",
                    "id": "",
                },
            ),
            "concepts[0].facets.semantics.authorship.id",
        ),
        (
            lambda payload: payload["bundle"]["snapshot"].__setitem__(
                "source_snapshot_hash", "not-a-hash"
            ),
            "bundle.snapshot.source_snapshot_hash",
        ),
        (
            lambda payload: payload["concepts"][0]["document"].__setitem__(
                "canonical_path", "../outside.md"
            ),
            "concepts[0].document.canonical_path",
        ),
        (
            lambda payload: payload["concepts"][0].__setitem__("lifecycle", "stable"),
            "concepts[0].lifecycle",
        ),
        (
            lambda payload: payload["concepts"][0]["facets"]["structure"].__setitem__(
                "origin", "generated"
            ),
            "concepts[0].facets.structure.origin",
        ),
        (
            lambda payload: payload["concepts"][0]["facets"]["structure"].__setitem__(
                "evidence", "available"
            ),
            "concepts[0].facets.structure.evidence",
        ),
        (
            lambda payload: payload["concepts"][0]["facets"]["semantics"].__setitem__(
                "verification", "verified"
            ),
            "concepts[0].facets.semantics.verification",
        ),
    ],
)
def test_invalid_actor_hash_path_and_status_are_field_specific(
    mutate: Callable[[dict[str, Any]], None], field: str
):
    payload = _minimum_payload()
    mutate(payload)
    _assert_model_error(payload, field)


@pytest.mark.parametrize(
    ("mutate", "field"),
    [
        (
            lambda payload: payload["concepts"][0].__setitem__(
                "locator", "llm-wiki://guides/sync_cmd"
            ),
            "concepts[0].locator",
        ),
        (
            lambda payload: payload["concepts"][0]["document"].__setitem__(
                "canonical_path", "guides/sync_cmd.md"
            ),
            "concepts[0].document.canonical_path",
        ),
        (
            lambda payload: payload["concepts"][0]["document"].__setitem__(
                "role", "mixed"
            ),
            "concepts[0].document.role",
        ),
        (
            lambda payload: (
                payload["concepts"][0]["document"].__setitem__("role", "mixed"),
                payload["concepts"][0]["facets"]["semantics"].__setitem__(
                    "ownership", "mixed"
                ),
            ),
            "concepts[0].document.role",
        ),
        (
            lambda payload: (
                payload["concepts"][0].__setitem__(
                    "locator", "llm-wiki://guides/sync_cmd"
                ),
                payload["concepts"][0]["document"].update(
                    {
                        "page_kind": "guides",
                        "canonical_path": "guides/sync_cmd.md",
                    }
                ),
            ),
            "concepts[0].concept_kind",
        ),
    ],
)
def test_concept_coordinates_are_bound_to_the_surface_registry(
    mutate: Callable[[dict[str, Any]], None], field: str
):
    payload = _minimum_payload()
    mutate(payload)
    _assert_model_error(payload, field)


@pytest.mark.parametrize(
    ("target", "field"),
    [
        ({}, "relationships[0].target"),
        (
            {
                "source_path": "src/llm_wiki_cli/commands/sync_cmd.py",
                "canonical_path": "modules/sync_cmd.md",
            },
            "relationships[0].target",
        ),
        (
            {"source_path": "/absolute/source.py"},
            "relationships[0].target.source_path",
        ),
    ],
)
def test_relationship_target_is_a_validated_one_of(target: dict[str, str], field: str):
    payload = _full_payload()
    payload["relationships"][0]["target"] = target
    _assert_model_error(payload, field)


@pytest.mark.parametrize(
    ("mutate", "field"),
    [
        (
            lambda target: target.pop("normalized_target"),
            "relationships[1].target.normalized_target",
        ),
        (
            lambda target: target["location"].__setitem__("end", 10),
            "relationships[1].target.location.end",
        ),
    ],
)
def test_link_observations_are_complete_and_have_valid_offsets(
    mutate: Callable[[dict[str, Any]], None], field: str
):
    payload = _full_payload()
    mutate(payload["relationships"][1]["target"])

    _assert_model_error(payload, field)


def test_integral_float_offsets_normalize_to_wire_integers():
    payload = _full_payload()
    payload["relationships"][1]["target"]["location"] = {
        "start": 10.0,
        "end": 34.0,
    }

    normalized = knowledge_index_to_payload(parse_knowledge_index(payload))

    assert normalized["relationships"][1]["target"]["location"] == {
        "start": 10,
        "end": 34,
    }
    assert list(_knowledge_schema_validator().iter_errors(payload)) == []


def test_manually_constructed_integral_float_offsets_normalize_to_wire_integers():
    model = parse_knowledge_index(_full_payload())
    link = model.relationships[1]
    assert link.target.location is not None
    location = replace(link.target.location, start=10.0)  # type: ignore[arg-type]
    target = replace(link.target, location=location)
    manual = replace(
        model,
        relationships=(model.relationships[0], replace(link, target=target)),
    )

    normalized = knowledge_index_to_payload(manual)

    assert normalized["relationships"][1]["target"]["location"]["start"] == 10
    assert type(normalized["relationships"][1]["target"]["location"]["start"]) is int


def test_link_offsets_are_bounded_for_portable_serialization():
    payload = _full_payload()
    payload["relationships"][1]["target"]["location"]["start"] = 2**63

    _assert_model_error(payload, "relationships[1].target.location.start")
    assert list(_knowledge_schema_validator().iter_errors(payload))


def test_malformed_empty_link_observation_is_retained_losslessly():
    payload = _full_payload()
    payload["relationships"][1].update(
        {
            "target": {
                "target_class": "malformed",
                "raw_target": "",
                "normalized_target": "",
                "label": "",
                "location": {"start": 10, "end": 12},
            },
            "resolution": "unresolved",
        }
    )

    normalized = knowledge_index_to_payload(parse_knowledge_index(payload))

    assert (
        normalized["relationships"][1]["target"]
        == (payload["relationships"][1]["target"])
    )


def test_relationship_resolution_is_closed_and_field_specific():
    payload = _full_payload()
    payload["relationships"][0]["resolution"] = "missing"

    _assert_model_error(payload, "relationships[0].resolution")


@pytest.mark.parametrize(
    ("target_class", "uri"),
    [
        ("external", "https://example.com/docs"),
        ("mail", "mailto:docs@example.com"),
    ],
)
def test_external_link_target_classes_preserve_observation_and_uri(
    target_class: str, uri: str
):
    payload = _full_payload()
    payload["relationships"][1].update(
        {
            "target": {
                "target_class": target_class,
                "external_uri": uri,
                "raw_target": uri,
                "normalized_target": uri,
                "label": "documentation",
                "location": {"start": 20, "end": 58},
            },
            "resolution": "external",
        }
    )

    model = parse_knowledge_index(payload)

    assert model.relationships[1].target.target_class is TargetClass(target_class)
    assert (
        knowledge_index_to_payload(model)["relationships"][1]["target"]
        == (payload["relationships"][1]["target"])
    )


@pytest.mark.parametrize(
    ("target_class", "uri", "field"),
    [
        ("mail", "https://example.com", "relationships[1].target.external_uri"),
        (
            "external",
            "mailto:docs@example.com",
            "relationships[1].target.target_class",
        ),
    ],
)
def test_mail_and_external_target_classes_match_uri_scheme(
    target_class: str, uri: str, field: str
):
    payload = _full_payload()
    payload["relationships"][1].update(
        {
            "target": {
                "target_class": target_class,
                "external_uri": uri,
                "raw_target": uri,
                "normalized_target": uri,
                "label": "documentation",
                "location": {"start": 20, "end": 58},
            },
            "resolution": "external",
        }
    )

    _assert_model_error(payload, field)


@pytest.mark.parametrize(
    "uri",
    [
        "http://user@example.invalid/docs",
        "https://user:password@example.invalid/docs",
        "ftp://user:password@example.invalid/archive",
        "https://user@[bad",
    ],
)
def test_schema_and_model_reject_external_uri_authority_userinfo(uri: str):
    payload = _full_payload()
    payload["relationships"][1].update(
        {
            "target": {
                "target_class": "external",
                "external_uri": uri,
                "raw_target": uri,
                "normalized_target": uri,
                "label": "documentation",
                "location": {"start": 20, "end": 58},
            },
            "resolution": "external",
        }
    )

    error = _assert_model_error(payload, "relationships[1].target.external_uri")
    assert "credential-bearing URI authority userinfo" in error.reason
    assert list(_knowledge_schema_validator().iter_errors(payload))


@pytest.mark.parametrize(
    ("field", "credentialed_target"),
    [
        ("raw_target", "http://user@example.invalid/docs"),
        (
            "normalized_target",
            "ftp://user:password@example.invalid/archive",
        ),
        (
            "raw_target",
            '<https://user:password@example.invalid/docs> "Documentation"',
        ),
        (
            "raw_target",
            "<https://user:secret@example.invalid/path>",
        ),
        (
            "normalized_target",
            "<//user@example.invalid/docs>",
        ),
        (
            "normalized_target",
            "<https://user:secret@example.invalid/path>",
        ),
        (
            "raw_target",
            'docs/reference.md "https://user:password@example.invalid/private"',
        ),
        (
            "raw_target",
            'docs/reference.md "<https://user:password@example.invalid/private>"',
        ),
        (
            "raw_target",
            'docs/reference.md "see https://user:password@example.invalid/private"',
        ),
        (
            "raw_target",
            "docs/reference.md (https://user:password@example.invalid/private)",
        ),
        (
            "raw_target",
            "docs/reference.md see https://user:password@example.invalid/private",
        ),
        ("raw_target", "//user@example.invalid/docs"),
        ("normalized_target", "//user:password@example.invalid/docs"),
        ("raw_target", "https://user@[bad"),
        ("normalized_target", "//user@[bad"),
    ],
)
def test_schema_and_model_reject_observation_uri_authority_userinfo(
    field: str, credentialed_target: str
):
    payload = _full_payload()
    target = {
        "target_class": "unknown",
        "raw_target": "docs/reference.md",
        "normalized_target": "docs/reference.md",
        "label": "documentation",
        "location": {"start": 20, "end": 58},
    }
    target[field] = credentialed_target
    payload["relationships"][1].update(
        {
            "target": target,
            "resolution": "unresolved",
        }
    )

    error = _assert_model_error(payload, f"relationships[1].target.{field}")
    assert "credential-bearing URI authority userinfo" in error.reason
    assert list(_knowledge_schema_validator().iter_errors(payload))


@pytest.mark.parametrize(
    ("mutate", "field"),
    [
        (
            lambda payload: payload["concepts"][0].__setitem__(
                "title", "broken\ud800title"
            ),
            "concepts[0].title",
        ),
        (
            lambda payload: payload["relationships"][1]["target"].__setitem__(
                "label", "broken\udfff-label"
            ),
            "relationships[1].target.label",
        ),
        (
            lambda payload: payload.__setitem__(
                "extensions",
                {"example.com/custom": {"nested": ["broken\ud800value"]}},
            ),
            "extensions.example.com/custom.nested[0]",
        ),
        (
            lambda payload: payload.__setitem__(
                "extensions",
                {"example.com/custom": {"nested": {"broken\udfffkey": "value"}}},
            ),
            "extensions.example.com/custom.nested",
        ),
    ],
)
def test_schema_and_model_reject_unpaired_surrogate_strings(
    mutate: Callable[[dict[str, Any]], None], field: str
):
    payload = _full_payload()
    mutate(payload)

    error = _assert_model_error(payload, field)
    assert "encodable as UTF-8" in error.reason
    assert list(_knowledge_schema_validator().iter_errors(payload))


def test_schema_and_model_allow_valid_non_bmp_unicode_strings():
    payload = _full_payload()
    payload["concepts"][0]["title"] = "Sync \U0001f600"
    payload["extensions"] = {"example.com/custom": {"nested": ["valid \U0001f680"]}}

    assert list(_knowledge_schema_validator().iter_errors(payload)) == []
    model = parse_knowledge_index(payload)
    assert serialize_knowledge_index(model).encode("utf-8")


@pytest.mark.parametrize(
    ("target", "resolution"),
    [
        (
            {
                "target_class": "mail",
                "external_uri": "mailto:user@example.invalid",
                "raw_target": "mailto:user@example.invalid",
                "normalized_target": "mailto:user@example.invalid",
                "label": "email",
                "location": {"start": 20, "end": 58},
            },
            "external",
        ),
        (
            {
                "target_class": "unknown",
                "raw_target": "docs/user@example.invalid.md",
                "normalized_target": "docs/user@example.invalid.md",
                "label": "documentation",
                "location": {"start": 20, "end": 58},
            },
            "unresolved",
        ),
        (
            {
                "target_class": "unknown",
                "raw_target": 'docs/reference.md "mailto:user@example.invalid"',
                "normalized_target": "docs/reference.md",
                "label": "documentation",
                "location": {"start": 20, "end": 58},
            },
            "unresolved",
        ),
        (
            {
                "target_class": "unknown",
                "raw_target": "docs//user@example.invalid.md",
                "normalized_target": "docs//user@example.invalid.md",
                "label": "documentation",
                "location": {"start": 20, "end": 58},
            },
            "unresolved",
        ),
        (
            {
                "target_class": "external",
                "external_uri": (
                    "https://example.invalid/?next=https://user@example.invalid/path"
                ),
                "raw_target": (
                    "https://example.invalid/?next=https://user@example.invalid/path"
                ),
                "normalized_target": (
                    "https://example.invalid/?next=https://user@example.invalid/path"
                ),
                "label": "documentation",
                "location": {"start": 20, "end": 58},
            },
            "external",
        ),
        (
            {
                "target_class": "unknown",
                "raw_target": (
                    'docs/reference.md "https://example.invalid/'
                    '?next=https://user@example.invalid/path"'
                ),
                "normalized_target": "docs/reference.md",
                "label": "documentation",
                "location": {"start": 20, "end": 58},
            },
            "unresolved",
        ),
        (
            {
                "target_class": "unknown",
                "raw_target": (
                    'docs/reference.md "see https://example.invalid/'
                    '?next=https://user@example.invalid/path"'
                ),
                "normalized_target": "docs/reference.md",
                "label": "documentation",
                "location": {"start": 20, "end": 58},
            },
            "unresolved",
        ),
    ],
)
def test_schema_and_model_allow_at_outside_uri_authority(
    target: dict[str, object], resolution: str
):
    payload = _full_payload()
    payload["relationships"][1].update(
        {
            "target": target,
            "resolution": resolution,
        }
    )

    assert list(_knowledge_schema_validator().iter_errors(payload)) == []
    parse_knowledge_index(payload)


@pytest.mark.parametrize(
    ("resolution", "target_class"),
    [
        ("ambiguous", "concept"),
        ("unresolved", "concept"),
        ("resolved", "anchor"),
        ("resolved", "asset"),
        ("unresolved", "malformed"),
    ],
)
def test_noncanonical_link_outcomes_preserve_target_class_and_raw_target(
    resolution: str, target_class: str
):
    payload = _full_payload()
    payload["relationships"][1].update(
        {
            "target": {
                "target_class": target_class,
                "raw_target": "raw link target",
                "normalized_target": "raw link target",
                "label": "raw link",
                "location": {"start": 5, "end": 27},
            },
            "resolution": resolution,
        }
    )

    normalized = knowledge_index_to_payload(parse_knowledge_index(payload))

    assert normalized["relationships"][1]["resolution"] == resolution
    assert normalized["relationships"][1]["target"] == {
        "target_class": target_class,
        "raw_target": "raw link target",
        "normalized_target": "raw link target",
        "label": "raw link",
        "location": {"start": 5, "end": 27},
    }


@pytest.mark.parametrize(
    ("target", "field"),
    [
        (
            {"locator": "llm-wiki://modules/not-present"},
            "relationships[1].target.locator",
        ),
        (
            {"canonical_path": "modules/not-present.md"},
            "relationships[1].target.canonical_path",
        ),
    ],
)
def test_resolved_internal_relationship_targets_must_exist(
    target: dict[str, str], field: str
):
    payload = _full_payload()
    link_target = payload["relationships"][1]["target"]
    link_target.pop("canonical_path")
    link_target.update(target)
    _assert_model_error(payload, field)


@pytest.mark.parametrize(
    ("relationship_index", "evidence", "field"),
    [
        (
            0,
            {"state": "present", "page_hash": _hash("5")},
            "relationships[0].evidence.concept_observation_hash",
        ),
        (
            1,
            {"state": "present", "concept_observation_hash": _hash("8")},
            "relationships[1].evidence.page_hash",
        ),
    ],
)
def test_present_core_relationship_evidence_is_kind_specific(
    relationship_index: int, evidence: dict[str, str], field: str
):
    payload = _full_payload()
    payload["relationships"][relationship_index]["evidence"] = evidence
    _assert_model_error(payload, field)


def test_present_structural_evidence_cannot_have_unknown_scope():
    payload = _full_payload()
    payload["concepts"][0]["facets"]["structure"]["basis"] = {"scope": "unknown"}

    _assert_model_error(payload, "concepts[0].facets.structure.basis.scope")


@pytest.mark.parametrize(
    ("target", "field"),
    [
        (
            {"external_uri": "https://exa mple.invalid/docs"},
            "relationships[1].target.external_uri",
        ),
        (
            {"external_uri": "https:///missing-authority"},
            "relationships[1].target.external_uri",
        ),
        (
            {"external_uri": "https:missing-authority"},
            "relationships[1].target.external_uri",
        ),
        (
            {"external_uri": "ftp:/missing-authority"},
            "relationships[1].target.external_uri",
        ),
        (
            {"external_uri": "https://:443/missing-host"},
            "relationships[1].target.external_uri",
        ),
        (
            {"external_uri": "https://user@:443/missing-host"},
            "relationships[1].target.external_uri",
        ),
        (
            {"external_uri": "https://example.invalid/{bad}"},
            "relationships[1].target.external_uri",
        ),
        (
            {"external_uri": "https://example.invalid/pipe|bad"},
            "relationships[1].target.external_uri",
        ),
        (
            {"external_uri": "https://example.invalid/café"},
            "relationships[1].target.external_uri",
        ),
        (
            {"locator": "llm-wiki://modules//sync_cmd"},
            "relationships[1].target.locator",
        ),
    ],
)
def test_relationship_uris_are_normalized(target: dict[str, str], field: str):
    payload = _full_payload()
    payload["relationships"][1].update(
        {
            "target": target,
            "resolution": ("external" if "external_uri" in target else "resolved"),
        }
    )
    _assert_model_error(payload, field)


def test_duplicate_concept_locators_are_rejected():
    payload = _minimum_payload()
    duplicate = deepcopy(payload["concepts"][0])
    duplicate["title"] = "Duplicate"
    payload["concepts"].append(duplicate)

    _assert_model_error(payload, "concepts[1].locator")


@pytest.mark.parametrize(
    ("page_kind", "concept_kind", "role", "expected_kind"),
    [
        (
            "index",
            "navigation-document",
            "mixed",
            ConceptKind.NAVIGATION_DOCUMENT,
        ),
        (
            "log",
            "change-log-document",
            "generated",
            ConceptKind.CHANGE_LOG_DOCUMENT,
        ),
    ],
)
def test_document_only_pages_do_not_fabricate_structural_evidence(
    page_kind: str,
    concept_kind: str,
    role: str,
    expected_kind: ConceptKind,
):
    payload = _minimum_payload()
    concept = payload["concepts"][0]
    concept.update(
        {
            "locator": f"llm-wiki://{page_kind}",
            "concept_kind": concept_kind,
            "title": page_kind.title(),
            "document": {
                "page_kind": page_kind,
                "page_id": page_kind,
                "canonical_path": f"{page_kind}.md",
                "role": role,
            },
        }
    )
    concept["facets"]["semantics"]["ownership"] = role

    model = parse_knowledge_index(payload)
    structure = model.concepts[0].facets.structure

    assert model.concepts[0].concept_kind is expected_kind
    assert structure.origin is Origin.UNKNOWN
    assert structure.evidence is EvidenceState.UNKNOWN
    assert structure.basis is None


def test_document_only_pages_reject_claimed_structural_origin():
    payload = _minimum_payload()
    concept = payload["concepts"][0]
    concept.update(
        {
            "locator": "llm-wiki://index",
            "concept_kind": "navigation-document",
            "title": "Index",
            "document": {
                "page_kind": "index",
                "page_id": "index",
                "canonical_path": "index.md",
                "role": "mixed",
            },
        }
    )
    concept["facets"]["structure"]["origin"] = "extracted"
    concept["facets"]["semantics"]["ownership"] = "mixed"

    _assert_model_error(payload, "concepts[0].facets.structure")


def test_serialization_is_sorted_deterministic_and_has_one_trailing_newline():
    payload = _full_payload()
    payload["extensions"] = {
        "example.com/z-last": 2,
        "example.com/a-first": 1,
    }
    model = parse_knowledge_index(payload)

    first = serialize_knowledge_index(model)
    second = serialize_knowledge_index(parse_knowledge_index(deepcopy(payload)))

    assert first == second
    assert (
        first
        == json.dumps(
            knowledge_index_to_payload(model),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    assert first.endswith("\n")
    assert not first.endswith("\n\n")


def test_canonical_payload_ignores_core_collection_input_order():
    payload = _full_payload()
    second_concept = deepcopy(payload["concepts"][0])
    second_concept.update(
        {
            "locator": "llm-wiki://modules/alpha",
            "title": "alpha",
        }
    )
    second_concept["document"].update(
        {
            "page_id": "alpha",
            "canonical_path": "modules/alpha.md",
        }
    )
    second_concept["facets"]["structure"]["basis"].update(
        {
            "source_path": "src/llm_wiki_cli/alpha.py",
            "concept_observation_hash": _hash("9"),
        }
    )
    second_concept["facets"]["semantics"]["page_hash"] = _hash("a")
    payload["concepts"].append(second_concept)
    payload["bundle"]["producer"]["extractors"].append(
        {
            "id": "alpha-extractor",
            "version": "builtin",
            "configuration_hash": _hash("b"),
        }
    )
    payload["bundle"]["producer"]["plugins"] = [
        {
            "id": "zeta-plugin",
            "version": "1",
            "configuration_hash": _hash("c"),
        },
        {
            "id": "alpha-plugin",
            "version": "1",
            "configuration_hash": _hash("d"),
        },
    ]
    extension_order = ["z-last", {"nested": [3, 1, 2]}, "a-first"]
    payload["extensions"] = {"example.com/ordered": extension_order}
    payload["relationships"][0]["extensions"] = {"example.com/ordered": extension_order}
    payload["relationships"].reverse()

    baseline_model = parse_knowledge_index(payload)
    baseline_payload = knowledge_index_to_payload(baseline_model)
    baseline_bytes = serialize_knowledge_index(baseline_model)
    collection_paths = {
        "concepts": ("concepts",),
        "relationships": ("relationships",),
        "extractors": ("bundle", "producer", "extractors"),
        "plugins": ("bundle", "producer", "plugins"),
    }

    for path in collection_paths.values():
        permuted = deepcopy(payload)
        collection = permuted
        for segment in path:
            collection = collection[segment]
        collection.reverse()

        permuted_model = parse_knowledge_index(permuted)
        assert knowledge_index_to_payload(permuted_model) == baseline_payload
        assert serialize_knowledge_index(permuted_model) == baseline_bytes

    assert [concept.locator for concept in baseline_model.concepts] == [
        concept["locator"] for concept in payload["concepts"]
    ]
    assert [
        relationship.kind.value for relationship in baseline_model.relationships
    ] == [relationship["kind"] for relationship in payload["relationships"]]
    assert [
        component.component_id
        for component in baseline_model.bundle.producer.extractors
    ] == [component["id"] for component in payload["bundle"]["producer"]["extractors"]]
    assert [
        component.component_id for component in baseline_model.bundle.producer.plugins
    ] == [component["id"] for component in payload["bundle"]["producer"]["plugins"]]
    assert [
        component["id"]
        for component in baseline_payload["bundle"]["producer"]["extractors"]
    ] == ["alpha-extractor", "python-ast"]
    assert [
        component["id"]
        for component in baseline_payload["bundle"]["producer"]["plugins"]
    ] == ["alpha-plugin", "zeta-plugin"]
    assert [concept["locator"] for concept in baseline_payload["concepts"]] == [
        "llm-wiki://modules/alpha",
        "llm-wiki://modules/sync_cmd",
    ]
    assert baseline_payload["relationships"] == sorted(
        baseline_payload["relationships"],
        key=lambda relationship: json.dumps(
            relationship,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
    )
    assert baseline_payload["extensions"]["example.com/ordered"] == extension_order
    assert (
        baseline_payload["relationships"][0]["extensions"]["example.com/ordered"]
        == extension_order
    )


def test_manual_dataclass_enum_wire_values_are_revalidated_and_normalized():
    model = parse_knowledge_index(_minimum_payload())
    repository = replace(
        model.bundle.repository,
        working_tree="dirty",  # type: ignore[arg-type]
    )
    manual = replace(model, bundle=replace(model.bundle, repository=repository))

    payload = knowledge_index_to_payload(manual)

    assert payload["bundle"]["repository"]["working_tree"] == "dirty"


def test_invalid_manual_dataclass_shape_uses_the_model_error_contract():
    model = parse_knowledge_index(_minimum_payload())
    manual = replace(model, bundle="invalid")  # type: ignore[arg-type]

    with pytest.raises(KnowledgeModelError) as exc_info:
        knowledge_index_to_payload(manual)

    assert exc_info.value.field == "model"


def test_computed_freshness_is_not_part_of_the_persisted_contract():
    model = parse_knowledge_index(_full_payload())
    payload = knowledge_index_to_payload(model)
    schema = load_knowledge_schema()

    def keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value) | {
                nested for child in value.values() for nested in keys(child)
            }
        if isinstance(value, list):
            return {nested for child in value for nested in keys(child)}
        return set()

    assert "freshness" not in keys(payload)
    assert "freshness" not in _schema_property_names(schema)
    assert not hasattr(model, "freshness")


def test_packaged_schema_loads_and_agrees_with_python_vocabulary():
    schema = load_knowledge_schema()
    enum_sets = _schema_enum_sets(schema)

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["type"] == "object"
    assert schema["properties"]["schema_version"]["const"] == (KNOWLEDGE_SCHEMA_VERSION)
    assert set(schema["required"]) == {
        "schema_version",
        "bundle",
        "concepts",
        "relationships",
    }
    assert schema["additionalProperties"] is False
    assert {
        "kind",
        "id",
        "version",
        "model",
        "organization",
        "extensions",
    } <= set(schema["$defs"]["actor"]["properties"])
    assert "limitations" in schema["$defs"]["component"]["properties"]

    for enum_type in (
        ConceptKind,
        Origin,
        EvidenceState,
        Resolution,
        TargetClass,
        Verification,
        Lifecycle,
        ComputedFreshness,
        ActorKind,
        RepositoryIdentitySource,
        KnowledgeProjectionProfile,
    ):
        assert frozenset(member.value for member in enum_type) in enum_sets


def test_packaged_schema_encodes_parser_safe_string_and_path_shapes():
    definitions = load_knowledge_schema()["$defs"]

    component_id = re.compile(definitions["component"]["properties"]["id"]["pattern"])
    assert component_id.fullmatch("python/ast")
    assert component_id.fullmatch("agent-wiki-cli")
    assert not component_id.fullmatch("/absolute")
    assert not component_id.fullmatch("white space")

    limitation_code = re.compile(definitions["limitationCode"]["pattern"])
    assert limitation_code.pattern == LIMITATION_CODE_PATTERN
    assert limitation_code.fullmatch("configuration-basis-unknown")
    assert limitation_code.fullmatch("example.com/partial-analysis")
    assert not limitation_code.fullmatch("human readable diagnostic")

    page_id = re.compile(definitions["document"]["properties"]["page_id"]["pattern"])
    assert page_id.fullmatch("SyncManifest(1)")
    assert not page_id.fullmatch(".hidden")
    assert not page_id.fullmatch("unsafe..page")
    assert not page_id.fullmatch("nested/page")

    canonical_path = definitions["document"]["properties"]["canonical_path"]
    assert {"pattern": r"\.md$"} in canonical_path["allOf"]

    identity_pattern = re.compile(definitions["repositoryIdentity"]["pattern"])
    assert identity_pattern.pattern == REPOSITORY_IDENTITY_PATTERN
    assert identity_pattern.fullmatch("github.com/example/project")
    assert identity_pattern.fullmatch("unknown")
    assert not identity_pattern.fullmatch("/absolute/checkout")
    assert not identity_pattern.fullmatch(r"C:\checkout")
    assert not identity_pattern.fullmatch("https://example.com/project")
    assert not identity_pattern.fullmatch("GitHub.com/example/project")
    assert not identity_pattern.fullmatch("sha256:" + ("a" * 64))

    revision_pattern = re.compile(definitions["evaluatedRevision"]["pattern"])
    assert revision_pattern.pattern == EVALUATED_REVISION_PATTERN
    assert revision_pattern.fullmatch(f"git:{'a' * 40}")
    assert revision_pattern.fullmatch(f"git:{'b' * 64}")
    assert revision_pattern.fullmatch("unknown")
    assert not revision_pattern.fullmatch("git:abc123")

    external_uri = definitions["relationshipTarget"]["properties"]["external_uri"]
    external_pattern = re.compile(external_uri["pattern"])
    assert external_pattern.match("https://example.com/docs")
    assert not external_pattern.match("llm-wiki://modules/example")
    assert not external_pattern.match("LLM-WIKI://modules/example")
    assert not external_pattern.match("https://exa mple.invalid/docs")
    assert not external_pattern.match(r"https://example.invalid\\docs")
    assert not external_pattern.match("https:///missing-authority")
    assert not external_pattern.match("https:missing-authority")
    assert not external_pattern.match("ftp:/missing-authority")
    assert not external_pattern.match("https://:443/missing-host")
    assert not external_pattern.match("https://user@:443/missing-host")
    assert not external_pattern.match("https://example.invalid/{bad}")
    assert not external_pattern.match("https://example.invalid/pipe|bad")
    assert not external_pattern.match("https://example.invalid/café")

    locator = re.compile(definitions["locator"]["pattern"])
    assert locator.fullmatch("llm-wiki://modules/sync_cmd")
    for unsafe in (
        "llm-wiki://user@host/page",
        "llm-wiki://host:123/page",
        "llm-wiki://host/page?query=1",
        "llm-wiki://host/page#fragment",
        r"llm-wiki://host/page\child",
        "llm-wiki://host/bad%2",
        "llm-wiki://host/../page",
        "llm-wiki://host//page",
        "llm-wiki://host/page/",
        "llm-wiki://host/encoded%2Fslash",
    ):
        assert not locator.fullmatch(unsafe)
    assert (
        "additionally performs URI authority parsing"
        in (definitions["locator"]["description"])
    )


def test_packaged_schema_encodes_actor_and_evidence_defaults_and_guards():
    definitions = load_knowledge_schema()["$defs"]

    actor_rules = definitions["actor"]["allOf"]
    unknown_actor_rule = next(
        rule
        for rule in actor_rules
        if rule["if"]["properties"]["kind"].get("const") == "unknown"
    )
    forbidden_actor_fields = {
        branch["required"][0] for branch in unknown_actor_rule["then"]["not"]["anyOf"]
    }
    assert forbidden_actor_fields == {"id", "version", "model", "organization"}
    assert definitions["semanticFacet"]["properties"]["authorship"]["default"] == {
        "kind": "unknown"
    }

    structure_rule = definitions["structureFacet"]["allOf"][0]
    assert structure_rule["if"]["properties"]["evidence"]["const"] == "present"
    assert "basis" in structure_rule["then"]["required"]
    present_basis = structure_rule["then"]["properties"]["basis"]
    assert set(present_basis["properties"]["scope"]["enum"]) == {
        "module",
        "entity",
        "aggregate",
    }
    basis_rules = present_basis["allOf"]
    module_entity_rule = next(
        rule
        for rule in basis_rules
        if set(rule["if"]["properties"]["scope"].get("enum", []))
        == {"module", "entity"}
    )
    assert set(module_entity_rule["then"]["required"]) == {
        "source_path",
        "extractor_ref",
        "source_content_hash",
        "concept_observation_hash",
    }
    aggregate_rule = next(
        rule
        for rule in basis_rules
        if rule["if"]["properties"]["scope"].get("const") == "aggregate"
    )
    assert aggregate_rule["then"]["required"] == ["aggregate_input_hash"]

    relationship_evidence_rule = definitions["relationshipEvidence"]["allOf"][0]
    assert relationship_evidence_rule["if"]["properties"]["state"]["const"] == "present"
    assert {
        branch["required"][0] for branch in relationship_evidence_rule["then"]["anyOf"]
    } == {
        "source_content_hash",
        "concept_observation_hash",
        "page_hash",
        "aggregate_input_hash",
    }


def test_packaged_schema_binds_relationship_kinds_resolutions_and_targets():
    definitions = load_knowledge_schema()["$defs"]
    relationship_rules = definitions["relationship"]["allOf"]
    target = definitions["relationshipTarget"]

    def _rule(field: str, value: str) -> dict[str, Any]:
        return next(
            rule
            for rule in relationship_rules
            if rule["if"]["properties"].get(field, {}).get("const") == value
        )

    resolved = _rule("resolution", "resolved")
    assert {
        branch["required"][0]
        for branch in resolved["then"]["properties"]["target"]["anyOf"]
    } == {"locator", "canonical_path", "source_path", "raw_target"}
    raw_resolved = resolved["then"]["properties"]["target"]["anyOf"][3]
    assert raw_resolved["properties"]["target_class"]["enum"] == ["anchor", "asset"]
    assert raw_resolved["required"] == ["raw_target", "target_class"]
    assert _rule("resolution", "external")["then"]["properties"]["target"][
        "required"
    ] == ["external_uri"]

    unresolved = next(
        rule
        for rule in relationship_rules
        if set(rule["if"]["properties"].get("resolution", {}).get("enum", []))
        == {"ambiguous", "unresolved"}
    )
    assert unresolved["then"]["properties"]["target"]["required"] == ["raw_target"]
    assert {
        branch["required"][0]
        for branch in unresolved["then"]["properties"]["target"]["not"]["anyOf"]
    } == {"locator", "canonical_path", "source_path", "external_uri"}

    assert set(definitions["resolution"]["enum"]) == {
        "resolved",
        "ambiguous",
        "external",
        "unresolved",
    }
    assert set(definitions["targetClass"]["enum"]) == {
        "unknown",
        "concept",
        "source",
        "external",
        "mail",
        "anchor",
        "asset",
        "malformed",
    }
    assert set(target["dependentRequired"]) == {
        "raw_target",
        "normalized_target",
        "label",
        "location",
    }

    derived_rule = _rule("kind", "derived_from")
    derived_from = derived_rule["then"]["properties"]
    assert derived_from["resolution"]["const"] == "resolved"
    assert set(derived_from["origin"]["enum"]) == {"extracted", "inferred"}
    assert derived_from["target"]["required"] == ["source_path"]
    derived_present = derived_rule["then"]["allOf"][0]
    assert (
        derived_present["if"]["properties"]["evidence"]["properties"]["state"]["const"]
        == "present"
    )
    assert derived_present["then"]["properties"]["evidence"]["required"] == [
        "concept_observation_hash"
    ]

    links_to = _rule("kind", "links_to")["then"]
    assert links_to["properties"]["origin"]["const"] == "markdown"
    assert set(links_to["properties"]["target"]["required"]) == {
        "raw_target",
        "normalized_target",
        "label",
        "location",
    }
    resolved_links = links_to["allOf"][0]["then"]["properties"]["target"]["anyOf"]
    assert {branch["required"][0] for branch in resolved_links} == {
        "locator",
        "canonical_path",
        "raw_target",
    }
    link_present = links_to["allOf"][1]
    assert (
        link_present["if"]["properties"]["evidence"]["properties"]["state"]["const"]
        == "present"
    )
    assert link_present["then"]["properties"]["evidence"]["required"] == ["page_hash"]


def _knowledge_schema_validator() -> Draft202012Validator:
    schema = load_knowledge_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.mark.parametrize(
    ("mutate", "field"),
    [
        (
            lambda payload: payload["bundle"]["producer"]["tool"].__setitem__(
                "configuration_hash", None
            ),
            "bundle.producer.tool.configuration_hash",
        ),
        (
            lambda payload: payload["concepts"][0]["facets"]["structure"][
                "basis"
            ].__setitem__("source_path", None),
            "concepts[0].facets.structure.basis.source_path",
        ),
        (
            lambda payload: payload["concepts"][0]["facets"]["semantics"][
                "authorship"
            ].__setitem__("model", None),
            "concepts[0].facets.semantics.authorship.model",
        ),
        (
            lambda payload: payload["relationships"][1]["evidence"].__setitem__(
                "page_hash", None
            ),
            "relationships[1].evidence.page_hash",
        ),
    ],
)
def test_explicit_null_is_not_treated_as_an_absent_optional_fact(
    mutate: Callable[[dict[str, Any]], None], field: str
):
    payload = _full_payload()
    mutate(payload)

    _assert_model_error(payload, field)
    assert list(_knowledge_schema_validator().iter_errors(payload))


def test_draft_2020_12_schema_accepts_minimum_and_full_model_payloads():
    validator = _knowledge_schema_validator()

    for payload in (_minimum_payload(), _full_payload()):
        assert list(validator.iter_errors(payload)) == []
        parse_knowledge_index(payload)


@pytest.mark.parametrize(
    ("case", "mutate"),
    [
        (
            "unknown actor metadata",
            lambda payload: payload["concepts"][0]["facets"]["semantics"].__setitem__(
                "authorship", {"kind": "unknown", "id": "claimed-identity"}
            ),
        ),
        (
            "identified actor without id",
            lambda payload: payload["concepts"][0]["facets"]["semantics"].__setitem__(
                "authorship", {"kind": "human"}
            ),
        ),
        (
            "malformed hash",
            lambda payload: payload["bundle"]["snapshot"].__setitem__(
                "source_snapshot_hash", "sha256:ABC"
            ),
        ),
        (
            "unsafe canonical path",
            lambda payload: payload["concepts"][0]["document"].__setitem__(
                "canonical_path", "../outside.md"
            ),
        ),
        (
            "non-Markdown canonical path",
            lambda payload: payload["concepts"][0]["document"].__setitem__(
                "canonical_path", "modules/sync_cmd.txt"
            ),
        ),
        (
            "invalid status",
            lambda payload: payload["concepts"][0].__setitem__("lifecycle", "stable"),
        ),
        (
            "derived relationship with document target",
            lambda payload: payload["relationships"][0].__setitem__(
                "target", {"canonical_path": "modules/sync_cmd.md"}
            ),
        ),
        (
            "links relationship with non-Markdown origin",
            lambda payload: payload["relationships"][1].__setitem__(
                "origin", "authored"
            ),
        ),
        (
            "present relationship evidence without hash",
            lambda payload: payload["relationships"][0].__setitem__(
                "evidence", {"state": "present"}
            ),
        ),
        (
            "present structural evidence without basis",
            lambda payload: payload["concepts"][0]["facets"]["structure"].pop("basis"),
        ),
        (
            "present module evidence without observation hash",
            lambda payload: payload["concepts"][0]["facets"]["structure"]["basis"].pop(
                "concept_observation_hash"
            ),
        ),
        (
            "present structural evidence with unknown scope",
            lambda payload: payload["concepts"][0]["facets"]["structure"].__setitem__(
                "basis", {"scope": "unknown"}
            ),
        ),
        (
            "present aggregate evidence without aggregate hash",
            lambda payload: payload["concepts"][0]["facets"]["structure"][
                "basis"
            ].__setitem__("scope", "aggregate"),
        ),
        (
            "present derived evidence without concept observation hash",
            lambda payload: payload["relationships"][0].__setitem__(
                "evidence", {"state": "present", "page_hash": _hash("5")}
            ),
        ),
        (
            "present link evidence without page hash",
            lambda payload: payload["relationships"][1].__setitem__(
                "evidence",
                {
                    "state": "present",
                    "concept_observation_hash": _hash("8"),
                },
            ),
        ),
        (
            "external relationship using internal scheme",
            lambda payload: payload["relationships"][1].update(
                {
                    "target": {"external_uri": "llm-wiki://modules/other"},
                    "resolution": "external",
                }
            ),
        ),
        (
            "external relationship URI containing whitespace",
            lambda payload: payload["relationships"][1].update(
                {
                    "target": {"external_uri": "https://exa mple.invalid/docs"},
                    "resolution": "external",
                }
            ),
        ),
        (
            "locator containing an empty path segment",
            lambda payload: payload["relationships"][1].__setitem__(
                "target", {"locator": "llm-wiki://modules//sync_cmd"}
            ),
        ),
    ],
)
def test_schema_and_model_reject_representative_invalid_payloads(
    case: str, mutate: Callable[[dict[str, Any]], None]
):
    payload = _full_payload()
    mutate(payload)

    with pytest.raises(KnowledgeModelError):
        parse_knowledge_index(payload)

    errors = list(_knowledge_schema_validator().iter_errors(payload))
    assert errors, f"JSON Schema unexpectedly accepted {case}"
