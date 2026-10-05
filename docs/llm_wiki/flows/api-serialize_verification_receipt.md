# serialize_verification_receipt

**Entry point:** `serialize_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as serialize_verification_receipt
    participant p1 as formatted_json_bytes
    participant p2 as verification_receipt_to_payload
    participant p3 as len (src/llm_wiki_cli/services…lize_verification_receipt)
    participant p4 as VerificationReceiptError
    participant p5 as formatted_json_text(…).encode
    participant p6 as validate_verification_receipt
    participant p7 as formatted_json_text
    participant p8 as _receipt_to_payload
    participant p9 as json.dumps (src/llm_wiki_cli/services…ce.py:formatted_json_text)
    participant p10 as isinstance (src/llm_wiki_cli/services…date_verification_receipt)
    participant p11 as _object
    participant p12 as _exact_fields
    participant p13 as _string
    participant p14 as _receipt_hash
    participant p15 as _scope_uid
    participant p16 as str (src/llm_wiki_cli/services…date_verification_receipt)
    participant p17 as _receipt_anchor_mapping
    participant p18 as hash_json
    participant p19 as dict (src/llm_wiki_cli/services…date_verification_receipt)
    p0->>p1: formatted_json_bytes
    p0->>p2: verification_receipt_to_payload
    p0-->>p3: len (src/llm_wiki_cli/services…lize_verification_receipt)(content)
    p0->>p4: VerificationReceiptError
    p1-->>p5: formatted_json_text(…).encode('utf-8')
    p2->>p6: validate_verification_receipt
    p1->>p7: formatted_json_text
    p2->>p8: _receipt_to_payload
    p7-->>p9: json.dumps (src/llm_wiki_cli/services…ce.py:formatted_json_text)(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
    p6-->>p10: isinstance (src/llm_wiki_cli/services…date_verification_receipt)(value, VerificationReceipt)
    p6->>p8: _receipt_to_payload
    p6->>p11: _object
    p6->>p12: _exact_fields
    p6->>p13: _string
    p6->>p4: VerificationReceiptError
    p6->>p14: _receipt_hash
    p6->>p11: _object
    p6->>p12: _exact_fields
    p6->>p13: _string
    p6->>p15: _scope_uid
    p6->>p4: VerificationReceiptError
    p6-->>p16: str (src/llm_wiki_cli/services…date_verification_receipt)(exc)
    p6->>p14: _receipt_hash
    p6->>p17: _receipt_anchor_mapping
    p6->>p14: _receipt_hash
    p6->>p18: hash_json
    p6-->>p19: dict (src/llm_wiki_cli/services…date_verification_receipt)(evidence)
    p6->>p4: VerificationReceiptError
    p6->>p17: _receipt_anchor_mapping
    p6->>p14: _receipt_hash
```

> Call sequence diagram shows 30 of 169 interactions; 139 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 50 (45 omitted); unresolved 1 of 19 (18 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 9 | - | external | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 9 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_object` | 13 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 14 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 14 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_object` | 13 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:_exact_fields` | 20 | - | external | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_exact_fields` | 20 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
> Omission summary shows 8 of 57 groups; 49 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. serialize_verification_receipt"]
    s2["2. formatted_json_bytes"]
    s3["3. formatted_json_text(…).encode"]
    s4["4. formatted_json_text"]
    s5["5. json.dumps (src/llm_wiki_cli/services…ce.py:formatted_json_text)"]
    s6["6. verification_receipt_to_payload"]
    s7["7. validate_verification_receipt"]
    s8["8. isinstance (src/llm_wiki_cli/services…date_verification_receipt)"]
    s9["9. _receipt_to_payload"]
    s10["10. dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)"]
    s11["11. dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)"]
    s12["12. check.to_payload"]
    s1 -->|"formatted_json_bytes(verification_receipt_to_payload(...))"| s2
    s2 -. "formatted_json_text(…).encode('utf-8')" .-> s3
    s2 -->|"formatted_json_text(value)"| s4
    s4 -. "json.dumps (src/llm_wiki_cli/services…ce.py:formatted_json_text)(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)" .-> s5
    s1 -->|"verification_receipt_to_payload(value)"| s6
    s6 -->|"validate_verification_receipt(value)"| s7
    s7 -. "isinstance (src/llm_wiki_cli/services…date_verification_receipt)(value, VerificationReceipt)" .-> s8
    s7 -->|"_receipt_to_payload(value)"| s9
    s9 -. "dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)(receipt.evidence)" .-> s10
    s9 -. "dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)(receipt.evaluated_snapshot)" .-> s11
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
| `formatted_json_text(…).encode` | - | - | - | - |
| `formatted_json_text` | `value: Any` | - | - | `...` |
| `json.dumps (src/llm_wiki_cli/services…ce.py:formatted_json_text)` | - | - | - | - |
| `verification_receipt_to_payload` | `value: VerificationReceipt \| object` | - | - | `_receipt_to_payload(...)` |
| `validate_verification_receipt` | `value: VerificationReceipt \| object` | `VerificationReceipt`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VerificationContractError`, `MAX_CHECKS_PER_RECEIPT` | - | `VerificationReceipt(...)` |
| `isinstance (src/llm_wiki_cli/services…date_verification_receipt)` | - | - | - | - |
| `_receipt_to_payload` | `receipt: VerificationReceipt` | - | - | `{...}` |
| `dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)` | - | - | - | - |
| `check.to_payload` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| serialize_verification_receipt | formatted_json_bytes | 790 | `formatted_json_bytes(verification_receipt_to_payload(...))` |
| formatted_json_bytes | formatted_json_text(…).encode | 193 | `formatted_json_text(value).encode('utf-8')` |
| formatted_json_bytes | formatted_json_text | 193 | `formatted_json_text(value)` |
| formatted_json_text | json.dumps (src/llm_wiki_cli/services…ce.py:formatted_json_text) | 179 | `json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)` |
| serialize_verification_receipt | verification_receipt_to_payload | 790 | `verification_receipt_to_payload(value)` |
| verification_receipt_to_payload | validate_verification_receipt | 781 | `validate_verification_receipt(value)` |
| validate_verification_receipt | isinstance (src/llm_wiki_cli/services…date_verification_receipt) | 806 | `isinstance(value, VerificationReceipt)` |
| validate_verification_receipt | _receipt_to_payload | 805 | `_receipt_to_payload(value)` |
| _receipt_to_payload | dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload) | 1101 | `dict(receipt.evidence)` |
| _receipt_to_payload | dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload) | 1103 | `dict(receipt.evaluated_snapshot)` |
| _receipt_to_payload | check.to_payload | 1107 | `check.to_payload(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `formatted_json_bytes` | `formatted_json_text(value).encode` | 193 |
| external_call | `formatted_json_text` | `json.dumps` | 179 |
| external_call | `validate_verification_receipt` | `isinstance` | 806 |
| unresolved_call | `_receipt_to_payload` | `check.to_payload` | 1107 |
| step_limit | `serialize_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `serialize_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `serialize_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
