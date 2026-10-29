# serialize_verification_receipt

**Entry point:** `serialize_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as serialize_verification_receipt
    participant p1 as formatted_json_bytes
    participant p2 as verification_receipt_to_payload
    participant p3 as VerificationReceiptError
    participant p4 as validate_verification_receipt
    participant p5 as _object
    participant p6 as _exact_fields
    participant p7 as _string
    participant p8 as _receipt_hash
    participant p9 as _scope_uid
    participant p10 as _receipt_anchor_mapping
    participant p11 as hash_json
    participant p12 as _parse_check
    participant p13 as _sha256
    participant p14 as _checker_id
    participant p15 as _normalized_anchor_mapping
    participant p16 as canonical_json_bytes
    participant p17 as _checker_version
    participant p18 as _array
    participant p19 as _parse_diagnostic
    participant p20 as _parse_coverage
    participant p21 as require_sha256
    participant p22 as _nonnegative_int
    participant p23 as formatted_json_text
    participant p24 as _receipt_to_payload
    participant p25 as VerificationResult
    participant p26 as VerificationReceipt
    participant p27 as require_mapping
    participant p28 as require_string
    participant p29 as len (src/llm_wiki_cli/services…lize_verification_receipt)
    participant p30 as formatted_json_text(…).encode
    p0->>p1: formatted_json_bytes
    p0->>p2: verification_receipt_to_payload
    p0->>p3: VerificationReceiptError
    p2->>p4: validate_verification_receipt
    p4->>p5: _object
    p4->>p6: _exact_fields
    p4->>p7: _string
    p4->>p8: _receipt_hash
    p4->>p9: _scope_uid
    p4->>p10: _receipt_anchor_mapping
    p4->>p11: hash_json
    p4->>p12: _parse_check
    p8->>p13: _sha256
    p12->>p14: _checker_id
    p10->>p15: _normalized_anchor_mapping
    p11->>p16: canonical_json_bytes
    p12->>p17: _checker_version
    p12->>p18: _array
    p12->>p19: _parse_diagnostic
    p12->>p20: _parse_coverage
    p13->>p21: require_sha256
    p20->>p22: _nonnegative_int
    p1->>p23: formatted_json_text
    p2->>p24: _receipt_to_payload
    p4->>p25: VerificationResult
    p4->>p26: VerificationReceipt
    p5->>p27: require_mapping
    p7->>p28: require_string
    p0-->>p29: len (src/llm_wiki_cli/services…lize_verification_receipt)(content)
    p1-->>p30: formatted_json_text(…).encode('utf-8')
```

> Call sequence diagram shows 30 of 169 interactions; 139 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 50 (49 omitted); unresolved 1 of 19 (18 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_evidence.py:formatted_json_text` | 4 | - | external | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:validate_verification_receipt` | 7 | - | external | 7 |
| `src/llm_wiki_cli/services/verification_contracts.py:validate_verification_receipt` | 7 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 16 |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 9 | - | external | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 9 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 14 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 14 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_object` | 13 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 2 |
> Omission summary shows 8 of 55 groups; 47 further groups are not expanded here. Counts above include all omitted interactions.
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
| formatted_json_bytes | formatted_json_text(…).encode | 215 | `formatted_json_text(value).encode('utf-8')` |
| formatted_json_bytes | formatted_json_text | 215 | `formatted_json_text(value)` |
| formatted_json_text | json.dumps (src/llm_wiki_cli/services…ce.py:formatted_json_text) | 201 | `json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)` |
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
| unresolved_call | `formatted_json_bytes` | `formatted_json_text(value).encode` | 215 |
| external_call | `formatted_json_text` | `json.dumps` | 201 |
| external_call | `validate_verification_receipt` | `isinstance` | 806 |
| unresolved_call | `_receipt_to_payload` | `check.to_payload` | 1107 |
| step_limit | `serialize_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `serialize_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `serialize_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
