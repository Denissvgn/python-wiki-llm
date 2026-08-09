# is_canonical_uuid

**Entry point:** `is_canonical_uuid` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_canonical_uuid
    participant p1 as SharedValidationError
    participant p2 as require_uuid
    participant p3 as require_trimmed_text
    participant p4 as require_nonempty_text
    participant p5 as isinstance
    participant p6 as strip
    participant p7 as any
    participant p8 as ord
    participant p9 as str
    participant p10 as UUID
    p0->>p1: SharedValidationError
    p0->>p2: require_uuid
    p2->>p3: require_trimmed_text
    p3->>p4: require_nonempty_text
    p4-->>p5: isinstance
    p4-->>p6: strip
    p4-->>p7: any
    p4-->>p8: ord
    p4-->>p8: ord
    p2-->>p9: str
    p2-->>p10: UUID
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. is_canonical_uuid"]
    s2["2. SharedValidationError"]
    s3["3. require_uuid"]
    s4["4. require_trimmed_text"]
    s5["5. require_nonempty_text"]
    s6["6. isinstance"]
    s7["7. strip"]
    s8["8. any"]
    s9["9. ord"]
    s10["10. ord"]
    s11["11. str"]
    s12["12. UUID"]
    s1 -->|"SharedValidationError('value must be a canonical UUID')"| s2
    s1 -->|"require_uuid(value, text_error=error, uuid_error=error, canonical_error=error)"| s3
    s3 -->|"require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)"| s4
    s4 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s5
    s5 -. "isinstance(value, str)" .-> s6
    s5 -. "value.strip(data not statically known)" .-> s7
    s5 -. "any(...)" .-> s8
    s5 -. "ord(character)" .-> s9
    s5 -. "ord(character)" .-> s10
    s3 -. "str(uuid.UUID(...))" .-> s11
    s3 -. "uuid.UUID(parsed)" .-> s12
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s3 "../modules/validation.md"
    click s4 "../modules/validation.md"
    click s5 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_canonical_uuid` | `value: object` | - | - | `False`, `True` |
| `SharedValidationError` | - | - | - | - |
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
| is_canonical_uuid | SharedValidationError | 1143 | `SharedValidationError('value must be a canonical UUID')` |
| is_canonical_uuid | require_uuid | 1145 | `require_uuid(value, text_error=error, uuid_error=error, canonical_error=error)` |
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

This flow starts at `is_canonical_uuid` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
