# write_verification_receipt

**Entry point:** `write_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as write_verification_receipt
    participant p1 as serialize_verification_receipt
    participant p2 as formatted_json_bytes
    participant p3 as encode
    participant p4 as formatted_json_text
    participant p5 as dumps
    participant p6 as verification_receipt_to_payload
    participant p7 as validate_verification_receipt
    participant p8 as isinstance
    participant p9 as _receipt_to_payload
    participant p10 as dict
    participant p11 as to_payload
    participant p12 as _object
    participant p13 as require_mapping
    participant p14 as VerificationReceiptError
    participant p15 as _exact_fields
    participant p16 as set
    participant p17 as require_exact_fields
    participant p18 as str
    participant p19 as tuple
    participant p20 as sorted
    p0->>p1: serialize_verification_receipt
    p1->>p2: formatted_json_bytes
    p2-->>p3: encode
    p2->>p4: formatted_json_text
    p4-->>p5: dumps
    p1->>p6: verification_receipt_to_payload
    p6->>p7: validate_verification_receipt
    p7-->>p8: isinstance
    p7->>p9: _receipt_to_payload
    p9-->>p10: dict
    p9-->>p10: dict
    p9-->>p11: to_payload
    p7->>p12: _object
    p12->>p13: require_mapping
    p13-->>p8: isinstance
    p13-->>p8: isinstance
    p13-->>p3: encode
    p12->>p14: VerificationReceiptError
    p12->>p14: VerificationReceiptError
    p7->>p15: _exact_fields
    p15-->>p16: set
    p15->>p17: require_exact_fields
    p17-->>p8: isinstance
    p17-->>p18: str
    p17-->>p16: set
    p17-->>p16: set
    p17-->>p16: set
    p17-->>p19: tuple
    p17-->>p20: sorted
    p17-->>p19: tuple
```

> Call sequence diagram shows 30 of 212 interactions; 182 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. write_verification_receipt"]
    s2["2. serialize_verification_receipt"]
    s3["3. formatted_json_bytes"]
    s4["4. encode"]
    s5["5. formatted_json_text"]
    s6["6. dumps"]
    s7["7. verification_receipt_to_payload"]
    s8["8. validate_verification_receipt"]
    s9["9. isinstance"]
    s10["10. _receipt_to_payload"]
    s11["11. dict"]
    s12["12. dict"]
    s1 -->|"serialize_verification_receipt(receipt)"| s2
    s2 -->|"formatted_json_bytes(verification_receipt_to_payload(...))"| s3
    s3 -. "formatted_json_text(value).encode('utf-8')" .-> s4
    s3 -->|"formatted_json_text(value)"| s5
    s5 -. "json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)" .-> s6
    s2 -->|"verification_receipt_to_payload(value)"| s7
    s7 -->|"validate_verification_receipt(value)"| s8
    s8 -. "isinstance(value, VerificationReceipt)" .-> s9
    s8 -->|"_receipt_to_payload(value)"| s10
    s10 -. "dict(receipt.evidence)" .-> s11
    s10 -. "dict(receipt.evaluated_snapshot)" .-> s12
    click s1 "../modules/verification_contracts.md"
    click s2 "../modules/verification_contracts.md"
    click s3 "../modules/knowledge_evidence.md"
    click s5 "../modules/knowledge_evidence.md"
    click s7 "../modules/verification_contracts.md"
    click s8 "../modules/verification_contracts.md"
    click s10 "../modules/verification_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `write_verification_receipt` | `wiki_dir: str \| Path`, `receipt: VerificationReceipt \| object` | `VERIFICATION_RECEIPT_FILENAME`, `VERIFICATION_RECEIPT_FILENAME` | - | `path` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| write_verification_receipt | serialize_verification_receipt | 981 | `serialize_verification_receipt(receipt)` |
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

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `formatted_json_bytes` | `formatted_json_text(value).encode` | 191 |
| external_call | `formatted_json_text` | `json.dumps` | 177 |
| unresolved_call | `validate_verification_receipt` | `isinstance` | 806 |
| step_limit | `write_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `write_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `write_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
