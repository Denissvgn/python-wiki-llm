# validate_verification_receipt

**Entry point:** `validate_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_verification_receipt
    participant p1 as isinstance (src/llm_wiki_cli/services…date_verification_receipt)
    participant p2 as _receipt_to_payload
    participant p3 as _object
    participant p4 as _exact_fields
    participant p5 as _string
    participant p6 as VerificationReceiptError
    participant p7 as _receipt_hash
    participant p8 as _scope_uid
    participant p9 as str (src/llm_wiki_cli/services…date_verification_receipt)
    participant p10 as _receipt_anchor_mapping
    participant p11 as hash_json
    participant p12 as dict (src/llm_wiki_cli/services…date_verification_receipt)
    participant p13 as VerificationResult
    participant p14 as len (src/llm_wiki_cli/services…date_verification_receipt)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…date_verification_receipt)(value, VerificationReceipt)
    p0->>p2: _receipt_to_payload
    p0->>p3: _object
    p0->>p4: _exact_fields
    p0->>p5: _string
    p0->>p6: VerificationReceiptError
    p0->>p7: _receipt_hash
    p0->>p3: _object
    p0->>p4: _exact_fields
    p0->>p5: _string
    p0->>p8: _scope_uid
    p0->>p6: VerificationReceiptError
    p0-->>p9: str (src/llm_wiki_cli/services…date_verification_receipt)(exc)
    p0->>p7: _receipt_hash
    p0->>p10: _receipt_anchor_mapping
    p0->>p7: _receipt_hash
    p0->>p11: hash_json
    p0-->>p12: dict (src/llm_wiki_cli/services…date_verification_receipt)(evidence)
    p0->>p6: VerificationReceiptError
    p0->>p10: _receipt_anchor_mapping
    p0->>p7: _receipt_hash
    p0->>p11: hash_json
    p0-->>p12: dict (src/llm_wiki_cli/services…date_verification_receipt)(evaluated_snapshot)
    p0->>p6: VerificationReceiptError
    p0->>p13: VerificationResult
    p0->>p6: VerificationReceiptError
    p0->>p3: _object
    p0->>p6: VerificationReceiptError
    p0-->>p14: len (src/llm_wiki_cli/services…date_verification_receipt)(raw_checks)
    p0->>p6: VerificationReceiptError
```

> Call sequence diagram shows 30 of 167 interactions; 137 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 51 (46 omitted); unresolved 0 of 19 (19 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 3 | - | external | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 3 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_object` | 7 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 8 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_object` | 7 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:_exact_fields` | 14 | - | external | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_exact_fields` | 14 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
> Omission summary shows 8 of 62 groups; 54 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_verification_receipt"]
    s2["2. isinstance (src/llm_wiki_cli/services…date_verification_receipt)"]
    s3["3. _receipt_to_payload"]
    s4["4. dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)"]
    s5["5. dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)"]
    s6["6. check.to_payload"]
    s7["7. _object"]
    s8["8. require_mapping"]
    s9["9. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s10["10. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s11["11. key.encode"]
    s12["12. VerificationReceiptError"]
    s1 -. "isinstance (src/llm_wiki_cli/services…date_verification_receipt)(value, VerificationReceipt)" .-> s2
    s1 -->|"_receipt_to_payload(value)"| s3
    s3 -. "dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)(receipt.evidence)" .-> s4
    s3 -. "dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)(receipt.evaluated_snapshot)" .-> s5
    s3 -. "check.to_payload(data not statically known)" .-> s6
    s1 -->|"_object(payload, 'receipt')"| s7
    s7 -->|"require_mapping(value, error=VerificationReceiptError(...), require_string_keys=True, key_error=VerificationReceiptError(...))"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s9
    s8 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s10
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
| `isinstance (src/llm_wiki_cli/services…date_verification_receipt)` | - | - | - | - |
| `_receipt_to_payload` | `receipt: VerificationReceipt` | - | - | `{...}` |
| `dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)` | - | - | - | - |
| `check.to_payload` | - | - | - | - |
| `_object` | `value: object`, `field_name: str` | - | - | `require_mapping(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `key.encode` | - | - | - | - |
| `VerificationReceiptError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_verification_receipt | isinstance (src/llm_wiki_cli/services…date_verification_receipt) | 806 | `isinstance(value, VerificationReceipt)` |
| validate_verification_receipt | _receipt_to_payload | 805 | `_receipt_to_payload(value)` |
| _receipt_to_payload | dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload) | 1101 | `dict(receipt.evidence)` |
| _receipt_to_payload | dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload) | 1103 | `dict(receipt.evaluated_snapshot)` |
| _receipt_to_payload | check.to_payload | 1107 | `check.to_payload(data not statically known)` |
| validate_verification_receipt | _object | 809 | `_object(payload, 'receipt')` |
| _object | require_mapping | 1441 | `require_mapping(value, error=VerificationReceiptError(...), require_string_keys=True, key_error=VerificationReceiptError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 765 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 769 | `isinstance(key, str)` |
| require_mapping | key.encode | 774 | `key.encode('utf-8')` |
| _object | VerificationReceiptError | 1443 | `VerificationReceiptError(field_name, 'must be an object')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_verification_receipt` | `isinstance` | 806 |
| unresolved_call | `_receipt_to_payload` | `check.to_payload` | 1107 |
| external_call | `require_mapping` | `isinstance` | 765 |
| external_call | `require_mapping` | `isinstance` | 769 |
| unresolved_call | `require_mapping` | `key.encode` | 774 |
| step_limit | `validate_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `validate_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
