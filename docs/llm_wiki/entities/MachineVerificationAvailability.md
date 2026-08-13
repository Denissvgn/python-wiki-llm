# MachineVerificationAvailability

**Location:** `src/llm_wiki_cli/services/knowledge_consumption.py:74`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_consumption](../modules/knowledge_consumption.md)

## Description

Whether the read session evaluated a disposable machine receipt.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `NOT_EVALUATED` | `'not-evaluated'` | — |
| `ABSENT` | `'absent'` | — |
| `INVALID` | `'invalid'` | — |
| `RECORDED` | `'recorded'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MachineVerificationAvailability (src/llm_wiki_cli/services/knowledge_consumption.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/doctor_service.py"]
    n4["src/llm_wiki_cli/services/knowledge_projection.py"]
    n5["src/llm_wiki_cli/services/knowledge_verification.py"]
    n6["src/llm_wiki_cli/services/lint_service.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/knowledge_consumption.md"
    click n3 "../modules/doctor_service.md"
    click n4 "../modules/knowledge_projection.md"
    click n5 "../modules/knowledge_verification.md"
    click n6 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_consumption](../modules/knowledge_consumption.md) | 0 | `ABSENT`, `INVALID`, `NOT_EVALUATED`, `RECORDED` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `doctor_service` | import | [doctor_service](../modules/doctor_service.md) | — |
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `knowledge_verification` | import | [knowledge_verification](../modules/knowledge_verification.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
