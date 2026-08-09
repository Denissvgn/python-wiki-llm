# run_verification

**Entry point:** `run_verification` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run_verification
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as _selected_contracts
    participant p4 as VerificationContractError
    participant p5 as tuple
    participant p6 as sorted
    participant p7 as len
    participant p8 as set
    participant p9 as UnknownVerificationCheckerError
    participant p10 as _checker_id
    participant p11 as fullmatch
    participant p12 as append
    participant p13 as run
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: _selected_contracts
    p3-->>p1: isinstance
    p3->>p4: VerificationContractError
    p3-->>p5: tuple
    p3-->>p6: sorted
    p3-->>p5: tuple
    p3->>p4: VerificationContractError
    p3-->>p7: len
    p3->>p4: VerificationContractError
    p3-->>p7: len
    p3-->>p7: len
    p3-->>p8: set
    p3->>p4: VerificationContractError
    p3-->>p1: isinstance
    p3->>p9: UnknownVerificationCheckerError
    p3->>p10: _checker_id
    p10-->>p1: isinstance
    p10-->>p11: fullmatch
    p10->>p4: VerificationContractError
    p3->>p9: UnknownVerificationCheckerError
    p3-->>p12: append
    p3->>p9: UnknownVerificationCheckerError
    p3-->>p5: tuple
    p3-->>p6: sorted
    p0-->>p5: tuple
    p0-->>p13: run
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run_verification"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. _selected_contracts"]
    s5["5. isinstance"]
    s6["6. VerificationContractError"]
    s7["7. tuple"]
    s8["8. sorted"]
    s9["9. tuple"]
    s10["10. VerificationContractError"]
    s11["11. len"]
    s12["12. VerificationContractError"]
    s1 -. "isinstance(context, VerificationContext)" .-> s2
    s1 -. "TypeError('context must be a VerificationContext')" .-> s3
    s1 -->|"_selected_contracts(checker_ids)"| s4
    s4 -. "isinstance(checker_ids, (...))" .-> s5
    s4 -->|"VerificationContractError('checker_ids must be a sequence of checker ids, not text')"| s6
    s4 -. "tuple(sorted(...))" .-> s7
    s4 -. "sorted(_CHECKER_REGISTRY)" .-> s8
    s4 -. "tuple(checker_ids)" .-> s9
    s4 -->|"VerificationContractError('at least one checker must be selected')"| s10
    s4 -. "len(selected)" .-> s11
    s4 -->|"VerificationContractError('too many checkers were selected')"| s12
    b0["mutation contracts.append"]
    s4 -. "mutation contracts.append" .-> b0
    click s1 "../modules/verification_contracts.md"
    click s4 "../modules/verification_contracts.md"
    click s6 "../modules/verification_contracts.md"
    click s10 "../modules/verification_contracts.md"
    click s12 "../modules/verification_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run_verification` | `context: VerificationContext`, `checker_ids: Sequence[str] \| None` | `VerificationContext` | - | `tuple(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_selected_contracts` | `checker_ids: Sequence[str] \| None` | `_CHECKER_REGISTRY`, `MAX_CHECKS_PER_RECEIPT`, `VerificationContractError`, `_CHECKER_REGISTRY` | - | `tuple(...)` |
| `isinstance` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |
| `tuple` | - | - | - | - |
| `sorted` | - | - | - | - |
| `tuple` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |
| `len` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run_verification | isinstance | 719 | `isinstance(context, VerificationContext)` |
| run_verification | TypeError | 720 | `TypeError('context must be a VerificationContext')` |
| run_verification | _selected_contracts | 721 | `_selected_contracts(checker_ids)` |
| _selected_contracts | isinstance | 681 | `isinstance(checker_ids, (...))` |
| _selected_contracts | VerificationContractError | 682 | `VerificationContractError('checker_ids must be a sequence of checker ids, not text')` |
| _selected_contracts | tuple | 686 | `tuple(sorted(...))` |
| _selected_contracts | sorted | 686 | `sorted(_CHECKER_REGISTRY)` |
| _selected_contracts | tuple | 688 | `tuple(checker_ids)` |
| _selected_contracts | VerificationContractError | 691 | `VerificationContractError('at least one checker must be selected')` |
| _selected_contracts | len | 692 | `len(selected)` |
| _selected_contracts | VerificationContractError | 693 | `VerificationContractError('too many checkers were selected')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `contracts.append` | `_selected_contracts` | 707 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run_verification` | `isinstance` | 719 |
| unresolved_call | `run_verification` | `TypeError` | 720 |
| unresolved_call | `_selected_contracts` | `isinstance` | 681 |
| unresolved_call | `_selected_contracts` | `sorted` | 686 |
| step_limit | `run_verification` | `first 12 steps` | 0 |

## Behavior

This flow starts at `run_verification` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
