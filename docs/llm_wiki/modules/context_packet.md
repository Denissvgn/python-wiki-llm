# context_packet Module

**Path:** `src/llm_wiki_cli/services/context_packet.py`

## Description

Canonical Qualified Context Packet construction and verification.

The packet builder coordinates one source inventory, one wiki surface
evaluation, and one native-knowledge read view.  Context response construction
then consumes only those captured values.  Optimistic source and wiki anchors
are checked before the canonical bytes are returned, so a mutation cannot
silently detach the response from its declared basis.

This module is deliberately provider- and persistence-free.  It returns bytes
in memory, never refreshes native artifacts, and keeps structural validation
separate from live reconciliation.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `context_service`, `wiki_surface` |
| `..` | `__version__` |
| `..config` | `DEFAULT_WIKI_DIR`, `PathValidationError`, `validate_path` |
| `.contracts` | `CONTEXT_KNOWLEDGE_PROTOCOL_VERSION`, `QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION`, `QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION`, `TYPED_GRAPH_SCHEMA_VERSION` |
| `.dependencies` | `analyze_dependencies` |
| `.documentation_queries` | `CONTEXT_COVERAGE_LIMITATION_CODE_MAX_LENGTH`, `CONTEXT_COVERAGE_LIMITATION_LIMIT`, `DocumentationGraphQueryService`, `DocumentationQueryError`, `knowledge_view_selection_eligible` |
| `.documentation_query_builder` | `validate_live_query_source_selection` |
| `.extraction_jobs` | `ExtractionJobPlan`, `ExtractionJobRequest` |
| `.extraction_service` | `InventoryResult` |
| `.knowledge_consumption` | `KnowledgeReadView` |
| `.knowledge_envelope` | `KnowledgeEnvelopeError`, `hash_source_snapshot`, `validate_configured_public_identity` |
| `.knowledge_evidence` | `canonical_json_bytes`, `is_valid_sha256`, `sha256_bytes` |
| `.knowledge_freshness` | `KNOWN_FRESHNESS_REASON_CODES`, `REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION` |
| `.knowledge_graph` | `CORE_RELATIONSHIP_KINDS`, `ENDPOINT_KINDS`, `GRAPH_COVERAGE_ANALYZERS`, `GRAPH_EVIDENCE_STATES`, `GRAPH_ORIGINS`, `GRAPH_RESOLUTIONS`, `is_supported_relationship_kind` |
| `.knowledge_model` | `ComputedFreshness`, `ConceptKind`, `EvidenceState`, `Lifecycle`, `Origin`, `Resolution`, `TargetClass`, `Verification`, `concept_kind_for_page_kind` |
| `.knowledge_observability` | `knowledge_freshness_disclosure` |
| `.knowledge_verification` | `verification_summaries_for_concepts` |
| `.plugins` | `runtime_plugin_fallback_root` |
| `.source_snapshot` | `SourceSnapshot`, `SourceSnapshotError`, `build_source_snapshot`, `capture_source_selection_inputs`, `source_snapshot_inputs_match_current_files`, `source_snapshot_matches_current_files` |
| `.validation` | `require_repository_relative_path` |
| `.wiki_media` | `contains_uri_authority_userinfo` |
| `.wiki_surface_index` | `SurfaceIndexEvaluation`, `evaluate_surface_index` |
| `__future__` | `annotations` |
| `collections.abc` | `Callable`, `Mapping`, `Sequence` |
| `copy` | `deepcopy` |
| `dataclasses` | `dataclass` |
| `enum` | `Enum` |
| `json` | `json` |
| `math` | `math` |
| `os` | `os` |
| `pathlib` | `Path` |
| `re` | `re` |
| `types` | `MappingProxyType` |
| `typing` | `Any` |
| `urllib.parse` | `urlsplit` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/context_packet.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/context_packet.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (3) |
| Outbound | `src` (23) |

> All 25 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [_PacketWireContract](../entities/PacketWireContract.md) | 180 | — | One immutable schema/protocol/policy binding for canonical packets. |
| [ContextPacketError](../entities/ContextPacketError.md) | 227 | `ValueError` | Base failure for context-packet construction and consumption. |
| [ContextPacketMalformedError](../entities/ContextPacketMalformedError.md) | 233 | `ContextPacketError` | The supplied bytes do not satisfy the canonical packet contract. |
| [ContextPacketSourceMutationError](../entities/ContextPacketSourceMutationError.md) | 244 | `ContextPacketError` | A captured source or wiki anchor changed before packet return. |
| [ContextPacketUnavailableError](../entities/ContextPacketUnavailableError.md) | 256 | `ContextPacketError` | A required read-only packet capability is unavailable. |
| [ContextPacketPathPolicyError](../entities/ContextPacketPathPolicyError.md) | 262 | `ContextPacketError` | A structural packet field violates its declared path policy. |
| [CapturedContextRead](../entities/CapturedContextRead.md) | 301 | — | One coordinated in-memory source/wiki read used by a packet response. |
| [QualifiedContextPacket](../entities/QualifiedContextPacket.md) | 349 | — | Immutable canonical packet bytes plus safe value accessors. |
| [ContextPacketValidation](../entities/ContextPacketValidation.md) | 386 | — | Successful structural validation with explicitly unevaluated freshness. |
| [ContextBasisComparison](../entities/ContextBasisComparison.md) | 429 | — | Comparison with caller data, which can never assert currentness. |
| [ContextPacketReconciliation](../entities/ContextPacketReconciliation.md) | 455 | — | Consumer-time comparison against one fresh official read. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_packet_contract_for_schema` | `(schema_version: object) -> _PacketWireContract` | — | — |
| `_packet_contract_for_request` | `(request: Mapping[str, Any]) -> _PacketWireContract` | — | — |
| `_validate_reconciliation_contract` | `(*, packet_id: object, policy: object, state: object, current: object, facets: object, limitations: object) -> None` | — | — |
| `capture_context_read` | `(src_dir: str = '.', wiki_dir: str = DEFAULT_WIKI_DIR, *, allow_external_src: bool = False, read_only: bool = True, job_request: ExtractionJobRequest \| None = None, plan_reporter: Callable[[ExtractionJobPlan], None] \| None = None, source_selection: str \| Path \| None = None, allow_selection_mismatch: bool = False, strict_wiki_symlinks: bool = False) -> CapturedContextRead` | — | Capture one source inventory, wiki surface, and knowledge read view. |
| `build_context_from_captured_read` | `(captured: CapturedContextRead, request: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]` | — | Build a versioned context payload solely from one captured read. |
| `_build_legacy_context_from_captured_read` | `(captured: CapturedContextRead, normalized: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]` | — | Retain the frozen v1 response construction without semantic changes. |
| `_build_knowledge_context_from_captured_read` | `(captured: CapturedContextRead, normalized: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]` | — | Build explicit v2 knowledge selection from the coordinated capture. |
| `_captured_source_classification` | `(captured: CapturedContextRead, inventory: Mapping[str, Any], normalized: Mapping[str, Any], warnings: list[str]) -> dict[str, str]` | — | — |
| `_captured_source_payload` | `(inventory: Mapping[str, Any], classification: Mapping[str, str], budget: int, *, freshness_rank_by_source: Mapping[str, int]) -> tuple[dict[str, Any], bool]` | — | — |
| `_captured_query_service` | `(captured: CapturedContextRead, inventory: Mapping[str, Any], query_surface: Mapping[str, Any], knowledge_view: KnowledgeReadView \| None) -> DocumentationGraphQueryService` | — | — |
| `_explicit_filter_enrichment_from_captured_read` | `(query_service: DocumentationGraphQueryService \| None, query_surface: Mapping[str, Any] \| None, filters: Mapping[str, Any], warnings: list[str]) -> dict[str, Any]` | — | — |
| `build_qualified_context` | `(src_dir: str = '.', wiki_dir: str = DEFAULT_WIKI_DIR, request: Mapping[str, Any] \| None = None, *, allow_external_src: bool = False, read_only: bool = True, job_request: ExtractionJobRequest \| None = None, plan_reporter: Callable[[ExtractionJobPlan], None] \| None = None, source_selection: str \| Path \| None = None) -> QualifiedContextPacket` | — | Build a canonical packet in memory from one coordinated read view. |
| `_fit_knowledge_packet_response` | `(captured: CapturedContextRead, request: Mapping[str, Any], response: dict[str, Any], packet_contract: _PacketWireContract) -> dict[str, Any]` | — | Tail-reduce v2 native selection before the canonical byte limit. |
| `_set_knowledge_collection_prefix` | `(selection: dict[str, Any], bounds: dict[str, Any], name: str, original_items: list[Any], returned: int) -> None` | — | — |
| `_candidate_packet_size` | `(captured: CapturedContextRead, request: Mapping[str, Any], response: Mapping[str, Any], packet_contract: _PacketWireContract) -> int` | — | — |
| `validate_context_packet` | `(packet_bytes: bytes \| bytearray \| memoryview) -> ContextPacketValidation` | — | Strictly validate canonical bytes without performing live reads. |
| `compare_context_packet_basis` | `(packet_bytes: bytes \| bytearray \| memoryview, expected_basis: Mapping[str, Any]) -> ContextBasisComparison` | — | Compare caller-provided expected basis without claiming currentness. |
| `reconcile_context_packet` | `(packet_bytes: bytes \| bytearray \| memoryview, src_dir: str = '.', wiki_dir: str = DEFAULT_WIKI_DIR, *, allow_external_src: bool = False, read_only: bool = True, job_request: ExtractionJobRequest \| None = None, plan_reporter: Callable[[ExtractionJobPlan], None] \| None = None, source_selection: str \| Path \| None = None) -> ContextPacketReconciliation` | — | Validate first, then compare every packet facet with a fresh read. |
| `_build_protocol_enrichment_from_captured_read` | `(captured: CapturedContextRead, inventory: dict[str, Any], filters: dict[str, Any], warnings: list[str], *, prefer_fresh: bool = False, freshness_ranking_out: dict[str, int] \| None = None) -> dict[str, Any]` | — | — |
| `_normalized_request` | `(request: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_packet_body` | `(captured: CapturedContextRead, request: Mapping[str, Any], response: Mapping[str, Any], packet_contract: _PacketWireContract) -> dict[str, Any]` | — | — |
| `_packet_basis` | `(captured: CapturedContextRead, packet_contract: _PacketWireContract, request: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_freshness_basis` | `(view: KnowledgeReadView) -> dict[str, Any]` | — | — |
| `_packet_limitations` | `(response: Mapping[str, Any], basis: Mapping[str, Any]) -> list[str]` | — | — |
| `_context_policy_digest` | `(schema_version: str = CONTEXT_PACKET_SCHEMA_VERSION) -> str` | — | — |
| `_path_policy_digest` | `() -> str` | — | — |
| `_path_policy_receipt` | `(value: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_mapping_key_is_repository_path` | `(pointer: tuple[str, ...]) -> bool` | — | — |
| `_list_item_is_repository_path` | `(pointer: tuple[str, ...]) -> bool` | — | — |
| `_is_free_text_pointer` | `(pointer: tuple[str, ...]) -> bool` | — | — |
| `_repository_path` | `(value: object, field: str) -> str` | — | — |
| `_reject_machine_local_path` | `(value: object, error: ContextPacketPathPolicyError) -> None` | — | — |
| `_reconciliation_facets` | `(packet: Mapping[str, Any], live: Mapping[str, Any]) -> dict[str, dict[str, Any]]` | — | — |
| `_live_facet` | `(expected: Any, observed: Any, *, mismatch_reason: str) -> dict[str, Any]` | — | — |
| `_unevaluated_facet` | `(matches: bool, reason: str) -> dict[str, Any]` | — | — |
| `_packet_id` | `(body: Mapping[str, Any]) -> str` | — | — |
| `_encode_packet_payload` | `(payload: Mapping[str, Any]) -> bytes` | — | — |
| `_coerce_packet_bytes` | `(value: bytes \| bytearray \| memoryview) -> bytes` | — | — |
| `_strict_json_payload` | `(raw: bytes) -> dict[str, Any]` | — | — |
| `_validate_json_tree` | `(value: Any) -> None` | — | — |
| `_validate_packet_shape` | `(payload: Mapping[str, Any], packet_contract: _PacketWireContract) -> None` | — | — |
| `_validate_assurance` | `(value: Any) -> None` | — | — |
| `_validate_packet_request` | `(value: Any, packet_contract: _PacketWireContract) -> dict[str, Any]` | — | — |
| `_validate_response` | `(value: Any, request: Mapping[str, Any], packet_contract: _PacketWireContract) -> None` | — | — |
| `_validate_explicit_knowledge_response` | `(value: Any, request: Mapping[str, Any], *, source_priorities: Mapping[str, str] \| None = None) -> None` | — | — |
| `_validate_explicit_knowledge_bounds` | `(value: Any) -> dict[str, dict[str, int \| bool]]` | — | — |
| `_validate_collection_bound` | `(value: Any, field: str, *, returned_limit: int \| None = None) -> dict[str, int \| bool]` | — | — |
| `_validate_explicit_selection` | `(value: Any, bounds: Mapping[str, Mapping[str, int \| bool]], *, freshness_evaluated: bool, source_priorities: Mapping[str, str] \| None) -> None` | — | — |
| `_validate_explicit_concept` | `(value: Mapping[str, Any], field: str, *, freshness_evaluated: bool) -> None` | — | — |
| `_validate_explicit_page` | `(value: Mapping[str, Any], field: str) -> None` | — | — |
| `_validate_wiki_page_coordinate` | `(*, page_kind: object, page_id: object, canonical_path: object, mcp_uri: object, role: object, field: str) -> None` | — | — |
| `_validate_explicit_relationship` | `(value: Mapping[str, Any], field: str) -> None` | — | — |
| `_validate_knowledge_relationship_semantics` | `(relationship: Mapping[str, Any], target: Mapping[str, Any], field: str) -> None` | — | — |
| `_validate_context_endpoint` | `(value: Any, field: str) -> None` | — | — |
| `_validate_canonical_coverage` | `(value: Mapping[str, Any], field: str, *, includes_analyzer: bool = False) -> None` | — | — |
| `_validate_portable_uri` | `(value: str, field: str) -> None` | — | — |
| `_validate_native_wiki_uri` | `(value: str, field: str) -> None` | — | — |
| `_validate_normalized_context_target` | `(value: str, field: str) -> None` | — | — |
| `_wiki_uri_for_canonical_path` | `(value: str, field: str) -> str` | — | — |
| `_reject_raw_projection_content` | `(value: Any, field: str) -> None` | — | — |
| `_validate_explicit_ranking_policy` | `(value: Any, knowledge_value: Any, *, response_truncated: Any) -> None` | — | — |
| `_validate_explicit_source_bounds` | `(response: Mapping[str, Any]) -> None` | — | — |
| `_explicit_response_source_priorities` | `(response: Mapping[str, Any]) -> dict[str, str]` | — | — |
| `_validate_basis` | `(value: Any, packet_contract: _PacketWireContract) -> None` | — | — |
| `_validate_repository_basis` | `(value: Any) -> None` | — | — |
| `_validate_knowledge_basis` | `(value: Any, packet_contract: _PacketWireContract) -> None` | — | — |
| `_validate_freshness_basis` | `(value: Any, packet_contract: _PacketWireContract) -> None` | — | — |
| `_validate_response_basis_consistency` | `(response: Mapping[str, Any], basis: Mapping[str, Any], request: Mapping[str, Any], packet_contract: _PacketWireContract) -> None` | — | — |
| `_validate_delivery` | `(value: Any, response: Mapping[str, Any], basis: Mapping[str, Any]) -> None` | — | — |
| `_validate_path_policy_shape` | `(value: Any) -> None` | — | — |
| `_mapping` | `(value: Any, field: str) -> Mapping[str, Any]` | — | — |
| `_exact_fields` | `(value: Mapping[str, Any], allowed: set[str] \| frozenset[str], field: str, *, required: set[str] \| frozenset[str] \| None = None) -> None` | — | — |
| `_string_list` | `(value: Any, field: str) -> list[str]` | — | — |
| `_object_list` | `(value: Any, field: str) -> list[Mapping[str, Any]]` | — | — |
| `_stable_code` | `(value: Any, field: str) -> str` | — | — |
| `_nonnegative_integer` | `(value: Any, field: str) -> int` | — | — |
| `_source_anchor` | `(snapshot: SourceSnapshot) -> str` | — | — |
| `_source_snapshot_anchor_payload` | `(snapshot: SourceSnapshot) -> dict[str, Any]` | — | — |
| `_assert_source_unchanged` | `(snapshot: SourceSnapshot, expected_anchor: str) -> None` | — | — |
| `_assert_source_inputs_unchanged` | `(snapshot: SourceSnapshot, expected_anchor: str) -> None` | — | — |
| `_assert_selection_unchanged` | `(captured: CapturedContextRead) -> None` | — | — |
| `_wiki_anchor` | `(root: Path, *, reject_all_symlinks: bool = False) -> str` | — | — |
| `_wiki_symlink_is_captured_input` | `(relative_path: str) -> bool` | — | — |
| `_assert_wiki_unchanged` | `(root: Path, expected_anchor: str, *, reject_all_symlinks: bool = False) -> None` | — | — |
| `_domain_hash` | `(domain: str, value: Mapping[str, Any]) -> str` | — | — |
| `_wire_value` | `(value: Any) -> Any` | — | — |
| `_freeze_json` | `(value: Any) -> Any` | — | — |
| `_thaw_json` | `(value: Any) -> Any` | — | — |
| `_pointer` | `(parts: Sequence[str]) -> str` | — | — |
