# require_uuid

**Entry point:** `require_uuid` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_uuid
    participant p1 as require_trimmed_text
    participant p2 as require_nonempty_text
    participant p3 as isinstance
    participant p4 as strip
    participant p5 as any
    participant p6 as ord
    participant p7 as str
    participant p8 as UUID
    p0->>p1: require_trimmed_text
    p1->>p2: require_nonempty_text
    p2-->>p3: isinstance
    p2-->>p4: strip
    p2-->>p5: any
    p2-->>p6: ord
    p2-->>p6: ord
    p0-->>p7: str
    p0-->>p8: UUID
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_uuid"]
    s2["2. require_trimmed_text"]
    s3["3. require_nonempty_text"]
    s4["4. isinstance"]
    s5["5. strip"]
    s6["6. any"]
    s7["7. ord"]
    s8["8. ord"]
    s9["9. str"]
    s10["10. UUID"]
    s1 -->|"require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)"| s2
    s2 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s3
    s3 -. "isinstance(value, str)" .-> s4
    s3 -. "value.strip(data not statically known)" .-> s5
    s3 -. "any(...)" .-> s6
    s3 -. "ord(character)" .-> s7
    s3 -. "ord(character)" .-> s8
    s1 -. "str(uuid.UUID(...))" .-> s9
    s1 -. "uuid.UUID(parsed)" .-> s10
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s3 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_uuid` | `value: object`, `text_error: Exception`, `uuid_error: Exception`, `canonical_error: Exception`, `reject_control_characters: bool` | - | - | `parsed` |
| `require_trimmed_text` | `value: object`, `error: Exception`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: Exception`, `trim_error: Exception \| None`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |
| `ord` | - | - | - | - |
| `str` | - | - | - | - |
| `UUID` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_uuid | require_trimmed_text | 1126 | `require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)` |
| require_trimmed_text | require_nonempty_text | 658 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance | 574 | `isinstance(value, str)` |
| require_nonempty_text | strip | 576 | `value.strip(data not statically known)` |
| require_nonempty_text | any | 582 | `any(...)` |
| require_nonempty_text | ord | 583 | `ord(character)` |
| require_nonempty_text | ord | 584 | `ord(character)` |
| require_uuid | str | 1132 | `str(uuid.UUID(...))` |
| require_uuid | UUID | 1132 | `uuid.UUID(parsed)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_nonempty_text` | `isinstance` | 574 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 576 |
| unresolved_call | `require_nonempty_text` | `any` | 582 |
| unresolved_call | `require_nonempty_text` | `ord` | 583 |
| unresolved_call | `require_nonempty_text` | `ord` | 584 |
| external_call | `require_uuid` | `uuid.UUID` | 1132 |

## Behavior

This flow starts at `require_uuid` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
