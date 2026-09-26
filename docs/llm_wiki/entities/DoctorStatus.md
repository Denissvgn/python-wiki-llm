# DoctorStatus

**Location:** `src/llm_wiki_cli/services/health_policy.py:14`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [health_policy](../modules/health_policy.md)

## Description

Closed overall health vocabulary for the doctor contract.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `HEALTHY` | `'healthy'` | — |
| `DEGRADED` | `'degraded'` | — |
| `UNHEALTHY` | `'unhealthy'` | — |
| `ABSENT` | `'absent'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DoctorStatus (src/llm_wiki_cli/services/health_policy.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/doctor_service.py"]
    n4["classify_health_sections (src/llm_wiki_cli/services/health_policy.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    click n0 "../modules/health_policy.md"
    click n3 "../modules/doctor_service.md"
    click n4 "../modules/health_policy.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [health_policy](../modules/health_policy.md) | 0 | `ABSENT`, `DEGRADED`, `HEALTHY`, `UNHEALTHY` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `doctor_service` | import | [doctor_service](../modules/doctor_service.md) | — |
| `classify_health_sections` | type_reference | [health_policy](../modules/health_policy.md) | — |
