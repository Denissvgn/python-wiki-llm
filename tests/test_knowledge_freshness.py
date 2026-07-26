"""Contract tests for pure, consumer-computed concept freshness (KNOW-201)."""

from __future__ import annotations

import builtins
import socket
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli.services import knowledge_evidence, knowledge_freshness
from llm_wiki_cli.services.knowledge_evidence import ConceptObservationBasis
from llm_wiki_cli.services.knowledge_freshness import (
    ConceptFreshnessBasis,
    KnowledgeFreshnessError,
    LiveKnowledgeEvaluation,
    evaluate_knowledge_freshness,
)
from llm_wiki_cli.services.knowledge_model import (
    ComputedFreshness,
    EvidenceBasis,
    EvidenceState,
    KnowledgeIndex,
    ObservationScope,
    Origin,
    ProducerComponent,
    ProducerRecord,
    StructuralFacet,
    parse_knowledge_index,
    serialize_knowledge_index,
)
from tests.knowledge_fixtures import (
    FIXTURE_SOURCE_PATH,
    fixture_hash,
    freshness_fixtures,
    one_module_two_entities_fixture,
    removed_source_fixtures,
)

USER_LOCATOR = "llm-wiki://entities/User"
SIBLING_LOCATOR = "llm-wiki://entities/AccountService"
MODULE_LOCATOR = "llm-wiki://modules/accounts"
INDEX_LOCATOR = "llm-wiki://index"
WORKFLOW_LOCATOR = "llm-wiki://workflows/onboarding"


@pytest.fixture
def knowledge() -> KnowledgeIndex:
    return parse_knowledge_index(one_module_two_entities_fixture().knowledge_payload)


def _concept(knowledge: KnowledgeIndex, locator: str):
    return next(concept for concept in knowledge.concepts if concept.locator == locator)


def _known_basis(knowledge: KnowledgeIndex, locator: str) -> EvidenceBasis:
    concept = _concept(knowledge, locator)
    basis = concept.facets.structure.basis
    assert concept.facets.structure.evidence is EvidenceState.PRESENT
    assert basis is not None
    assert basis.scope in {ObservationScope.MODULE, ObservationScope.ENTITY}
    assert basis.source_path is not None
    assert basis.extractor_ref is not None
    assert basis.source_content_hash is not None
    assert basis.concept_observation_hash is not None
    return basis


def _replace_concept(
    knowledge: KnowledgeIndex,
    locator: str,
    replacement,
) -> KnowledgeIndex:
    return replace(
        knowledge,
        concepts=tuple(
            replacement if concept.locator == locator else concept
            for concept in knowledge.concepts
        ),
    )


def _replace_producer(
    knowledge: KnowledgeIndex,
    producer: ProducerRecord,
) -> KnowledgeIndex:
    return replace(
        knowledge,
        bundle=replace(knowledge.bundle, producer=producer),
    )


def _replace_recorded_source_basis(
    knowledge: KnowledgeIndex,
    *,
    source_hash: str,
    observation_by_locator: dict[str, str] | None = None,
) -> KnowledgeIndex:
    observation_by_locator = observation_by_locator or {}
    concepts = []
    for concept in knowledge.concepts:
        basis = concept.facets.structure.basis
        if (
            basis is None
            or basis.scope not in {ObservationScope.MODULE, ObservationScope.ENTITY}
            or basis.source_path != FIXTURE_SOURCE_PATH
        ):
            concepts.append(concept)
            continue
        next_basis = replace(
            basis,
            source_content_hash=source_hash,
            concept_observation_hash=observation_by_locator.get(
                concept.locator,
                basis.concept_observation_hash,
            ),
        )
        concepts.append(
            replace(
                concept,
                facets=replace(
                    concept.facets,
                    structure=replace(concept.facets.structure, basis=next_basis),
                ),
            )
        )
    return replace(knowledge, concepts=tuple(concepts))


def _live_evaluation(
    knowledge: KnowledgeIndex,
    *,
    schema_version: str | None = None,
    producer: ProducerRecord | None = None,
    generation_options_hash: str | None = None,
    source_hash_by_path: dict[str, str] | None = None,
    missing_source_paths: frozenset[str] = frozenset(),
    observation_by_locator: dict[str, str | None] | None = None,
    extractor_ref_by_locator: dict[str, str] | None = None,
    scope_by_locator: dict[str, str] | None = None,
    omit_locators: frozenset[str] = frozenset(),
) -> LiveKnowledgeEvaluation:
    observation_by_locator = observation_by_locator or {}
    extractor_ref_by_locator = extractor_ref_by_locator or {}
    scope_by_locator = scope_by_locator or {}

    recorded_by_path: dict[str, str] = {}
    for concept in knowledge.concepts:
        basis = concept.facets.structure.basis
        if (
            basis is not None
            and basis.scope in {ObservationScope.MODULE, ObservationScope.ENTITY}
            and basis.source_path is not None
            and basis.source_content_hash is not None
        ):
            recorded_by_path.setdefault(basis.source_path, basis.source_content_hash)
    live_source_hashes = (
        dict(recorded_by_path)
        if source_hash_by_path is None
        else dict(source_hash_by_path)
    )
    for path in missing_source_paths:
        live_source_hashes.pop(path, None)

    concept_bases: dict[str, ConceptObservationBasis] = {}
    for concept in knowledge.concepts:
        if concept.locator in omit_locators:
            continue
        basis = concept.facets.structure.basis
        if (
            basis is None
            or basis.scope not in {ObservationScope.MODULE, ObservationScope.ENTITY}
            or basis.source_path is None
            or basis.extractor_ref is None
            or basis.concept_observation_hash is None
            or basis.source_path in missing_source_paths
            or basis.source_path not in live_source_hashes
        ):
            continue
        observation_hash = observation_by_locator.get(
            concept.locator,
            basis.concept_observation_hash,
        )
        concept_bases[concept.locator] = ConceptObservationBasis(
            scope=scope_by_locator.get(concept.locator, basis.scope.value),
            source_path=basis.source_path,
            extractor_ref=extractor_ref_by_locator.get(
                concept.locator,
                basis.extractor_ref,
            ),
            source_content_hash=live_source_hashes[basis.source_path],
            concept_observation_hash=observation_hash,
            unknown_reason=(
                "live-observation-unavailable" if observation_hash is None else None
            ),
        )

    return LiveKnowledgeEvaluation(
        schema_version=(
            knowledge.schema_version if schema_version is None else schema_version
        ),
        producer=knowledge.bundle.producer if producer is None else producer,
        generation_options_hash=(
            knowledge.bundle.snapshot.generation_options_hash
            if generation_options_hash is None
            else generation_options_hash
        ),
        source_content_hashes=live_source_hashes,
        missing_source_paths=missing_source_paths,
        concept_bases=concept_bases,
    )


def _result(
    knowledge: KnowledgeIndex,
    live: LiveKnowledgeEvaluation | None,
    locator: str = USER_LOCATOR,
):
    return evaluate_knowledge_freshness(knowledge, live).by_locator[locator]


def _plugin(
    component_id: str = "fixture/plugin",
    *,
    version: str = "1.0.0",
    configuration_hash: str | None = None,
    limitations: tuple[str, ...] = ("metadata-only",),
) -> ProducerComponent:
    return ProducerComponent(
        component_id=component_id,
        version=version,
        configuration_hash=(
            fixture_hash(f"{component_id}:configuration")
            if configuration_hash is None
            else configuration_hash
        ),
        limitations=limitations,
    )


def test_existing_fixture_reason_codes_are_the_service_contract():
    expected = {
        "unknown-no-live-evaluation": (
            knowledge_freshness.REASON_LIVE_EVALUATION_NOT_PERFORMED
        ),
        "current": (knowledge_freshness.REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION),
        "byte-only-source-change": (
            knowledge_freshness.REASON_SOURCE_BYTES_CHANGED_CONCEPT_OBSERVATION_UNCHANGED
        ),
        "concept-relevant-source-change": (
            knowledge_freshness.REASON_CONCEPT_OBSERVATION_CHANGED
        ),
        "changed-extractor-version-basis": (
            knowledge_freshness.REASON_EXTRACTOR_VERSION_CHANGED
        ),
        "changed-extractor-config-basis": (
            knowledge_freshness.REASON_EXTRACTOR_CONFIGURATION_CHANGED
        ),
        "removed-source-with-prior-evidence": (
            knowledge_freshness.REASON_RELIABLY_MAPPED_SOURCE_MISSING
        ),
        "removed-source-without-recoverable-evidence": (
            knowledge_freshness.REASON_MISSING_SOURCE_HAS_NO_RELIABLE_RECORDED_BASIS
        ),
    }
    cases = {
        case.name: case for case in (*freshness_fixtures(), *removed_source_fixtures())
    }

    assert set(expected) <= set(cases)
    for name, reason_code in expected.items():
        assert cases[name].reason == reason_code


def test_no_live_evaluation_is_unknown_for_every_concept(knowledge):
    report = evaluate_knowledge_freshness(knowledge)

    assert set(report.by_locator) == {concept.locator for concept in knowledge.concepts}
    assert {result.state for result in report.by_locator.values()} == {
        ComputedFreshness.UNKNOWN
    }
    assert {result.reason_code for result in report.by_locator.values()} == {
        knowledge_freshness.REASON_LIVE_EVALUATION_NOT_PERFORMED
    }
    assert not any(
        result.live_comparison_performed for result in report.by_locator.values()
    )
    assert report.counts[ComputedFreshness.UNKNOWN] == len(knowledge.concepts)


@pytest.mark.parametrize(
    ("case_name", "expected_state"),
    [
        ("current", ComputedFreshness.CURRENT),
        (
            "byte-only-source-change",
            ComputedFreshness.NONSEMANTIC_SOURCE_CHANGE,
        ),
        ("concept-relevant-source-change", ComputedFreshness.SOURCE_CHANGED),
    ],
)
def test_matching_and_source_change_states_use_fixture_reasons(
    knowledge,
    case_name,
    expected_state,
):
    case = next(case for case in freshness_fixtures() if case.name == case_name)
    assert case.recorded_source_hash is not None
    assert case.recorded_observation_hash is not None
    assert case.live_source_hash is not None
    assert case.live_observation_hash is not None
    recorded = _replace_recorded_source_basis(
        knowledge,
        source_hash=case.recorded_source_hash,
        observation_by_locator={
            USER_LOCATOR: case.recorded_observation_hash,
        },
    )
    live = _live_evaluation(
        recorded,
        source_hash_by_path={FIXTURE_SOURCE_PATH: case.live_source_hash},
        observation_by_locator={USER_LOCATOR: case.live_observation_hash},
    )

    result = _result(recorded, live)

    assert result.locator == USER_LOCATOR
    assert result.state is expected_state is case.expected
    assert result.reason_code == case.reason
    assert result.live_comparison_performed
    assert isinstance(result.recorded_basis, ConceptFreshnessBasis)
    assert isinstance(result.live_basis, ConceptFreshnessBasis)
    assert result.recorded_basis.analysis_basis_hash is not None
    assert (
        result.recorded_basis.analysis_basis_hash
        == result.live_basis.analysis_basis_hash
    )
    if expected_state is ComputedFreshness.CURRENT:
        assert result.description == "unchanged since observation"
        assert not {"true", "verified", "approved"} & set(result.description.split())


def test_entity_change_does_not_stale_unchanged_sibling(knowledge):
    recorded_hash = fixture_hash("sibling-isolation:source:v1")
    live_hash = fixture_hash("sibling-isolation:source:v2")
    changed_user_observation = fixture_hash("sibling-isolation:user:v2")
    recorded = _replace_recorded_source_basis(
        knowledge,
        source_hash=recorded_hash,
    )

    report = evaluate_knowledge_freshness(
        recorded,
        _live_evaluation(
            recorded,
            source_hash_by_path={FIXTURE_SOURCE_PATH: live_hash},
            observation_by_locator={
                USER_LOCATOR: changed_user_observation,
            },
        ),
    )

    assert report.by_locator[USER_LOCATOR].state is ComputedFreshness.SOURCE_CHANGED
    assert (
        report.by_locator[USER_LOCATOR].reason_code
        == knowledge_freshness.REASON_CONCEPT_OBSERVATION_CHANGED
    )
    assert (
        report.by_locator[SIBLING_LOCATOR].state
        is ComputedFreshness.NONSEMANTIC_SOURCE_CHANGE
    )
    assert (
        report.by_locator[SIBLING_LOCATOR].reason_code
        == knowledge_freshness.REASON_SOURCE_BYTES_CHANGED_CONCEPT_OBSERVATION_UNCHANGED
    )


def test_source_missing_requires_a_reliable_recorded_basis(knowledge):
    with_prior, without_prior = removed_source_fixtures()

    missing = _result(
        knowledge,
        _live_evaluation(
            knowledge,
            source_hash_by_path={},
            missing_source_paths=frozenset({FIXTURE_SOURCE_PATH}),
        ),
    )
    assert missing.state is with_prior.expected is ComputedFreshness.SOURCE_MISSING
    assert missing.reason_code == with_prior.reason
    assert missing.live_comparison_performed
    assert isinstance(missing.recorded_basis, ConceptFreshnessBasis)
    assert missing.live_basis is None

    user = _concept(knowledge, USER_LOCATOR)
    known_user_basis = _known_basis(knowledge, USER_LOCATOR)
    unknown_user = replace(
        user,
        facets=replace(
            user.facets,
            structure=StructuralFacet(
                origin=Origin.UNKNOWN,
                evidence=EvidenceState.UNKNOWN,
                basis=replace(
                    known_user_basis,
                    concept_observation_hash=None,
                ),
            ),
        ),
    )
    unreliable = _replace_concept(knowledge, USER_LOCATOR, unknown_user)
    unknown = _result(
        unreliable,
        _live_evaluation(
            unreliable,
            source_hash_by_path={},
            missing_source_paths=frozenset({FIXTURE_SOURCE_PATH}),
        ),
    )

    assert unknown.state is without_prior.expected is ComputedFreshness.UNKNOWN
    assert unknown.reason_code == without_prior.reason
    assert not unknown.live_comparison_performed
    assert isinstance(unknown.recorded_basis, ConceptFreshnessBasis)
    assert unknown.recorded_basis.concept_observation_hash is None
    assert unknown.live_basis is None


def test_missing_source_precedes_an_incompatible_basis(knowledge):
    extractor = knowledge.bundle.producer.extractors[0]
    incompatible = replace(
        knowledge.bundle.producer,
        extractors=(replace(extractor, version=f"{extractor.version}-changed"),),
    )

    result = _result(
        knowledge,
        _live_evaluation(
            knowledge,
            producer=incompatible,
            source_hash_by_path={},
            missing_source_paths=frozenset({FIXTURE_SOURCE_PATH}),
        ),
    )

    assert result.state is ComputedFreshness.SOURCE_MISSING
    assert (
        result.reason_code == knowledge_freshness.REASON_RELIABLY_MAPPED_SOURCE_MISSING
    )


def test_no_live_evaluation_precedes_every_other_condition(knowledge):
    # The recorded basis is reliable and the fixture can otherwise represent a
    # missing source or incompatible producer; without supplied live evidence,
    # neither condition may be inferred from persisted state.
    result = _result(knowledge, None)

    assert result.state is ComputedFreshness.UNKNOWN
    assert (
        result.reason_code == knowledge_freshness.REASON_LIVE_EVALUATION_NOT_PERFORMED
    )
    assert not result.live_comparison_performed


def test_incompatible_basis_precedes_hash_difference_states(knowledge):
    changed_source = fixture_hash("basis-precedence:source")
    changed_observation = fixture_hash("basis-precedence:observation")

    for observation in (
        _known_basis(knowledge, USER_LOCATOR).concept_observation_hash,
        changed_observation,
    ):
        result = _result(
            knowledge,
            _live_evaluation(
                knowledge,
                generation_options_hash=fixture_hash("options:changed"),
                source_hash_by_path={FIXTURE_SOURCE_PATH: changed_source},
                observation_by_locator={USER_LOCATOR: observation},
            ),
        )
        assert result.state is ComputedFreshness.BASIS_INCOMPATIBLE
        assert (
            result.reason_code == knowledge_freshness.REASON_GENERATION_OPTIONS_CHANGED
        )


def test_identical_source_with_different_observation_is_incompatible(knowledge):
    result = _result(
        knowledge,
        _live_evaluation(
            knowledge,
            observation_by_locator={
                USER_LOCATOR: fixture_hash("nondeterministic-observation")
            },
        ),
    )

    assert result.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert (
        result.reason_code
        == knowledge_freshness.REASON_IDENTICAL_SOURCE_OBSERVATION_MISMATCH
    )
    assert result.live_comparison_performed


@pytest.mark.parametrize(
    ("source_changed", "state", "reason"),
    [
        (
            False,
            ComputedFreshness.BASIS_INCOMPATIBLE,
            knowledge_freshness.REASON_IDENTICAL_SOURCE_OBSERVATION_MISMATCH,
        ),
        (
            True,
            ComputedFreshness.SOURCE_CHANGED,
            knowledge_freshness.REASON_CONCEPT_OBSERVATION_CHANGED,
        ),
    ],
)
def test_definitively_absent_entity_occurrence_is_an_observation_change(
    knowledge,
    source_changed,
    state,
    reason,
):
    recorded = _known_basis(knowledge, USER_LOCATOR)
    assert recorded.source_path is not None
    assert recorded.extractor_ref is not None
    assert recorded.source_content_hash is not None
    live_source_hash = (
        fixture_hash("entity-removed:source")
        if source_changed
        else recorded.source_content_hash
    )
    live = _live_evaluation(
        knowledge,
        source_hash_by_path={recorded.source_path: live_source_hash},
        omit_locators=frozenset({USER_LOCATOR}),
    )
    absent = ConceptObservationBasis(
        scope=ObservationScope.ENTITY.value,
        source_path=recorded.source_path,
        extractor_ref=recorded.extractor_ref,
        source_content_hash=live_source_hash,
        concept_observation_hash=None,
        unknown_reason=knowledge_evidence.UNKNOWN_ENTITY_NOT_FOUND,
    )
    live = replace(
        live,
        concept_bases={
            **dict(live.concept_bases),
            USER_LOCATOR: absent,
        },
    )

    result = _result(knowledge, live)

    assert result.state is state
    assert result.reason_code == reason
    assert result.live_comparison_performed
    assert result.live_basis is not None
    assert (
        result.live_basis.unknown_reason == knowledge_evidence.UNKNOWN_ENTITY_NOT_FOUND
    )


@pytest.mark.parametrize(
    ("live_changes", "reason"),
    [
        (
            {"schema_version": "llm-wiki-knowledge/future"},
            knowledge_freshness.REASON_SCHEMA_VERSION_CHANGED,
        ),
        (
            {"generation_options_hash": fixture_hash("options:future")},
            knowledge_freshness.REASON_GENERATION_OPTIONS_CHANGED,
        ),
    ],
)
def test_schema_and_options_are_part_of_the_basis(
    knowledge,
    live_changes,
    reason,
):
    result = _result(
        knowledge,
        _live_evaluation(knowledge, **live_changes),
    )

    assert result.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert result.reason_code == reason
    assert result.live_comparison_performed


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        (
            {"component_id": "agent-wiki-cli-next"},
            knowledge_freshness.REASON_TOOL_ID_CHANGED,
        ),
        (
            {"version": "999.0.0"},
            knowledge_freshness.REASON_TOOL_VERSION_CHANGED,
        ),
        (
            {"configuration_hash": fixture_hash("tool:configuration:changed")},
            knowledge_freshness.REASON_TOOL_CONFIGURATION_CHANGED,
        ),
        (
            {"limitations": ("different-analysis-boundary",)},
            knowledge_freshness.REASON_TOOL_LIMITATIONS_CHANGED,
        ),
    ],
)
def test_tool_identity_and_configuration_are_part_of_the_basis(
    knowledge,
    changes,
    reason,
):
    producer = knowledge.bundle.producer
    live_producer = replace(producer, tool=replace(producer.tool, **changes))

    result = _result(
        knowledge,
        _live_evaluation(knowledge, producer=live_producer),
    )

    assert result.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert result.reason_code == reason


def test_unknown_tool_configuration_is_incompatible(knowledge):
    producer = knowledge.bundle.producer
    unknown_tool = replace(
        producer.tool,
        configuration_hash=None,
        limitations=tuple(
            sorted(
                {
                    *producer.tool.limitations,
                    "configuration-basis-unknown",
                }
            )
        ),
    )
    recorded_producer = replace(producer, tool=unknown_tool)
    recorded = _replace_producer(knowledge, recorded_producer)

    result = _result(
        recorded,
        _live_evaluation(recorded, producer=recorded_producer),
    )

    assert result.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert result.reason_code == knowledge_freshness.REASON_TOOL_CONFIGURATION_UNKNOWN


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        (
            {"version": "extractor-v2"},
            knowledge_freshness.REASON_EXTRACTOR_VERSION_CHANGED,
        ),
        (
            {"configuration_hash": fixture_hash("extractor:configuration:changed")},
            knowledge_freshness.REASON_EXTRACTOR_CONFIGURATION_CHANGED,
        ),
        (
            {"limitations": ("different-boundary",)},
            knowledge_freshness.REASON_EXTRACTOR_LIMITATIONS_CHANGED,
        ),
    ],
)
def test_referenced_extractor_basis_changes_are_incompatible(
    knowledge,
    changes,
    reason,
):
    producer = knowledge.bundle.producer
    extractor = producer.extractors[0]
    live_producer = replace(
        producer,
        extractors=(replace(extractor, **changes),),
    )

    result = _result(
        knowledge,
        _live_evaluation(knowledge, producer=live_producer),
    )

    assert result.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert result.reason_code == reason


def test_extractor_selection_and_availability_are_distinct(knowledge):
    producer = knowledge.bundle.producer
    extractor = producer.extractors[0]
    selected = replace(extractor, component_id="fixture/selected-extractor")
    selected_producer = replace(producer, extractors=(selected,))

    selection_changed = _result(
        knowledge,
        _live_evaluation(
            knowledge,
            producer=selected_producer,
            extractor_ref_by_locator={
                USER_LOCATOR: selected.component_id,
            },
        ),
    )
    unavailable = _result(
        knowledge,
        _live_evaluation(
            knowledge,
            producer=replace(producer, extractors=()),
        ),
    )

    assert selection_changed.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert (
        selection_changed.reason_code
        == knowledge_freshness.REASON_EXTRACTOR_SELECTION_CHANGED
    )
    assert unavailable.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert (
        unavailable.reason_code == knowledge_freshness.REASON_LIVE_EXTRACTOR_UNAVAILABLE
    )


def test_unknown_extractor_configuration_is_incompatible(knowledge):
    producer = knowledge.bundle.producer
    extractor = producer.extractors[0]
    unknown = replace(
        extractor,
        configuration_hash=None,
        limitations=tuple(
            sorted(
                {
                    *extractor.limitations,
                    "configuration-basis-unknown",
                }
            )
        ),
    )

    result = _result(
        knowledge,
        _live_evaluation(
            knowledge,
            producer=replace(producer, extractors=(unknown,)),
        ),
    )

    assert result.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert (
        result.reason_code == knowledge_freshness.REASON_EXTRACTOR_CONFIGURATION_UNKNOWN
    )


@pytest.mark.parametrize("component_kind", ("tool", "extractor", "plugin"))
def test_unknown_contributing_component_version_is_incompatible(
    knowledge,
    component_kind,
):
    producer = knowledge.bundle.producer
    if component_kind == "tool":
        unknown = replace(
            producer.tool,
            version="unknown",
            limitations=tuple(sorted({*producer.tool.limitations, "version-unknown"})),
        )
        recorded_producer = replace(producer, tool=unknown)
    elif component_kind == "extractor":
        extractor = producer.extractors[0]
        unknown = replace(
            extractor,
            version="unknown",
            limitations=tuple(sorted({*extractor.limitations, "version-unknown"})),
        )
        recorded_producer = replace(producer, extractors=(unknown,))
    else:
        plugin = replace(
            _plugin(),
            version="unknown",
            limitations=("version-unknown",),
        )
        recorded_producer = replace(producer, plugins=(plugin,))
    recorded = _replace_producer(knowledge, recorded_producer)

    result = _result(
        recorded,
        _live_evaluation(recorded, producer=recorded_producer),
    )

    assert result.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert result.reason_code == knowledge_freshness.REASON_VERSION_UNKNOWN


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (
            lambda plugin: replace(plugin, version="2.0.0"),
            knowledge_freshness.REASON_PLUGIN_VERSION_CHANGED,
        ),
        (
            lambda plugin: replace(
                plugin,
                configuration_hash=fixture_hash("plugin:configuration:changed"),
            ),
            knowledge_freshness.REASON_PLUGIN_CONFIGURATION_CHANGED,
        ),
        (
            lambda plugin: replace(plugin, limitations=("different-boundary",)),
            knowledge_freshness.REASON_PLUGIN_LIMITATIONS_CHANGED,
        ),
    ],
)
def test_plugin_basis_changes_are_incompatible(knowledge, change, reason):
    plugin = _plugin()
    recorded_producer = replace(knowledge.bundle.producer, plugins=(plugin,))
    recorded = _replace_producer(knowledge, recorded_producer)
    live_producer = replace(recorded_producer, plugins=(change(plugin),))

    result = _result(
        recorded,
        _live_evaluation(recorded, producer=live_producer),
    )

    assert result.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert result.reason_code == reason


def test_plugin_set_and_unknown_configuration_are_incompatible(knowledge):
    plugin = _plugin()
    recorded_producer = replace(knowledge.bundle.producer, plugins=(plugin,))
    recorded = _replace_producer(knowledge, recorded_producer)

    changed_set = _result(
        recorded,
        _live_evaluation(
            recorded,
            producer=replace(recorded_producer, plugins=()),
        ),
    )
    unknown_plugin = replace(
        plugin,
        configuration_hash=None,
        limitations=(
            "configuration-basis-unknown",
            "metadata-only",
        ),
    )
    unknown_configuration = _result(
        recorded,
        _live_evaluation(
            recorded,
            producer=replace(recorded_producer, plugins=(unknown_plugin,)),
        ),
    )

    assert changed_set.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert changed_set.reason_code == knowledge_freshness.REASON_PLUGIN_SET_CHANGED
    assert unknown_configuration.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert (
        unknown_configuration.reason_code
        == knowledge_freshness.REASON_PLUGIN_CONFIGURATION_UNKNOWN
    )


def test_semantically_unordered_component_arrays_are_compatible(knowledge):
    producer = knowledge.bundle.producer
    referenced = producer.extractors[0]
    extra_extractor = ProducerComponent(
        component_id="fixture/other-extractor",
        version="1.0.0",
        configuration_hash=fixture_hash("other-extractor:configuration"),
        limitations=(),
    )
    first_plugin = _plugin("fixture/plugin-a")
    second_plugin = _plugin("fixture/plugin-b")
    recorded_producer = replace(
        producer,
        extractors=(referenced, extra_extractor),
        plugins=(first_plugin, second_plugin),
    )
    recorded = _replace_producer(knowledge, recorded_producer)
    permuted = replace(
        recorded_producer,
        extractors=tuple(reversed(recorded_producer.extractors)),
        plugins=tuple(reversed(recorded_producer.plugins)),
    )

    result = _result(
        recorded,
        _live_evaluation(recorded, producer=permuted),
    )

    assert result.state is ComputedFreshness.CURRENT
    assert (
        result.reason_code
        == knowledge_freshness.REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION
    )


def test_unrelated_extractor_change_does_not_invalidate_concept_basis(knowledge):
    producer = knowledge.bundle.producer
    referenced = producer.extractors[0]
    unrelated = ProducerComponent(
        component_id="fixture/other-language-extractor",
        version="1.0.0",
        configuration_hash=fixture_hash("other-language:configuration"),
    )
    recorded_producer = replace(
        producer,
        extractors=(referenced, unrelated),
    )
    recorded = _replace_producer(knowledge, recorded_producer)
    live_producer = replace(
        recorded_producer,
        extractors=(referenced, replace(unrelated, version="2.0.0")),
    )

    result = _result(
        recorded,
        _live_evaluation(recorded, producer=live_producer),
    )

    assert result.state is ComputedFreshness.CURRENT
    assert (
        result.reason_code
        == knowledge_freshness.REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION
    )


def test_source_mapping_and_observation_scope_changes_are_incompatible(knowledge):
    recorded_basis = _known_basis(knowledge, USER_LOCATOR)
    assert recorded_basis.extractor_ref is not None
    assert recorded_basis.concept_observation_hash is not None
    changed_path = "src/moved_accounts.py"
    moved_basis = ConceptObservationBasis(
        scope=recorded_basis.scope.value,
        source_path=changed_path,
        extractor_ref=recorded_basis.extractor_ref,
        source_content_hash=recorded_basis.source_content_hash,
        concept_observation_hash=recorded_basis.concept_observation_hash,
    )
    moved_live = _live_evaluation(knowledge)
    moved_live = replace(
        moved_live,
        source_content_hashes={
            **dict(moved_live.source_content_hashes),
            changed_path: recorded_basis.source_content_hash,
        },
        concept_bases={
            **dict(moved_live.concept_bases),
            USER_LOCATOR: moved_basis,
        },
    )
    mapping_changed = _result(knowledge, moved_live)
    scope_changed = _result(
        knowledge,
        _live_evaluation(
            knowledge,
            scope_by_locator={USER_LOCATOR: ObservationScope.MODULE.value},
        ),
    )

    assert mapping_changed.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert (
        mapping_changed.reason_code == knowledge_freshness.REASON_SOURCE_MAPPING_CHANGED
    )
    assert scope_changed.state is ComputedFreshness.BASIS_INCOMPATIBLE
    assert (
        scope_changed.reason_code
        == knowledge_freshness.REASON_OBSERVATION_SCOPE_CHANGED
    )


def test_missing_live_concept_basis_is_unknown(knowledge):
    result = _result(
        knowledge,
        _live_evaluation(
            knowledge,
            omit_locators=frozenset({USER_LOCATOR}),
        ),
    )

    assert result.state is ComputedFreshness.UNKNOWN
    assert result.reason_code == knowledge_freshness.REASON_LIVE_BASIS_UNAVAILABLE
    assert not result.live_comparison_performed
    assert isinstance(result.recorded_basis, ConceptFreshnessBasis)
    assert result.live_basis is None


def test_document_and_aggregate_freshness_remain_unmodeled(knowledge):
    aggregate_concept = _concept(knowledge, WORKFLOW_LOCATOR)
    aggregate_basis = EvidenceBasis(
        scope=ObservationScope.AGGREGATE,
        aggregate_input_hash=fixture_hash("workflow:aggregate-inputs"),
    )
    aggregate_concept = replace(
        aggregate_concept,
        facets=replace(
            aggregate_concept.facets,
            structure=StructuralFacet(
                origin=Origin.INFERRED,
                evidence=EvidenceState.PRESENT,
                basis=aggregate_basis,
            ),
        ),
    )
    with_aggregate = _replace_concept(
        knowledge,
        WORKFLOW_LOCATOR,
        aggregate_concept,
    )

    report = evaluate_knowledge_freshness(
        with_aggregate,
        _live_evaluation(with_aggregate),
    )

    for locator in (INDEX_LOCATOR, WORKFLOW_LOCATOR):
        result = report.by_locator[locator]
        assert result.state is ComputedFreshness.UNKNOWN
        assert result.reason_code == knowledge_freshness.REASON_FRESHNESS_NOT_MODELED
        assert not result.live_comparison_performed


def test_results_are_sorted_complete_and_count_every_state(knowledge):
    reversed_knowledge = replace(
        knowledge,
        concepts=tuple(reversed(knowledge.concepts)),
    )
    live = _live_evaluation(reversed_knowledge)
    live = replace(
        live,
        source_content_hashes=dict(reversed(tuple(live.source_content_hashes.items()))),
        concept_bases=dict(reversed(tuple(live.concept_bases.items()))),
    )

    first = evaluate_knowledge_freshness(reversed_knowledge, live)
    second = evaluate_knowledge_freshness(knowledge, _live_evaluation(knowledge))
    expected_locators = sorted(concept.locator for concept in knowledge.concepts)

    assert list(first.by_locator) == expected_locators
    assert list(second.by_locator) == expected_locators
    assert first == second
    assert all(
        locator == result.locator for locator, result in first.by_locator.items()
    )
    assert set(first.counts) == set(ComputedFreshness)
    assert sum(first.counts.values()) == len(knowledge.concepts)
    assert first.counts[ComputedFreshness.CURRENT] == 3
    assert first.counts[ComputedFreshness.UNKNOWN] == 3
    assert all(
        first.counts[state] == 0
        for state in (
            ComputedFreshness.NONSEMANTIC_SOURCE_CHANGE,
            ComputedFreshness.SOURCE_CHANGED,
            ComputedFreshness.BASIS_INCOMPATIBLE,
            ComputedFreshness.SOURCE_MISSING,
        )
    )


def test_extra_live_concept_does_not_create_a_recorded_freshness_result(knowledge):
    live = _live_evaluation(knowledge)
    extra_locator = "llm-wiki://entities/NewSinceObservation"
    live = replace(
        live,
        concept_bases={
            **dict(live.concept_bases),
            extra_locator: live.concept_bases[USER_LOCATOR],
        },
    )

    report = evaluate_knowledge_freshness(knowledge, live)

    assert extra_locator not in report.by_locator
    assert set(report.by_locator) == {concept.locator for concept in knowledge.concepts}
    assert sum(report.counts.values()) == len(knowledge.concepts)


def test_empty_knowledge_index_returns_all_zero_counts(knowledge):
    empty = replace(knowledge, concepts=(), relationships=())
    live = LiveKnowledgeEvaluation(
        schema_version=empty.schema_version,
        producer=empty.bundle.producer,
        generation_options_hash=empty.bundle.snapshot.generation_options_hash,
        source_content_hashes={},
    )

    report = evaluate_knowledge_freshness(empty, live)

    assert dict(report.by_locator) == {}
    assert set(report.counts) == set(ComputedFreshness)
    assert all(count == 0 for count in report.counts.values())


def test_present_and_missing_source_sets_must_not_overlap(knowledge):
    source_hash = _known_basis(
        knowledge,
        USER_LOCATOR,
    ).source_content_hash
    assert source_hash is not None

    with pytest.raises(KnowledgeFreshnessError) as exc_info:
        evaluate_knowledge_freshness(
            knowledge,
            LiveKnowledgeEvaluation(
                schema_version=knowledge.schema_version,
                producer=knowledge.bundle.producer,
                generation_options_hash=(
                    knowledge.bundle.snapshot.generation_options_hash
                ),
                source_content_hashes={FIXTURE_SOURCE_PATH: source_hash},
                missing_source_paths=frozenset({FIXTURE_SOURCE_PATH}),
                concept_bases={},
            ),
        )

    assert "missing_source_paths" in exc_info.value.field


def test_live_basis_must_match_path_wide_source_status(knowledge):
    live = _live_evaluation(knowledge)
    user_basis = live.concept_bases[USER_LOCATOR]
    inconsistent = replace(
        user_basis,
        source_content_hash=fixture_hash("inconsistent-live-source"),
    )

    with pytest.raises(KnowledgeFreshnessError) as exc_info:
        evaluate_knowledge_freshness(
            knowledge,
            replace(
                live,
                concept_bases={
                    **dict(live.concept_bases),
                    USER_LOCATOR: inconsistent,
                },
            ),
        )

    assert "concept_bases" in exc_info.value.field


def test_live_input_rejects_invalid_hashes_and_non_basis_values(knowledge):
    valid = _live_evaluation(knowledge)

    with pytest.raises(KnowledgeFreshnessError) as hash_error:
        evaluate_knowledge_freshness(
            knowledge,
            replace(
                valid,
                source_content_hashes={FIXTURE_SOURCE_PATH: "not-a-hash"},
            ),
        )
    assert "source_content_hashes" in hash_error.value.field

    with pytest.raises(KnowledgeFreshnessError) as basis_error:
        evaluate_knowledge_freshness(
            knowledge,
            replace(
                valid,
                concept_bases={USER_LOCATOR: object()},  # type: ignore[dict-item]
            ),
        )
    assert "concept_bases" in basis_error.value.field


def test_freshness_evaluator_performs_no_io_or_live_analysis(
    knowledge,
    monkeypatch,
):
    live = _live_evaluation(knowledge)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("freshness evaluation attempted I/O or live analysis")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "glob", forbidden)
    monkeypatch.setattr(Path, "rglob", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(
        knowledge_evidence,
        "build_module_observation_basis",
        forbidden,
    )
    monkeypatch.setattr(
        knowledge_evidence,
        "build_entity_observation_basis",
        forbidden,
    )

    report = evaluate_knowledge_freshness(knowledge, live)

    assert report.by_locator[USER_LOCATOR].state is ComputedFreshness.CURRENT


def test_evaluation_does_not_mutate_or_serialize_freshness_into_knowledge(knowledge):
    before = serialize_knowledge_index(knowledge)
    before_lifecycle = tuple(concept.lifecycle for concept in knowledge.concepts)
    before_verification = tuple(
        concept.facets.semantics.verification for concept in knowledge.concepts
    )

    report = evaluate_knowledge_freshness(knowledge, _live_evaluation(knowledge))

    assert report.by_locator[USER_LOCATOR].state is ComputedFreshness.CURRENT
    assert serialize_knowledge_index(knowledge) == before
    assert tuple(concept.lifecycle for concept in knowledge.concepts) == (
        before_lifecycle
    )
    assert (
        tuple(concept.facets.semantics.verification for concept in knowledge.concepts)
        == before_verification
    )
    assert '"freshness"' not in before
