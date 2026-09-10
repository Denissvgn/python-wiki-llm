# verify

**Entry point:** `verify` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as verify
    participant p1 as build_verification_receipt
    participant p2 as isinstance (src/llm_wiki_cli/services…build_verification_receipt)
    participant p3 as TypeError (src/llm_wiki_cli/services…build_verification_receipt)
    participant p4 as tuple (src/llm_wiki_cli/services…build_verification_receipt)
    participant p5 as VerificationContractError
    participant p6 as any
    participant p7 as all
    participant p8 as VerificationReceipt
    participant p9 as run_verification
    participant p10 as isinstance (src/llm_wiki_cli/services…tracts.py:run_verification)
    participant p11 as TypeError (src/llm_wiki_cli/services…tracts.py:run_verification)
    participant p12 as _selected_contracts
    participant p13 as isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    participant p14 as tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    participant p15 as sorted
    participant p16 as len
    participant p17 as set
    participant p18 as UnknownVerificationCheckerError
    participant p19 as _checker_id
    participant p20 as isinstance (src/llm_wiki_cli/services…n_contracts.py:_checker_id)
    p0->>p1: build_verification_receipt
    p1-->>p2: isinstance (src/llm_wiki_cli/services…build_verification_receipt)
    p1-->>p3: TypeError (src/llm_wiki_cli/services…build_verification_receipt)
    p1-->>p4: tuple (src/llm_wiki_cli/services…build_verification_receipt)
    p1->>p5: VerificationContractError
    p1-->>p6: any
    p1-->>p2: isinstance (src/llm_wiki_cli/services…build_verification_receipt)
    p1->>p5: VerificationContractError
    p1-->>p7: all
    p1->>p8: VerificationReceipt
    p0->>p9: run_verification
    p9-->>p10: isinstance (src/llm_wiki_cli/services…tracts.py:run_verification)
    p9-->>p11: TypeError (src/llm_wiki_cli/services…tracts.py:run_verification)
    p9->>p12: _selected_contracts
    p12-->>p13: isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    p12->>p5: VerificationContractError
    p12-->>p14: tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    p12-->>p15: sorted
    p12-->>p14: tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    p12->>p5: VerificationContractError
    p12-->>p16: len
    p12->>p5: VerificationContractError
    p12-->>p16: len
    p12-->>p16: len
    p12-->>p17: set
    p12->>p5: VerificationContractError
    p12-->>p13: isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    p12->>p18: UnknownVerificationCheckerError
    p12->>p19: _checker_id
    p19-->>p20: isinstance (src/llm_wiki_cli/services…n_contracts.py:_checker_id)
```

> Call sequence diagram shows 30 of 39 interactions; 9 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. verify"]
    s2["2. build_verification_receipt"]
    s3["3. isinstance (src/llm_wiki_cli/services…build_verification_receipt)"]
    s4["4. TypeError (src/llm_wiki_cli/services…build_verification_receipt)"]
    s5["5. tuple (src/llm_wiki_cli/services…build_verification_receipt)"]
    s6["6. VerificationContractError"]
    s7["7. any"]
    s8["8. isinstance (src/llm_wiki_cli/services…build_verification_receipt)"]
    s9["9. VerificationContractError"]
    s10["10. all"]
    s11["11. VerificationReceipt"]
    s12["12. run_verification"]
    s1 -->|"build_verification_receipt(context, run_verification(...))"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…build_verification_receipt)(context, VerificationContext)" .-> s3
    s2 -. "TypeError (src/llm_wiki_cli/services…build_verification_receipt)('context must be a VerificationContext')" .-> s4
    s2 -. "tuple (src/llm_wiki_cli/services…build_verification_receipt)(checks)" .-> s5
    s2 -->|"VerificationContractError('checks must not be empty')"| s6
    s2 -. "any(...)" .-> s7
    s2 -. "isinstance (src/llm_wiki_cli/services…build_verification_receipt)(check, VerificationCheckResult)" .-> s8
    s2 -->|"VerificationContractError('checks must contain VerificationCheckResult values')"| s9
    s2 -. "all(...)" .-> s10
    s2 -->|"VerificationReceipt(…)"| s11
    s1 -->|"run_verification(context, checker_ids)"| s12
    click s1 "../modules/verification_contracts.md"
    click s2 "../modules/verification_contracts.md"
    click s6 "../modules/verification_contracts.md"
    click s9 "../modules/verification_contracts.md"
    click s11 "../modules/verification_contracts.md"
    click s12 "../modules/verification_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `verify` | `context: VerificationContext`, `checker_ids: Sequence[str] \| None` | - | - | `build_verification_receipt(...)` |
| `build_verification_receipt` | `context: VerificationContext`, `checks: Sequence[VerificationCheckResult]` | `VerificationContext`, `VerificationCheckResult`, `VerificationResult`, `VerificationResult`, `VerificationResult` | - | `VerificationReceipt(...)` |
| `isinstance (src/llm_wiki_cli/services…build_verification_receipt)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…build_verification_receipt)` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…build_verification_receipt)` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |
| `any` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…build_verification_receipt)` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |
| `all` | - | - | - | - |
| `VerificationReceipt` | - | - | - | - |
| `run_verification` | `context: VerificationContext`, `checker_ids: Sequence[str] \| None` | `VerificationContext` | - | `tuple(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| verify | build_verification_receipt | 770 | `build_verification_receipt(context, run_verification(...))` |
| build_verification_receipt | isinstance (src/llm_wiki_cli/services…build_verification_receipt) | 731 | `isinstance(context, VerificationContext)` |
| build_verification_receipt | TypeError (src/llm_wiki_cli/services…build_verification_receipt) | 732 | `TypeError('context must be a VerificationContext')` |
| build_verification_receipt | tuple (src/llm_wiki_cli/services…build_verification_receipt) | 733 | `tuple(checks)` |
| build_verification_receipt | VerificationContractError | 735 | `VerificationContractError('checks must not be empty')` |
| build_verification_receipt | any | 736 | `any(...)` |
| build_verification_receipt | isinstance (src/llm_wiki_cli/services…build_verification_receipt) | 737 | `isinstance(check, VerificationCheckResult)` |
| build_verification_receipt | VerificationContractError | 740 | `VerificationContractError('checks must contain VerificationCheckResult values')` |
| build_verification_receipt | all | 745 | `all(...)` |
| build_verification_receipt | VerificationReceipt | 751 | `VerificationReceipt(knowledge_hash=context.knowledge_hash, scope_uid=context.scope_uid, scope_hash=context.scope_hash, evidence=context.evidence, evidence_hash=context.evidence_hash, evaluated_snapshot=context.evaluated_snapshot, snapshot_hash=context.snapshot_hash, result=result, checks=normalized_checks)` |
| verify | run_verification | 772 | `run_verification(context, checker_ids)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_verification_receipt` | `isinstance` | 731 |
| external_call | `build_verification_receipt` | `TypeError` | 732 |
| external_call | `build_verification_receipt` | `any` | 736 |
| external_call | `build_verification_receipt` | `isinstance` | 737 |
| external_call | `build_verification_receipt` | `all` | 745 |
| step_limit | `verify` | `first 12 steps` | 0 |

## Behavior

This flow starts at `verify` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
