# require_no_control_characters

**Entry point:** `require_no_control_characters` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_no_control_characters
    participant p1 as isinstance
    participant p2 as contains_control_character
    participant p3 as any
    participant p4 as ord
    p0-->>p1: isinstance
    p0->>p2: contains_control_character
    p2-->>p3: any
    p2-->>p4: ord
    p2-->>p4: ord
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_no_control_characters"]
    s2["2. isinstance"]
    s3["3. contains_control_character"]
    s4["4. any"]
    s5["5. ord"]
    s6["6. ord"]
    s1 -. "isinstance(value, str)" .-> s2
    s1 -->|"contains_control_character(value, reject_delete_character=reject_delete_character)"| s3
    s3 -. "any(...)" .-> s4
    s3 -. "ord(character)" .-> s5
    s3 -. "ord(character)" .-> s6
    click s1 "../modules/validation.md"
    click s3 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_no_control_characters` | `value: object`, `error: Exception`, `reject_delete_character: bool` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `contains_control_character` | `value: str`, `reject_delete_character: bool` | - | - | `any(...)` |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |
| `ord` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_no_control_characters | isinstance | 628 | `isinstance(value, str)` |
| require_no_control_characters | contains_control_character | 628 | `contains_control_character(value, reject_delete_character=reject_delete_character)` |
| contains_control_character | any | 643 | `any(...)` |
| contains_control_character | ord | 644 | `ord(character)` |
| contains_control_character | ord | 645 | `ord(character)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_no_control_characters` | `isinstance` | 628 |
| unresolved_call | `contains_control_character` | `any` | 643 |
| unresolved_call | `contains_control_character` | `ord` | 644 |
| unresolved_call | `contains_control_character` | `ord` | 645 |

## Behavior

This flow starts at `require_no_control_characters` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
