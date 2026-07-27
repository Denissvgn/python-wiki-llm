"""Pure live freshness comparison for generated knowledge concepts.

The persisted knowledge index records observations and their reproducibility
basis.  This module compares those records with already evaluated live inputs;
it never reads source files, invokes extraction, writes artifacts, or persists
the resulting freshness state.
"""

from __future__ import annotations

import posixpath
import re
from collections import Counter
from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field
from types import MappingProxyType

from .contracts import (
    GOVERNANCE_HASH_EXTENSION_KEY,
    KNOWLEDGE_SCHEMA_VERSION,
)
from .knowledge_evidence import (
    UNKNOWN_ENTITY_NOT_FOUND,
    ConceptObservationBasis,
    hash_json,
    is_valid_sha256,
)
from .knowledge_model import (
    BundleRecord,
    ComputedFreshness,
    ConceptRecord,
    EvidenceBasis,
    EvidenceState,
    KnowledgeIndex,
    KnowledgeModelError,
    ObservationScope,
    ProducerComponent,
    ProducerRecord,
    SnapshotRecord,
    knowledge_index_to_payload,
    parse_knowledge_index,
)
from .wiki_surface import PageKind

REASON_LIVE_EVALUATION_NOT_PERFORMED = "live-evaluation-not-performed"
REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION = "recorded-basis-matches-live-evaluation"
REASON_SOURCE_BYTES_CHANGED_CONCEPT_OBSERVATION_UNCHANGED = (
    "source-bytes-changed-concept-observation-unchanged"
)
REASON_CONCEPT_OBSERVATION_CHANGED = "concept-observation-changed"
REASON_EXTRACTOR_VERSION_CHANGED = "extractor-version-changed"
REASON_EXTRACTOR_CONFIGURATION_CHANGED = "extractor-configuration-changed"
REASON_RELIABLY_MAPPED_SOURCE_MISSING = "reliably-mapped-source-missing"
REASON_MISSING_SOURCE_HAS_NO_RELIABLE_RECORDED_BASIS = (
    "missing-source-has-no-reliable-recorded-basis"
)

REASON_RECORDED_BASIS_UNAVAILABLE = "recorded-basis-unavailable"
REASON_LIVE_BASIS_UNAVAILABLE = "live-basis-unavailable"
REASON_FRESHNESS_NOT_MODELED = "freshness-not-modeled"
REASON_SCHEMA_VERSION_CHANGED = "knowledge-schema-version-changed"
REASON_GENERATION_OPTIONS_CHANGED = "generation-options-changed"
REASON_TOOL_ID_CHANGED = "producer-tool-id-changed"
REASON_TOOL_VERSION_CHANGED = "producer-tool-version-changed"
REASON_TOOL_CONFIGURATION_CHANGED = "producer-tool-configuration-changed"
REASON_TOOL_CONFIGURATION_UNKNOWN = "producer-tool-configuration-unknown"
REASON_TOOL_LIMITATIONS_CHANGED = "producer-tool-limitations-changed"
REASON_VERSION_UNKNOWN = "version-unknown"
REASON_EXTRACTOR_SELECTION_CHANGED = "extractor-selection-changed"
REASON_LIVE_EXTRACTOR_UNAVAILABLE = "live-extractor-unavailable"
REASON_EXTRACTOR_LIMITATIONS_CHANGED = "extractor-limitations-changed"
REASON_EXTRACTOR_CONFIGURATION_UNKNOWN = "extractor-configuration-unknown"
REASON_PLUGIN_SET_CHANGED = "plugin-set-changed"
REASON_PLUGIN_VERSION_CHANGED = "plugin-version-changed"
REASON_PLUGIN_CONFIGURATION_CHANGED = "plugin-configuration-changed"
REASON_PLUGIN_LIMITATIONS_CHANGED = "plugin-limitations-changed"
REASON_PLUGIN_CONFIGURATION_UNKNOWN = "plugin-configuration-unknown"
REASON_SOURCE_MAPPING_CHANGED = "source-mapping-changed"
REASON_OBSERVATION_SCOPE_CHANGED = "observation-scope-changed"
REASON_IDENTICAL_SOURCE_OBSERVATION_MISMATCH = "identical-source-observation-mismatch"

_CONFIGURATION_BASIS_UNKNOWN = "configuration-basis-unknown"
_STRUCTURAL_PAGE_KINDS = frozenset({PageKind.MODULES, PageKind.ENTITIES})
_WINDOWS_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:")

_REASON_DESCRIPTIONS = MappingProxyType(
    {
        REASON_LIVE_EVALUATION_NOT_PERFORMED: "live evaluation was not performed",
        REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION: ("unchanged since observation"),
        REASON_SOURCE_BYTES_CHANGED_CONCEPT_OBSERVATION_UNCHANGED: (
            "concept observation is unchanged since observation; source bytes changed"
        ),
        REASON_CONCEPT_OBSERVATION_CHANGED: (
            "concept observation changed since observation"
        ),
        REASON_EXTRACTOR_VERSION_CHANGED: "extractor version changed",
        REASON_EXTRACTOR_CONFIGURATION_CHANGED: "extractor configuration changed",
        REASON_RELIABLY_MAPPED_SOURCE_MISSING: ("reliably mapped source is missing"),
        REASON_MISSING_SOURCE_HAS_NO_RELIABLE_RECORDED_BASIS: (
            "a missing source cannot be asserted without a reliable recorded basis"
        ),
        REASON_RECORDED_BASIS_UNAVAILABLE: (
            "a reliable recorded concept basis is unavailable"
        ),
        REASON_LIVE_BASIS_UNAVAILABLE: ("a reliable live concept basis is unavailable"),
        REASON_FRESHNESS_NOT_MODELED: (
            "live structural freshness is not modeled for this concept"
        ),
        REASON_SCHEMA_VERSION_CHANGED: "knowledge schema version changed",
        REASON_GENERATION_OPTIONS_CHANGED: "generation options changed",
        REASON_TOOL_ID_CHANGED: "producer tool identity changed",
        REASON_TOOL_VERSION_CHANGED: "producer tool version changed",
        REASON_TOOL_CONFIGURATION_CHANGED: "producer tool configuration changed",
        REASON_TOOL_CONFIGURATION_UNKNOWN: (
            "producer tool configuration basis is unknown"
        ),
        REASON_TOOL_LIMITATIONS_CHANGED: "producer tool limitations changed",
        REASON_VERSION_UNKNOWN: (
            "a contributing producer component version is unknown"
        ),
        REASON_EXTRACTOR_SELECTION_CHANGED: "selected extractor changed",
        REASON_LIVE_EXTRACTOR_UNAVAILABLE: (
            "the recorded extractor is unavailable in the live producer basis"
        ),
        REASON_EXTRACTOR_LIMITATIONS_CHANGED: "extractor limitations changed",
        REASON_EXTRACTOR_CONFIGURATION_UNKNOWN: (
            "extractor configuration basis is unknown"
        ),
        REASON_PLUGIN_SET_CHANGED: "contributing plugin set changed",
        REASON_PLUGIN_VERSION_CHANGED: "contributing plugin version changed",
        REASON_PLUGIN_CONFIGURATION_CHANGED: (
            "contributing plugin configuration changed"
        ),
        REASON_PLUGIN_LIMITATIONS_CHANGED: ("contributing plugin limitations changed"),
        REASON_PLUGIN_CONFIGURATION_UNKNOWN: (
            "contributing plugin configuration basis is unknown"
        ),
        REASON_SOURCE_MAPPING_CHANGED: "concept source mapping changed",
        REASON_OBSERVATION_SCOPE_CHANGED: "concept observation scope changed",
        REASON_IDENTICAL_SOURCE_OBSERVATION_MISMATCH: (
            "identical source under an identical basis produced a different "
            "observation; the record or producer may be corrupt or nondeterministic"
        ),
    }
)
KNOWN_FRESHNESS_REASON_CODES = frozenset(_REASON_DESCRIPTIONS)


class KnowledgeFreshnessError(ValueError):
    """Field-specific failure at the pure live-comparison boundary."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True)
class LiveKnowledgeEvaluation:
    """Already evaluated live inputs required for freshness comparison.

    ``source_content_hashes`` and ``missing_source_paths`` are path-wide so
    sibling concepts cannot accidentally receive contradictory source status.
    ``concept_bases`` may include locators not present in the recorded index;
    they are ignored because freshness is evaluated for recorded concepts.
    """

    schema_version: str
    producer: ProducerRecord
    generation_options_hash: str
    source_content_hashes: Mapping[str, str]
    missing_source_paths: AbstractSet[str] = frozenset()
    concept_bases: Mapping[str, ConceptObservationBasis] = field(default_factory=dict)


@dataclass(frozen=True)
class ConceptFreshnessBasis:
    """Normalized recorded or live concept basis returned to consumers."""

    scope: ObservationScope
    source_path: str
    extractor_ref: str
    source_content_hash: str
    concept_observation_hash: str | None
    analysis_basis_hash: str | None
    unknown_reason: str | None = None


@dataclass(frozen=True)
class ConceptFreshnessResult:
    """One consumer-computed freshness outcome."""

    locator: str
    state: ComputedFreshness
    reason_code: str
    recorded_basis: ConceptFreshnessBasis | None
    live_basis: ConceptFreshnessBasis | None
    live_comparison_performed: bool
    description: str


@dataclass(frozen=True)
class KnowledgeFreshnessReport:
    """Freshness results for every recorded concept and aggregate counts."""

    by_locator: Mapping[str, ConceptFreshnessResult]
    counts: Mapping[ComputedFreshness, int]


@dataclass(frozen=True)
class _ValidatedLiveEvaluation:
    schema_version: str
    producer: ProducerRecord
    generation_options_hash: str
    source_content_hashes: Mapping[str, str]
    missing_source_paths: frozenset[str]
    concept_bases: Mapping[str, ConceptObservationBasis]


def evaluate_knowledge_freshness(
    knowledge: KnowledgeIndex | object,
    live: LiveKnowledgeEvaluation | None = None,
) -> KnowledgeFreshnessReport:
    """Evaluate every concept exactly once from supplied in-memory values."""

    try:
        model = (
            parse_knowledge_index(knowledge_index_to_payload(knowledge))
            if isinstance(knowledge, KnowledgeIndex)
            else parse_knowledge_index(knowledge)
        )
    except (KnowledgeModelError, TypeError, ValueError) as exc:
        raise KnowledgeFreshnessError(
            "knowledge",
            f"must be a validated knowledge index: {exc}",
        ) from exc

    validated_live = None if live is None else _validate_live_evaluation(model, live)
    results: dict[str, ConceptFreshnessResult] = {}
    counts: Counter[ComputedFreshness] = Counter()
    for concept in sorted(model.concepts, key=lambda item: item.locator):
        result = _evaluate_concept(model, concept, validated_live)
        results[concept.locator] = result
        counts[result.state] += 1

    complete_counts = {state: counts.get(state, 0) for state in ComputedFreshness}
    return KnowledgeFreshnessReport(
        by_locator=MappingProxyType(results),
        counts=MappingProxyType(complete_counts),
    )


def _validate_live_evaluation(
    recorded: KnowledgeIndex,
    live: LiveKnowledgeEvaluation,
) -> _ValidatedLiveEvaluation:
    if not isinstance(live, LiveKnowledgeEvaluation):
        raise KnowledgeFreshnessError(
            "live",
            "must be a LiveKnowledgeEvaluation or None",
        )
    if not isinstance(live.schema_version, str) or not live.schema_version:
        raise KnowledgeFreshnessError(
            "live.schema_version",
            "must be a non-empty string",
        )
    if not isinstance(live.producer, ProducerRecord):
        raise KnowledgeFreshnessError(
            "live.producer",
            "must be a validated ProducerRecord",
        )
    if not is_valid_sha256(live.generation_options_hash):
        raise KnowledgeFreshnessError(
            "live.generation_options_hash",
            "must be a canonical lowercase SHA-256 value",
        )
    _validate_live_producer(recorded, live)

    if not isinstance(live.source_content_hashes, Mapping):
        raise KnowledgeFreshnessError(
            "live.source_content_hashes",
            "must be a path-to-hash mapping",
        )
    source_hashes: dict[str, str] = {}
    for path, content_hash in live.source_content_hashes.items():
        _validate_source_path(path, "live.source_content_hashes")
        if not is_valid_sha256(content_hash):
            raise KnowledgeFreshnessError(
                f"live.source_content_hashes.{path}",
                "must be a canonical lowercase SHA-256 value",
            )
        source_hashes[path] = content_hash

    missing_value = live.missing_source_paths
    if isinstance(missing_value, (str, bytes)) or not isinstance(
        missing_value,
        AbstractSet,
    ):
        raise KnowledgeFreshnessError(
            "live.missing_source_paths",
            "must be a set of repository-relative source paths",
        )
    missing: set[str] = set()
    for path in missing_value:
        _validate_source_path(path, "live.missing_source_paths")
        missing.add(path)
    overlap = set(source_hashes) & missing
    if overlap:
        path = min(overlap)
        raise KnowledgeFreshnessError(
            "live.missing_source_paths",
            f"also marks present source path {path!r} as missing",
        )

    if not isinstance(live.concept_bases, Mapping):
        raise KnowledgeFreshnessError(
            "live.concept_bases",
            "must be a locator-to-basis mapping",
        )
    bases: dict[str, ConceptObservationBasis] = {}
    for locator, basis in live.concept_bases.items():
        if not isinstance(locator, str) or not locator:
            raise KnowledgeFreshnessError(
                "live.concept_bases",
                "must use non-empty string locator keys",
            )
        if not isinstance(basis, ConceptObservationBasis):
            raise KnowledgeFreshnessError(
                f"live.concept_bases.{locator}",
                "must be a ConceptObservationBasis",
            )
        captured_hash = source_hashes.get(basis.source_path)
        if captured_hash is None:
            raise KnowledgeFreshnessError(
                f"live.concept_bases.{locator}.source_path",
                "must refer to a source in live.source_content_hashes",
            )
        if basis.source_content_hash != captured_hash:
            raise KnowledgeFreshnessError(
                f"live.concept_bases.{locator}.source_content_hash",
                "must match the path-wide live source content hash",
            )
        bases[locator] = basis

    return _ValidatedLiveEvaluation(
        schema_version=live.schema_version,
        producer=live.producer,
        generation_options_hash=live.generation_options_hash,
        source_content_hashes=MappingProxyType(source_hashes),
        missing_source_paths=frozenset(missing),
        concept_bases=MappingProxyType(bases),
    )


def _validate_live_producer(
    recorded: KnowledgeIndex,
    live: LiveKnowledgeEvaluation,
) -> None:
    snapshot = recorded.bundle.snapshot
    probe = KnowledgeIndex(
        schema_version=KNOWLEDGE_SCHEMA_VERSION,
        bundle=BundleRecord(
            repository=recorded.bundle.repository,
            snapshot=SnapshotRecord(
                source_snapshot_hash=snapshot.source_snapshot_hash,
                markdown_snapshot_hash=snapshot.markdown_snapshot_hash,
                surface_index_hash=snapshot.surface_index_hash,
                generation_options_hash=live.generation_options_hash,
                extensions={
                    key: value
                    for key, value in snapshot.extensions.items()
                    if key != GOVERNANCE_HASH_EXTENSION_KEY
                },
            ),
            producer=live.producer,
            extensions=recorded.bundle.extensions,
        ),
        concepts=(),
        relationships=(),
    )
    try:
        knowledge_index_to_payload(probe)
    except (KnowledgeModelError, TypeError, ValueError) as exc:
        raise KnowledgeFreshnessError(
            "live.producer",
            f"does not satisfy the normalized producer contract: {exc}",
        ) from exc


def _evaluate_concept(
    knowledge: KnowledgeIndex,
    concept: ConceptRecord,
    live: _ValidatedLiveEvaluation | None,
) -> ConceptFreshnessResult:
    recorded_raw = concept.facets.structure.basis
    recorded_details = _recorded_basis_details(knowledge, recorded_raw)
    if live is None:
        return _result(
            concept.locator,
            ComputedFreshness.UNKNOWN,
            REASON_LIVE_EVALUATION_NOT_PERFORMED,
            recorded_details,
            None,
            compared=False,
        )

    if (
        concept.document.page_kind not in _STRUCTURAL_PAGE_KINDS
        or recorded_raw is not None
        and recorded_raw.scope is ObservationScope.AGGREGATE
    ):
        return _result(
            concept.locator,
            ComputedFreshness.UNKNOWN,
            REASON_FRESHNESS_NOT_MODELED,
            recorded_details,
            None,
            compared=False,
        )

    recorded = _reliable_recorded_basis(concept)
    if recorded is None:
        reason = REASON_RECORDED_BASIS_UNAVAILABLE
        if (
            recorded_raw is not None
            and recorded_raw.source_path is not None
            and recorded_raw.source_path in live.missing_source_paths
        ):
            reason = REASON_MISSING_SOURCE_HAS_NO_RELIABLE_RECORDED_BASIS
        return _result(
            concept.locator,
            ComputedFreshness.UNKNOWN,
            reason,
            recorded_details,
            None,
            compared=False,
        )

    assert recorded.source_path is not None
    if recorded.source_path in live.missing_source_paths:
        return _result(
            concept.locator,
            ComputedFreshness.SOURCE_MISSING,
            REASON_RELIABLY_MAPPED_SOURCE_MISSING,
            recorded_details,
            None,
            compared=True,
        )

    live_source_hash = live.source_content_hashes.get(recorded.source_path)
    live_raw = live.concept_bases.get(concept.locator)
    live_details = None if live_raw is None else _live_basis_details(live, live_raw)
    live_entity_absent = (
        live_raw is not None
        and live_raw.unknown_reason == UNKNOWN_ENTITY_NOT_FOUND
        and recorded.scope is ObservationScope.ENTITY
    )
    if (
        live_source_hash is None
        or live_raw is None
        or not live_raw.is_known
        and not live_entity_absent
    ):
        return _result(
            concept.locator,
            ComputedFreshness.UNKNOWN,
            REASON_LIVE_BASIS_UNAVAILABLE,
            recorded_details,
            live_details,
            compared=False,
        )

    if live_raw.source_path != recorded.source_path:
        return _result(
            concept.locator,
            ComputedFreshness.BASIS_INCOMPATIBLE,
            REASON_SOURCE_MAPPING_CHANGED,
            recorded_details,
            live_details,
            compared=True,
        )
    if live_raw.scope != recorded.scope.value:
        return _result(
            concept.locator,
            ComputedFreshness.BASIS_INCOMPATIBLE,
            REASON_OBSERVATION_SCOPE_CHANGED,
            recorded_details,
            live_details,
            compared=True,
        )
    if live_raw.extractor_ref != recorded.extractor_ref:
        return _result(
            concept.locator,
            ComputedFreshness.BASIS_INCOMPATIBLE,
            REASON_EXTRACTOR_SELECTION_CHANGED,
            recorded_details,
            live_details,
            compared=True,
        )

    incompatibility = _basis_incompatibility_reason(
        knowledge,
        recorded,
        live,
    )
    if incompatibility is not None:
        return _result(
            concept.locator,
            ComputedFreshness.BASIS_INCOMPATIBLE,
            incompatibility,
            recorded_details,
            live_details,
            compared=True,
        )

    assert recorded.source_content_hash is not None
    assert recorded.concept_observation_hash is not None
    if live_entity_absent:
        if recorded.source_content_hash == live_source_hash:
            return _result(
                concept.locator,
                ComputedFreshness.BASIS_INCOMPATIBLE,
                REASON_IDENTICAL_SOURCE_OBSERVATION_MISMATCH,
                recorded_details,
                live_details,
                compared=True,
            )
        return _result(
            concept.locator,
            ComputedFreshness.SOURCE_CHANGED,
            REASON_CONCEPT_OBSERVATION_CHANGED,
            recorded_details,
            live_details,
            compared=True,
        )

    assert live_raw.concept_observation_hash is not None
    source_matches = recorded.source_content_hash == live_source_hash
    observation_matches = (
        recorded.concept_observation_hash == live_raw.concept_observation_hash
    )
    if source_matches and observation_matches:
        return _result(
            concept.locator,
            ComputedFreshness.CURRENT,
            REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION,
            recorded_details,
            live_details,
            compared=True,
        )
    if not source_matches and observation_matches:
        return _result(
            concept.locator,
            ComputedFreshness.NONSEMANTIC_SOURCE_CHANGE,
            REASON_SOURCE_BYTES_CHANGED_CONCEPT_OBSERVATION_UNCHANGED,
            recorded_details,
            live_details,
            compared=True,
        )
    if source_matches:
        return _result(
            concept.locator,
            ComputedFreshness.BASIS_INCOMPATIBLE,
            REASON_IDENTICAL_SOURCE_OBSERVATION_MISMATCH,
            recorded_details,
            live_details,
            compared=True,
        )
    return _result(
        concept.locator,
        ComputedFreshness.SOURCE_CHANGED,
        REASON_CONCEPT_OBSERVATION_CHANGED,
        recorded_details,
        live_details,
        compared=True,
    )


def _reliable_recorded_basis(concept: ConceptRecord) -> EvidenceBasis | None:
    structure = concept.facets.structure
    basis = structure.basis
    if (
        structure.evidence is not EvidenceState.PRESENT
        or basis is None
        or basis.scope not in {ObservationScope.MODULE, ObservationScope.ENTITY}
        or basis.source_path is None
        or basis.extractor_ref is None
        or basis.source_content_hash is None
        or basis.concept_observation_hash is None
    ):
        return None
    return basis


def _basis_incompatibility_reason(
    recorded: KnowledgeIndex,
    recorded_basis: EvidenceBasis,
    live: _ValidatedLiveEvaluation,
) -> str | None:
    if live.schema_version != recorded.schema_version:
        return REASON_SCHEMA_VERSION_CHANGED

    if _version_unknown(recorded.bundle.producer.tool) or _version_unknown(
        live.producer.tool
    ):
        return REASON_VERSION_UNKNOWN
    if _configuration_marked_unknown(
        recorded.bundle.producer.tool
    ) or _configuration_marked_unknown(live.producer.tool):
        return REASON_TOOL_CONFIGURATION_UNKNOWN
    component_reason = _component_change_reason(
        recorded.bundle.producer.tool,
        live.producer.tool,
        prefix="tool",
    )
    if component_reason is not None:
        return component_reason

    assert recorded_basis.extractor_ref is not None
    recorded_extractors = _components_by_id(recorded.bundle.producer.extractors)
    live_extractors = _components_by_id(live.producer.extractors)
    recorded_extractor = recorded_extractors.get(recorded_basis.extractor_ref)
    live_extractor = live_extractors.get(recorded_basis.extractor_ref)
    if live_extractor is None or recorded_extractor is None:
        return REASON_LIVE_EXTRACTOR_UNAVAILABLE
    if _version_unknown(recorded_extractor) or _version_unknown(live_extractor):
        return REASON_VERSION_UNKNOWN
    if _configuration_unknown(recorded_extractor) or _configuration_unknown(
        live_extractor
    ):
        return REASON_EXTRACTOR_CONFIGURATION_UNKNOWN
    component_reason = _component_change_reason(
        recorded_extractor,
        live_extractor,
        prefix="extractor",
    )
    if component_reason is not None:
        return component_reason

    recorded_plugins = _components_by_id(recorded.bundle.producer.plugins)
    live_plugins = _components_by_id(live.producer.plugins)
    if set(recorded_plugins) != set(live_plugins):
        return REASON_PLUGIN_SET_CHANGED
    for component_id in sorted(recorded_plugins):
        recorded_plugin = recorded_plugins[component_id]
        live_plugin = live_plugins[component_id]
        if _version_unknown(recorded_plugin) or _version_unknown(live_plugin):
            return REASON_VERSION_UNKNOWN
        if _configuration_unknown(recorded_plugin) or _configuration_unknown(
            live_plugin
        ):
            return REASON_PLUGIN_CONFIGURATION_UNKNOWN
        component_reason = _component_change_reason(
            recorded_plugin,
            live_plugin,
            prefix="plugin",
        )
        if component_reason is not None:
            return component_reason

    if recorded.bundle.snapshot.generation_options_hash != live.generation_options_hash:
        return REASON_GENERATION_OPTIONS_CHANGED
    return None


def _component_change_reason(
    recorded: ProducerComponent,
    live: ProducerComponent,
    *,
    prefix: str,
) -> str | None:
    if recorded.component_id != live.component_id:
        return (
            REASON_TOOL_ID_CHANGED
            if prefix == "tool"
            else REASON_EXTRACTOR_SELECTION_CHANGED
        )
    if recorded.version != live.version:
        return {
            "tool": REASON_TOOL_VERSION_CHANGED,
            "extractor": REASON_EXTRACTOR_VERSION_CHANGED,
            "plugin": REASON_PLUGIN_VERSION_CHANGED,
        }[prefix]
    if recorded.configuration_hash != live.configuration_hash:
        return {
            "tool": REASON_TOOL_CONFIGURATION_CHANGED,
            "extractor": REASON_EXTRACTOR_CONFIGURATION_CHANGED,
            "plugin": REASON_PLUGIN_CONFIGURATION_CHANGED,
        }[prefix]
    if recorded.limitations != live.limitations:
        return {
            "tool": REASON_TOOL_LIMITATIONS_CHANGED,
            "extractor": REASON_EXTRACTOR_LIMITATIONS_CHANGED,
            "plugin": REASON_PLUGIN_LIMITATIONS_CHANGED,
        }[prefix]
    return None


def _recorded_basis_details(
    knowledge: KnowledgeIndex,
    basis: EvidenceBasis | None,
) -> ConceptFreshnessBasis | None:
    if (
        basis is None
        or basis.source_path is None
        or basis.extractor_ref is None
        or basis.source_content_hash is None
    ):
        return None
    return ConceptFreshnessBasis(
        scope=basis.scope,
        source_path=basis.source_path,
        extractor_ref=basis.extractor_ref,
        source_content_hash=basis.source_content_hash,
        concept_observation_hash=basis.concept_observation_hash,
        analysis_basis_hash=_analysis_basis_hash(
            knowledge.schema_version,
            knowledge.bundle.producer,
            knowledge.bundle.snapshot.generation_options_hash,
            basis.extractor_ref,
        ),
    )


def _live_basis_details(
    live: _ValidatedLiveEvaluation,
    basis: ConceptObservationBasis,
) -> ConceptFreshnessBasis:
    return ConceptFreshnessBasis(
        scope=ObservationScope(basis.scope),
        source_path=basis.source_path,
        extractor_ref=basis.extractor_ref,
        source_content_hash=basis.source_content_hash,
        concept_observation_hash=basis.concept_observation_hash,
        analysis_basis_hash=_analysis_basis_hash(
            live.schema_version,
            live.producer,
            live.generation_options_hash,
            basis.extractor_ref,
        ),
        unknown_reason=basis.unknown_reason,
    )


def _analysis_basis_hash(
    schema_version: str,
    producer: ProducerRecord,
    generation_options_hash: str,
    extractor_ref: str,
) -> str | None:
    extractor = _components_by_id(producer.extractors).get(extractor_ref)
    if extractor is None:
        return None
    return hash_json(
        {
            "domain": "llm-wiki/concept-freshness-basis/v1",
            "schema_version": schema_version,
            "generation_options_hash": generation_options_hash,
            "tool": _component_basis_payload(producer.tool),
            "extractor": _component_basis_payload(extractor),
            "plugins": [
                _component_basis_payload(component)
                for component in sorted(
                    producer.plugins,
                    key=lambda item: item.component_id,
                )
            ],
        }
    )


def _component_basis_payload(component: ProducerComponent) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": component.component_id,
        "version": component.version,
        "limitations": list(component.limitations),
    }
    if component.configuration_hash is not None:
        payload["configuration_hash"] = component.configuration_hash
    return payload


def _components_by_id(
    components: tuple[ProducerComponent, ...],
) -> dict[str, ProducerComponent]:
    return {component.component_id: component for component in components}


def _configuration_unknown(component: ProducerComponent) -> bool:
    return (
        component.configuration_hash is None
        or _CONFIGURATION_BASIS_UNKNOWN in component.limitations
    )


def _configuration_marked_unknown(component: ProducerComponent) -> bool:
    return _CONFIGURATION_BASIS_UNKNOWN in component.limitations


def _version_unknown(component: ProducerComponent) -> bool:
    return component.version == "unknown" or "version-unknown" in component.limitations


def _result(
    locator: str,
    state: ComputedFreshness,
    reason_code: str,
    recorded_basis: ConceptFreshnessBasis | None,
    live_basis: ConceptFreshnessBasis | None,
    *,
    compared: bool,
) -> ConceptFreshnessResult:
    return ConceptFreshnessResult(
        locator=locator,
        state=state,
        reason_code=reason_code,
        recorded_basis=recorded_basis,
        live_basis=live_basis,
        live_comparison_performed=compared,
        description=_REASON_DESCRIPTIONS[reason_code],
    )


def _validate_source_path(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise KnowledgeFreshnessError(
            field_name,
            "must contain non-empty string source paths",
        )
    if (
        value.startswith(("/", "\\", "../"))
        or "\\" in value
        or _WINDOWS_DRIVE_PREFIX_RE.match(value)
        or posixpath.normpath(value) != value
        or value in {".", ".."}
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise KnowledgeFreshnessError(
            field_name,
            f"contains unsafe repository-relative source path {value!r}",
        )


__all__ = [
    "KNOWN_FRESHNESS_REASON_CODES",
    "REASON_CONCEPT_OBSERVATION_CHANGED",
    "REASON_EXTRACTOR_CONFIGURATION_CHANGED",
    "REASON_EXTRACTOR_CONFIGURATION_UNKNOWN",
    "REASON_EXTRACTOR_LIMITATIONS_CHANGED",
    "REASON_EXTRACTOR_SELECTION_CHANGED",
    "REASON_EXTRACTOR_VERSION_CHANGED",
    "REASON_FRESHNESS_NOT_MODELED",
    "REASON_GENERATION_OPTIONS_CHANGED",
    "REASON_IDENTICAL_SOURCE_OBSERVATION_MISMATCH",
    "REASON_LIVE_BASIS_UNAVAILABLE",
    "REASON_LIVE_EVALUATION_NOT_PERFORMED",
    "REASON_LIVE_EXTRACTOR_UNAVAILABLE",
    "REASON_MISSING_SOURCE_HAS_NO_RELIABLE_RECORDED_BASIS",
    "REASON_OBSERVATION_SCOPE_CHANGED",
    "REASON_PLUGIN_CONFIGURATION_CHANGED",
    "REASON_PLUGIN_CONFIGURATION_UNKNOWN",
    "REASON_PLUGIN_LIMITATIONS_CHANGED",
    "REASON_PLUGIN_SET_CHANGED",
    "REASON_PLUGIN_VERSION_CHANGED",
    "REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION",
    "REASON_RECORDED_BASIS_UNAVAILABLE",
    "REASON_RELIABLY_MAPPED_SOURCE_MISSING",
    "REASON_SCHEMA_VERSION_CHANGED",
    "REASON_SOURCE_BYTES_CHANGED_CONCEPT_OBSERVATION_UNCHANGED",
    "REASON_SOURCE_MAPPING_CHANGED",
    "REASON_TOOL_CONFIGURATION_CHANGED",
    "REASON_TOOL_CONFIGURATION_UNKNOWN",
    "REASON_TOOL_ID_CHANGED",
    "REASON_TOOL_LIMITATIONS_CHANGED",
    "REASON_TOOL_VERSION_CHANGED",
    "REASON_VERSION_UNKNOWN",
    "ConceptFreshnessBasis",
    "ConceptFreshnessResult",
    "KnowledgeFreshnessError",
    "KnowledgeFreshnessReport",
    "LiveKnowledgeEvaluation",
    "evaluate_knowledge_freshness",
]
