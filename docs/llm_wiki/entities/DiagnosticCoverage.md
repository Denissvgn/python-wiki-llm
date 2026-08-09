# DiagnosticCoverage

**Location:** `src/llm_wiki_cli/services/verification_contracts.py:139`
**Kind:** Class
**Bases:** —
**Module:** [verification_contracts](../modules/verification_contracts.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Disclosure for deterministic diagnostic truncation.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `observed` | `int` | *required* | — |
| `emitted` | `int` | *required* | — |
| `omitted` | `int` | *required* | — |
| `limit` | `int` | `MAX_DIAGNOSTICS_PER_CHECK` | — |
| `truncated` | `bool` | `False` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_payload` | `() -> dict[str, int \| bool]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DiagnosticCoverage (src/llm_wiki_cli/services/verification_contracts.py)"]
    n1["_bounded_result (src/llm_wiki_cli/services/verification_contracts.py)"]
    n2["_parse_coverage (src/llm_wiki_cli/services/verification_contracts.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/verification_contracts.md"
    click n1 "../modules/verification_contracts.md"
    click n2 "../modules/verification_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [verification_contracts](../modules/verification_contracts.md) | 2 | `emitted`, `limit`, `observed`, `omitted`, `truncated` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_bounded_result` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_parse_coverage` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_parse_coverage` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
