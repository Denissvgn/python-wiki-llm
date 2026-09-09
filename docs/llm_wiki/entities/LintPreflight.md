# _LintPreflight

**Location:** `src/llm_wiki_cli/services/lint_service.py:340`
**Kind:** Class
**Bases:** —
**Module:** [lint_service](../modules/lint_service.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_LintPreflight` in `src/llm_wiki_cli/services/lint_service.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `team` | `TeamPolicyContext` | *required* | — |
| `selection_inputs` | `dict[str, object] \| None` | *required* | — |
| `manifest` | `SyncManifest \| None` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_LintPreflight (src/llm_wiki_cli/services/lint_service.py)"]
    n1["_preflight_lint_inputs (src/llm_wiki_cli/services/lint_service.py)"]
    n1 --> n0
    click n0 "../modules/lint_service.md"
    click n1 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [lint_service](../modules/lint_service.md) | 0 | `manifest`, `selection_inputs`, `team` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_preflight_lint_inputs` | call | [lint_service](../modules/lint_service.md) | 1 |
| `_preflight_lint_inputs` | type_reference | [lint_service](../modules/lint_service.md) | — |
