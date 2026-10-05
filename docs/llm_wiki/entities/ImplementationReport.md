# ImplementationReport

**Location:** `src/llm_wiki_cli/services/implementation_evidence.py:739`
**Kind:** Class
**Bases:** —
**Module:** [implementation_evidence](../modules/implementation_evidence.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `ImplementationReport` in `src/llm_wiki_cli/services/implementation_evidence.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `by_locator` | `Mapping[str, ImplementationComparison]` | *required* | — |
| `by_coordinate` | `Mapping[str, ImplementationComparison]` | *required* | — |
| `analysis_scope` | `str` | `'snapshot'` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `()` | — | — |
| `to_payload` | `() -> dict` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ImplementationReport (src/llm_wiki_cli/services/implementation_evidence.py)"]
    n1["compare_knowledge_implementation (src/llm_wiki_cli/services/implementation_evidence.py)"]
    n2["select_implementation_comparison (src/llm_wiki_cli/services/implementation_evidence.py)"]
    n3["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/implementation_evidence.md"
    click n1 "../modules/implementation_evidence.md"
    click n2 "../modules/implementation_evidence.md"
    click n3 "../modules/knowledge_consumption.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [implementation_evidence](../modules/implementation_evidence.md) | 2 | `analysis_scope`, `by_coordinate`, `by_locator` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `compare_knowledge_implementation` | call | [implementation_evidence](../modules/implementation_evidence.md) | 1 |
| `compare_knowledge_implementation` | type_reference | [implementation_evidence](../modules/implementation_evidence.md) | — |
| `select_implementation_comparison` | type_reference | [implementation_evidence](../modules/implementation_evidence.md) | — |
| `knowledge_consumption` | import | [knowledge_consumption](../modules/knowledge_consumption.md) | — |
