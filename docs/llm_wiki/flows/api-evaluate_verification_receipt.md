# evaluate_verification_receipt

**Entry point:** `evaluate_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as evaluate_verification_receipt
    participant p1 as validate_verification_receipt
    participant p2 as isinstance (src/llm_wiki_cli/services…date_verification_receipt)
    participant p3 as _receipt_to_payload
    participant p4 as dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)
    participant p5 as check.to_payload
    participant p6 as _object
    participant p7 as require_mapping
    participant p8 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p9 as key.encode
    participant p10 as VerificationReceiptError
    participant p11 as _exact_fields
    participant p12 as set (src/llm_wiki_cli/services…ontracts.py:_exact_fields)
    participant p13 as require_exact_fields
    participant p14 as isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p15 as str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p16 as set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p17 as tuple (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p18 as sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p19 as invalid_error
    participant p20 as error_factory
    p0->>p1: validate_verification_receipt
    p1-->>p2: isinstance (src/llm_wiki_cli/services…date_verification_receipt)
    p1->>p3: _receipt_to_payload
    p3-->>p4: dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)
    p3-->>p4: dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)
    p3-->>p5: check.to_payload
    p1->>p6: _object
    p6->>p7: require_mapping
    p7-->>p8: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p7-->>p8: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p7-->>p9: key.encode
    p6->>p10: VerificationReceiptError
    p6->>p10: VerificationReceiptError
    p1->>p11: _exact_fields
    p11-->>p12: set (src/llm_wiki_cli/services…ontracts.py:_exact_fields)
    p11->>p13: require_exact_fields
    p13-->>p14: isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p13-->>p15: str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p13-->>p16: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p13-->>p16: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p13-->>p16: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p13-->>p17: tuple (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p13-->>p18: sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p13-->>p17: tuple (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p13-->>p18: sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p13-->>p19: invalid_error
    p13-->>p20: error_factory
    p11->>p10: VerificationReceiptError
    p11->>p10: VerificationReceiptError
    p11->>p10: VerificationReceiptError
```

> Call sequence diagram shows 30 of 178 interactions; 148 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. evaluate_verification_receipt"]
    s2["2. validate_verification_receipt"]
    s3["3. isinstance (src/llm_wiki_cli/services…date_verification_receipt)"]
    s4["4. _receipt_to_payload"]
    s5["5. dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)"]
    s6["6. dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)"]
    s7["7. check.to_payload"]
    s8["8. _object"]
    s9["9. require_mapping"]
    s10["10. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s11["11. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s12["12. key.encode"]
    s1 -->|"validate_verification_receipt(receipt)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…date_verification_receipt)(value, VerificationReceipt)" .-> s3
    s2 -->|"_receipt_to_payload(value)"| s4
    s4 -. "dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)(receipt.evidence)" .-> s5
    s4 -. "dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)(receipt.evaluated_snapshot)" .-> s6
    s4 -. "check.to_payload(data not statically known)" .-> s7
    s2 -->|"_object(payload, 'receipt')"| s8
    s8 -->|"require_mapping(value, error=VerificationReceiptError(...), require_string_keys=True, key_error=VerificationReceiptError(...))"| s9
    s9 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s10
    s9 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s11
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
| `evaluate_verification_receipt` | `receipt: VerificationReceipt \| object`, `context: VerificationContext` | `VerificationContext`, `VerificationInvalidationReason`, `VerificationInvalidationReason`, `VerificationInvalidationReason`, `VerificationInvalidationReason`, `VerificationInvalidationReason`, `VerificationInvalidationReason` | - | `VerificationReceiptEvaluation(...)` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| evaluate_verification_receipt | validate_verification_receipt | 1037 | `validate_verification_receipt(receipt)` |
| validate_verification_receipt | isinstance (src/llm_wiki_cli/services…date_verification_receipt) | 806 | `isinstance(value, VerificationReceipt)` |
| validate_verification_receipt | _receipt_to_payload | 805 | `_receipt_to_payload(value)` |
| _receipt_to_payload | dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload) | 1101 | `dict(receipt.evidence)` |
| _receipt_to_payload | dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload) | 1103 | `dict(receipt.evaluated_snapshot)` |
| _receipt_to_payload | check.to_payload | 1107 | `check.to_payload(data not statically known)` |
| validate_verification_receipt | _object | 809 | `_object(payload, 'receipt')` |
| _object | require_mapping | 1441 | `require_mapping(value, error=VerificationReceiptError(...), require_string_keys=True, key_error=VerificationReceiptError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 731 | `isinstance(key, str)` |
| require_mapping | key.encode | 736 | `key.encode('utf-8')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_verification_receipt` | `isinstance` | 806 |
| unresolved_call | `_receipt_to_payload` | `check.to_payload` | 1107 |
| external_call | `require_mapping` | `isinstance` | 727 |
| external_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `evaluate_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `evaluate_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `evaluate_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
