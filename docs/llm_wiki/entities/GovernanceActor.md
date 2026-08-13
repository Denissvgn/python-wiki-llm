# GovernanceActor

**Location:** `src/llm_wiki_cli/services/knowledge_governance.py:143`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_governance](../modules/knowledge_governance.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Explicit event author; never inferred from Git metadata.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `kind` | `str` | *required* | — |
| `actor_id` | `str` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_payload` | `() -> dict[str, str]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["GovernanceActor (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n1["_lifecycle_mutation (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n2["_actor (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n3["_parse_actor (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n4["add_review_event (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n5["set_lifecycle (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/knowledge_governance.md"
    click n1 "../modules/knowledge_cmd.md"
    click n2 "../modules/knowledge_governance.md"
    click n3 "../modules/knowledge_governance.md"
    click n4 "../modules/knowledge_governance.md"
    click n5 "../modules/knowledge_governance.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_governance](../modules/knowledge_governance.md) | 1 | `actor_id`, `kind` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_lifecycle_mutation` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 1 |
| `_actor` | call | [knowledge_governance](../modules/knowledge_governance.md) | 1 |
| `_actor` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_parse_actor` | call | [knowledge_governance](../modules/knowledge_governance.md) | 1 |
| `_parse_actor` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `add_review_event` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `set_lifecycle` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
