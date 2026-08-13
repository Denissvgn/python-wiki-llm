# _KnowledgeLintState

**Location:** `src/llm_wiki_cli/services/lint_service.py:327`
**Kind:** Class
**Bases:** —
**Module:** [lint_service](../modules/lint_service.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_KnowledgeLintState` in `src/llm_wiki_cli/services/lint_service.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `enabled` | `bool` | `False` | — |
| `load_result` | `KnowledgeLoadResult \| None` | `None` | — |
| `view` | `KnowledgeReadView \| None` | `None` | — |
| `load_issues` | `tuple[KnowledgeLoadIssue, ...]` | `()` | — |
| `freshness_error_field` | `str \| None` | `None` | — |
| `freshness_error_message` | `str \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_KnowledgeLintState (src/llm_wiki_cli/services/lint_service.py)"]
    n1["_check_knowledge_lint (src/llm_wiki_cli/services/lint_service.py)"]
    n2["_evaluate_knowledge_lint_state (src/llm_wiki_cli/services/lint_service.py)"]
    n3["_load_knowledge_lint_state (src/llm_wiki_cli/services/lint_service.py)"]
    n4["_run_report_checks (src/llm_wiki_cli/services/lint_service.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/lint_service.md"
    click n1 "../modules/lint_service.md"
    click n2 "../modules/lint_service.md"
    click n3 "../modules/lint_service.md"
    click n4 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [lint_service](../modules/lint_service.md) | 0 | `enabled`, `freshness_error_field`, `freshness_error_message`, `load_issues`, `load_result`, `view` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_check_knowledge_lint` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `_evaluate_knowledge_lint_state` | call | [lint_service](../modules/lint_service.md) | 3 |
| `_evaluate_knowledge_lint_state` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `_load_knowledge_lint_state` | call | [lint_service](../modules/lint_service.md) | 4 |
| `_load_knowledge_lint_state` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `_run_report_checks` | call | [lint_service](../modules/lint_service.md) | 1 |
