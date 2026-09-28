# concept_identity Module

**Path:** `src/llm_wiki_cli/services/concept_identity.py`

## Description

Pure stable-identity primitives for knowledge concepts.

The records in this module deliberately contain no filesystem behavior.  They
validate the small identity vocabulary used by a governance ledger, derive an
initial deterministic UID, detect registry collisions, and return immutable
move/alias updates.  Once an allocation is persisted, its ``uid`` is authority;
callers must carry it forward rather than deriving it again after a move.

Natural keys are shared by storage indexes and governance. They combine a
concept kind with a normalized relative page path. Credential-related words
such as `Secret` or `ApiKey` are ordinary identifier text; path traversal,
control characters and credential-bearing authorities remain invalid.

## Imports

| Source | Symbols |
|--------|---------|
| `.validation` | `require_repository_relative_path` |
| `.wiki_surface` | `WikiSurfaceError`, `canonical_path`, `iter_page_kinds`, `mcp_uri`, `validate_exact_page_coordinate` |
| `__future__` | `annotations` |
| `collections` | `defaultdict` |
| `collections.abc` | `Iterable`, `Sequence` |
| `dataclasses` | `dataclass` |
| `enum` | `Enum` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `re` | `re` |
| `typing` | `TypeVar`, `cast` |
| `unicodedata` | `unicodedata` |
| `urllib.parse` | `quote`, `unquote`, `urlsplit` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/migrate_cmd.py"]
    n1["src/llm_wiki_cli/services/concept_identity.py"]
    n2["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n3["src/llm_wiki_cli/services/knowledge_governance.py"]
    n4["src/llm_wiki_cli/services/knowledge_projection.py"]
    n5["src/llm_wiki_cli/services/knowledge_storage.py"]
    n6["src/llm_wiki_cli/services/knowledge_storage_access.py"]
    n7["src/llm_wiki_cli/services/mcp_server.py"]
    n8["src/llm_wiki_cli/services/validation.py"]
    n9["src/llm_wiki_cli/services/wiki_surface.py"]
    n0 --> n1
    n0 --> n3
    n0 --> n8
    n0 --> n9
    n1 --> n8
    n1 --> n9
    n2 --> n1
    n2 --> n8
    n2 --> n9
    n3 --> n1
    n3 --> n8
    n4 --> n1
    n4 --> n3
    n4 --> n8
    n4 --> n9
    n5 --> n1
    n6 --> n1
    n6 --> n3
    n6 --> n5
    n7 --> n1
    n7 --> n2
    n7 --> n8
    n7 --> n9
    n9 --> n8
    click n0 "../modules/migrate_cmd.md"
    click n1 "../modules/concept_identity.md"
    click n2 "../modules/documentation_query_builder.md"
    click n3 "../modules/knowledge_governance.md"
    click n4 "../modules/knowledge_projection.md"
    click n5 "../modules/knowledge_storage.md"
    click n6 "../modules/knowledge_storage_access.md"
    click n7 "../modules/mcp_server.md"
    click n8 "../modules/validation.md"
    click n9 "../modules/wiki_surface.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [migrate_cmd](../modules/migrate_cmd.md) |
| Inbound | [documentation_query_builder](../modules/documentation_query_builder.md) |
| Inbound | [knowledge_governance](../modules/knowledge_governance.md) |
| Inbound | [knowledge_projection](../modules/knowledge_projection.md) |
| Inbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Inbound | [knowledge_storage_access](../modules/knowledge_storage_access.md) |
| Inbound | [mcp_server](../modules/mcp_server.md) |
| Outbound | [validation](../modules/validation.md) |
| Outbound | [wiki_surface](../modules/wiki_surface.md) |

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [ConceptIdentityError](../entities/ConceptIdentityError.md) | Class | 76 | `ValueError` | Field-specific validation failure for stable concept identity. |
| [AliasType](../entities/AliasType.md) | Enum | 86 | `str`, `Enum` | The two coordinate namespaces that may retain historical aliases. |
| [ConceptReference](../entities/ConceptReference.md) | Class | 94 | — | One current, regenerable concept coordinate before UID allocation. |
| [ConceptAllocation](../entities/ConceptAllocation.md) | Class | 116 | — | A persisted UID bound to the concept's current coordinates. |
| [IdentityAlias](../entities/IdentityAlias.md) | Class | 154 | — | One historical locator or natural key owned by a persisted UID. |
| [IdentityCollision](../entities/IdentityCollision.md) | Class | 171 | — | One deterministic registry conflict found without resolving it. |
| [IdentityCollisionError](../entities/IdentityCollisionError.md) | Class | 215 | `ConceptIdentityError` | Raised when allocations or aliases do not form a unique registry. |
| [IdentityUpdate](../entities/IdentityUpdate.md) | Class | 233 | — | A replacement allocation and the complete canonical alias collection. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `validate_bundle_id` | `(value: object) -> str` | — | Validate a stored, checkout-independent bundle identifier. |
| `validate_concept_kind` | `(value: object) -> str` | — | Validate a core lowercase kind or a qualified extension kind. |
| `natural_key_for` | `(concept_kind: str, canonical_path: str) -> str` | — | Build a natural key from safe coordinates, independent of governance. |
| `validate_natural_key` | `(value: object) -> str` | — | Validate one normalized, non-prose concept natural key. |
| `validate_locator` | `(value: object) -> str` | — | Validate an exact canonical Markdown route or ``llm-wiki`` URI. |
| `validate_concept_uid` | `(value: object) -> str` | — | Validate the persisted stable UID wire format. |
| `validate_alias_type` | `(value: AliasType \| str) -> AliasType` | — | Return a validated alias namespace. |
| `validate_alias_value` | `(alias_type: AliasType \| str, value: object) -> str` | — | Validate an alias according to its coordinate namespace. |
| `identity_coordinate_key` | `(alias_type: AliasType \| str, value: object) -> str` | — | Return a collision key shared by equivalent locator spellings. |
| `derive_concept_uid` | `(bundle_id: object, concept_kind: object, natural_key: object) -> str` | — | Derive the deterministic initial UID for one validated natural key. |
| `allocate_concept` | `(bundle_id: object, reference: ConceptReference, *, allocations: Iterable[ConceptAllocation] = (), aliases: Iterable[IdentityAlias] = ()) -> ConceptAllocation` | — | Return an existing exact identity or allocate a deterministic new UID. |
| `find_identity_collisions` | `(allocations: Iterable[ConceptAllocation], aliases: Iterable[IdentityAlias] = ()) -> tuple[IdentityCollision, ...]` | — | Return every deterministic UID/current-coordinate/alias conflict. |
| `validate_identity_registry` | `(allocations: Iterable[ConceptAllocation], aliases: Iterable[IdentityAlias] = ()) -> tuple[tuple[ConceptAllocation, ...], tuple[IdentityAlias, ...]]` | — | Validate uniqueness and return canonical immutable registry records. |
| `aliases_for_move` | `(allocation: ConceptAllocation, new_reference: ConceptReference, *, aliases: Iterable[IdentityAlias] = ()) -> tuple[IdentityAlias, ...]` | — | Retain prior natural key/locator values as immutable aliases. |
| `move_allocation` | `(allocation: ConceptAllocation, new_reference: ConceptReference, *, allocations: Iterable[ConceptAllocation] = (), aliases: Iterable[IdentityAlias] = ()) -> IdentityUpdate` | — | Carry a UID to new coordinates and retain both prior aliases. |
| `add_identity_alias` | `(allocation: ConceptAllocation, alias_type: AliasType \| str, value: object, *, allocations: Iterable[ConceptAllocation] = (), aliases: Iterable[IdentityAlias] = ()) -> IdentityUpdate` | — | Add one explicit alias idempotently after full collision validation. |
| `_uid_tag` | `(concept_kind: str) -> str` | — | — |
| `_machine_text` | `(value: object, field: str, *, maximum: int) -> str` | — | — |
| `_safe_decoded_coordinate` | `(value: str, field: str) -> None` | — | — |
| `_looks_absolute_path` | `(value: str) -> bool` | — | — |
| `_contains_uri_userinfo` | `(value: str) -> bool` | — | — |
| `_contains_coordinate_userinfo` | `(value: str) -> bool` | — | — |
| `_typed_tuple` | `(values: Iterable[_RecordT], expected_type: type[_RecordT], field: str) -> tuple[_RecordT, ...]` | — | — |
| `_sorted_aliases` | `(values: Iterable[IdentityAlias]) -> tuple[IdentityAlias, ...]` | — | — |
| `_deduplicated_aliases` | `(values: Iterable[IdentityAlias]) -> tuple[IdentityAlias, ...]` | — | — |