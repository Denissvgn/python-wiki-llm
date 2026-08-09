# preflight_runtime_capture_records

**Entry point:** `preflight_runtime_capture_records` (`api`)
**Source:** [documentation_claim_evidence](../modules/documentation_claim_evidence.md)
**Modules touched:** [documentation_claim_evidence](../modules/documentation_claim_evidence.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as preflight_runtime_capture_records
    participant p1 as resolve
    participant p2 as Path
    participant p3 as _normalize_capture_record
    participant p4 as _mapping
    participant p5 as require_mapping
    participant p6 as isinstance
    participant p7 as encode
    participant p8 as DocumentationClaimEvidenceError
    participant p9 as _exact_fields
    participant p10 as require_exact_fields
    participant p11 as str
    participant p12 as set
    participant p13 as tuple
    participant p14 as sorted
    participant p15 as invalid_error
    participant p16 as error_factory
    participant p17 as _capture_result
    participant p18 as frozenset
    p0-->>p1: resolve
    p0-->>p2: Path
    p0->>p3: _normalize_capture_record
    p3->>p4: _mapping
    p4->>p5: require_mapping
    p5-->>p6: isinstance
    p5-->>p6: isinstance
    p5-->>p7: encode
    p4->>p8: DocumentationClaimEvidenceError
    p3->>p9: _exact_fields
    p9->>p10: require_exact_fields
    p10-->>p6: isinstance
    p10-->>p11: str
    p10-->>p12: set
    p10-->>p12: set
    p10-->>p12: set
    p10-->>p13: tuple
    p10-->>p14: sorted
    p10-->>p13: tuple
    p10-->>p14: sorted
    p10-->>p15: invalid_error
    p10-->>p16: error_factory
    p9->>p8: DocumentationClaimEvidenceError
    p9->>p8: DocumentationClaimEvidenceError
    p9->>p8: DocumentationClaimEvidenceError
    p3->>p8: DocumentationClaimEvidenceError
    p3->>p17: _capture_result
    p17->>p4: _mapping
    p17->>p9: _exact_fields
    p17-->>p18: frozenset
```

> Call sequence diagram shows 30 of 232 interactions; 202 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. preflight_runtime_capture_records"]
    s2["2. resolve"]
    s3["3. Path"]
    s4["4. _normalize_capture_record"]
    s5["5. _mapping"]
    s6["6. require_mapping"]
    s7["7. isinstance"]
    s8["8. isinstance"]
    s9["9. encode"]
    s10["10. DocumentationClaimEvidenceError"]
    s11["11. _exact_fields"]
    s12["12. require_exact_fields"]
    s1 -. "Path(wiki_root).resolve(data not statically known)" .-> s2
    s1 -. "Path(wiki_root)" .-> s3
    s1 -->|"_normalize_capture_record(raw, 'runtime_captures')"| s4
    s4 -->|"_mapping(value, field_name)"| s5
    s5 -->|"require_mapping(value, error=DocumentationClaimEvidenceError(...), require_string_keys=True)"| s6
    s6 -. "isinstance(value, Mapping)" .-> s7
    s6 -. "isinstance(key, str)" .-> s8
    s6 -. "key.encode('utf-8')" .-> s9
    s5 -->|"DocumentationClaimEvidenceError(...)"| s10
    s4 -->|"_exact_fields(record, _CAPTURE_FIELDS, _CAPTURE_REQUIRED, field_name)"| s11
    s11 -->|"require_exact_fields(value, allowed=allowed, required=required, mapping_error=DocumentationClaimEvidenceError(...), missing_error=..., unknown_error=...)"| s12
    b0["mutation checked.append"]
    s1 -. "mutation checked.append" .-> b0
    click s1 "../modules/documentation_claim_evidence.md"
    click s4 "../modules/documentation_claim_evidence.md"
    click s5 "../modules/documentation_claim_evidence.md"
    click s6 "../modules/validation.md"
    click s10 "../modules/documentation_claim_evidence.md"
    click s11 "../modules/documentation_claim_evidence.md"
    click s12 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `preflight_runtime_capture_records` | `records: Iterable[Mapping[str, Any]]`, `wiki_root: str \| Path` | - | - | `tuple(...)` |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `_normalize_capture_record` | `value: object`, `field_name: str` | `_CAPTURE_FIELDS`, `_CAPTURE_REQUIRED`, `RUNTIME_CAPTURE_SCHEMA_VERSION`, `RUNTIME_CAPTURE_SCHEMA_VERSION`, `_UNINSPECTED_MEDIA_SUFFIXES`, `_UNINSPECTED_MEDIA_LIMITATIONS` | - | `normalized` |
| `_mapping` | `value: object`, `field_name: str` | - | - | `require_mapping(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `DocumentationClaimEvidenceError` | - | - | - | - |
| `_exact_fields` | `value: Mapping[str, Any]`, `allowed: frozenset[str]`, `required: frozenset[str]`, `field_name: str` | - | - | `require_exact_fields(...)` |
| `require_exact_fields` | `value: object`, `allowed: Iterable[str]`, `required: Iterable[str]`, `mapping_error: Exception`, `missing_error: _ErrorFactory`, `unknown_error: _ErrorFactory`, `invalid_error: Callable[[tuple[str, ...], tuple[str, ...]], Exception] \| None`, `stringify_keys: bool` | `Mapping` | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| preflight_runtime_capture_records | resolve | 537 | `Path(wiki_root).resolve(data not statically known)` |
| preflight_runtime_capture_records | Path | 537 | `Path(wiki_root)` |
| preflight_runtime_capture_records | _normalize_capture_record | 540 | `_normalize_capture_record(raw, 'runtime_captures')` |
| _normalize_capture_record | _mapping | 650 | `_mapping(value, field_name)` |
| _mapping | require_mapping | 1423 | `require_mapping(value, error=DocumentationClaimEvidenceError(...), require_string_keys=True)` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance | 731 | `isinstance(key, str)` |
| require_mapping | encode | 736 | `key.encode('utf-8')` |
| _mapping | DocumentationClaimEvidenceError | 1425 | `DocumentationClaimEvidenceError(...)` |
| _normalize_capture_record | _exact_fields | 651 | `_exact_fields(record, _CAPTURE_FIELDS, _CAPTURE_REQUIRED, field_name)` |
| _exact_fields | require_exact_fields | 1447 | `require_exact_fields(value, allowed=allowed, required=required, mapping_error=DocumentationClaimEvidenceError(...), missing_error=..., unknown_error=...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `checked.append` | `preflight_runtime_capture_records` | 542 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `preflight_runtime_capture_records` | `Path(wiki_root).resolve` | 537 |
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `preflight_runtime_capture_records` | `first 12 steps` | 0 |
| truncated_flow | `preflight_runtime_capture_records` | `depth limit` | 0 |

## Behavior

This flow starts at `preflight_runtime_capture_records` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
