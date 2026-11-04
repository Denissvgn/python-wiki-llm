# is_canonical_uuid

**Entry point:** `is_canonical_uuid` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_canonical_uuid
    participant p1 as SharedValidationError
    participant p2 as require_uuid
    participant p3 as require_trimmed_text
    participant p4 as str
    participant p5 as uuid.UUID
    participant p6 as require_nonempty_text
    participant p7 as isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)
    participant p8 as _validation_error
    participant p9 as value.strip
    participant p10 as contains_control_character
    participant p11 as isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)
    participant p12 as pattern.search
    participant p13 as error
    p0->>p1: SharedValidationError
    p0->>p2: require_uuid
    p2->>p3: require_trimmed_text
    p2-->>p4: str(uuid.UUID(...))
    p2-->>p5: uuid.UUID(parsed)
    p3->>p6: require_nonempty_text
    p6-->>p7: isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)(value, str)
    p6->>p8: _validation_error
    p6-->>p9: value.strip
    p6->>p8: _validation_error
    p6->>p8: _validation_error
    p6->>p10: contains_control_character
    p6->>p8: _validation_error
    p8-->>p11: isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)
    p10-->>p12: pattern.search(value)
    p8-->>p13: error(context)
```

> Call sequence diagram shows 16 of 16 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 4 (0 omitted); unresolved 3 of 3 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 10; effect analysis evaluated: 9, partial: 0, unavailable: 1. Counts include steps omitted from the displayed trace.

Collector observations for 9 source steps with known totals: observed: 40, emitted: 40, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `is_canonical_uuid` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `SharedValidationError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `require_uuid` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `require_trimmed_text` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `require_nonempty_text` | `available` | `evaluated` | `available` | `9` | `9` | `0` |
| `isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validation_error` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `error` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `value.strip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validation_error` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `_validation_error` | `available` | `evaluated` | `available` | `3` | `3` | `0` |

```mermaid
flowchart LR
    s1["1. is_canonical_uuid"]
    s2["2. SharedValidationError"]
    s3["3. require_uuid"]
    s4["4. require_trimmed_text"]
    s5["5. require_nonempty_text"]
    s6["6. isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)"]
    s7["7. _validation_error"]
    s8["8. isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)"]
    s9["9. error"]
    s10["10. value.strip"]
    s11["11. _validation_error"]
    s12["12. _validation_error"]
    s1 -->|"SharedValidationError('value must be a canonical UUID')"| s2
    s1 -->|"require_uuid(value, text_error=error, uuid_error=error, canonical_error=error)"| s3
    s3 -->|"require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)"| s4
    s4 -->|"require_nonempty_text(value, error=error, error_context=error_context, require_trimmed=True, reject_control_characters=reject_control_characters)"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)(value, str)" .-> s6
    s5 -->|"_validation_error(error, error_context)"| s7
    s7 -. "isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)" .-> s8
    s7 -. "error(context)" .-> s9
    s5 -. "value.strip(data not statically known)" .-> s10
    s5 -->|"_validation_error(error, error_context)"| s11
    s5 -->|"_validation_error(..., error_context)"| s12
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s3 "../modules/validation.md"
    click s4 "../modules/validation.md"
    click s5 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s11 "../modules/validation.md"
    click s12 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_canonical_uuid` | `value: object` | - | - | `False`, `True` |
| `SharedValidationError` | - | - | - | - |
| `require_uuid` | `value: object`, `text_error: Exception`, `uuid_error: Exception`, `canonical_error: Exception`, `reject_control_characters: bool` | - | - | `parsed` |
| `require_trimmed_text` | `value: object`, `error: _ValidationError`, `error_context: str`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: _ValidationError`, `trim_error: _ValidationError \| None`, `error_context: str`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)` | - | - | - | - |
| `error` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_canonical_uuid | SharedValidationError | 1203 | `SharedValidationError('value must be a canonical UUID')` |
| is_canonical_uuid | require_uuid | 1205 | `require_uuid(value, text_error=error, uuid_error=error, canonical_error=error)` |
| require_uuid | require_trimmed_text | 1186 | `require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)` |
| require_trimmed_text | require_nonempty_text | 711 | `require_nonempty_text(value, error=error, error_context=error_context, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text) | 637 | `isinstance(value, str)` |
| require_nonempty_text | _validation_error | 638 | `_validation_error(error, error_context)` |
| _validation_error | isinstance (src/llm_wiki_cli/services…ation.py:_validation_error) | 95 | `isinstance(error, Exception)` |
| _validation_error | error | 95 | `error(context)` |
| require_nonempty_text | value.strip | 639 | `value.strip(data not statically known)` |
| require_nonempty_text | _validation_error | 642 | `_validation_error(error, error_context)` |
| require_nonempty_text | _validation_error | 644 | `_validation_error(..., error_context)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_nonempty_text` | `isinstance` | 637 |
| external_call | `_validation_error` | `isinstance` | 95 |
| unresolved_call | `_validation_error` | `error` | 95 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 639 |
| step_limit | `is_canonical_uuid` | `first 12 steps` | 0 |

## Behavior

This flow starts at `is_canonical_uuid` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
