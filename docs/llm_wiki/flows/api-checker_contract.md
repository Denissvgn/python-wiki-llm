# checker_contract

**Entry point:** `checker_contract` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as checker_contract
    participant p1 as _checker_id
    participant p2 as isinstance
    participant p3 as fullmatch
    participant p4 as VerificationContractError
    participant p5 as UnknownVerificationCheckerError
    p0->>p1: _checker_id
    p1-->>p2: isinstance
    p1-->>p3: fullmatch
    p1->>p4: VerificationContractError
    p0->>p5: UnknownVerificationCheckerError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. checker_contract"]
    s2["2. _checker_id"]
    s3["3. isinstance"]
    s4["4. fullmatch"]
    s5["5. VerificationContractError"]
    s6["6. UnknownVerificationCheckerError"]
    s1 -->|"_checker_id(checker_id, 'checker_id')"| s2
    s2 -. "isinstance(value, str)" .-> s3
    s2 -. "_CHECKER_ID_RE.fullmatch(value)" .-> s4
    s2 -->|"VerificationContractError(...)"| s5
    s1 -->|"UnknownVerificationCheckerError(checker_id)"| s6
    click s1 "../modules/verification_contracts.md"
    click s2 "../modules/verification_contracts.md"
    click s5 "../modules/verification_contracts.md"
    click s6 "../modules/verification_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `checker_contract` | `checker_id: str` | `_CHECKER_REGISTRY` | - | `_CHECKER_REGISTRY[...]` |
| `_checker_id` | `value: object`, `field_name: str` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `fullmatch` | - | - | - | - |
| `VerificationContractError` | - | - | - | - |
| `UnknownVerificationCheckerError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| checker_contract | _checker_id | 671 | `_checker_id(checker_id, 'checker_id')` |
| _checker_id | isinstance | 1359 | `isinstance(value, str)` |
| _checker_id | fullmatch | 1359 | `_CHECKER_ID_RE.fullmatch(value)` |
| _checker_id | VerificationContractError | 1360 | `VerificationContractError(...)` |
| checker_contract | UnknownVerificationCheckerError | 675 | `UnknownVerificationCheckerError(checker_id)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_checker_id` | `isinstance` | 1359 |
| unresolved_call | `_checker_id` | `_CHECKER_ID_RE.fullmatch` | 1359 |

## Behavior

This flow starts at `checker_contract` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
