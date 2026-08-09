# knowledge_artifacts Module

**Path:** `src/llm_wiki_cli/services/knowledge_artifacts.py`

## Description

Deterministic commit protocol for generated knowledge artifacts.

The surface index and knowledge index are independently atomic files.  The
sync manifest is replaced last and commits the exact bytes of both projections
plus the complete evaluated-envelope hash.  Until that final replacement, a
validated reader must reject any orphan or mixed projection set.

## Imports

| Source | Symbols |
|--------|---------|
| `.contracts` | `KNOWLEDGE_SCHEMA_VERSION`, `SECTION_OWNERSHIP_EXTENSION_KEY`, `TYPED_GRAPH_EXTENSION_KEY` |
| `.infrastructure_sync` | `INFRASTRUCTURE_GENERATION_INPUT_KEY`, `INFRASTRUCTURE_SYNC_SCHEMA_VERSION`, `InfrastructureSyncError`, `infrastructure_evidence_by_page` |
| `.io` | `write_bytes_atomic` |
| `.knowledge_envelope` | `EvaluatedEnvelope`, `INVENTORY_HASH_EXTENSION` |
| `.knowledge_evidence` | `formatted_json_bytes`, `is_valid_sha256`, `sha256_bytes` |
| `.knowledge_governance` | `governance_hash_from_knowledge` |
| `.knowledge_graph` | `KnowledgeGraphError`, `typed_graph_from_knowledge_extensions` |
| `.knowledge_index` | `serialize_knowledge_index`, `validate_knowledge_index` |
| `.knowledge_model` | `ConceptKind`, `EvidenceBasis`, `EvidenceState`, `KnowledgeIndex`, `Origin` |
| `.section_ownership` | `SectionOwnershipError`, `validate_section_ownership` |
| `.sync_manifest` | `MANIFEST_FILENAME`, `SyncManifest`, `SyncManifestError` |
| `.validation` | `is_portable_relative_path`, `require_exact_fields`, `require_nonnegative_int` |
| `.wiki_surface` | `PageKind`, `WikiSurfaceError`, `canonical_path`, `iter_page_kinds`, `mcp_uri` |
| `.wiki_surface_index` | `SURFACE_INDEX_FILENAME`, `WIKI_SURFACE_INDEX_SCHEMA_VERSION` |
| `__future__` | `annotations` |
| `collections` | `Counter` |
| `collections.abc` | `Callable`, `Mapping` |
| `dataclasses` | `dataclass` |
| `enum` | `Enum` |
| `json` | `json` |
| `pathlib` | `Path` |
| `re` | `re` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/knowledge_artifacts.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (15) |
| Outbound | `src` (14) |

> All 29 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [KnowledgeArtifactError](../entities/KnowledgeArtifactError.md) | Class | 71 | `ValueError` | Field-specific failure while planning a generated artifact commit. |
| [ArtifactWriteState](../entities/ArtifactWriteState.md) | Enum | 81 | `str`, `Enum` | User-facing state for one planned artifact replacement. |
| [CommitStage](../entities/CommitStage.md) | Enum | 89 | `str`, `Enum` | Fault-injection points reached after each successful atomic replacement. |
| [PlannedArtifactWrite](../entities/PlannedArtifactWrite.md) | Class | 98 | — | One exact-byte action in a knowledge artifact commit. |
| [ValidatedKnowledgeArtifacts](../entities/ValidatedKnowledgeArtifacts.md) | Class | 110 | — | Validated canonical projections and their exact-byte commitments. |
| [KnowledgeCommitPlan](../entities/KnowledgeCommitPlan.md) | Class | 122 | — | A fully validated, immutable three-artifact commit plan. |
| [KnowledgeCommitResult](../entities/KnowledgeCommitResult.md) | Class | 144 | — | Outcome of a real or dry-run commit. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `validate_surface_index_bytes` | `(surface_index_bytes: bytes) -> Mapping[str, Any]` | — | Parse and strictly validate canonical surface-index v1 bytes. |
| `validate_knowledge_artifacts` | `(*, surface_index_bytes: bytes, knowledge_index_bytes: bytes, manifest: SyncManifest) -> ValidatedKnowledgeArtifacts` | — | Validate canonical projections, cross-artifact parity, and manifest basis. |
| `build_knowledge_commit_plan` | `(wiki_dir: str \| Path, *, surface_index_bytes: bytes, knowledge_index_bytes: bytes, manifest: SyncManifest) -> KnowledgeCommitPlan` | — | Validate and plan one manifest-last knowledge artifact commit. |
| `commit_knowledge_artifacts` | `(plan: KnowledgeCommitPlan, *, dry_run: bool = False, fault_injector: FaultInjector \| None = None) -> KnowledgeCommitResult` | — | Apply *plan* in projection/projection/manifest order. |
| `_planned_write` | `(path: Path, relative_path: str, content: bytes, *, force_replace: bool = False) -> PlannedArtifactWrite` | — | — |
| `_apply_write` | `(artifact: PlannedArtifactWrite, stage: CommitStage, fault_injector: FaultInjector \| None) -> None` | — | — |
| `_verify_persisted` | `(artifact: PlannedArtifactWrite) -> None` | — | — |
| `_decode_json_object` | `(content: bytes, field: str) -> Mapping[str, Any]` | — | — |
| `_unique_json_object` | `(pairs: list[tuple[str, Any]], field: str) -> dict[str, Any]` | — | — |
| `_reject_json_constant` | `(value: str, field: str) -> None` | — | — |
| `_is_future_schema_version` | `(value: object, current: str, pattern: re.Pattern[str]) -> bool` | — | — |
| `_validate_surface_payload` | `(payload: Mapping[str, Any]) -> None` | — | — |
| `_validate_utf8_json` | `(value: object, field: str) -> None` | — | — |
| `_validate_surface_knowledge_parity` | `(surface: Mapping[str, Any], knowledge: KnowledgeIndex) -> None` | — | — |
| `_surface_page_index` | `(surface: Mapping[str, Any]) -> dict[str, tuple[int, Mapping[str, Any]]]` | — | — |
| `_validate_manifest_knowledge_parity` | `(manifest: SyncManifest, surface: Mapping[str, Any], knowledge: KnowledgeIndex) -> None` | — | — |
| `_basis_payload` | `(value: EvidenceBasis \| None) -> dict[str, Any] \| None` | — | — |
| `_validate_surface_assets` | `(surface: Mapping[str, Any], valid_page_paths: set[str]) -> None` | — | — |
| `_validate_surface_counts` | `(surface: Mapping[str, Any], surface_by_path: Mapping[str, tuple[int, Mapping[str, Any]]]) -> None` | — | — |
| `_validate_surface_asset_counts` | `(value: object, assets_value: object) -> None` | — | — |
| `_validate_surface_dependency_pages` | `(surface: Mapping[str, Any]) -> None` | — | — |
| `_validate_asset_path_list` | `(value: object, field: str) -> None` | — | — |
| `_validate_surface_flows` | `(surface: Mapping[str, Any], surface_by_path: Mapping[str, tuple[int, Mapping[str, Any]]]) -> None` | — | — |
| `_validate_optional_surface_flow_fields` | `(flow: Mapping[str, Any], field: str) -> None` | — | — |
| `_validate_surface_flow_routes` | `(value: object, field: str) -> None` | — | — |
| `_validate_surface_flow_evidence` | `(value: object, field: str) -> None` | — | — |
| `_validate_surface_flow_records` | `(value: object, field: str, schema: Mapping[str, type]) -> None` | — | — |
| `_validate_surface_keys` | `(value: Mapping[str, Any], field: str, required: set[str], optional: set[str]) -> None` | — | — |
| `_validate_exact_surface_keys` | `(value: Mapping[str, Any], field: str, expected: set[str]) -> None` | — | — |
| `_nonnegative_integer` | `(value: object, field: str) -> int` | — | — |
| `_is_safe_relative_path` | `(value: object) -> bool` | — | — |
