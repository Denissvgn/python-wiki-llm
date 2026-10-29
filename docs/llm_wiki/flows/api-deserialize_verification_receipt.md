# deserialize_verification_receipt

**Entry point:** `deserialize_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as deserialize_verification_receipt
    participant p1 as validate_verification_receipt
    participant p2 as serialize_verification_receipt
    participant p3 as VerificationReceiptError
    participant p4 as formatted_json_bytes
    participant p5 as verification_receipt_to_payload
    participant p6 as _object
    participant p7 as _exact_fields
    participant p8 as _string
    participant p9 as _receipt_hash
    participant p10 as _scope_uid
    participant p11 as _receipt_anchor_mapping
    participant p12 as hash_json
    participant p13 as _parse_check
    participant p14 as _sha256
    participant p15 as _checker_id
    participant p16 as _normalized_anchor_mapping
    participant p17 as canonical_json_bytes
    participant p18 as _checker_version
    participant p19 as _array
    participant p20 as _parse_diagnostic
    participant p21 as _parse_coverage
    participant p22 as require_sha256
    participant p23 as _nonnegative_int
    participant p24 as require_nonnegative_int
    participant p25 as require_trimmed_text
    participant p26 as _receipt_to_payload
    participant p27 as VerificationResult
    participant p28 as VerificationReceipt
    participant p29 as isinstance (src/llm_wiki_cli/services…lize_verification_receipt)
    participant p30 as content.decode
    p0->>p1: validate_verification_receipt
    p0->>p2: serialize_verification_receipt
    p0->>p3: VerificationReceiptError
    p2->>p4: formatted_json_bytes
    p2->>p5: verification_receipt_to_payload
    p1->>p6: _object
    p1->>p7: _exact_fields
    p1->>p8: _string
    p1->>p9: _receipt_hash
    p1->>p10: _scope_uid
    p1->>p11: _receipt_anchor_mapping
    p1->>p12: hash_json
    p1->>p13: _parse_check
    p9->>p14: _sha256
    p13->>p15: _checker_id
    p11->>p16: _normalized_anchor_mapping
    p12->>p17: canonical_json_bytes
    p13->>p18: _checker_version
    p13->>p19: _array
    p13->>p20: _parse_diagnostic
    p13->>p21: _parse_coverage
    p14->>p22: require_sha256
    p21->>p23: _nonnegative_int
    p23->>p24: require_nonnegative_int
    p22->>p25: require_trimmed_text
    p1->>p26: _receipt_to_payload
    p1->>p27: VerificationResult
    p1->>p28: VerificationReceipt
    p0-->>p29: isinstance (src/llm_wiki_cli/services…lize_verification_receipt)(content, bytes)
    p0-->>p30: content.decode('utf-8')
```

> Call sequence diagram shows 30 of 182 interactions; 152 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 54 (53 omitted); unresolved 1 of 20 (19 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/verification_contracts.py:deserialize_verification_receipt` | 1 | - | external | 3 |
| `src/llm_wiki_cli/services/verification_contracts.py:deserialize_verification_receipt` | 1 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 3 |
| `src/llm_wiki_cli/services/verification_contracts.py:validate_verification_receipt` | 10 | - | external | 7 |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 12 | - | external | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 12 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_object` | 16 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 17 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 17 | - | unresolved | 1 |
> Omission summary shows 8 of 64 groups; 56 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 109; effect analysis evaluated: 64, partial: 0, unavailable: 45. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `deserialize_verification_receipt` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…lize_verification_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `TypeError` | `not_applicable` | `not_applicable` | `not_applicable` |
| `len (src/llm_wiki_cli/services…lize_verification_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `VerificationReceiptError` | `unavailable` | `unavailable` | `unavailable` |
| `content.decode` | `not_applicable` | `not_applicable` | `not_applicable` |
| `VerificationReceiptError` | `unavailable` | `unavailable` | `unavailable` |
| `json.loads` | `not_applicable` | `not_applicable` | `not_applicable` |
| `VerificationReceiptError` | `unavailable` | `unavailable` | `unavailable` |
| `validate_verification_receipt` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…date_verification_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `_receipt_to_payload` | `available` | `evaluated` | `available` |

```mermaid
flowchart LR
    s1["1. deserialize_verification_receipt"]
    s2["2. isinstance (src/llm_wiki_cli/services…lize_verification_receipt)"]
    s3["3. TypeError"]
    s4["4. len (src/llm_wiki_cli/services…lize_verification_receipt)"]
    s5["5. VerificationReceiptError"]
    s6["6. content.decode"]
    s7["7. VerificationReceiptError"]
    s8["8. json.loads"]
    s9["9. VerificationReceiptError"]
    s10["10. validate_verification_receipt"]
    s11["11. isinstance (src/llm_wiki_cli/services…date_verification_receipt)"]
    s12["12. _receipt_to_payload"]
    s1 -. "isinstance (src/llm_wiki_cli/services…lize_verification_receipt)(content, bytes)" .-> s2
    s1 -. "TypeError('content must be bytes')" .-> s3
    s1 -. "len (src/llm_wiki_cli/services…lize_verification_receipt)(content)" .-> s4
    s1 -->|"VerificationReceiptError('receipt', 'exceeds the byte limit')"| s5
    s1 -. "content.decode('utf-8')" .-> s6
    s1 -->|"VerificationReceiptError('receipt', 'must be valid UTF-8')"| s7
    s1 -. "json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)" .-> s8
    s1 -->|"VerificationReceiptError('receipt', ...)"| s9
    s1 -->|"validate_verification_receipt(payload)"| s10
    s10 -. "isinstance (src/llm_wiki_cli/services…date_verification_receipt)(value, VerificationReceipt)" .-> s11
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
| `isinstance (src/llm_wiki_cli/services…lize_verification_receipt)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `len (src/llm_wiki_cli/services…lize_verification_receipt)` | - | - | - | - |
| `VerificationReceiptError` | - | - | - | - |
| `content.decode` | - | - | - | - |
| `VerificationReceiptError` | - | - | - | - |
| `json.loads` | - | - | - | - |
| `VerificationReceiptError` | - | - | - | - |
| `validate_verification_receipt` | `value: VerificationReceipt \| object` | `VerificationReceipt`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VERIFICATION_RECEIPT_SCHEMA_VERSION`, `VerificationContractError`, `MAX_CHECKS_PER_RECEIPT` | - | `VerificationReceipt(...)` |
| `isinstance (src/llm_wiki_cli/services…date_verification_receipt)` | - | - | - | - |
| `_receipt_to_payload` | `receipt: VerificationReceipt` | - | - | `{...}` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| deserialize_verification_receipt | isinstance (src/llm_wiki_cli/services…lize_verification_receipt) | 894 | `isinstance(content, bytes)` |
| deserialize_verification_receipt | TypeError | 895 | `TypeError('content must be bytes')` |
| deserialize_verification_receipt | len (src/llm_wiki_cli/services…lize_verification_receipt) | 896 | `len(content)` |
| deserialize_verification_receipt | VerificationReceiptError | 897 | `VerificationReceiptError('receipt', 'exceeds the byte limit')` |
| deserialize_verification_receipt | content.decode | 899 | `content.decode('utf-8')` |
| deserialize_verification_receipt | VerificationReceiptError | 901 | `VerificationReceiptError('receipt', 'must be valid UTF-8')` |
| deserialize_verification_receipt | json.loads | 921 | `json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)` |
| deserialize_verification_receipt | VerificationReceiptError | 929 | `VerificationReceiptError('receipt', ...)` |
| deserialize_verification_receipt | validate_verification_receipt | 933 | `validate_verification_receipt(payload)` |
| validate_verification_receipt | isinstance (src/llm_wiki_cli/services…date_verification_receipt) | 806 | `isinstance(value, VerificationReceipt)` |
| validate_verification_receipt | _receipt_to_payload | 805 | `_receipt_to_payload(value)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `deserialize_verification_receipt` | `isinstance` | 894 |
| external_call | `deserialize_verification_receipt` | `TypeError` | 895 |
| unresolved_call | `deserialize_verification_receipt` | `content.decode` | 899 |
| external_call | `deserialize_verification_receipt` | `json.loads` | 921 |
| external_call | `validate_verification_receipt` | `isinstance` | 806 |
| step_limit | `deserialize_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `deserialize_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `deserialize_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
