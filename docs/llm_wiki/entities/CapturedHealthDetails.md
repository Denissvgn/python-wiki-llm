# CapturedHealthDetails

**Location:** `src/llm_wiki_cli/services/health_details.py:33`
**Kind:** Class
**Bases:** —
**Module:** [health_details](../modules/health_details.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

An immutable capture with independently owned output dictionaries.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `encoded` | `str` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_payload` | `() -> dict[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["CapturedHealthDetails (src/llm_wiki_cli/services/health_details.py)"]
    n1["src/llm_wiki_cli/services/doctor_service.py"]
    n2["capture_health_details (src/llm_wiki_cli/services/health_details.py)"]
    n3["src/llm_wiki_cli/services/lint_service.py"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/health_details.md"
    click n1 "../modules/doctor_service.md"
    click n2 "../modules/health_details.md"
    click n3 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [health_details](../modules/health_details.md) | 1 | `encoded` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `doctor_service` | import | [doctor_service](../modules/doctor_service.md) | — |
| `capture_health_details` | call | [health_details](../modules/health_details.md) | 1 |
| `capture_health_details` | type_reference | [health_details](../modules/health_details.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
