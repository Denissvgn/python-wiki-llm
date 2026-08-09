# GovernanceLedger

**Location:** `src/llm_wiki_cli/services/knowledge_governance.py:264`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_governance](../modules/knowledge_governance.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Validated non-rebuildable governance authority.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `bundle_id` | `str` | *required* | — |
| `concepts` | `Mapping[str, GovernanceAllocation]` | `field(default_factory=dict)` | — |
| `aliases` | `Mapping[str, GovernanceAlias]` | `field(default_factory=dict)` | — |
| `lifecycle_events` | `Mapping[str, LifecycleEvent]` | `field(default_factory=dict)` | — |
| `review_events` | `Mapping[str, ReviewEvent]` | `field(default_factory=dict)` | — |
| `schema_version` | `str` | `GOVERNANCE_SCHEMA_VERSION` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `empty` | `(bundle_id: str \| None = None) -> 'GovernanceLedger'` | `@classmethod` | — |
| `from_payload` | `(payload: object, *, expected_bundle_id: str \| None = None) -> 'GovernanceLedger'` | `@classmethod` | — |
| `to_payload` | `() -> dict[str, object]` | — | — |
| `to_bytes` | `() -> bytes` | — | — |
| `content_hash` | `() -> str` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["GovernanceLedger (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n1["_assert_bundle_continuity (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n2["_concept_for_uid (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n3["_init_ledger (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n4["_mutation_preview_payload (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n5["_prepare_existing_mutation (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n6["_projected_commit_plan (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n7["_status_payload (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n8["src/llm_wiki_cli/services/knowledge_generation.py"]
    n9["_add_supersession_edges (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n10["add_alias (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n11["add_review_event (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    click n0 "../modules/knowledge_governance.md"
    click n1 "../modules/knowledge_cmd.md"
    click n2 "../modules/knowledge_cmd.md"
    click n3 "../modules/knowledge_cmd.md"
    click n4 "../modules/knowledge_cmd.md"
    click n5 "../modules/knowledge_cmd.md"
    click n6 "../modules/knowledge_cmd.md"
    click n7 "../modules/knowledge_cmd.md"
    click n8 "../modules/knowledge_generation.md"
    click n9 "../modules/knowledge_governance.md"
    click n10 "../modules/knowledge_governance.md"
    click n11 "../modules/knowledge_governance.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_governance](../modules/knowledge_governance.md) | 5 | `aliases`, `bundle_id`, `concepts`, `lifecycle_events`, `review_events`, `schema_version` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_assert_bundle_continuity` | type_reference | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `_concept_for_uid` | type_reference | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `_init_ledger` | call | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `_init_ledger` | type_reference | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `_mutation_preview_payload` | type_reference | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `_prepare_existing_mutation` | type_reference | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `_projected_commit_plan` | type_reference | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `_status_payload` | type_reference | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) |
| `_add_supersession_edges` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `add_alias` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `add_review_event` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
