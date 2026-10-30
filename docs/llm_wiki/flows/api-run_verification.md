# run_verification

**Entry point:** `run_verification` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run_verification
    participant p1 as isinstance (src/llm_wiki_cli/services…tracts.py:run_verification)
    participant p2 as TypeError
    participant p3 as _selected_contracts
    participant p4 as tuple (src/llm_wiki_cli/services…tracts.py:run_verification)
    participant p5 as contract.run
    participant p6 as isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    participant p7 as VerificationContractError
    participant p8 as tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)
    participant p9 as sorted
    participant p10 as len
    participant p11 as set
    participant p12 as UnknownVerificationCheckerError
    participant p13 as _checker_id
    participant p14 as contracts.append
    participant p15 as isinstance (src/llm_wiki_cli/services…n_contracts.py:_checker_id)
    participant p16 as _CHECKER_ID_RE.fullmatch
    p0-->>p1: isinstance (src/llm_wiki_cli/services…tracts.py:run_verification)(context, VerificationContext)
    p0-->>p2: TypeError('context must be a VerificationContext')
    p0->>p3: _selected_contracts
    p0-->>p4: tuple (src/llm_wiki_cli/services…tracts.py:run_verification)(...)
    p0-->>p5: contract.run(context)
    p3-->>p6: isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)(checker_ids, (...))
    p3->>p7: VerificationContractError
    p3-->>p8: tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)(sorted(...))
    p3-->>p9: sorted(_CHECKER_REGISTRY)
    p3-->>p8: tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)(checker_ids)
    p3->>p7: VerificationContractError
    p3-->>p10: len(selected)
    p3->>p7: VerificationContractError
    p3-->>p10: len(selected)
    p3-->>p10: len(set(...))
    p3-->>p11: set(selected)
    p3->>p7: VerificationContractError
    p3-->>p6: isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)(checker_id, str)
    p3->>p12: UnknownVerificationCheckerError
    p3->>p13: _checker_id
    p3->>p12: UnknownVerificationCheckerError
    p3-->>p14: contracts.append(_CHECKER_REGISTRY[...])
    p3->>p12: UnknownVerificationCheckerError
    p3-->>p8: tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)(sorted(...))
    p3-->>p9: sorted(contracts, key=...)
    p13-->>p15: isinstance (src/llm_wiki_cli/services…n_contracts.py:_checker_id)(value, str)
    p13-->>p16: _CHECKER_ID_RE.fullmatch(value)
    p13->>p7: VerificationContractError
```

> Call sequence diagram shows 28 of 28 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 15 of 15 (0 omitted); unresolved 3 of 3 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 11; effect analysis evaluated: 3, partial: 0, unavailable: 8. Counts include steps omitted from the displayed trace.

Collector observations for 3 source steps with known totals: observed: 14, emitted: 14, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `run_verification` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_cli/services…tracts.py:run_verification)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_selected_contracts` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `VerificationContractError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `sorted` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `VerificationContractError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `len` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `VerificationContractError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

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
| run_verification | isinstance (src/llm_wiki_cli/services…tracts.py:run_verification) | 748 | `isinstance(context, VerificationContext)` |
| run_verification | TypeError | 749 | `TypeError('context must be a VerificationContext')` |
| run_verification | _selected_contracts | 750 | `_selected_contracts(checker_ids)` |
| _selected_contracts | isinstance (src/llm_wiki_cli/services…cts.py:_selected_contracts) | 710 | `isinstance(checker_ids, (...))` |
| _selected_contracts | VerificationContractError | 711 | `VerificationContractError('checker_ids must be a sequence of checker ids, not text')` |
| _selected_contracts | tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts) | 715 | `tuple(sorted(...))` |
| _selected_contracts | sorted | 715 | `sorted(_CHECKER_REGISTRY)` |
| _selected_contracts | tuple (src/llm_wiki_cli/services…cts.py:_selected_contracts) | 717 | `tuple(checker_ids)` |
| _selected_contracts | VerificationContractError | 720 | `VerificationContractError('at least one checker must be selected')` |
| _selected_contracts | len | 721 | `len(selected)` |
| _selected_contracts | VerificationContractError | 722 | `VerificationContractError('too many checkers were selected')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `contracts.append` | `_selected_contracts` | 736 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run_verification` | `isinstance` | 748 |
| external_call | `run_verification` | `TypeError` | 749 |
| external_call | `_selected_contracts` | `isinstance` | 710 |
| external_call | `_selected_contracts` | `sorted` | 715 |
| step_limit | `run_verification` | `first 12 steps` | 0 |

## Behavior

This flow starts at `run_verification` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
