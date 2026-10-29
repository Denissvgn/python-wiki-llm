# validate_verification_receipt

**Entry point:** `validate_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_verification_receipt
    participant p1 as _object
    participant p2 as _exact_fields
    participant p3 as _string
    participant p4 as _receipt_hash
    participant p5 as _scope_uid
    participant p6 as _receipt_anchor_mapping
    participant p7 as hash_json
    participant p8 as _parse_check
    participant p9 as _receipt_to_payload
    participant p10 as VerificationReceiptError
    participant p11 as VerificationResult
    participant p12 as VerificationReceipt
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
    participant p23 as require_nonnegative_int
    participant p24 as require_trimmed_text
    participant p25 as require_nonempty_text
    participant p26 as require_mapping
    participant p27 as require_string
    participant p28 as sha256_bytes
    participant p29 as isinstance (src/llm_wiki_cli/services…date_verification_receipt)
    participant p30 as raw_checks.items
    p0->>p1: _object
    p0->>p2: _exact_fields
    p0->>p3: _string
    p0->>p4: _receipt_hash
    p0->>p5: _scope_uid
    p0->>p6: _receipt_anchor_mapping
    p0->>p7: hash_json
    p0->>p8: _parse_check
    p0->>p9: _receipt_to_payload
    p0->>p10: VerificationReceiptError
    p0->>p11: VerificationResult
    p0->>p12: VerificationReceipt
    p4->>p13: _sha256
    p8->>p14: _checker_id
    p6->>p15: _normalized_anchor_mapping
    p7->>p16: canonical_json_bytes
    p8->>p17: _checker_version
    p8->>p18: _array
    p8->>p19: _parse_diagnostic
    p8->>p20: _parse_coverage
    p13->>p21: require_sha256
    p20->>p22: _nonnegative_int
    p22->>p23: require_nonnegative_int
    p21->>p24: require_trimmed_text
    p24->>p25: require_nonempty_text
    p1->>p26: require_mapping
    p3->>p27: require_string
    p7->>p28: sha256_bytes
    p0-->>p29: isinstance (src/llm_wiki_cli/services…date_verification_receipt)(value, VerificationReceipt)
    p0-->>p30: raw_checks.items
```

> Call sequence diagram shows 30 of 167 interactions; 137 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 51 (50 omitted); unresolved 1 of 19 (18 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 3 | - | external | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 3 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 8 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_object` | 7 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:_exact_fields` | 14 | - | external | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_exact_fields` | 14 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 16 | - | external | 9 |
> Omission summary shows 8 of 55 groups; 47 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 98; effect analysis evaluated: 57, partial: 1, unavailable: 40. Counts include steps omitted from the displayed trace.

Collector observations for 58 source steps with known totals: observed: 225, emitted: 224, omitted: 1. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `validate_verification_receipt` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `isinstance (src/llm_wiki_cli/services…date_verification_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_receipt_to_payload` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `dict (src/llm_wiki_cli/services…ts.py:_receipt_to_payload)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `check.to_payload` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_object` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `require_mapping` | `available` | `evaluated` | `available` | `8` | `8` | `0` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `key.encode` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `VerificationReceiptError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

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

*No boundary-effect observations were captured in this static trace.*

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
