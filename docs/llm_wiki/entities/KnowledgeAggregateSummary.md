# KnowledgeAggregateSummary

**Location:** `src/llm_wiki_cli/services/knowledge_observability.py:225`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_observability](../modules/knowledge_observability.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Low-cardinality knowledge status safe for reports and local metrics.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `availability` | `str` | *required* | — |
| `reason` | `str` | *required* | — |
| `concepts_evaluated` | `int` | *required* | — |
| `freshness_counts` | `Mapping[str, int] \| None` | *required* | — |
| `evidence_issue_counts` | `Mapping[str, int] \| None` | *required* | — |
| `degraded_reason` | `str \| None` | *required* | — |
| `phase_durations_ms` | `Mapping[str, int \| None]` | *required* | — |
| `freshness_evaluated` | `bool` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_payload` | `() -> dict[str, object]` | — | — |
| `freshness` | `() -> str` | `@property` | Return the required user-facing freshness disclosure. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeAggregateSummary (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n1["KnowledgeLintSummary (src/llm_wiki_cli/services/lint_service.py)"]
    n2["summarize_knowledge_view (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n3["KnowledgeLintSummary.aggregate_payload (src/llm_wiki_cli/services/lint_service.py)"]
    n4["_safe_knowledge_summary (src/llm_wiki_cli/services/metrics.py)"]
    n5["record_validation_event (src/llm_wiki_cli/services/metrics.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/knowledge_observability.md"
    click n1 "../modules/lint_service.md"
    click n2 "../modules/knowledge_observability.md"
    click n3 "../modules/lint_service.md"
    click n4 "../modules/metrics.md"
    click n5 "../modules/metrics.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_observability](../modules/knowledge_observability.md) | 3 | `availability`, `concepts_evaluated`, `degraded_reason`, `evidence_issue_counts`, `freshness_counts`, `freshness_evaluated`, `phase_durations_ms`, `reason` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Subclass | `KnowledgeLintSummary` | [lint_service](../modules/lint_service.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `summarize_knowledge_view` | call | [knowledge_observability](../modules/knowledge_observability.md) |
| `summarize_knowledge_view` | type_reference | [knowledge_observability](../modules/knowledge_observability.md) |
| `KnowledgeLintSummary.aggregate_payload` | call | [lint_service](../modules/lint_service.md) |
| `_safe_knowledge_summary` | call | [metrics](../modules/metrics.md) |
| `_safe_knowledge_summary` | type_reference | [metrics](../modules/metrics.md) |
| `record_validation_event` | type_reference | [metrics](../modules/metrics.md) |
