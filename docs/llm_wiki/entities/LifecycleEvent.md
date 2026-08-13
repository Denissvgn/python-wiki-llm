# LifecycleEvent

**Location:** `src/llm_wiki_cli/services/knowledge_governance.py:191`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_governance](../modules/knowledge_governance.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One predecessor-linked lifecycle transition.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `event_id` | `str` | *required* | — |
| `concept_uid` | `str` | *required* | — |
| `previous_event_id` | `str \| None` | *required* | — |
| `from_state` | `Lifecycle` | *required* | — |
| `to_state` | `Lifecycle` | *required* | — |
| `actor` | `GovernanceActor` | *required* | — |
| `authored_at` | `str` | *required* | — |
| `reason` | `str` | *required* | — |
| `successor_uid` | `str \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_payload` | `() -> dict[str, object]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["LifecycleEvent (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n1["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n2["_lifecycle_event_digest_payload (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n3["_lifecycle_event_summary (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n4["_ordered_lifecycle_events (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n5["_parse_lifecycle_event (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n6["_validate_lifecycle_event_fields (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n7["_validate_lifecycle_histories (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n8["current_lifecycle (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n9["lifecycle_state_by_uid (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n10["set_lifecycle (src/llm_wiki_cli/services/knowledge_governance.py)"]
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
    click n0 "../modules/knowledge_governance.md"
    click n1 "../modules/knowledge_cmd.md"
    click n2 "../modules/knowledge_governance.md"
    click n3 "../modules/knowledge_governance.md"
    click n4 "../modules/knowledge_governance.md"
    click n5 "../modules/knowledge_governance.md"
    click n6 "../modules/knowledge_governance.md"
    click n7 "../modules/knowledge_governance.md"
    click n8 "../modules/knowledge_governance.md"
    click n9 "../modules/knowledge_governance.md"
    click n10 "../modules/knowledge_governance.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_governance](../modules/knowledge_governance.md) | 1 | `actor`, `authored_at`, `concept_uid`, `event_id`, `from_state`, `previous_event_id`, `reason`, `successor_uid`, `to_state` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_cmd` | import | [knowledge_cmd](../modules/knowledge_cmd.md) | — |
| `_lifecycle_event_digest_payload` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_lifecycle_event_summary` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_ordered_lifecycle_events` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_parse_lifecycle_event` | call | [knowledge_governance](../modules/knowledge_governance.md) | 1 |
| `_parse_lifecycle_event` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_validate_lifecycle_event_fields` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_validate_lifecycle_histories` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `current_lifecycle` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `lifecycle_state_by_uid` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `set_lifecycle` | call | [knowledge_governance](../modules/knowledge_governance.md) | 1 |
