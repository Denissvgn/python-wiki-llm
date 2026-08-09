# parse_utc_timestamp

**Entry point:** `parse_utc_timestamp` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as parse_utc_timestamp
    participant p1 as require_trimmed_text
    participant p2 as require_nonempty_text
    participant p3 as isinstance
    participant p4 as strip
    participant p5 as any
    participant p6 as ord
    participant p7 as endswith
    participant p8 as fromisoformat
    participant p9 as utcoffset
    p0->>p1: require_trimmed_text
    p1->>p2: require_nonempty_text
    p2-->>p3: isinstance
    p2-->>p4: strip
    p2-->>p5: any
    p2-->>p6: ord
    p2-->>p6: ord
    p0-->>p5: any
    p0-->>p6: ord
    p0-->>p7: endswith
    p0-->>p7: endswith
    p0-->>p8: fromisoformat
    p0-->>p9: utcoffset
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. parse_utc_timestamp"]
    s2["2. require_trimmed_text"]
    s3["3. require_nonempty_text"]
    s4["4. isinstance"]
    s5["5. strip"]
    s6["6. any"]
    s7["7. ord"]
    s8["8. ord"]
    s9["9. any"]
    s10["10. ord"]
    s11["11. endswith"]
    s12["12. endswith"]
    s1 -->|"require_trimmed_text(value, error=string_error, reject_control_characters=False)"| s2
    s2 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s3
    s3 -. "isinstance(value, str)" .-> s4
    s3 -. "value.strip(data not statically known)" .-> s5
    s3 -. "any(...)" .-> s6
    s3 -. "ord(character)" .-> s7
    s3 -. "ord(character)" .-> s8
    s1 -. "any(...)" .-> s9
    s1 -. "ord(character)" .-> s10
    s1 -. "parsed.endswith('Z')" .-> s11
    s1 -. "parsed.endswith('Z')" .-> s12
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s3 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `parse_utc_timestamp` | `value: object`, `string_error: Exception`, `timestamp_error: Exception`, `require_z: bool`, `reject_control_characters: bool`, `control_error: Exception \| None`, `z_error: Exception \| None`, `utc_error: Exception \| None` | `_ZERO_UTC_OFFSET` | - | `(...)` |
| `require_trimmed_text` | `value: object`, `error: Exception`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: Exception`, `trim_error: Exception \| None`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |
| `ord` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |
| `endswith` | - | - | - | - |
| `endswith` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| parse_utc_timestamp | require_trimmed_text | 1169 | `require_trimmed_text(value, error=string_error, reject_control_characters=False)` |
| require_trimmed_text | require_nonempty_text | 658 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance | 574 | `isinstance(value, str)` |
| require_nonempty_text | strip | 576 | `value.strip(data not statically known)` |
| require_nonempty_text | any | 582 | `any(...)` |
| require_nonempty_text | ord | 583 | `ord(character)` |
| require_nonempty_text | ord | 584 | `ord(character)` |
| parse_utc_timestamp | any | 1174 | `any(...)` |
| parse_utc_timestamp | ord | 1175 | `ord(character)` |
| parse_utc_timestamp | endswith | 1178 | `parsed.endswith('Z')` |
| parse_utc_timestamp | endswith | 1180 | `parsed.endswith('Z')` |

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
| unresolved_call | `parse_utc_timestamp` | `any` | 1174 |
| unresolved_call | `parse_utc_timestamp` | `ord` | 1175 |
| unresolved_call | `parse_utc_timestamp` | `parsed.endswith` | 1178 |
| unresolved_call | `parse_utc_timestamp` | `parsed.endswith` | 1180 |
| step_limit | `parse_utc_timestamp` | `first 12 steps` | 0 |

## Behavior

This flow starts at `parse_utc_timestamp` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
