# validate_verification_receipt

**Entry point:** `validate_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_verification_receipt
    participant p1 as isinstance
    participant p2 as _receipt_to_payload
    participant p3 as dict
    participant p4 as to_payload
    participant p5 as _object
    participant p6 as require_mapping
    participant p7 as encode
    participant p8 as VerificationReceiptError
    participant p9 as _exact_fields
    participant p10 as set
    participant p11 as require_exact_fields
    participant p12 as str
    participant p13 as tuple
    participant p14 as sorted
    participant p15 as invalid_error
    participant p16 as error_factory
    participant p17 as _string
    p0-->>p1: isinstance
    p0->>p2: _receipt_to_payload
    p2-->>p3: dict
    p2-->>p3: dict
    p2-->>p4: to_payload
    p0->>p5: _object
    p5->>p6: require_mapping
    p6-->>p1: isinstance
    p6-->>p1: isinstance
    p6-->>p7: encode
    p5->>p8: VerificationReceiptError
    p5->>p8: VerificationReceiptError
    p0->>p9: _exact_fields
    p9-->>p10: set
    p9->>p11: require_exact_fields
    p11-->>p1: isinstance
    p11-->>p12: str
    p11-->>p10: set
    p11-->>p10: set
    p11-->>p10: set
    p11-->>p13: tuple
    p11-->>p14: sorted
    p11-->>p13: tuple
    p11-->>p14: sorted
    p11-->>p15: invalid_error
    p11-->>p16: error_factory
    p9->>p8: VerificationReceiptError
    p9->>p8: VerificationReceiptError
    p9->>p8: VerificationReceiptError
    p0->>p17: _string
```

> Call sequence diagram shows 30 of 169 interactions; 139 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_verification_receipt"]
    s2["2. isinstance"]
    s3["3. _receipt_to_payload"]
    s4["4. dict"]
    s5["5. dict"]
    s6["6. to_payload"]
    s7["7. _object"]
    s8["8. require_mapping"]
    s9["9. isinstance"]
    s10["10. isinstance"]
    s11["11. encode"]
    s12["12. VerificationReceiptError"]
    s1 -. "isinstance(value, VerificationReceipt)" .-> s2
    s1 -->|"_receipt_to_payload(value)"| s3
    s3 -. "dict(receipt.evidence)" .-> s4
    s3 -. "dict(receipt.evaluated_snapshot)" .-> s5
    s3 -. "check.to_payload(data not statically known)" .-> s6
    s1 -->|"_object(payload, 'receipt')"| s7
    s7 -->|"require_mapping(value, error=VerificationReceiptError(...), require_string_keys=True, key_error=VerificationReceiptError(...))"| s8
    s8 -. "isinstance(value, Mapping)" .-> s9
    s8 -. "isinstance(key, str)" .-> s10
    s8 -. "key.encode('utf-8')" .-> s11
    s7 -->|"VerificationReceiptError(field_name, 'must be an object')"| s12
    click s1 "../modules/verification_contracts.md"
    click s3 "../modules/verification_contracts.md"
    click s7 "../modules/verification_contracts.md"
    click s8 "../modules/validation.md"
    click s12 "../modules/verification_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_verification_receipt` | `value: VerificationReceipt \| object` | `VerificationReceipt`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VerificationContractError`, `MAX_CHECKS_PER_RECEIPT` | - | `VerificationReceipt(...)` |
| `isinstance` | - | - | - | - |
| `_receipt_to_payload` | `receipt: VerificationReceipt` | - | - | `{...}` |
| `dict` | - | - | - | - |
| `dict` | - | - | - | - |
| `to_payload` | - | - | - | - |
| `_object` | `value: object`, `field_name: str` | - | - | `require_mapping(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `VerificationReceiptError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_verification_receipt | isinstance | 806 | `isinstance(value, VerificationReceipt)` |
| validate_verification_receipt | _receipt_to_payload | 805 | `_receipt_to_payload(value)` |
| _receipt_to_payload | dict | 1101 | `dict(receipt.evidence)` |
| _receipt_to_payload | dict | 1103 | `dict(receipt.evaluated_snapshot)` |
| _receipt_to_payload | to_payload | 1107 | `check.to_payload(data not statically known)` |
| validate_verification_receipt | _object | 809 | `_object(payload, 'receipt')` |
| _object | require_mapping | 1441 | `require_mapping(value, error=VerificationReceiptError(...), require_string_keys=True, key_error=VerificationReceiptError(...))` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance | 731 | `isinstance(key, str)` |
| require_mapping | encode | 736 | `key.encode('utf-8')` |
| _object | VerificationReceiptError | 1443 | `VerificationReceiptError(field_name, 'must be an object')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_verification_receipt` | `isinstance` | 806 |
| unresolved_call | `_receipt_to_payload` | `check.to_payload` | 1107 |
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `validate_verification_receipt` | `first 12 steps` | 0 |

## Behavior

This flow starts at `validate_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
