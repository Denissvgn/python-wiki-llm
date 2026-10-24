# knowledge_freshness Module

**Path:** `src/llm_wiki_cli/services/knowledge_freshness.py`

## Description

Pure live freshness comparison for generated knowledge concepts.

The persisted knowledge index records observations and their reproducibility
basis.  This module compares those records with already evaluated live inputs;
it never reads source files, invokes extraction, writes artifacts, or persists
the resulting freshness state.

An unreliable recorded basis cannot establish structural currentness. Its
result remains unknown with no live comparison, even if this operation already
computed a valid live basis. Retaining that independently computed basis lets
consumers distinguish a captured failure from fresh normalization without
accepting or repairing the captured evidence. Snapshot-only evaluation supplies
no live observation; unavailable and malformed live bases retain their causes.

Fresh rejection detail is transported with live concept bases as non-comparing
service state, separately from source and producer comparison facts. Recorded
bases never acquire reconstructed rejection coordinates. The diagnostic cannot
turn unknown evidence into known evidence or alter freshness classification.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `analysis_compatibility` |
| `.contracts` | `GOVERNANCE_HASH_EXTENSION_KEY`, `KNOWLEDGE_SCHEMA_VERSION` |
| `.freshness_wording` | `SOURCE_CHANGED_STRUCTURE_UNCHANGED` |
| `.knowledge_artifacts` | `ValidatedKnowledgeArtifacts`, `require_validated_artifacts`, `require_validated_artifacts` |
| `.knowledge_evidence` | `UNKNOWN_ENTITY_NOT_FOUND`, `ConceptObservationBasis`, `hash_json`, `is_valid_sha256` |
| `.knowledge_model` | `BundleRecord`, `ComputedFreshness`, `ConceptRecord`, `EvidenceBasis`, `EvidenceState`, `KnowledgeIndex`, `KnowledgeModelError`, `ObservationScope`, `ProducerComponent`, `ProducerRecord`, `SnapshotRecord`, `_knowledge_index_to_payload_unchecked`, `knowledge_index_to_payload`, `parse_knowledge_index` |
| `.normalization_diagnostics` | `NormalizationDiagnostic` |
| `.validation` | `require_repository_relative_path` |
| `.wiki_surface` | `PageKind` |
| `__future__` | `annotations` |
| `collections` | `Counter` |
| `collections.abc` | `Mapping`, `Set` |
| `dataclasses` | `dataclass`, `field` |
| `types` | `MappingProxyType` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/knowledge_freshness.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/knowledge_freshness.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (9) |
| Outbound | `src` (9) |

> All 18 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [KnowledgeFreshnessError](../entities/KnowledgeFreshnessError.md) | 166 | `ValueError` | Field-specific failure at the pure live-comparison boundary. |
| [LiveKnowledgeEvaluation](../entities/LiveKnowledgeEvaluation.md) | 176 | — | Already evaluated live inputs required for freshness comparison. |
| [ConceptFreshnessBasis](../entities/ConceptFreshnessBasis.md) | 198 | — | Normalized recorded or live concept basis returned to consumers. |
| [ConceptFreshnessResult](../entities/ConceptFreshnessResult.md) | 212 | — | One consumer-computed freshness outcome. |
| [KnowledgeFreshnessReport](../entities/KnowledgeFreshnessReport.md) | 225 | — | Freshness results for every recorded concept and aggregate counts. |
| [_ValidatedLiveEvaluation](../entities/ValidatedLiveEvaluation.md) | 239 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `evaluate_knowledge_freshness` | `(knowledge: KnowledgeIndex \| object, live: LiveKnowledgeEvaluation \| None = None) -> KnowledgeFreshnessReport` | — | Evaluate every concept exactly once from supplied in-memory values. |
| `evaluate_validated_knowledge_freshness` | `(artifacts: object, live: LiveKnowledgeEvaluation \| None = None) -> KnowledgeFreshnessReport` | — | Reuse a validator-issued immutable recorded model; live inputs still validate. |
| `_evaluate_model_freshness` | `(model: KnowledgeIndex, live: LiveKnowledgeEvaluation \| None) -> KnowledgeFreshnessReport` | — | — |
| `_validate_live_evaluation` | `(recorded: KnowledgeIndex, live: LiveKnowledgeEvaluation) -> _ValidatedLiveEvaluation` | — | — |
| `_validate_live_producer` | `(recorded: KnowledgeIndex, live: LiveKnowledgeEvaluation) -> None` | — | — |
| `structural_freshness_modeled` | `(concept: ConceptRecord) -> bool` | — | Whether the contract models this concept, independent of basis presence. |
| `_evaluate_concept` | `(knowledge: KnowledgeIndex, concept: ConceptRecord, live: _ValidatedLiveEvaluation \| None) -> ConceptFreshnessResult` | — | — |
| `analysis_basis_diagnostic` | `(recorded: ProducerRecord, live: ProducerRecord, *, extractor_ref: str) -> dict \| None` | — | Explain the captured components that actually qualify this concept. |
| `_reliable_recorded_basis` | `(concept: ConceptRecord) -> EvidenceBasis \| None` | — | — |
| `_basis_incompatibility_reason` | `(recorded: KnowledgeIndex, recorded_basis: EvidenceBasis, live: _ValidatedLiveEvaluation) -> str \| None` | — | — |
| `_component_change_reason` | `(recorded: ProducerComponent, live: ProducerComponent, *, prefix: str, policy: str = 'auto', plugins: bool = False) -> str \| None` | — | — |
| `_recorded_basis_details` | `(knowledge: KnowledgeIndex, basis: EvidenceBasis \| None) -> ConceptFreshnessBasis \| None` | — | — |
| `_live_basis_details` | `(live: _ValidatedLiveEvaluation, basis: ConceptObservationBasis) -> ConceptFreshnessBasis` | — | — |
| `_analysis_basis_hash` | `(schema_version: str, producer: ProducerRecord, generation_options_hash: str, extractor_ref: str) -> str \| None` | — | — |
| `_component_basis_payload` | `(component: ProducerComponent) -> dict[str, object]` | — | — |
| `_components_by_id` | `(components: tuple[ProducerComponent, ...]) -> dict[str, ProducerComponent]` | — | — |
| `_configuration_unknown` | `(component: ProducerComponent) -> bool` | — | — |
| `_configuration_marked_unknown` | `(component: ProducerComponent) -> bool` | — | — |
| `_version_unknown` | `(component: ProducerComponent) -> bool` | — | — |
| `comparable_producer_components` | `(recorded: ProducerComponent, live: ProducerComponent, *, configuration_required: bool = True) -> bool` | — | Apply the same conservative component rule to report consistency checks. |
| `_result` | `(locator: str, state: ComputedFreshness, reason_code: str, recorded_basis: ConceptFreshnessBasis \| None, live_basis: ConceptFreshnessBasis \| None, *, compared: bool, description: str \| None = None) -> ConceptFreshnessResult` | — | — |
| `_validate_source_path` | `(value: object, field_name: str) -> None` | — | — |