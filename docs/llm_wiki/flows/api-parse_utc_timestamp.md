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
    participant p8 as isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)
    participant p9 as _validation_error
    participant p10 as value.strip
    participant p11 as contains_control_character
    participant p12 as isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)
    participant p13 as pattern.search
    participant p14 as error
    p0->>p1: require_trimmed_text
    p0-->>p2: any(...)
    p0-->>p3: ord(character)
    p0-->>p4: parsed.endswith('Z')
    p0-->>p4: parsed.endswith('Z')
    p0-->>p5: datetime.fromisoformat(normalized)
    p0-->>p6: timestamp.utcoffset
    p1->>p7: require_nonempty_text
    p7-->>p8: isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)(value, str)
    p7->>p9: _validation_error
    p7-->>p10: value.strip
    p7->>p9: _validation_error
    p7->>p9: _validation_error
    p7->>p11: contains_control_character
    p7->>p9: _validation_error
    p9-->>p12: isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)
    p11-->>p13: pattern.search(value)
    p9-->>p14: error(context)
```

> Call sequence diagram shows 18 of 18 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 5 (0 omitted); unresolved 6 of 6 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 8; effect analysis evaluated: 8, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 8 source steps with known totals: observed: 41, emitted: 41, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. parse_utc_timestamp"]
    s2["2. require_trimmed_text"]
    s3["3. require_nonempty_text"]
    s4["4. isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)"]
    s5["5. _validation_error"]
    s6["6. isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)"]
    s7["7. error"]
    s8["8. value.strip"]
    s9["9. _validation_error"]
    s10["10. _validation_error"]
    s11["11. contains_control_character"]
    s12["12. pattern.search"]
    s1 -->|"require_trimmed_text(value, error=string_error, reject_control_characters=False)"| s2
    s2 -->|"require_nonempty_text(value, error=error, error_context=error_context, require_trimmed=True, reject_control_characters=reject_control_characters)"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)(value, str)" .-> s4
    s3 -->|"_validation_error(error, error_context)"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)" .-> s6
    s5 -. "error(context)" .-> s7
    s3 -. "value.strip(data not statically known)" .-> s8
    s3 -->|"_validation_error(error, error_context)"| s9
    s3 -->|"_validation_error(..., error_context)"| s10
    s3 -->|"contains_control_character(parsed, reject_delete_character=reject_delete_character)"| s11
    s11 -. "pattern.search(value)" .-> s12
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s3 "../modules/validation.md"
    click s5 "../modules/validation.md"
    click s9 "../modules/validation.md"
    click s10 "../modules/validation.md"
    click s11 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `parse_utc_timestamp` | `value: object`, `string_error: Exception`, `timestamp_error: Exception`, `require_z: bool`, `reject_control_characters: bool`, `control_error: Exception \| None`, `z_error: Exception \| None`, `utc_error: Exception \| None` | `_ZERO_UTC_OFFSET` | - | `(...)` |
| `require_trimmed_text` | `value: object`, `error: _ValidationError`, `error_context: str`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: _ValidationError`, `trim_error: _ValidationError \| None`, `error_context: str`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)` | - | - | - | - |
| `error` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `contains_control_character` | `value: str`, `reject_delete_character: bool` | `_ASCII_CONTROL_DELETE`, `_ASCII_CONTROL` | - | `...` |
| `pattern.search` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| parse_utc_timestamp | require_trimmed_text | 1229 | `require_trimmed_text(value, error=string_error, reject_control_characters=False)` |
| require_trimmed_text | require_nonempty_text | 711 | `require_nonempty_text(value, error=error, error_context=error_context, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text) | 637 | `isinstance(value, str)` |
| require_nonempty_text | _validation_error | 638 | `_validation_error(error, error_context)` |
| _validation_error | isinstance (src/llm_wiki_cli/services…ation.py:_validation_error) | 95 | `isinstance(error, Exception)` |
| _validation_error | error | 95 | `error(context)` |
| require_nonempty_text | value.strip | 639 | `value.strip(data not statically known)` |
| require_nonempty_text | _validation_error | 642 | `_validation_error(error, error_context)` |
| require_nonempty_text | _validation_error | 644 | `_validation_error(..., error_context)` |
| require_nonempty_text | contains_control_character | 645 | `contains_control_character(parsed, reject_delete_character=reject_delete_character)` |
| contains_control_character | pattern.search | 699 | `pattern.search(value)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_nonempty_text` | `isinstance` | 637 |
| external_call | `_validation_error` | `isinstance` | 95 |
| unresolved_call | `_validation_error` | `error` | 95 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 639 |
| unresolved_call | `contains_control_character` | `pattern.search` | 699 |
| step_limit | `parse_utc_timestamp` | `first 12 steps` | 0 |

## Behavior

This flow starts at `parse_utc_timestamp` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
