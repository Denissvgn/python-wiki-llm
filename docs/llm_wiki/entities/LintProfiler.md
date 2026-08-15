# _LintProfiler

**Location:** `src/llm_wiki_cli/services/lint_service.py:182`
**Kind:** Class
**Bases:** —
**Module:** [lint_service](../modules/lint_service.md)

## Description

_Auto-generated from `_LintProfiler` in `src/llm_wiki_cli/services/lint_service.py`._

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `() -> None` | — | — |
| `phase` | `(name: str) -> Iterator[None]` | `@contextmanager` | — |
| `to_dict` | `() -> dict` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_LintProfiler (src/llm_wiki_cli/services/lint_service.py)"]
    n1["_collect_lint_inputs (src/llm_wiki_cli/services/lint_service.py)"]
    n2["_profile_phase (src/llm_wiki_cli/services/lint_service.py)"]
    n3["_profile_report_to_dict (src/llm_wiki_cli/services/lint_service.py)"]
    n4["_run_report_checks (src/llm_wiki_cli/services/lint_service.py)"]
    n5["build_report (src/llm_wiki_cli/services/lint_service.py)"]
    n6["run (src/llm_wiki_cli/services/lint_service.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/lint_service.md"
    click n1 "../modules/lint_service.md"
    click n2 "../modules/lint_service.md"
    click n3 "../modules/lint_service.md"
    click n4 "../modules/lint_service.md"
    click n5 "../modules/lint_service.md"
    click n6 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [lint_service](../modules/lint_service.md) | 3 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_collect_lint_inputs` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `_profile_phase` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `_profile_report_to_dict` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `_run_report_checks` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `build_report` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `run` | call | [lint_service](../modules/lint_service.md) | 1 |
