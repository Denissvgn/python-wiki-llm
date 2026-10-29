# parse_utc_timestamp

**Entry point:** `parse_utc_timestamp` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as parse_utc_timestamp
    participant p1 as require_trimmed_text
    participant p2 as any
    participant p3 as ord
    participant p4 as parsed.endswith
    participant p5 as datetime.fromisoformat
    participant p6 as timestamp.utcoffset
    participant p7 as require_nonempty_text
    participant p8 as isinstance
    participant p9 as value.strip
    participant p10 as contains_control_character
    participant p11 as pattern.search
    p0->>p1: require_trimmed_text
    p0-->>p2: any(...)
    p0-->>p3: ord(character)
    p0-->>p4: parsed.endswith('Z')
    p0-->>p4: parsed.endswith('Z')
    p0-->>p5: datetime.fromisoformat(normalized)
    p0-->>p6: timestamp.utcoffset
    p1->>p7: require_nonempty_text
    p7-->>p8: isinstance(value, str)
    p7-->>p9: value.strip
    p7->>p10: contains_control_character
    p10-->>p11: pattern.search(value)
```

> Call sequence diagram shows 12 of 12 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 4 (0 omitted); unresolved 5 of 5 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 4; effect analysis evaluated: 4, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. parse_utc_timestamp"]
    s2["2. require_trimmed_text"]
    s3["3. require_nonempty_text"]
    s4["4. isinstance"]
    s5["5. value.strip"]
    s6["6. contains_control_character"]
    s7["7. pattern.search"]
    s8["8. any"]
    s9["9. ord"]
    s10["10. parsed.endswith"]
    s11["11. parsed.endswith"]
    s12["12. datetime.fromisoformat"]
    s1 -->|"require_trimmed_text(value, error=string_error, reject_control_characters=False)"| s2
    s2 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s3
    s3 -. "isinstance(value, str)" .-> s4
    s3 -. "value.strip(data not statically known)" .-> s5
    s3 -->|"contains_control_character(parsed, reject_delete_character=reject_delete_character)"| s6
    s6 -. "pattern.search(value)" .-> s7
    s1 -. "any(...)" .-> s8
    s1 -. "ord(character)" .-> s9
    s1 -. "parsed.endswith('Z')" .-> s10
    s1 -. "parsed.endswith('Z')" .-> s11
    s1 -. "datetime.fromisoformat(normalized)" .-> s12
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s3 "../modules/validation.md"
    click s6 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `parse_utc_timestamp` | `value: object`, `string_error: Exception`, `timestamp_error: Exception`, `require_z: bool`, `reject_control_characters: bool`, `control_error: Exception \| None`, `z_error: Exception \| None`, `utc_error: Exception \| None` | `_ZERO_UTC_OFFSET` | - | `(...)` |
| `require_trimmed_text` | `value: object`, `error: Exception`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: Exception`, `trim_error: Exception \| None`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `contains_control_character` | `value: str`, `reject_delete_character: bool` | `_ASCII_CONTROL_DELETE`, `_ASCII_CONTROL` | - | `...` |
| `pattern.search` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |
| `parsed.endswith` | - | - | - | - |
| `parsed.endswith` | - | - | - | - |
| `datetime.fromisoformat` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| parse_utc_timestamp | require_trimmed_text | 1207 | `require_trimmed_text(value, error=string_error, reject_control_characters=False)` |
| require_trimmed_text | require_nonempty_text | 696 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance | 623 | `isinstance(value, str)` |
| require_nonempty_text | value.strip | 625 | `value.strip(data not statically known)` |
| require_nonempty_text | contains_control_character | 631 | `contains_control_character(parsed, reject_delete_character=reject_delete_character)` |
| contains_control_character | pattern.search | 685 | `pattern.search(value)` |
| parse_utc_timestamp | any | 1212 | `any(...)` |
| parse_utc_timestamp | ord | 1213 | `ord(character)` |
| parse_utc_timestamp | parsed.endswith | 1216 | `parsed.endswith('Z')` |
| parse_utc_timestamp | parsed.endswith | 1218 | `parsed.endswith('Z')` |
| parse_utc_timestamp | datetime.fromisoformat | 1220 | `datetime.fromisoformat(normalized)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_nonempty_text` | `isinstance` | 623 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 625 |
| unresolved_call | `contains_control_character` | `pattern.search` | 685 |
| external_call | `parse_utc_timestamp` | `any` | 1212 |
| external_call | `parse_utc_timestamp` | `ord` | 1213 |
| unresolved_call | `parse_utc_timestamp` | `parsed.endswith` | 1216 |
| unresolved_call | `parse_utc_timestamp` | `parsed.endswith` | 1218 |
| external_call | `parse_utc_timestamp` | `datetime.fromisoformat` | 1220 |
| step_limit | `parse_utc_timestamp` | `first 12 steps` | 0 |

## Behavior

This flow starts at `parse_utc_timestamp` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
