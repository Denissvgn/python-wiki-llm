# verification_receipt_to_payload

**Entry point:** `verification_receipt_to_payload` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as verification_receipt_to_payload
    participant p1 as validate_verification_receipt
    participant p2 as isinstance
    participant p3 as _receipt_to_payload
    participant p4 as dict
    participant p5 as to_payload
    participant p6 as _object
    participant p7 as require_mapping
    participant p8 as encode
    participant p9 as VerificationReceiptError
    participant p10 as _exact_fields
    participant p11 as set
    participant p12 as require_exact_fields
    participant p13 as str
    participant p14 as tuple
    participant p15 as sorted
    participant p16 as invalid_error
    participant p17 as error_factory
    p0->>p1: validate_verification_receipt
    p1-->>p2: isinstance
    p1->>p3: _receipt_to_payload
    p3-->>p4: dict
    p3-->>p4: dict
    p3-->>p5: to_payload
    p1->>p6: _object
    p6->>p7: require_mapping
    p7-->>p2: isinstance
    p7-->>p2: isinstance
    p7-->>p8: encode
    p6->>p9: VerificationReceiptError
    p6->>p9: VerificationReceiptError
    p1->>p10: _exact_fields
    p10-->>p11: set
    p10->>p12: require_exact_fields
    p12-->>p2: isinstance
    p12-->>p13: str
    p12-->>p11: set
    p12-->>p11: set
    p12-->>p11: set
    p12-->>p14: tuple
    p12-->>p15: sorted
    p12-->>p14: tuple
    p12-->>p15: sorted
    p12-->>p16: invalid_error
    p12-->>p17: error_factory
    p10->>p9: VerificationReceiptError
    p10->>p9: VerificationReceiptError
    p10->>p9: VerificationReceiptError
```

> Call sequence diagram shows 30 of 164 interactions; 134 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. verification_receipt_to_payload"]
    s2["2. validate_verification_receipt"]
    s3["3. isinstance"]
    s4["4. _receipt_to_payload"]
    s5["5. dict"]
    s6["6. dict"]
    s7["7. to_payload"]
    s8["8. _object"]
    s9["9. require_mapping"]
    s10["10. isinstance"]
    s11["11. isinstance"]
    s12["12. encode"]
    s1 -->|"validate_verification_receipt(value)"| s2
    s2 -. "isinstance(value, VerificationReceipt)" .-> s3
    s2 -->|"_receipt_to_payload(value)"| s4
    s4 -. "dict(receipt.evidence)" .-> s5
    s4 -. "dict(receipt.evaluated_snapshot)" .-> s6
    s4 -. "check.to_payload(data not statically known)" .-> s7
    s2 -->|"_object(payload, 'receipt')"| s8
    s8 -->|"require_mapping(value, error=VerificationReceiptError(...), require_string_keys=True, key_error=VerificationReceiptError(...))"| s9
    s9 -. "isinstance(value, Mapping)" .-> s10
    s9 -. "isinstance(key, str)" .-> s11
    s9 -. "key.encode('utf-8')" .-> s12
    click s1 "../modules/verification_contracts.md"
    click s2 "../modules/verification_contracts.md"
    click s4 "../modules/verification_contracts.md"
    click s8 "../modules/verification_contracts.md"
    click s9 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `verification_receipt_to_payload` | `value: VerificationReceipt \| object` | - | - | `_receipt_to_payload(...)` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| verification_receipt_to_payload | validate_verification_receipt | 781 | `validate_verification_receipt(value)` |
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
| step_limit | `verification_receipt_to_payload` | `first 12 steps` | 0 |
| truncated_flow | `verification_receipt_to_payload` | `depth limit` | 0 |

## Behavior

This flow starts at `verification_receipt_to_payload` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
