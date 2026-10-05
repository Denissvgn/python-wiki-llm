# evaluate_verification_receipt

**Entry point:** `evaluate_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as evaluate_verification_receipt
    participant p1 as validate_verification_receipt
    participant p2 as isinstance (src/llm_wiki_cli/services…uate_verification_receipt)
    participant p3 as TypeError
    participant p4 as add
    participant p5 as dict (src/llm_wiki_cli/services…uate_verification_receipt)
    participant p6 as _CHECKER_REGISTRY.get
    participant p7 as VerificationReceiptEvaluation
    participant p8 as tuple (src/llm_wiki_cli/services…uate_verification_receipt)
    participant p9 as isinstance (src/llm_wiki_cli/services…date_verification_receipt)
    participant p10 as _receipt_to_payload
    participant p11 as _object
    participant p12 as _exact_fields
    participant p13 as _string
    participant p14 as VerificationReceiptError
    participant p15 as _receipt_hash
    participant p16 as _scope_uid
    participant p17 as str (src/llm_wiki_cli/services…date_verification_receipt)
    p0->>p1: validate_verification_receipt
    p0-->>p2: isinstance (src/llm_wiki_cli/services…uate_verification_receipt)(context, VerificationContext)
    p0-->>p3: TypeError('context must be a VerificationContext')
    p0-->>p4: add(VerificationInvalidationReason.KNOWLEDGE_CHANGED)
    p0-->>p4: add(VerificationInvalidationReason.SCOPE_CHANGED)
    p0-->>p5: dict (src/llm_wiki_cli/services…uate_verification_receipt)(current_receipt.evidence)
    p0-->>p5: dict (src/llm_wiki_cli/services…uate_verification_receipt)(context.evidence)
    p0-->>p4: add(VerificationInvalidationReason.EVIDENCE_CHANGED)
    p0-->>p5: dict (src/llm_wiki_cli/services…uate_verification_receipt)(current_receipt.evaluated_snapshot)
    p0-->>p5: dict (src/llm_wiki_cli/services…uate_verification_receipt)(context.evaluated_snapshot)
    p0-->>p4: add(VerificationInvalidationReason.SNAPSHOT_CHANGED)
    p0-->>p6: _CHECKER_REGISTRY.get(check.checker_id)
    p0-->>p4: add(VerificationInvalidationReason.UNKNOWN_CHECKER)
    p0-->>p4: add(VerificationInvalidationReason.CHECKER_VERSION_CHANGED)
    p0->>p7: VerificationReceiptEvaluation
    p0-->>p8: tuple (src/llm_wiki_cli/services…uate_verification_receipt)(reasons)
    p1-->>p9: isinstance (src/llm_wiki_cli/services…date_verification_receipt)(value, VerificationReceipt)
    p1->>p10: _receipt_to_payload
    p1->>p11: _object
    p1->>p12: _exact_fields
    p1->>p13: _string
    p1->>p14: VerificationReceiptError
    p1->>p15: _receipt_hash
    p1->>p11: _object
    p1->>p12: _exact_fields
    p1->>p13: _string
    p1->>p16: _scope_uid
    p1->>p14: VerificationReceiptError
    p1-->>p17: str (src/llm_wiki_cli/services…date_verification_receipt)(exc)
    p1->>p15: _receipt_hash
```

> Call sequence diagram shows 30 of 178 interactions; 148 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 9 of 55 (46 omitted); unresolved 7 of 25 (18 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 4 | - | external | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 4 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_object` | 8 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 9 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 9 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_object` | 8 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:_exact_fields` | 15 | - | external | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_exact_fields` | 15 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
> Omission summary shows 8 of 59 groups; 51 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 765 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 769 | `isinstance(key, str)` |
| require_mapping | key.encode | 774 | `key.encode('utf-8')` |

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
| step_limit | `evaluate_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `evaluate_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `evaluate_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
