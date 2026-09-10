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
    participant p3 as formatted_json_text(…).encode
    participant p4 as formatted_json_text
    participant p5 as json.dumps
    participant p6 as verification_receipt_to_payload
    participant p7 as validate_verification_receipt
    participant p8 as isinstance (src/llm_wiki_cli/services…date_verification_receipt)
    participant p9 as _receipt_to_payload
    participant p10 as dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)
    participant p11 as check.to_payload
    participant p12 as _object
    participant p13 as require_mapping
    participant p14 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p15 as key.encode
    participant p16 as VerificationReceiptError
    participant p17 as _exact_fields
    participant p18 as set (src/llm_wiki_cli/services…ontracts.py:_exact_fields)
    participant p19 as require_exact_fields
    participant p20 as isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p21 as str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p22 as set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p23 as tuple (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p24 as sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p0->>p1: serialize_verification_receipt
    p1->>p2: formatted_json_bytes
    p2-->>p3: formatted_json_text(…).encode
    p2->>p4: formatted_json_text
    p4-->>p5: json.dumps
    p1->>p6: verification_receipt_to_payload
    p6->>p7: validate_verification_receipt
    p7-->>p8: isinstance (src/llm_wiki_cli/services…date_verification_receipt)
    p7->>p9: _receipt_to_payload
    p9-->>p10: dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)
    p9-->>p10: dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)
    p9-->>p11: check.to_payload
    p7->>p12: _object
    p12->>p13: require_mapping
    p13-->>p14: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p13-->>p14: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p13-->>p15: key.encode
    p12->>p16: VerificationReceiptError
    p12->>p16: VerificationReceiptError
    p7->>p17: _exact_fields
    p17-->>p18: set (src/llm_wiki_cli/services…ontracts.py:_exact_fields)
    p17->>p19: require_exact_fields
    p19-->>p20: isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p19-->>p21: str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p19-->>p22: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p19-->>p22: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p19-->>p22: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p19-->>p23: tuple (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p19-->>p24: sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p19-->>p23: tuple (src/llm_wiki_cli/services…n.py:require_exact_fields)
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
    s4["4. formatted_json_text(…).encode"]
    s5["5. formatted_json_text"]
    s6["6. json.dumps"]
    s7["7. verification_receipt_to_payload"]
    s8["8. validate_verification_receipt"]
    s9["9. isinstance (src/llm_wiki_cli/services…date_verification_receipt)"]
    s10["10. _receipt_to_payload"]
    s11["11. dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)"]
    s12["12. dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)"]
    s1 -->|"serialize_verification_receipt(receipt)"| s2
    s2 -->|"formatted_json_bytes(verification_receipt_to_payload(...))"| s3
    s3 -. "formatted_json_text(…).encode('utf-8')" .-> s4
    s3 -->|"formatted_json_text(value)"| s5
    s5 -. "json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)" .-> s6
    s2 -->|"verification_receipt_to_payload(value)"| s7
    s7 -->|"validate_verification_receipt(value)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…date_verification_receipt)(value, VerificationReceipt)" .-> s9
    s8 -->|"_receipt_to_payload(value)"| s10
    s10 -. "dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)(receipt.evidence)" .-> s11
    s10 -. "dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)(receipt.evaluated_snapshot)" .-> s12
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
| `formatted_json_text(…).encode` | - | - | - | - |
| `formatted_json_text` | `value: Any` | - | - | `...` |
| `json.dumps` | - | - | - | - |
| `verification_receipt_to_payload` | `value: VerificationReceipt \| object` | - | - | `_receipt_to_payload(...)` |
| `validate_verification_receipt` | `value: VerificationReceipt \| object` | `VerificationReceipt`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VerificationContractError`, `MAX_CHECKS_PER_RECEIPT` | - | `VerificationReceipt(...)` |
| `isinstance (src/llm_wiki_cli/services…date_verification_receipt)` | - | - | - | - |
| `_receipt_to_payload` | `receipt: VerificationReceipt` | - | - | `{...}` |
| `dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| write_verification_receipt | serialize_verification_receipt | 981 | `serialize_verification_receipt(receipt)` |
| serialize_verification_receipt | formatted_json_bytes | 790 | `formatted_json_bytes(verification_receipt_to_payload(...))` |
| formatted_json_bytes | formatted_json_text(…).encode | 192 | `formatted_json_text(value).encode('utf-8')` |
| formatted_json_bytes | formatted_json_text | 192 | `formatted_json_text(value)` |
| formatted_json_text | json.dumps | 178 | `json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)` |
| serialize_verification_receipt | verification_receipt_to_payload | 790 | `verification_receipt_to_payload(value)` |
| verification_receipt_to_payload | validate_verification_receipt | 781 | `validate_verification_receipt(value)` |
| validate_verification_receipt | isinstance (src/llm_wiki_cli/services…date_verification_receipt) | 806 | `isinstance(value, VerificationReceipt)` |
| validate_verification_receipt | _receipt_to_payload | 805 | `_receipt_to_payload(value)` |
| _receipt_to_payload | dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload) | 1101 | `dict(receipt.evidence)` |
| _receipt_to_payload | dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload) | 1103 | `dict(receipt.evaluated_snapshot)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `formatted_json_bytes` | `formatted_json_text(value).encode` | 192 |
| external_call | `formatted_json_text` | `json.dumps` | 178 |
| external_call | `validate_verification_receipt` | `isinstance` | 806 |
| step_limit | `write_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `write_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `write_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
