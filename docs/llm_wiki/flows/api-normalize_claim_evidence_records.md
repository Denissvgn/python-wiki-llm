# normalize_claim_evidence_records

**Entry point:** `normalize_claim_evidence_records` (`api`)
**Source:** [documentation_claim_evidence](../modules/documentation_claim_evidence.md)
**Modules touched:** [documentation_claim_evidence](../modules/documentation_claim_evidence.md), [knowledge_graph](../modules/knowledge_graph.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as normalize_claim_evidence_records
    participant p1 as _object_array
    participant p2 as require_mapping_list
    participant p3 as require_list
    participant p4 as isinstance
    participant p5 as require_mapping
    participant p6 as encode
    participant p7 as DocumentationClaimEvidenceError
    participant p8 as tuple
    participant p9 as _normalize_claim_record
    participant p10 as _mapping
    participant p11 as _exact_fields
    participant p12 as require_exact_fields
    participant p13 as str
    participant p14 as set
    participant p15 as sorted
    participant p16 as invalid_error
    participant p17 as error_factory
    p0->>p1: _object_array
    p1->>p2: require_mapping_list
    p2->>p3: require_list
    p3-->>p4: isinstance
    p2->>p5: require_mapping
    p5-->>p4: isinstance
    p5-->>p4: isinstance
    p5-->>p6: encode
    p1->>p7: DocumentationClaimEvidenceError
    p1->>p7: DocumentationClaimEvidenceError
    p0-->>p8: tuple
    p0->>p9: _normalize_claim_record
    p9->>p10: _mapping
    p10->>p5: require_mapping
    p10->>p7: DocumentationClaimEvidenceError
    p9->>p11: _exact_fields
    p11->>p12: require_exact_fields
    p12-->>p4: isinstance
    p12-->>p13: str
    p12-->>p14: set
    p12-->>p14: set
    p12-->>p14: set
    p12-->>p8: tuple
    p12-->>p15: sorted
    p12-->>p8: tuple
    p12-->>p15: sorted
    p12-->>p16: invalid_error
    p12-->>p17: error_factory
    p11->>p7: DocumentationClaimEvidenceError
    p11->>p7: DocumentationClaimEvidenceError
```

> Call sequence diagram shows 30 of 257 interactions; 227 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. normalize_claim_evidence_records"]
    s2["2. _object_array"]
    s3["3. require_mapping_list"]
    s4["4. require_list"]
    s5["5. isinstance"]
    s6["6. require_mapping"]
    s7["7. isinstance"]
    s8["8. isinstance"]
    s9["9. encode"]
    s10["10. DocumentationClaimEvidenceError"]
    s11["11. DocumentationClaimEvidenceError"]
    s12["12. tuple"]
    s1 -->|"_object_array(value, 'claim_evidence')"| s2
    s2 -->|"require_mapping_list(value, error=DocumentationClaimEvidenceError(...), item_error=DocumentationClaimEvidenceError(...), require_string_keys=True)"| s3
    s3 -->|"require_list(value, error=error)"| s4
    s4 -. "isinstance(value, list)" .-> s5
    s3 -->|"require_mapping(item, error=..., require_string_keys=require_string_keys)"| s6
    s6 -. "isinstance(value, Mapping)" .-> s7
    s6 -. "isinstance(key, str)" .-> s8
    s6 -. "key.encode('utf-8')" .-> s9
    s2 -->|"DocumentationClaimEvidenceError(...)"| s10
    s2 -->|"DocumentationClaimEvidenceError(...)"| s11
    s1 -. "tuple(...)" .-> s12
    click s1 "../modules/documentation_claim_evidence.md"
    click s2 "../modules/documentation_claim_evidence.md"
    click s3 "../modules/validation.md"
    click s4 "../modules/validation.md"
    click s6 "../modules/validation.md"
    click s10 "../modules/documentation_claim_evidence.md"
    click s11 "../modules/documentation_claim_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `normalize_claim_evidence_records` | `value: object` | - | - | `tuple(...)` |
| `_object_array` | `value: object`, `field_name: str` | - | - | `require_mapping_list(...)` |
| `require_mapping_list` | `value: object`, `error: Exception`, `item_error: Exception \| None`, `require_string_keys: bool` | - | - | `items` |
| `require_list` | `value: object`, `error: Exception` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `DocumentationClaimEvidenceError` | - | - | - | - |
| `DocumentationClaimEvidenceError` | - | - | - | - |
| `tuple` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| normalize_claim_evidence_records | _object_array | 192 | `_object_array(value, 'claim_evidence')` |
| _object_array | require_mapping_list | 1431 | `require_mapping_list(value, error=DocumentationClaimEvidenceError(...), item_error=DocumentationClaimEvidenceError(...), require_string_keys=True)` |
| require_mapping_list | require_list | 1015 | `require_list(value, error=error)` |
| require_list | isinstance | 764 | `isinstance(value, list)` |
| require_mapping_list | require_mapping | 1017 | `require_mapping(item, error=..., require_string_keys=require_string_keys)` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance | 731 | `isinstance(key, str)` |
| require_mapping | encode | 736 | `key.encode('utf-8')` |
| _object_array | DocumentationClaimEvidenceError | 1433 | `DocumentationClaimEvidenceError(...)` |
| _object_array | DocumentationClaimEvidenceError | 1434 | `DocumentationClaimEvidenceError(...)` |
| normalize_claim_evidence_records | tuple | 193 | `tuple(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_list` | `isinstance` | 764 |
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `normalize_claim_evidence_records` | `first 12 steps` | 0 |
| truncated_flow | `normalize_claim_evidence_records` | `depth limit` | 0 |

## Behavior

This flow starts at `normalize_claim_evidence_records` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
