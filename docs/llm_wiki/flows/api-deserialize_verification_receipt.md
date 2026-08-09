# deserialize_verification_receipt

**Entry point:** `deserialize_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as deserialize_verification_receipt
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as len
    participant p4 as VerificationReceiptError
    participant p5 as decode
    participant p6 as loads
    participant p7 as validate_verification_receipt
    participant p8 as _receipt_to_payload
    participant p9 as dict
    participant p10 as to_payload
    participant p11 as _object
    participant p12 as require_mapping
    participant p13 as encode
    participant p14 as _exact_fields
    participant p15 as set
    participant p16 as require_exact_fields
    participant p17 as str
    participant p18 as tuple
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p3: len
    p0->>p4: VerificationReceiptError
    p0-->>p5: decode
    p0->>p4: VerificationReceiptError
    p0-->>p6: loads
    p0->>p4: VerificationReceiptError
    p0->>p7: validate_verification_receipt
    p7-->>p1: isinstance
    p7->>p8: _receipt_to_payload
    p8-->>p9: dict
    p8-->>p9: dict
    p8-->>p10: to_payload
    p7->>p11: _object
    p11->>p12: require_mapping
    p12-->>p1: isinstance
    p12-->>p1: isinstance
    p12-->>p13: encode
    p11->>p4: VerificationReceiptError
    p11->>p4: VerificationReceiptError
    p7->>p14: _exact_fields
    p14-->>p15: set
    p14->>p16: require_exact_fields
    p16-->>p1: isinstance
    p16-->>p17: str
    p16-->>p15: set
    p16-->>p15: set
    p16-->>p15: set
    p16-->>p18: tuple
```

> Call sequence diagram shows 30 of 182 interactions; 152 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. deserialize_verification_receipt"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. len"]
    s5["5. VerificationReceiptError"]
    s6["6. decode"]
    s7["7. VerificationReceiptError"]
    s8["8. loads"]
    s9["9. VerificationReceiptError"]
    s10["10. validate_verification_receipt"]
    s11["11. isinstance"]
    s12["12. _receipt_to_payload"]
    s1 -. "isinstance(content, bytes)" .-> s2
    s1 -. "TypeError('content must be bytes')" .-> s3
    s1 -. "len(content)" .-> s4
    s1 -->|"VerificationReceiptError('receipt', 'exceeds the byte limit')"| s5
    s1 -. "content.decode('utf-8')" .-> s6
    s1 -->|"VerificationReceiptError('receipt', 'must be valid UTF-8')"| s7
    s1 -. "json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)" .-> s8
    s1 -->|"VerificationReceiptError('receipt', ...)"| s9
    s1 -->|"validate_verification_receipt(payload)"| s10
    s10 -. "isinstance(value, VerificationReceipt)" .-> s11
    s10 -->|"_receipt_to_payload(value)"| s12
    click s1 "../modules/verification_contracts.md"
    click s5 "../modules/verification_contracts.md"
    click s7 "../modules/verification_contracts.md"
    click s9 "../modules/verification_contracts.md"
    click s10 "../modules/verification_contracts.md"
    click s12 "../modules/verification_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `deserialize_verification_receipt` | `content: bytes` | `MAX_RECEIPT_BYTES`, `VerificationReceiptError` | - | `receipt` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `len` | - | - | - | - |
| `VerificationReceiptError` | - | - | - | - |
| `decode` | - | - | - | - |
| `VerificationReceiptError` | - | - | - | - |
| `loads` | - | - | - | - |
| `VerificationReceiptError` | - | - | - | - |
| `validate_verification_receipt` | `value: VerificationReceipt \| object` | `VerificationReceipt`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VerificationContractError`, `MAX_CHECKS_PER_RECEIPT` | - | `VerificationReceipt(...)` |
| `isinstance` | - | - | - | - |
| `_receipt_to_payload` | `receipt: VerificationReceipt` | - | - | `{...}` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| deserialize_verification_receipt | isinstance | 894 | `isinstance(content, bytes)` |
| deserialize_verification_receipt | TypeError | 895 | `TypeError('content must be bytes')` |
| deserialize_verification_receipt | len | 896 | `len(content)` |
| deserialize_verification_receipt | VerificationReceiptError | 897 | `VerificationReceiptError('receipt', 'exceeds the byte limit')` |
| deserialize_verification_receipt | decode | 899 | `content.decode('utf-8')` |
| deserialize_verification_receipt | VerificationReceiptError | 901 | `VerificationReceiptError('receipt', 'must be valid UTF-8')` |
| deserialize_verification_receipt | loads | 921 | `json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)` |
| deserialize_verification_receipt | VerificationReceiptError | 929 | `VerificationReceiptError('receipt', ...)` |
| deserialize_verification_receipt | validate_verification_receipt | 933 | `validate_verification_receipt(payload)` |
| validate_verification_receipt | isinstance | 806 | `isinstance(value, VerificationReceipt)` |
| validate_verification_receipt | _receipt_to_payload | 805 | `_receipt_to_payload(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `deserialize_verification_receipt` | `isinstance` | 894 |
| unresolved_call | `deserialize_verification_receipt` | `TypeError` | 895 |
| unresolved_call | `deserialize_verification_receipt` | `content.decode` | 899 |
| external_call | `deserialize_verification_receipt` | `json.loads` | 921 |
| unresolved_call | `validate_verification_receipt` | `isinstance` | 806 |
| step_limit | `deserialize_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `deserialize_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `deserialize_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
