# VerificationCheckResult

**Location:** `src/llm_wiki_cli/services/verification_contracts.py:187`
**Kind:** Class
**Bases:** —
**Module:** [verification_contracts](../modules/verification_contracts.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Normalized output from one application-owned checker.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `checker_id` | `str` | *required* | — |
| `checker_version` | `str` | *required* | — |
| `result` | `VerificationResult` | *required* | — |
| `diagnostics` | `tuple[VerificationDiagnostic, ...]` | `()` | — |
| `diagnostic_coverage` | `DiagnosticCoverage` | `field(default_factory=lambda: DiagnosticCoverage(observed=0, emitted=0, omitted=0))` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_payload` | `() -> dict[str, object]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["VerificationCheckResult (src/llm_wiki_cli/services/verification_contracts.py)"]
    n1["_artifact_integrity_checker (src/llm_wiki_cli/services/verification_contracts.py)"]
    n2["_bounded_result (src/llm_wiki_cli/services/verification_contracts.py)"]
    n3["_internal_links_checker (src/llm_wiki_cli/services/verification_contracts.py)"]
    n4["_parse_check (src/llm_wiki_cli/services/verification_contracts.py)"]
    n5["build_verification_receipt (src/llm_wiki_cli/services/verification_contracts.py)"]
    n6["CheckerContract.run (src/llm_wiki_cli/services/verification_contracts.py)"]
    n7["run_verification (src/llm_wiki_cli/services/verification_contracts.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/verification_contracts.md"
    click n1 "../modules/verification_contracts.md"
    click n2 "../modules/verification_contracts.md"
    click n3 "../modules/verification_contracts.md"
    click n4 "../modules/verification_contracts.md"
    click n5 "../modules/verification_contracts.md"
    click n6 "../modules/verification_contracts.md"
    click n7 "../modules/verification_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [verification_contracts](../modules/verification_contracts.md) | 2 | `checker_id`, `checker_version`, `diagnostic_coverage`, `diagnostics`, `result` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_artifact_integrity_checker` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `_bounded_result` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_bounded_result` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `_internal_links_checker` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `_parse_check` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_parse_check` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `build_verification_receipt` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `CheckerContract.run` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `run_verification` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
