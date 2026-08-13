# KnowledgePhaseDurations

**Location:** `src/llm_wiki_cli/services/knowledge_observability.py:194`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_observability](../modules/knowledge_observability.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Operational phase durations in milliseconds.

``None`` means that a phase was not run.  In particular, snapshot-only
status must not fabricate zero-duration evaluation or check phases.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `load_ms` | `int \| None` | `None` | — |
| `evaluate_ms` | `int \| None` | `None` | — |
| `check_ms` | `int \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_payload` | `() -> dict[str, int \| None]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgePhaseDurations (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n1["_snapshot_result (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n2["_validated_phase_durations (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n3["summarize_knowledge_view (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n4["_run_report_checks (src/llm_wiki_cli/services/lint_service.py)"]
    n5["_set_knowledge_summary (src/llm_wiki_cli/services/lint_service.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/knowledge_observability.md"
    click n1 "../modules/knowledge_observability.md"
    click n2 "../modules/knowledge_observability.md"
    click n3 "../modules/knowledge_observability.md"
    click n4 "../modules/lint_service.md"
    click n5 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_observability](../modules/knowledge_observability.md) | 2 | `check_ms`, `evaluate_ms`, `load_ms` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_snapshot_result` | call | [knowledge_observability](../modules/knowledge_observability.md) | 1 |
| `_validated_phase_durations` | call | [knowledge_observability](../modules/knowledge_observability.md) | 1 |
| `summarize_knowledge_view` | call | [knowledge_observability](../modules/knowledge_observability.md) | 1 |
| `summarize_knowledge_view` | type_reference | [knowledge_observability](../modules/knowledge_observability.md) | — |
| `_run_report_checks` | call | [lint_service](../modules/lint_service.md) | 1 |
| `_set_knowledge_summary` | type_reference | [lint_service](../modules/lint_service.md) | — |
