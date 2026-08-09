# knowledge_governance Module

**Path:** `src/llm_wiki_cli/services/knowledge_governance.py`

## Description

Durable authority for stable concept identity and explicit governance.

The governance ledger is intentionally narrow.  It stores stable allocations,
historical aliases, lifecycle events, and digest-bound human-review events.
It never stores Markdown, extracted facts, credentials, absolute paths, or a
computed assertion that a review remains valid.

The generated knowledge index is a disposable read projection of this ledger.
This module therefore owns ledger parsing, validation, deterministic state
derivation, optimistic concurrency checks, and durable atomic replacement.
Projection helpers live near the bottom of the module and operate only on
already-validated in-memory knowledge values.

## Imports

| Source | Symbols |
|--------|---------|
| `.concept_identity` | `AliasType`, `ConceptAllocation`, `ConceptIdentityError`, `derive_concept_uid`, `identity_coordinate_key`, `validate_alias_value`, `validate_bundle_id`, `validate_concept_kind`, `validate_concept_uid`, `validate_natural_key` |
| `.contracts` | `GOVERNANCE_EXTENSION_KEY`, `GOVERNANCE_HASH_EXTENSION_KEY`, `GOVERNANCE_SCHEMA_VERSION`, `SECTION_OWNERSHIP_EXTENSION_KEY` |
| `.io` | `first_unsafe_path_component` |
| `.knowledge_envelope` | `INVENTORY_HASH_EXTENSION` |
| `.knowledge_evidence` | `canonical_json_text`, `formatted_json_bytes`, `is_valid_sha256`, `sha256_bytes` |
| `.knowledge_graph` | `validate_typed_graph`, `DEFAULT_EVIDENCE_LIMIT`, `GRAPH_INPUT_NAMES`, `GraphConcept`, `KnowledgeGraphInputs`, `materialize_typed_graph`, `relationship_edge_key`, `validate_typed_graph` |
| `.knowledge_model` | `ConceptKind`, `ConceptRecord`, `EvidenceState`, `KnowledgeIndex`, `Lifecycle` |
| `.validation` | `require_exact_fields`, `require_list`, `require_mapping`, `require_no_control_characters`, `require_nonnegative_int`, `require_repository_relative_path`, `require_sha256` |
| `.wiki_media` | `contains_uri_authority_userinfo` |
| `__future__` | `annotations` |
| `collections` | `defaultdict` |
| `collections.abc` | `Iterator`, `Mapping`, `Sequence` |
| `contextlib` | `contextmanager` |
| `dataclasses` | `dataclass`, `field`, `replace` |
| `datetime` | `datetime`, `timezone` |
| `enum` | `Enum` |
| `fcntl` | `fcntl`, `fcntl` |
| `json` | `json` |
| `msvcrt` | `msvcrt`, `msvcrt` |
| `os` | `os` |
| `pathlib` | `Path` |
| `re` | `re` |
| `stat` | `stat` |
| `sys` | `sys` |
| `tempfile` | `tempfile` |
| `typing` | `Any`, `Callable` |
| `uuid` | `uuid` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/knowledge_governance.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/knowledge_governance.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (16) |
| Outbound | `src` (9) |

> All 24 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [GovernanceError](../entities/GovernanceError.md) | Class | 111 | `ValueError` | A field-specific governance validation or mutation failure. |
| [GovernanceConflictError](../entities/GovernanceConflictError.md) | Class | 127 | `GovernanceError` | Raised when optimistic concurrency detects a changed ledger. |
| [GovernanceWriteStage](../entities/GovernanceWriteStage.md) | Enum | 134 | `str`, `Enum` | Fault-injection points for the durable ledger replacement. |
| [GovernanceActor](../entities/GovernanceActor.md) | Class | 143 | — | Explicit event author; never inferred from Git metadata. |
| [GovernanceAllocation](../entities/GovernanceAllocation.md) | Class | 154 | — | One authoritative stable concept allocation. |
| [GovernanceAlias](../entities/GovernanceAlias.md) | Class | 171 | — | A historical locator or natural key owned by one UID. |
| [LifecycleEvent](../entities/LifecycleEvent.md) | Class | 191 | — | One predecessor-linked lifecycle transition. |
| [ReviewEvidence](../entities/ReviewEvidence.md) | Class | 220 | — | The explicit evidence basis to which a review was authored. |
| [ReviewEvent](../entities/ReviewEvent.md) | Class | 238 | — | One section-scoped, digest-bound human review event. |
| [GovernanceLedger](../entities/GovernanceLedger.md) | Class | 264 | — | Validated non-rebuildable governance authority. |
| [GovernanceLoadResult](../entities/GovernanceLoadResult.md) | Class | 322 | — | — |
| [GovernanceWriteResult](../entities/GovernanceWriteResult.md) | Class | 329 | — | — |
| [ConceptGovernanceReference](../entities/ConceptGovernanceReference.md) | Class | 337 | — | Current generated concept coordinates used for reconciliation. |
| [ReviewValidity](../entities/ReviewValidity.md) | Class | 346 | — | Computed review validity; this is never persisted in the ledger. |
| [FaultInjector](../entities/FaultInjector.md) | Type alias | 358 | `Callable[[GovernanceWriteStage], None]` | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `alias_key` | `(alias_type: str, value: str) -> str` | — | Return the canonical merge-stable key for one alias. |
| `natural_key_for` | `(concept_kind: str, canonical_path: str) -> str` | — | Build the initial natural key without using an absolute checkout path. |
| `derive_concept_uid` | `(bundle_id: str, concept_kind: str, natural_key: str) -> str` | — | Derive an initial UID; the persisted allocation is authoritative. |
| `parse_governance_ledger` | `(payload: object, *, expected_bundle_id: str \| None = None) -> GovernanceLedger` | — | Validate and deserialize one governance payload. |
| `validate_governance_ledger` | `(ledger: GovernanceLedger, *, expected_bundle_id: str \| None = None) -> GovernanceLedger` | — | Validate all allocation, alias, reference, and event-history invariants. |
| `_read_governance_bytes` | `(path: Path, *, missing_ok: bool) -> bytes \| None` | — | Read at most one bounded regular ledger without following its leaf. |
| `load_governance` | `(wiki_dir: str \| Path, *, expected_bundle_id: str \| None = None) -> GovernanceLoadResult` | — | Load one canonical regular-file ledger and reject duplicate JSON keys. |
| `save_governance` | `(wiki_dir: str \| Path, ledger: GovernanceLedger, *, expected_hash: str \| None \| object = _MISSING, fault_injector: FaultInjector \| None = None) -> GovernanceWriteResult` | — | Durably replace a ledger after an optional compare-and-swap check. |
| `governance_lock` | `(wiki_dir: str \| Path) -> Iterator[None]` | `@contextmanager` | Hold the dedicated non-blocking governance mutation lock. |
| `reconcile_concepts` | `(ledger: GovernanceLedger, concepts: Sequence[ConceptGovernanceReference], *, moves: Mapping[str, str] \| None = None) -> GovernanceLedger` | — | Carry supported moves and allocate only genuinely new concepts. |
| `move_concept` | `(ledger: GovernanceLedger, uid: str, *, locator: str, natural_key: str, concept_kind: str \| None = None) -> GovernanceLedger` | — | Explicitly move an ambiguously changed concept and retain both aliases. |
| `add_alias` | `(ledger: GovernanceLedger, uid: str, alias_type: str, value: str) -> GovernanceLedger` | — | Add one explicit historical alias without changing the allocation. |
| `current_lifecycle` | `(ledger: GovernanceLedger, uid: str) -> tuple[Lifecycle, LifecycleEvent \| None]` | — | Derive one concept's current lifecycle deterministically. |
| `set_lifecycle` | `(ledger: GovernanceLedger, uid: str, state: Lifecycle \| str, *, actor: GovernanceActor, authored_at: str \| datetime \| None = None, successor_uid: str \| None = None, reason: str = 'explicit-lifecycle-change') -> GovernanceLedger` | — | Append one valid explicit lifecycle transition. |
| `add_review_event` | `(ledger: GovernanceLedger, uid: str, *, section_locator: str, scope_hash: str, evidence: ReviewEvidence, reviewer: GovernanceActor, method: str, method_version: str, authored_at: str \| datetime \| None = None) -> GovernanceLedger` | — | Append one explicit section review without storing a validity verdict. |
| `authored_event_time` | `(value: object = None) -> str` | — | Return a canonical real UTC authored-event time. |
| `lifecycle_state_by_uid` | `(ledger: GovernanceLedger) -> dict[str, tuple[Lifecycle, str \| None, LifecycleEvent \| None]]` | — | Derive lifecycle, successor, and terminal event for every allocation. |
| `concept_references_from_knowledge` | `(knowledge: KnowledgeIndex) -> tuple[ConceptGovernanceReference, ...]` | — | Return canonical identity references from a generated projection. |
| `current_review_evidence` | `(concept: ConceptRecord) -> ReviewEvidence \| None` | — | Return the comparable review evidence basis for one current concept. |
| `review_scope_hash` | `(knowledge: KnowledgeIndex, section_locator: str) -> str` | — | Return one reviewable semantic section hash or fail explicitly. |
| `evaluate_review_event` | `(event: ReviewEvent, ledger: GovernanceLedger, knowledge: KnowledgeIndex) -> ReviewValidity` | — | Compute current validity without mutating or trusting stored truth. |
| `strip_governance_projection` | `(knowledge: KnowledgeIndex) -> KnowledgeIndex` | — | Remove disposable governance fields before rebuilding from authority. |
| `apply_governance_projection` | `(knowledge: KnowledgeIndex, ledger: GovernanceLedger, *, event_limit: int = DEFAULT_EVENT_LIMIT) -> KnowledgeIndex` | — | Build the complete disposable governance projection from the ledger. |
| `validate_governance_projection` | `(knowledge: KnowledgeIndex, *, ledger: GovernanceLedger \| None = None, event_limit: int \| None = None) -> Mapping[str, object] \| None` | — | Validate projection/core parity and optionally exact ledger parity. |
| `governance_hash_from_knowledge` | `(knowledge: KnowledgeIndex) -> str \| None` | — | Return the validated governance commitment in a knowledge projection. |
| `governance_bundle_id_from_knowledge` | `(knowledge: KnowledgeIndex) -> str \| None` | — | Return the validated stable bundle ID from a governance projection. |
| `_validate_concept_summary` | `(value: object, path: str, *, limit: int \| None) -> dict[str, object]` | — | — |
| `_validate_bounded_events` | `(value: object, path: str, *, limit: int \| None, event_type: str) -> dict[str, object]` | — | — |
| `_validate_lifecycle_summary` | `(value: Mapping[str, object], path: str) -> dict[str, object]` | — | — |
| `_validate_review_summary` | `(value: Mapping[str, object], path: str) -> dict[str, object]` | — | — |
| `_add_supersession_edges` | `(extensions: dict[str, Any], ledger: GovernanceLedger, concepts: Sequence[ConceptRecord], governance_hash: str, *, inventory_hash: object = None) -> dict[str, Any]` | — | — |
| `_governance_supersession_edge_payloads` | `(knowledge: KnowledgeIndex) -> tuple[str, ...]` | — | Return exact canonical governance-edge payloads for ledger parity. |
| `_validate_supersession_projection` | `(knowledge: KnowledgeIndex, expected: set[tuple[str, str]]) -> None` | — | — |
| `_section_records_by_locator` | `(knowledge: KnowledgeIndex) -> dict[str, Mapping[str, object]]` | — | — |
| `_ordered_lifecycle_events` | `(values: Sequence[LifecycleEvent]) -> list[LifecycleEvent]` | — | — |
| `_lifecycle_event_summary` | `(event: LifecycleEvent) -> dict[str, object]` | — | — |
| `_review_event_summary` | `(event: ReviewEvent, validity: ReviewValidity) -> dict[str, object]` | — | — |
| `_bounded_event_payload` | `(items: Sequence[dict[str, object]], limit: int) -> dict[str, object]` | — | — |
| `_event_limit` | `(value: object) -> int` | — | — |
| `_nonnegative_int` | `(value: object, path: str) -> int` | — | — |
| `_parse_lifecycle_event` | `(event_id: str, value: object) -> LifecycleEvent` | — | — |
| `_parse_review_event` | `(event_id: str, value: object) -> ReviewEvent` | — | — |
| `_validate_lifecycle_event_fields` | `(event: LifecycleEvent, concepts: Mapping[str, GovernanceAllocation]) -> None` | — | — |
| `_validate_lifecycle_histories` | `(concepts: Mapping[str, GovernanceAllocation], events: Mapping[str, LifecycleEvent]) -> None` | — | — |
| `_validate_review_event_fields` | `(event: ReviewEvent, concepts: Mapping[str, GovernanceAllocation], aliases: Mapping[str, GovernanceAlias]) -> None` | — | — |
| `_parse_review_evidence` | `(value: object, path: str) -> ReviewEvidence` | — | — |
| `_review_evidence` | `(value: ReviewEvidence, path: str) -> ReviewEvidence` | — | — |
| `_validated_references` | `(values: Sequence[ConceptGovernanceReference]) -> tuple[ConceptGovernanceReference, ...]` | — | — |
| `_put_alias` | `(aliases: dict[str, GovernanceAlias], alias: GovernanceAlias, allocations: Mapping[str, GovernanceAllocation]) -> dict[str, GovernanceAlias]` | — | — |
| `_write_durable_atomic` | `(path: Path, content: bytes, *, fault_injector: FaultInjector \| None) -> None` | — | — |
| `_fsync_directory` | `(path: Path) -> None` | — | — |
| `_governance_lock_root` | `(wiki_dir: Path) -> Path` | — | — |
| `_decode_unique_json` | `(content: bytes) -> object` | — | — |
| `_parse_actor` | `(value: object, path: str) -> GovernanceActor` | — | — |
| `_actor` | `(value: GovernanceActor, path: str) -> GovernanceActor` | — | — |
| `_object` | `(value: object, path: str) -> dict[str, object]` | — | — |
| `_array` | `(value: object, path: str) -> list[object]` | — | — |
| `_exact_fields` | `(value: Mapping[str, object], path: str, required: set[str], *, optional: set[str] \| frozenset[str] = frozenset()) -> None` | — | — |
| `_safe_id` | `(value: object, path: str) -> str` | — | — |
| `_event_id` | `(value: object, path: str, *, prefix: str) -> str` | — | — |
| `_lifecycle_event_digest_payload` | `(event: LifecycleEvent) -> dict[str, object]` | — | — |
| `_review_event_digest_payload` | `(event: ReviewEvent) -> dict[str, object]` | — | — |
| `_derived_event_id` | `(prefix: str, payload: Mapping[str, object]) -> str` | — | — |
| `_safe_name` | `(value: object, path: str, *, allow_slash: bool = False) -> str` | — | — |
| `_safe_text` | `(value: str, path: str) -> None` | — | Apply credential, URI-userinfo, and absolute-path domain safeguards. |
| `_machine_code` | `(value: object, path: str) -> str` | — | — |
| `_alias_type` | `(value: object, path: str) -> str` | — | — |
| `_identity_value` | `(value: object, alias_type: str, path: str) -> str` | — | — |
| `_identity_ownership_key` | `(alias_type: str, value: str) -> str` | — | — |
| `_relative_path` | `(value: object, path: str) -> str` | — | — |
| `_section_locator` | `(value: object, path: str) -> str` | — | — |
| `_hash` | `(value: object, path: str) -> str` | — | — |
| `_existing_uid` | `(value: object, concepts: Mapping[str, GovernanceAllocation], path: str) -> str` | — | — |
| `_bundle_id` | `(value: object, path: str) -> str` | — | — |
| `_concept_kind` | `(value: object, path: str) -> str` | — | — |
| `_concept_uid` | `(value: object, path: str) -> str` | — | — |
| `_natural_key` | `(value: object, path: str) -> str` | — | — |
