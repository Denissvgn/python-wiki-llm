# SnapshotKnowledgeObservability

**Location:** `src/llm_wiki_cli/services/knowledge_observability.py:389`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_observability](../modules/knowledge_observability.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One snapshot-only read view and its aggregate operational summary.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `view` | `KnowledgeReadView` | *required* | — |
| `summary` | `KnowledgeAggregateSummary` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SnapshotKnowledgeObservability (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n1["_snapshot_result (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n2["load_snapshot_knowledge_observability (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/knowledge_observability.md"
    click n1 "../modules/knowledge_observability.md"
    click n2 "../modules/knowledge_observability.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_observability](../modules/knowledge_observability.md) | 0 | `summary`, `view` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_snapshot_result` | call | [knowledge_observability](../modules/knowledge_observability.md) |
| `_snapshot_result` | type_reference | [knowledge_observability](../modules/knowledge_observability.md) |
| `load_snapshot_knowledge_observability` | type_reference | [knowledge_observability](../modules/knowledge_observability.md) |
