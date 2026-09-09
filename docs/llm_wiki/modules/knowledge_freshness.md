# knowledge_freshness Module

**Path:** `src/llm_wiki_cli/services/knowledge_freshness.py`

## Description

Pure live freshness comparison for generated knowledge concepts.

The persisted knowledge index records observations and their reproducibility
basis.  This module compares those records with already evaluated live inputs;
it never reads source files, invokes extraction, writes artifacts, or persists
the resulting freshness state.

## Imports

| Source | Symbols |
|--------|---------|
| `.contracts` | `GOVERNANCE_HASH_EXTENSION_KEY`, `KNOWLEDGE_SCHEMA_VERSION` |
| `.knowledge_artifacts` | `ValidatedKnowledgeArtifacts`, `require_validated_artifacts`, `require_validated_artifacts` |
| `.knowledge_evidence` | `UNKNOWN_ENTITY_NOT_FOUND`, `ConceptObservationBasis`, `hash_json`, `is_valid_sha256` |
| `.knowledge_model` | `BundleRecord`, `ComputedFreshness`, `ConceptRecord`, `EvidenceBasis`, `EvidenceState`, `KnowledgeIndex`, `KnowledgeModelError`, `ObservationScope`, `ProducerComponent`, `ProducerRecord`, `SnapshotRecord`, `_knowledge_index_to_payload_unchecked`, `knowledge_index_to_payload`, `parse_knowledge_index` |
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
| Inbound | `src` (6) |
| Outbound | `src` (6) |

> All 12 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [KnowledgeFreshnessError](../entities/KnowledgeFreshnessError.md) | 150 | `ValueError` | Field-specific failure at the pure live-comparison boundary. |
| [LiveKnowledgeEvaluation](../entities/LiveKnowledgeEvaluation.md) | 160 | — | Already evaluated live inputs required for freshness comparison. |
| [ConceptFreshnessBasis](../entities/ConceptFreshnessBasis.md) | 178 | — | Normalized recorded or live concept basis returned to consumers. |
| [ConceptFreshnessResult](../entities/ConceptFreshnessResult.md) | 191 | — | One consumer-computed freshness outcome. |
| [KnowledgeFreshnessReport](../entities/KnowledgeFreshnessReport.md) | 204 | — | Freshness results for every recorded concept and aggregate counts. |
| [_ValidatedLiveEvaluation](../entities/ValidatedLiveEvaluation.md) | 212 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `evaluate_knowledge_freshness` | `(knowledge: KnowledgeIndex \| object, live: LiveKnowledgeEvaluation \| None = None) -> KnowledgeFreshnessReport` | — | Evaluate every concept exactly once from supplied in-memory values. |
| `evaluate_validated_knowledge_freshness` | `(artifacts: object, live: LiveKnowledgeEvaluation \| None = None) -> KnowledgeFreshnessReport` | — | Reuse a validator-issued immutable recorded model; live inputs still validate. |
| `_evaluate_model_freshness` | `(model: KnowledgeIndex, live: LiveKnowledgeEvaluation \| None) -> KnowledgeFreshnessReport` | — | — |
| `_validate_live_evaluation` | `(recorded: KnowledgeIndex, live: LiveKnowledgeEvaluation) -> _ValidatedLiveEvaluation` | — | — |
| `_validate_live_producer` | `(recorded: KnowledgeIndex, live: LiveKnowledgeEvaluation) -> None` | — | — |
| `_evaluate_concept` | `(knowledge: KnowledgeIndex, concept: ConceptRecord, live: _ValidatedLiveEvaluation \| None) -> ConceptFreshnessResult` | — | — |
| `_reliable_recorded_basis` | `(concept: ConceptRecord) -> EvidenceBasis \| None` | — | — |
| `_basis_incompatibility_reason` | `(recorded: KnowledgeIndex, recorded_basis: EvidenceBasis, live: _ValidatedLiveEvaluation) -> str \| None` | — | — |
| `_component_change_reason` | `(recorded: ProducerComponent, live: ProducerComponent, *, prefix: str) -> str \| None` | — | — |
| `_recorded_basis_details` | `(knowledge: KnowledgeIndex, basis: EvidenceBasis \| None) -> ConceptFreshnessBasis \| None` | — | — |
| `_live_basis_details` | `(live: _ValidatedLiveEvaluation, basis: ConceptObservationBasis) -> ConceptFreshnessBasis` | — | — |
| `_analysis_basis_hash` | `(schema_version: str, producer: ProducerRecord, generation_options_hash: str, extractor_ref: str) -> str \| None` | — | — |
| `_component_basis_payload` | `(component: ProducerComponent) -> dict[str, object]` | — | — |
| `_components_by_id` | `(components: tuple[ProducerComponent, ...]) -> dict[str, ProducerComponent]` | — | — |
| `_configuration_unknown` | `(component: ProducerComponent) -> bool` | — | — |
| `_configuration_marked_unknown` | `(component: ProducerComponent) -> bool` | — | — |
| `_version_unknown` | `(component: ProducerComponent) -> bool` | — | — |
| `_result` | `(locator: str, state: ComputedFreshness, reason_code: str, recorded_basis: ConceptFreshnessBasis \| None, live_basis: ConceptFreshnessBasis \| None, *, compared: bool) -> ConceptFreshnessResult` | — | — |
| `_validate_source_path` | `(value: object, field_name: str) -> None` | — | — |
