# write_verification_receipt

**Entry point:** `write_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md), and 1 more

**Complete modules touched:**

- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as write_verification_receipt
    participant p1 as serialize_verification_receipt
    participant p2 as write_bytes_atomic
    participant p3 as first_unsafe_path_component
    participant p4 as VerificationReceiptError
    participant p5 as verification_receipt_path
    participant p6 as formatted_json_bytes
    participant p7 as verification_receipt_to_payload
    participant p8 as validate_verification_receipt
    participant p9 as _object
    participant p10 as _exact_fields
    participant p11 as _string
    participant p12 as _receipt_hash
    participant p13 as _scope_uid
    participant p14 as _receipt_anchor_mapping
    participant p15 as hash_json
    participant p16 as _parse_check
    participant p17 as _sha256
    participant p18 as _checker_id
    participant p19 as _normalized_anchor_mapping
    participant p20 as canonical_json_bytes
    participant p21 as _checker_version
    participant p22 as _array
    participant p23 as _parse_diagnostic
    participant p24 as _parse_coverage
    participant p25 as before_wiki_write
    participant p26 as after_wiki_write
    participant p27 as formatted_json_text
    participant p28 as _receipt_to_payload
    participant p29 as Path (src/llm_wiki_cli/services…rite_verification_receipt)
    participant p30 as root.is_symlink
    p0->>p1: serialize_verification_receipt
    p0->>p2: write_bytes_atomic
    p0->>p3: first_unsafe_path_component
    p0->>p4: VerificationReceiptError
    p0->>p5: verification_receipt_path
    p1->>p6: formatted_json_bytes
    p1->>p7: verification_receipt_to_payload
    p7->>p8: validate_verification_receipt
    p8->>p9: _object
    p8->>p10: _exact_fields
    p8->>p11: _string
    p8->>p12: _receipt_hash
    p8->>p13: _scope_uid
    p8->>p14: _receipt_anchor_mapping
    p8->>p15: hash_json
    p8->>p16: _parse_check
    p12->>p17: _sha256
    p16->>p18: _checker_id
    p14->>p19: _normalized_anchor_mapping
    p15->>p20: canonical_json_bytes
    p16->>p21: _checker_version
    p16->>p22: _array
    p16->>p23: _parse_diagnostic
    p16->>p24: _parse_coverage
    p2->>p25: before_wiki_write
    p2->>p26: after_wiki_write
    p6->>p27: formatted_json_text
    p7->>p28: _receipt_to_payload
    p0-->>p29: Path (src/llm_wiki_cli/services…rite_verification_receipt)(wiki_dir)
    p0-->>p30: root.is_symlink
```

> Call sequence diagram shows 30 of 232 interactions; 202 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 82 (81 omitted); unresolved 1 of 42 (41 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_evidence.py:formatted_json_bytes` | 3 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:formatted_json_text` | 5 | - | external | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:validate_verification_receipt` | 8 | - | external | 7 |
| `src/llm_wiki_cli/services/verification_contracts.py:validate_verification_receipt` | 8 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 18 |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 10 | - | external | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:_receipt_to_payload` | 10 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_object` | 14 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 15 | - | external | 2 |
> Omission summary shows 8 of 65 groups; 57 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
| formatted_json_bytes | formatted_json_text(…).encode | 210 | `formatted_json_text(value).encode('utf-8')` |
| formatted_json_bytes | formatted_json_text | 210 | `formatted_json_text(value)` |
| formatted_json_text | json.dumps | 196 | `json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)` |
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
| unresolved_call | `formatted_json_bytes` | `formatted_json_text(value).encode` | 210 |
| external_call | `formatted_json_text` | `json.dumps` | 196 |
| external_call | `validate_verification_receipt` | `isinstance` | 806 |
| step_limit | `write_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `write_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `write_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
