# require_exact_choice

**Entry point:** `require_exact_choice` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_exact_choice
    participant p1 as require_string
    participant p2 as isinstance
    participant p3 as encode
    participant p4 as frozenset
    p0->>p1: require_string
    p1-->>p2: isinstance
    p1-->>p3: encode
    p0-->>p4: frozenset
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_exact_choice"]
    s2["2. require_string"]
    s3["3. isinstance"]
    s4["4. encode"]
    s5["5. frozenset"]
    s1 -->|"require_string(value, error=error)"| s2
    s2 -. "isinstance(value, str)" .-> s3
    s2 -. "value.encode('utf-8')" .-> s4
    s1 -. "frozenset(choices)" .-> s5
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_exact_choice` | `value: object`, `choices: Iterable[str]`, `error: Exception` | - | - | `parsed` |
| `require_string` | `value: object`, `error: Exception`, `utf8_error: Exception \| None` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `frozenset` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_exact_choice | require_string | 1054 | `require_string(value, error=error)` |
| require_string | isinstance | 706 | `isinstance(value, str)` |
| require_string | encode | 710 | `value.encode('utf-8')` |
| require_exact_choice | frozenset | 1055 | `frozenset(choices)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_string` | `isinstance` | 706 |
| unresolved_call | `require_string` | `value.encode` | 710 |
| unresolved_call | `require_exact_choice` | `frozenset` | 1055 |

## Behavior

This flow starts at `require_exact_choice` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
