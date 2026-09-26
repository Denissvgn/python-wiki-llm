# HealthDetailsError

**Location:** `src/llm_wiki_cli/services/health_contract.py:38`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [health_contract](../modules/health_contract.md)

## Description

Detailed health data is incomplete, unsupported or inconsistent.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["HealthDetailsError (src/llm_wiki_cli/services/health_contract.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/ci_report.py"]
    n3["_fail (src/llm_wiki_cli/services/health_contract.py)"]
    n4["capture_health_details (src/llm_wiki_cli/services/health_details.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/health_contract.md"
    click n2 "../modules/ci_report.md"
    click n3 "../modules/health_contract.md"
    click n4 "../modules/health_details.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [health_contract](../modules/health_contract.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `ci_report` | import | [ci_report](../modules/ci_report.md) | — |
| `_fail` | call | [health_contract](../modules/health_contract.md) | 1 |
| `capture_health_details` | call | [health_details](../modules/health_details.md) | 2 |
