# serialize_verification_receipt

**Entry point:** `serialize_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as serialize_verification_receipt
    participant p1 as formatted_json_bytes
    participant p2 as encode
    participant p3 as formatted_json_text
    participant p4 as dumps
    participant p5 as verification_receipt_to_payload
    participant p6 as validate_verification_receipt
    participant p7 as isinstance
    participant p8 as _receipt_to_payload
    participant p9 as dict
    participant p10 as to_payload
    participant p11 as _object
    participant p12 as require_mapping
    participant p13 as VerificationReceiptError
    participant p14 as _exact_fields
    participant p15 as set
    participant p16 as require_exact_fields
    participant p17 as str
    participant p18 as tuple
    participant p19 as sorted
    p0->>p1: formatted_json_bytes
    p1-->>p2: encode
    p1->>p3: formatted_json_text
    p3-->>p4: dumps
    p0->>p5: verification_receipt_to_payload
    p5->>p6: validate_verification_receipt
    p6-->>p7: isinstance
    p6->>p8: _receipt_to_payload
    p8-->>p9: dict
    p8-->>p9: dict
    p8-->>p10: to_payload
    p6->>p11: _object
    p11->>p12: require_mapping
    p12-->>p7: isinstance
    p12-->>p7: isinstance
    p12-->>p2: encode
    p11->>p13: VerificationReceiptError
    p11->>p13: VerificationReceiptError
    p6->>p14: _exact_fields
    p14-->>p15: set
    p14->>p16: require_exact_fields
    p16-->>p7: isinstance
    p16-->>p17: str
    p16-->>p15: set
    p16-->>p15: set
    p16-->>p15: set
    p16-->>p18: tuple
    p16-->>p19: sorted
    p16-->>p18: tuple
    p16-->>p19: sorted
```

> Call sequence diagram shows 30 of 169 interactions; 139 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. serialize_verification_receipt"]
    s2["2. formatted_json_bytes"]
    s3["3. encode"]
    s4["4. formatted_json_text"]
    s5["5. dumps"]
    s6["6. verification_receipt_to_payload"]
    s7["7. validate_verification_receipt"]
    s8["8. isinstance"]
    s9["9. _receipt_to_payload"]
    s10["10. dict"]
    s11["11. dict"]
    s12["12. to_payload"]
    s1 -->|"formatted_json_bytes(verification_receipt_to_payload(...))"| s2
    s2 -. "formatted_json_text(value).encode('utf-8')" .-> s3
    s2 -->|"formatted_json_text(value)"| s4
    s4 -. "json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)" .-> s5
    s1 -->|"verification_receipt_to_payload(value)"| s6
    s6 -->|"validate_verification_receipt(value)"| s7
    s7 -. "isinstance(value, VerificationReceipt)" .-> s8
    s7 -->|"_receipt_to_payload(value)"| s9
    s9 -. "dict(receipt.evidence)" .-> s10
    s9 -. "dict(receipt.evaluated_snapshot)" .-> s11
    s9 -. "check.to_payload(data not statically known)" .-> s12
    click s1 "../modules/verification_contracts.md"
    click s2 "../modules/knowledge_evidence.md"
    click s4 "../modules/knowledge_evidence.md"
    click s6 "../modules/verification_contracts.md"
    click s7 "../modules/verification_contracts.md"
    click s9 "../modules/verification_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `serialize_verification_receipt` | `value: VerificationReceipt \| object` | `MAX_RECEIPT_BYTES` | - | `content` |
| `formatted_json_bytes` | `value: Any` | - | - | `...` |
| `encode` | - | - | - | - |
| `formatted_json_text` | `value: Any` | - | - | `...` |
| `dumps` | - | - | - | - |
| `verification_receipt_to_payload` | `value: VerificationReceipt \| object` | - | - | `_receipt_to_payload(...)` |
| `validate_verification_receipt` | `value: VerificationReceipt \| object` | `VerificationReceipt`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VerificationContractError`, `MAX_CHECKS_PER_RECEIPT` | - | `VerificationReceipt(...)` |
| `isinstance` | - | - | - | - |
| `_receipt_to_payload` | `receipt: VerificationReceipt` | - | - | `{...}` |
| `dict` | - | - | - | - |
| `dict` | - | - | - | - |
| `to_payload` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| serialize_verification_receipt | formatted_json_bytes | 790 | `formatted_json_bytes(verification_receipt_to_payload(...))` |
| formatted_json_bytes | encode | 191 | `formatted_json_text(value).encode('utf-8')` |
| formatted_json_bytes | formatted_json_text | 191 | `formatted_json_text(value)` |
| formatted_json_text | dumps | 177 | `json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)` |
| serialize_verification_receipt | verification_receipt_to_payload | 790 | `verification_receipt_to_payload(value)` |
| verification_receipt_to_payload | validate_verification_receipt | 781 | `validate_verification_receipt(value)` |
| validate_verification_receipt | isinstance | 806 | `isinstance(value, VerificationReceipt)` |
| validate_verification_receipt | _receipt_to_payload | 805 | `_receipt_to_payload(value)` |
| _receipt_to_payload | dict | 1101 | `dict(receipt.evidence)` |
| _receipt_to_payload | dict | 1103 | `dict(receipt.evaluated_snapshot)` |
| _receipt_to_payload | to_payload | 1107 | `check.to_payload(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `formatted_json_bytes` | `formatted_json_text(value).encode` | 191 |
| external_call | `formatted_json_text` | `json.dumps` | 177 |
| unresolved_call | `validate_verification_receipt` | `isinstance` | 806 |
| unresolved_call | `_receipt_to_payload` | `check.to_payload` | 1107 |
| step_limit | `serialize_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `serialize_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `serialize_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
