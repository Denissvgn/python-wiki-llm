# LintIssue

**Location:** `src/llm_wiki_cli/services/lint_service.py:219`
**Kind:** Class
**Bases:** —
**Module:** [lint_service](../modules/lint_service.md)

**Decorators:** `@dataclass`

## Description

_Auto-generated from `LintIssue` in `src/llm_wiki_cli/services/lint_service.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `category` | `str` | *required* | — |
| `message` | `str` | *required* | — |
| `severity` | `str` | `'error'` | — |
| `path` | `str \| None` | `None` | — |
| `target` | `str \| None` | `None` | — |
| `reason_code` | `str \| None` | `None` | — |
| `hint` | `str \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["LintIssue (src/llm_wiki_cli/services/lint_service.py)"]
    n1["_diagnostic_freshness_states (src/llm_wiki_cli/services/doctor_service.py)"]
    n2["_diagnostic_reasons (src/llm_wiki_cli/services/doctor_service.py)"]
    n3["_issues (src/llm_wiki_cli/services/doctor_service.py)"]
    n4["_reasons (src/llm_wiki_cli/services/doctor_service.py)"]
    n5["_add (src/llm_wiki_cli/services/lint_service.py)"]
    n6["_coerce_plugin_issue (src/llm_wiki_cli/services/lint_service.py)"]
    n7["_diagnose (src/llm_wiki_cli/services/lint_service.py)"]
    n8["_lint_issue_payload (src/llm_wiki_cli/services/lint_service.py)"]
    n9["LintReport.by_category (src/llm_wiki_cli/services/lint_service.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/lint_service.md"
    click n1 "../modules/doctor_service.md"
    click n2 "../modules/doctor_service.md"
    click n3 "../modules/doctor_service.md"
    click n4 "../modules/doctor_service.md"
    click n5 "../modules/lint_service.md"
    click n6 "../modules/lint_service.md"
    click n7 "../modules/lint_service.md"
    click n8 "../modules/lint_service.md"
    click n9 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [lint_service](../modules/lint_service.md) | 0 | `category`, `hint`, `message`, `path`, `reason_code`, `severity`, `target` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_diagnostic_freshness_states` | type_reference | [doctor_service](../modules/doctor_service.md) |
| `_diagnostic_reasons` | type_reference | [doctor_service](../modules/doctor_service.md) |
| `_issues` | type_reference | [doctor_service](../modules/doctor_service.md) |
| `_reasons` | type_reference | [doctor_service](../modules/doctor_service.md) |
| `_add` | call | [lint_service](../modules/lint_service.md) |
| `_coerce_plugin_issue` | call | [lint_service](../modules/lint_service.md) |
| `_coerce_plugin_issue` | call | [lint_service](../modules/lint_service.md) |
| `_coerce_plugin_issue` | type_reference | [lint_service](../modules/lint_service.md) |
| `_diagnose` | call | [lint_service](../modules/lint_service.md) |
| `_lint_issue_payload` | type_reference | [lint_service](../modules/lint_service.md) |
| `LintReport.by_category` | type_reference | [lint_service](../modules/lint_service.md) |
