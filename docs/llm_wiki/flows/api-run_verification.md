# run_verification

**Entry point:** `run_verification` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run_verification
    participant p1 as isinstance (src/llm_wiki_cli/services…tracts.py:run_verification)
    participant p2 as TypeError
    participant p3 as _selected_contracts
    participant p4 as isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    participant p5 as VerificationContractError
    participant p6 as tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    participant p7 as sorted
    participant p8 as len
    participant p9 as set
    participant p10 as UnknownVerificationCheckerError
    participant p11 as _checker_id
    participant p12 as isinstance (src/llm_wiki_cli/services…n_contracts.py:_checker_id)
    participant p13 as _CHECKER_ID_RE.fullmatch
    participant p14 as contracts.append
    participant p15 as tuple (src/llm_wiki_cli/services…tracts.py:run_verification)
    participant p16 as contract.run
    p0-->>p1: isinstance (src/llm_wiki_cli/services…tracts.py:run_verification)
    p0-->>p2: TypeError
    p0->>p3: _selected_contracts
    p3-->>p4: isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    p3->>p5: VerificationContractError
    p3-->>p6: tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    p3-->>p7: sorted
    p3-->>p6: tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    p3->>p5: VerificationContractError
    p3-->>p8: len
    p3->>p5: VerificationContractError
    p3-->>p8: len
    p3-->>p8: len
    p3-->>p9: set
    p3->>p5: VerificationContractError
    p3-->>p4: isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    p3->>p10: UnknownVerificationCheckerError
    p3->>p11: _checker_id
    p11-->>p12: isinstance (src/llm_wiki_cli/services…n_contracts.py:_checker_id)
    p11-->>p13: _CHECKER_ID_RE.fullmatch
    p11->>p5: VerificationContractError
    p3->>p10: UnknownVerificationCheckerError
    p3-->>p14: contracts.append
    p3->>p10: UnknownVerificationCheckerError
    p3-->>p6: tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    p3-->>p7: sorted
    p0-->>p15: tuple (src/llm_wiki_cli/services…tracts.py:run_verification)
    p0-->>p16: contract.run
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run_verification"]
    s2["2. isinstance (src/llm_wiki_cli/services…tracts.py:run_verification)"]
    s3["3. TypeError"]
    s4["4. _selected_contracts"]
    s5["5. isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)"]
    s6["6. VerificationContractError"]
    s7["7. tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)"]
    s8["8. sorted"]
    s9["9. tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)"]
    s10["10. VerificationContractError"]
    s11["11. len"]
    s12["12. VerificationContractError"]
    s1 -. "isinstance (src/llm_wiki_cli/services…tracts.py:run_verification)(context, VerificationContext)" .-> s2
    s1 -. "TypeError('context must be a VerificationContext')" .-> s3
    s1 -->|"_selected_contracts(checker_ids)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)(checker_ids, (...))" .-> s5
    s4 -->|"VerificationContractError('checker_ids must be a sequence of checker ids, not text')"| s6
    s4 -. "tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)(sorted(...))" .-> s7
    s4 -. "sorted(_CHECKER_REGISTRY)" .-> s8
    s4 -. "tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)(checker_ids)" .-> s9
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
| `isinstance (src/llm_wiki_cli/services…tracts.py:run_verification)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_selected_contracts` | `checker_ids: Sequence[str] \| None` | `_CHECKER_REGISTRY`, `MAX_CHECKS_PER_RECEIPT`, `VerificationContractError`, `_CHECKER_REGISTRY` | - | `tuple(...)` |
| `isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)` | - | - | - | - |
| `sorted` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |
| `len` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run_verification | isinstance (src/llm_wiki_cli/services…tracts.py:run_verification) | 719 | `isinstance(context, VerificationContext)` |
| run_verification | TypeError | 720 | `TypeError('context must be a VerificationContext')` |
| run_verification | _selected_contracts | 721 | `_selected_contracts(checker_ids)` |
| _selected_contracts | isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts) | 681 | `isinstance(checker_ids, (...))` |
| _selected_contracts | VerificationContractError | 682 | `VerificationContractError('checker_ids must be a sequence of checker ids, not text')` |
| _selected_contracts | tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts) | 686 | `tuple(sorted(...))` |
| _selected_contracts | sorted | 686 | `sorted(_CHECKER_REGISTRY)` |
| _selected_contracts | tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts) | 688 | `tuple(checker_ids)` |
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
| external_call | `run_verification` | `isinstance` | 719 |
| external_call | `run_verification` | `TypeError` | 720 |
| external_call | `_selected_contracts` | `isinstance` | 681 |
| external_call | `_selected_contracts` | `sorted` | 686 |
| step_limit | `run_verification` | `first 12 steps` | 0 |

## Behavior

This flow starts at `run_verification` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
