# knowledge_consumption Module

**Path:** `src/llm_wiki_cli/services/knowledge_consumption.py`

## Description

One read-only knowledge session shared by native consumers.

The session loads and validates projection state once, then optionally computes
freshness once from an already collected :class:`LiveKnowledgeEvaluation`.
It never extracts source, walks a repository, repairs artifacts, or writes
state.  Callers should create one view per native operation and pass that view
to every downstream consumer participating in the operation.

## Imports

| Source | Symbols |
|--------|---------|
| `.implementation_evidence` | `ImplementationReport`, `DECLARATIONS_KEY`, `IMPLEMENTATION_KEY`, `compare_knowledge_implementation`, `compare_knowledge_implementation` |
| `.knowledge_artifacts` | `require_validated_artifacts` |
| `.knowledge_freshness` | `KnowledgeFreshnessReport`, `LiveKnowledgeEvaluation`, `evaluate_knowledge_freshness` |
| `.knowledge_loader` | `KnowledgeLoadIssue`, `KnowledgeLoadResult`, `KnowledgeMismatchPolicy`, `KnowledgeStateLoadError`, `load_knowledge_state` |
| `.knowledge_model` | `ComputedFreshness`, `EvidenceState`, `KnowledgeIndex`, `KnowledgeLoadState` |
| `.knowledge_verification` | `attach_machine_verification_read_view` |
| `.maintenance_status` | `build_maintenance_status`, `marker_from_validated_state` |
| `.sync_manifest` | `SyncManifest` |
| `__future__` | `annotations` |
| `collections` | `Counter` |
| `collections.abc` | `Mapping`, `Sequence` |
| `dataclasses` | `dataclass`, `field`, `replace` |
| `enum` | `Enum` |
| `pathlib` | `Path` |
| `re` | `re` |
| `types` | `MappingProxyType` |
| `typing` | `TYPE_CHECKING`, `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/knowledge_consumption.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (23) |
| Outbound | `src` (8) |

> All 30 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [KnowledgeAvailability](../entities/KnowledgeAvailability.md) | Enum | 45 | `str`, `Enum` | Knowledge capability available to every native read consumer. |
| [KnowledgeReadMode](../entities/KnowledgeReadMode.md) | Enum | 54 | `str`, `Enum` | Whether a read session evaluates live concept freshness. |
| [KnowledgeReadReason](../entities/KnowledgeReadReason.md) | Enum | 62 | `str`, `Enum` | Stable cross-consumer reasons for knowledge availability. |
| [MachineVerificationAvailability](../entities/MachineVerificationAvailability.md) | Enum | 77 | `str`, `Enum` | Whether the read session evaluated a disposable machine receipt. |
| [MachineVerificationReadView](../entities/MachineVerificationReadView.md) | Class | 115 | — | One receipt evaluation shared by all consumers in a read operation. |
| [KnowledgeReadCounts](../entities/KnowledgeReadCounts.md) | Class | 269 | — | Aggregate counts derived only from a ready knowledge projection. |
| [KnowledgeReadView](../entities/KnowledgeReadView.md) | Class | 291 | — | Validated, immutable-by-contract state for one native read operation. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_machine_invalidation_reasons` | `(value: object) -> tuple[str, ...]` | — | — |
| `_machine_verification_checks` | `(value: object) -> Mapping[str, Mapping[str, Any]]` | — | — |
| `_machine_verification_check` | `(checker_id: str, value: object) -> Mapping[str, Any]` | — | — |
| `_machine_diagnostics` | `(checker_id: str, value: object) -> tuple[Mapping[str, str], ...]` | — | — |
| `_machine_diagnostic_coverage` | `(checker_id: str, value: object, *, emitted: int) -> Mapping[str, int \| bool]` | — | — |
| `build_knowledge_read_view` | `(load_result: KnowledgeLoadResult, *, live_evaluation: LiveKnowledgeEvaluation \| None = None, snapshot_only: bool = False, mode: KnowledgeReadMode \| str \| None = None) -> KnowledgeReadView` | — | Build one shared view from an already completed artifact load. |
| `load_knowledge_read_view` | `(wiki_dir: str \| Path, *, live_evaluation: LiveKnowledgeEvaluation \| None = None, snapshot_only: bool = False, mode: KnowledgeReadMode \| str \| None = None, markdown_pages: Mapping[str, str \| bytes] \| None = None, include_machine_verification: bool = False) -> KnowledgeReadView` | — | Load exactly once and return a read-only native-consumer session. |
| `_read_mode` | `(*, snapshot_only: bool, mode: KnowledgeReadMode \| str \| None) -> KnowledgeReadMode` | — | — |
| `_loaded_freshness` | `(load_result, live_evaluation)` | — | — |
| `_snapshot_maintenance_report` | `(load_result)` | — | — |
| `_implementation_report` | `(knowledge, live_evaluation)` | — | Compare captured syntax independently of structural freshness. |
| `attach_implementation_read_view` | `(view: KnowledgeReadView, *, implementation_observations: Mapping \| None, analysis_scope: str, captured_paths: Sequence[str] \| frozenset[str] \| None = None, source_content_hashes: Mapping[str, str] \| None = None, analysis_compatibility_hash: str \| None = None, missing_source_paths: Sequence[str] \| frozenset[str] = ()) -> KnowledgeReadView` | — | Attach a selected-source comparison without upgrading global freshness. |
| `_validate_load_result` | `(result: KnowledgeLoadResult) -> None` | — | — |
| `_unsupported_reason` | `(issues: tuple[KnowledgeLoadIssue, ...]) -> KnowledgeReadReason \| None` | — | — |
| `_knowledge_counts` | `(knowledge: KnowledgeIndex, freshness: KnowledgeFreshnessReport \| None) -> KnowledgeReadCounts` | — | — |
