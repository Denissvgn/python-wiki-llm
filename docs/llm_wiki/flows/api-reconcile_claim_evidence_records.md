# reconcile_claim_evidence_records

**Entry point:** `reconcile_claim_evidence_records` (`api`)
**Source:** [documentation_claim_evidence](../modules/documentation_claim_evidence.md)
**Modules touched:** [documentation_claim_evidence](../modules/documentation_claim_evidence.md), [knowledge_graph](../modules/knowledge_graph.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as reconcile_claim_evidence_records
    participant p1 as _normalize_claim_record
    participant p2 as _mapping
    participant p3 as require_mapping
    participant p4 as isinstance
    participant p5 as encode
    participant p6 as DocumentationClaimEvidenceError
    participant p7 as _exact_fields
    participant p8 as require_exact_fields
    participant p9 as str
    participant p10 as set
    participant p11 as tuple
    participant p12 as sorted
    participant p13 as invalid_error
    participant p14 as error_factory
    participant p15 as _portable_path
    participant p16 as _text
    participant p17 as require_trimmed_text
    participant p18 as require_nonempty_text
    participant p19 as strip
    p0->>p1: _normalize_claim_record
    p1->>p2: _mapping
    p2->>p3: require_mapping
    p3-->>p4: isinstance
    p3-->>p4: isinstance
    p3-->>p5: encode
    p2->>p6: DocumentationClaimEvidenceError
    p1->>p7: _exact_fields
    p7->>p8: require_exact_fields
    p8-->>p4: isinstance
    p8-->>p9: str
    p8-->>p10: set
    p8-->>p10: set
    p8-->>p10: set
    p8-->>p11: tuple
    p8-->>p12: sorted
    p8-->>p11: tuple
    p8-->>p12: sorted
    p8-->>p13: invalid_error
    p8-->>p14: error_factory
    p7->>p6: DocumentationClaimEvidenceError
    p7->>p6: DocumentationClaimEvidenceError
    p7->>p6: DocumentationClaimEvidenceError
    p1->>p6: DocumentationClaimEvidenceError
    p1->>p15: _portable_path
    p15->>p16: _text
    p16->>p17: require_trimmed_text
    p17->>p18: require_nonempty_text
    p18-->>p4: isinstance
    p18-->>p19: strip
```

> Call sequence diagram shows 30 of 331 interactions; 301 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. reconcile_claim_evidence_records"]
    s2["2. _normalize_claim_record"]
    s3["3. _mapping"]
    s4["4. require_mapping"]
    s5["5. isinstance"]
    s6["6. isinstance"]
    s7["7. encode"]
    s8["8. DocumentationClaimEvidenceError"]
    s9["9. _exact_fields"]
    s10["10. require_exact_fields"]
    s11["11. isinstance"]
    s12["12. str"]
    s1 -->|"_normalize_claim_record(raw, 'claim_evidence')"| s2
    s2 -->|"_mapping(value, field_name)"| s3
    s3 -->|"require_mapping(value, error=DocumentationClaimEvidenceError(...), require_string_keys=True)"| s4
    s4 -. "isinstance(value, Mapping)" .-> s5
    s4 -. "isinstance(key, str)" .-> s6
    s4 -. "key.encode('utf-8')" .-> s7
    s3 -->|"DocumentationClaimEvidenceError(...)"| s8
    s2 -->|"_exact_fields(record, _CLAIM_FIELDS, _CLAIM_REQUIRED, field_name)"| s9
    s9 -->|"require_exact_fields(value, allowed=allowed, required=required, mapping_error=DocumentationClaimEvidenceError(...), missing_error=..., unknown_error=...)"| s10
    s10 -. "isinstance(value, Mapping)" .-> s11
    s10 -. "str(key)" .-> s12
    b0["mutation legacy_freshness.pop"]
    s1 -. "mutation legacy_freshness.pop" .-> b0
    b1["mutation reconciled.append"]
    s1 -. "mutation reconciled.append" .-> b1
    click s1 "../modules/documentation_claim_evidence.md"
    click s2 "../modules/documentation_claim_evidence.md"
    click s3 "../modules/documentation_claim_evidence.md"
    click s4 "../modules/validation.md"
    click s8 "../modules/documentation_claim_evidence.md"
    click s9 "../modules/documentation_claim_evidence.md"
    click s10 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `reconcile_claim_evidence_records` | `records: Iterable[Mapping[str, Any]]`, `service: DocumentationGraphQueryService` | `Mapping`, `_CLAIM_FIELDS` | - | `tuple(...)` |
| `_normalize_claim_record` | `value: object`, `field_name: str` | `_CLAIM_FIELDS`, `_CLAIM_REQUIRED`, `CLAIM_EVIDENCE_SCHEMA_VERSION`, `_RESOLUTIONS`, `CLAIM_EVIDENCE_SCHEMA_VERSION` | - | `{...}` |
| `_mapping` | `value: object`, `field_name: str` | - | - | `require_mapping(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `DocumentationClaimEvidenceError` | - | - | - | - |
| `_exact_fields` | `value: Mapping[str, Any]`, `allowed: frozenset[str]`, `required: frozenset[str]`, `field_name: str` | - | - | `require_exact_fields(...)` |
| `require_exact_fields` | `value: object`, `allowed: Iterable[str]`, `required: Iterable[str]`, `mapping_error: Exception`, `missing_error: _ErrorFactory`, `unknown_error: _ErrorFactory`, `invalid_error: Callable[[tuple[str, ...], tuple[str, ...]], Exception] \| None`, `stringify_keys: bool` | `Mapping` | - | - |
| `isinstance` | - | - | - | - |
| `str` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| reconcile_claim_evidence_records | _normalize_claim_record | 400 | `_normalize_claim_record(raw, 'claim_evidence')` |
| _normalize_claim_record | _mapping | 592 | `_mapping(value, field_name)` |
| _mapping | require_mapping | 1423 | `require_mapping(value, error=DocumentationClaimEvidenceError(...), require_string_keys=True)` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance | 731 | `isinstance(key, str)` |
| require_mapping | encode | 736 | `key.encode('utf-8')` |
| _mapping | DocumentationClaimEvidenceError | 1425 | `DocumentationClaimEvidenceError(...)` |
| _normalize_claim_record | _exact_fields | 593 | `_exact_fields(record, _CLAIM_FIELDS, _CLAIM_REQUIRED, field_name)` |
| _exact_fields | require_exact_fields | 1447 | `require_exact_fields(value, allowed=allowed, required=required, mapping_error=DocumentationClaimEvidenceError(...), missing_error=..., unknown_error=...)` |
| require_exact_fields | isinstance | 1205 | `isinstance(value, Mapping)` |
| require_exact_fields | str | 1207 | `str(key)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `legacy_freshness.pop` | `reconcile_claim_evidence_records` | 418 |
| mutation | `reconciled.append` | `reconcile_claim_evidence_records` | 433 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| unresolved_call | `require_exact_fields` | `isinstance` | 1205 |
| step_limit | `reconcile_claim_evidence_records` | `first 12 steps` | 0 |
| truncated_flow | `reconcile_claim_evidence_records` | `depth limit` | 0 |

## Behavior

This flow starts at `reconcile_claim_evidence_records` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
