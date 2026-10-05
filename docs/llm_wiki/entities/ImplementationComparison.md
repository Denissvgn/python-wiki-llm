# ImplementationComparison

**Location:** `src/llm_wiki_cli/services/implementation_evidence.py:714`
**Kind:** Class
**Bases:** —
**Module:** [implementation_evidence](../modules/implementation_evidence.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `ImplementationComparison` in `src/llm_wiki_cli/services/implementation_evidence.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `state` | `str` | *required* | — |
| `reason` | `str` | *required* | — |
| `coordinate` | `Mapping \| None` | `None` | — |
| `scope` | `str \| None` | `None` | — |
| `analysis_scope` | `str` | `'snapshot'` | — |
| `live_comparison_performed` | `bool` | `False` | — |
| `source_changed` | `bool \| None` | `None` | — |
| `documentation_changed` | `bool \| None` | `None` | — |
| `recorded` | `Mapping \| None` | `None` | — |
| `live` | `Mapping \| None` | `None` | — |
| `truncated` | `bool` | `False` | — |
| `limitations` | `tuple[str, ...]` | `LIMITATIONS` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `()` | — | — |
| `to_payload` | `() -> dict` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ImplementationComparison (src/llm_wiki_cli/services/implementation_evidence.py)"]
    n1["compact_implementation_summary (src/llm_wiki_cli/services/implementation_evidence.py)"]
    n2["compare_implementation_observations (src/llm_wiki_cli/services/implementation_evidence.py)"]
    n3["compare_knowledge_implementation (src/llm_wiki_cli/services/implementation_evidence.py)"]
    n4["select_implementation_comparison (src/llm_wiki_cli/services/implementation_evidence.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/implementation_evidence.md"
    click n1 "../modules/implementation_evidence.md"
    click n2 "../modules/implementation_evidence.md"
    click n3 "../modules/implementation_evidence.md"
    click n4 "../modules/implementation_evidence.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [implementation_evidence](../modules/implementation_evidence.md) | 2 | `analysis_scope`, `coordinate`, `documentation_changed`, `limitations`, `live`, `live_comparison_performed`, `reason`, `recorded`, `scope`, `source_changed`, `state`, `truncated` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `compact_implementation_summary` | type_reference | [implementation_evidence](../modules/implementation_evidence.md) | — |
| `compare_implementation_observations` | call | [implementation_evidence](../modules/implementation_evidence.md) | 1 |
| `compare_implementation_observations` | type_reference | [implementation_evidence](../modules/implementation_evidence.md) | — |
| `compare_knowledge_implementation` | call | [implementation_evidence](../modules/implementation_evidence.md) | 4 |
| `select_implementation_comparison` | call | [implementation_evidence](../modules/implementation_evidence.md) | 2 |
| `select_implementation_comparison` | type_reference | [implementation_evidence](../modules/implementation_evidence.md) | — |
