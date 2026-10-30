# verify_and_write_receipt

**Entry point:** `verify_and_write_receipt` (`api`)
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
    participant p0 as verify_and_write_receipt
    participant p1 as verify
    participant p2 as write_verification_receipt
    participant p3 as build_verification_receipt
    participant p4 as serialize_verification_receipt
    participant p5 as run_verification
    participant p6 as write_bytes_atomic
    participant p7 as formatted_json_bytes
    participant p8 as verification_receipt_to_payload
    participant p9 as _selected_contracts
    participant p10 as validate_verification_receipt
    participant p11 as _checker_id
    participant p12 as _object
    participant p13 as _exact_fields
    participant p14 as _string
    participant p15 as _receipt_hash
    participant p16 as _scope_uid
    participant p17 as _receipt_anchor_mapping
    participant p18 as hash_json
    participant p19 as _parse_check
    participant p20 as first_unsafe_path_component
    participant p21 as VerificationReceiptError
    participant p22 as verification_receipt_path
    participant p23 as VerificationContractError
    participant p24 as before_wiki_write
    participant p25 as VerificationReceipt
    participant p26 as after_wiki_write
    participant p27 as formatted_json_text
    participant p28 as _receipt_to_payload
    participant p29 as Path (src/llm_wiki_cli/services…rite_verification_receipt)
    participant p30 as root.is_symlink
    p0->>p1: verify
    p0->>p2: write_verification_receipt
    p1->>p3: build_verification_receipt
    p2->>p4: serialize_verification_receipt
    p1->>p5: run_verification
    p2->>p6: write_bytes_atomic
    p4->>p7: formatted_json_bytes
    p4->>p8: verification_receipt_to_payload
    p5->>p9: _selected_contracts
    p8->>p10: validate_verification_receipt
    p9->>p11: _checker_id
    p10->>p12: _object
    p10->>p13: _exact_fields
    p10->>p14: _string
    p10->>p15: _receipt_hash
    p10->>p16: _scope_uid
    p10->>p17: _receipt_anchor_mapping
    p10->>p18: hash_json
    p10->>p19: _parse_check
    p2->>p20: first_unsafe_path_component
    p2->>p21: VerificationReceiptError
    p2->>p22: verification_receipt_path
    p3->>p23: VerificationContractError
    p6->>p24: before_wiki_write
    p3->>p25: VerificationReceipt
    p6->>p26: after_wiki_write
    p7->>p27: formatted_json_text
    p8->>p28: _receipt_to_payload
    p2-->>p29: Path (src/llm_wiki_cli/services…rite_verification_receipt)(wiki_dir)
    p2-->>p30: root.is_symlink
```

> Call sequence diagram shows 30 of 211 interactions; 181 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 79 (78 omitted); unresolved 1 of 33 (32 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/verification_contracts.py:build_verification_receipt` | 3 | - | external | 6 |
| `src/llm_wiki_cli/services/verification_contracts.py:build_verification_receipt` | 3 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:run_verification` | 13 | - | external | 3 |
| `src/llm_wiki_cli/services/verification_contracts.py:_selected_contracts` | 16 | - | external | 11 |
| `src/llm_wiki_cli/services/verification_contracts.py:_selected_contracts` | 16 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 7 |
| `src/llm_wiki_cli/services/verification_contracts.py:_checker_id` | 31 | - | external | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_checker_id` | 31 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_checker_id` | 31 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 1 |
> Omission summary shows 8 of 48 groups; 40 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 100; effect analysis evaluated: 55, partial: 1, unavailable: 44. Counts include steps omitted from the displayed trace.

Collector observations for 56 source steps with known totals: observed: 223, emitted: 222, omitted: 1. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `verify_and_write_receipt` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `verify` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `build_verification_receipt` | `available` | `evaluated` | `available` | `8` | `8` | `0` |
| `isinstance (src/llm_wiki_cli/services…uild_verification_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…uild_verification_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `tuple (src/llm_wiki_cli/services…uild_verification_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `VerificationContractError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `any` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…uild_verification_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `VerificationContractError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `all` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `VerificationReceipt` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. verify_and_write_receipt"]
    s2["2. verify"]
    s3["3. build_verification_receipt"]
    s4["4. isinstance (src/llm_wiki_cli/services…uild_verification_receipt)"]
    s5["5. TypeError (src/llm_wiki_cli/services…uild_verification_receipt)"]
    s6["6. tuple (src/llm_wiki_cli/services…uild_verification_receipt)"]
    s7["7. VerificationContractError"]
    s8["8. any"]
    s9["9. isinstance (src/llm_wiki_cli/services…uild_verification_receipt)"]
    s10["10. VerificationContractError"]
    s11["11. all"]
    s12["12. VerificationReceipt"]
    s1 -->|"verify(context, checker_ids)"| s2
    s2 -->|"build_verification_receipt(context, run_verification(...))"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…uild_verification_receipt)(context, VerificationContext)" .-> s4
    s3 -. "TypeError (src/llm_wiki_cli/services…uild_verification_receipt)('context must be a VerificationContext')" .-> s5
    s3 -. "tuple (src/llm_wiki_cli/services…uild_verification_receipt)(checks)" .-> s6
    s3 -->|"VerificationContractError('checks must not be empty')"| s7
    s3 -. "any(...)" .-> s8
    s3 -. "isinstance (src/llm_wiki_cli/services…uild_verification_receipt)(check, VerificationCheckResult)" .-> s9
    s3 -->|"VerificationContractError('checks must contain VerificationCheckResult values')"| s10
    s3 -. "all(...)" .-> s11
    s3 -->|"VerificationReceipt(…)"| s12
    click s1 "../modules/verification_contracts.md"
    click s2 "../modules/verification_contracts.md"
    click s3 "../modules/verification_contracts.md"
    click s7 "../modules/verification_contracts.md"
    click s10 "../modules/verification_contracts.md"
    click s12 "../modules/verification_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `verify_and_write_receipt` | `wiki_dir: str \| Path`, `context: VerificationContext`, `checker_ids: Sequence[str] \| None` | - | - | `receipt` |
| `verify` | `context: VerificationContext`, `checker_ids: Sequence[str] \| None` | - | - | `build_verification_receipt(...)` |
| `build_verification_receipt` | `context: VerificationContext`, `checks: Sequence[VerificationCheckResult]` | `VerificationContext`, `VerificationCheckResult`, `VerificationResult`, `VerificationResult`, `VerificationResult` | - | `VerificationReceipt(...)` |
| `isinstance (src/llm_wiki_cli/services…uild_verification_receipt)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…uild_verification_receipt)` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…uild_verification_receipt)` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |
| `any` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…uild_verification_receipt)` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |
| `all` | - | - | - | - |
| `VerificationReceipt` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| verify_and_write_receipt | verify | 1026 | `verify(context, checker_ids)` |
| verify | build_verification_receipt | 770 | `build_verification_receipt(context, run_verification(...))` |
| build_verification_receipt | isinstance (src/llm_wiki_cli/services…uild_verification_receipt) | 731 | `isinstance(context, VerificationContext)` |
| build_verification_receipt | TypeError (src/llm_wiki_cli/services…uild_verification_receipt) | 732 | `TypeError('context must be a VerificationContext')` |
| build_verification_receipt | tuple (src/llm_wiki_cli/services…uild_verification_receipt) | 733 | `tuple(checks)` |
| build_verification_receipt | VerificationContractError | 735 | `VerificationContractError('checks must not be empty')` |
| build_verification_receipt | any | 736 | `any(...)` |
| build_verification_receipt | isinstance (src/llm_wiki_cli/services…uild_verification_receipt) | 737 | `isinstance(check, VerificationCheckResult)` |
| build_verification_receipt | VerificationContractError | 740 | `VerificationContractError('checks must contain VerificationCheckResult values')` |
| build_verification_receipt | all | 745 | `all(...)` |
| build_verification_receipt | VerificationReceipt | 751 | `VerificationReceipt(knowledge_hash=context.knowledge_hash, scope_uid=context.scope_uid, scope_hash=context.scope_hash, evidence=context.evidence, evidence_hash=context.evidence_hash, evaluated_snapshot=context.evaluated_snapshot, snapshot_hash=context.snapshot_hash, result=result, checks=normalized_checks)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_verification_receipt` | `isinstance` | 731 |
| external_call | `build_verification_receipt` | `TypeError` | 732 |
| external_call | `build_verification_receipt` | `any` | 736 |
| external_call | `build_verification_receipt` | `isinstance` | 737 |
| external_call | `build_verification_receipt` | `all` | 745 |
| step_limit | `verify_and_write_receipt` | `first 12 steps` | 0 |
| truncated_flow | `verify_and_write_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `verify_and_write_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
