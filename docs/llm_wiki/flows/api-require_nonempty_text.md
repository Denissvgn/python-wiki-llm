# require_nonempty_text

**Entry point:** `require_nonempty_text` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_nonempty_text
    participant p1 as isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)
    participant p2 as _validation_error
    participant p3 as value.strip
    participant p4 as contains_control_character
    participant p5 as isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)
    participant p6 as pattern.search
    participant p7 as error
    p0-->>p1: isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)(value, str)
    p0->>p2: _validation_error
    p0-->>p3: value.strip
    p0->>p2: _validation_error
    p0->>p2: _validation_error
    p0->>p4: contains_control_character
    p0->>p2: _validation_error
    p2-->>p5: isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)
    p4-->>p6: pattern.search(value)
    p2-->>p7: error(context)
```

> Call sequence diagram shows 10 of 10 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 2 of 2 (0 omitted); unresolved 3 of 3 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 6; effect analysis evaluated: 6, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 6 source steps with known totals: observed: 26, emitted: 26, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. require_nonempty_text"]
    s2["2. isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)"]
    s3["3. _validation_error"]
    s4["4. isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)"]
    s5["5. error"]
    s6["6. value.strip"]
    s7["7. _validation_error"]
    s8["8. _validation_error"]
    s9["9. contains_control_character"]
    s10["10. pattern.search"]
    s11["11. _validation_error"]
    s1 -. "isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)(value, str)" .-> s2
    s1 -->|"_validation_error(error, error_context)"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)" .-> s4
    s3 -. "error(context)" .-> s5
    s1 -. "value.strip(data not statically known)" .-> s6
    s1 -->|"_validation_error(error, error_context)"| s7
    s1 -->|"_validation_error(..., error_context)"| s8
    s1 -->|"contains_control_character(parsed, reject_delete_character=reject_delete_character)"| s9
    s9 -. "pattern.search(value)" .-> s10
    s1 -->|"_validation_error(error, error_context)"| s11
    click s1 "../modules/validation.md"
    click s3 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s8 "../modules/validation.md"
    click s9 "../modules/validation.md"
    click s11 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_nonempty_text | isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text) | 637 | `isinstance(value, str)` |
| require_nonempty_text | _validation_error | 638 | `_validation_error(error, error_context)` |
| _validation_error | isinstance (src/llm_wiki_cli/services…ation.py:_validation_error) | 95 | `isinstance(error, Exception)` |
| _validation_error | error | 95 | `error(context)` |
| require_nonempty_text | value.strip | 639 | `value.strip(data not statically known)` |
| require_nonempty_text | _validation_error | 642 | `_validation_error(error, error_context)` |
| require_nonempty_text | _validation_error | 644 | `_validation_error(..., error_context)` |
| require_nonempty_text | contains_control_character | 645 | `contains_control_character(parsed, reject_delete_character=reject_delete_character)` |
| contains_control_character | pattern.search | 699 | `pattern.search(value)` |
| require_nonempty_text | _validation_error | 646 | `_validation_error(error, error_context)` |

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

## Behavior

This flow starts at `require_nonempty_text` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
