# verify_and_write_receipt

**Entry point:** `verify_and_write_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as verify_and_write_receipt
    participant p1 as verify
    participant p2 as build_verification_receipt
    participant p3 as isinstance
    participant p4 as TypeError
    participant p5 as tuple
    participant p6 as VerificationContractError
    participant p7 as any
    participant p8 as all
    participant p9 as VerificationReceipt
    participant p10 as run_verification
    participant p11 as _selected_contracts
    participant p12 as sorted
    participant p13 as len
    participant p14 as set
    participant p15 as UnknownVerificationCheckerError
    participant p16 as _checker_id
    p0->>p1: verify
    p1->>p2: build_verification_receipt
    p2-->>p3: isinstance
    p2-->>p4: TypeError
    p2-->>p5: tuple
    p2->>p6: VerificationContractError
    p2-->>p7: any
    p2-->>p3: isinstance
    p2->>p6: VerificationContractError
    p2-->>p8: all
    p2->>p9: VerificationReceipt
    p1->>p10: run_verification
    p10-->>p3: isinstance
    p10-->>p4: TypeError
    p10->>p11: _selected_contracts
    p11-->>p3: isinstance
    p11->>p6: VerificationContractError
    p11-->>p5: tuple
    p11-->>p12: sorted
    p11-->>p5: tuple
    p11->>p6: VerificationContractError
    p11-->>p13: len
    p11->>p6: VerificationContractError
    p11-->>p13: len
    p11-->>p13: len
    p11-->>p14: set
    p11->>p6: VerificationContractError
    p11-->>p3: isinstance
    p11->>p15: UnknownVerificationCheckerError
    p11->>p16: _checker_id
```

> Call sequence diagram shows 30 of 191 interactions; 161 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. verify_and_write_receipt"]
    s2["2. verify"]
    s3["3. build_verification_receipt"]
    s4["4. isinstance"]
    s5["5. TypeError"]
    s6["6. tuple"]
    s7["7. VerificationContractError"]
    s8["8. any"]
    s9["9. isinstance"]
    s10["10. VerificationContractError"]
    s11["11. all"]
    s12["12. VerificationReceipt"]
    s1 -->|"verify(context, checker_ids)"| s2
    s2 -->|"build_verification_receipt(context, run_verification(...))"| s3
    s3 -. "isinstance(context, VerificationContext)" .-> s4
    s3 -. "TypeError('context must be a VerificationContext')" .-> s5
    s3 -. "tuple(checks)" .-> s6
    s3 -->|"VerificationContractError('checks must not be empty')"| s7
    s3 -. "any(...)" .-> s8
    s3 -. "isinstance(check, VerificationCheckResult)" .-> s9
    s3 -->|"VerificationContractError('checks must contain VerificationCheckResult values')"| s10
    s3 -. "all(...)" .-> s11
    s3 -->|"VerificationReceipt(knowledge_hash=context.knowledge_hash, scope_uid=context.scope_uid, scope_hash=context.scope_hash, evidence=context.evidence, evidence_hash…"| s12
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
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `tuple` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |
| `any` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |
| `all` | - | - | - | - |
| `VerificationReceipt` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| verify_and_write_receipt | verify | 1026 | `verify(context, checker_ids)` |
| verify | build_verification_receipt | 770 | `build_verification_receipt(context, run_verification(...))` |
| build_verification_receipt | isinstance | 731 | `isinstance(context, VerificationContext)` |
| build_verification_receipt | TypeError | 732 | `TypeError('context must be a VerificationContext')` |
| build_verification_receipt | tuple | 733 | `tuple(checks)` |
| build_verification_receipt | VerificationContractError | 735 | `VerificationContractError('checks must not be empty')` |
| build_verification_receipt | any | 736 | `any(...)` |
| build_verification_receipt | isinstance | 737 | `isinstance(check, VerificationCheckResult)` |
| build_verification_receipt | VerificationContractError | 740 | `VerificationContractError('checks must contain VerificationCheckResult values')` |
| build_verification_receipt | all | 745 | `all(...)` |
| build_verification_receipt | VerificationReceipt | 751 | `VerificationReceipt(knowledge_hash=context.knowledge_hash, scope_uid=context.scope_uid, scope_hash=context.scope_hash, evidence=context.evidence, evidence_hash=context.evidence_hash, evaluated_snapshot=context.evaluated_snapshot, snapshot_hash=context.snapshot_hash, result=result, checks=normalized_checks)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_verification_receipt` | `isinstance` | 731 |
| unresolved_call | `build_verification_receipt` | `TypeError` | 732 |
| unresolved_call | `build_verification_receipt` | `any` | 736 |
| unresolved_call | `build_verification_receipt` | `isinstance` | 737 |
| unresolved_call | `build_verification_receipt` | `all` | 745 |
| step_limit | `verify_and_write_receipt` | `first 12 steps` | 0 |
| truncated_flow | `verify_and_write_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `verify_and_write_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
