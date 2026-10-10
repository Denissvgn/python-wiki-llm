# require_choice

**Entry point:** `require_choice` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_choice
    participant p1 as require_trimmed_text
    participant p2 as frozenset
    participant p3 as choice_error
    participant p4 as require_nonempty_text
    participant p5 as isinstance
    participant p6 as value.strip
    participant p7 as contains_control_character
    participant p8 as pattern.search
    p0->>p1: require_trimmed_text
    p0-->>p2: frozenset(choices)
    p0-->>p3: choice_error(allowed)
    p1->>p4: require_nonempty_text
    p4-->>p5: isinstance(value, str)
    p4-->>p6: value.strip
    p4->>p7: contains_control_character
    p7-->>p8: pattern.search(value)
```

> Call sequence diagram shows 8 of 8 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 2 of 2 (0 omitted); unresolved 3 of 3 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_choice"]
    s2["2. require_trimmed_text"]
    s3["3. require_nonempty_text"]
    s4["4. isinstance"]
    s5["5. value.strip"]
    s6["6. contains_control_character"]
    s7["7. pattern.search"]
    s8["8. frozenset"]
    s9["9. choice_error"]
    s1 -->|"require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)"| s2
    s2 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s3
    s3 -. "isinstance(value, str)" .-> s4
    s3 -. "value.strip(data not statically known)" .-> s5
    s3 -->|"contains_control_character(parsed, reject_delete_character=reject_delete_character)"| s6
    s6 -. "pattern.search(value)" .-> s7
    s1 -. "frozenset(choices)" .-> s8
    s1 -. "choice_error(allowed)" .-> s9
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s3 "../modules/validation.md"
    click s6 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_choice` | `value: object`, `choices: Iterable[str]`, `text_error: Exception`, `choice_error: Callable[[frozenset[str]], Exception]`, `reject_control_characters: bool` | - | - | `parsed` |
| `require_trimmed_text` | `value: object`, `error: Exception`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: Exception`, `trim_error: Exception \| None`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `contains_control_character` | `value: str`, `reject_delete_character: bool` | `_ASCII_CONTROL_DELETE`, `_ASCII_CONTROL` | - | `...` |
| `pattern.search` | - | - | - | - |
| `frozenset` | - | - | - | - |
| `choice_error` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_choice | require_trimmed_text | 1073 | `require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)` |
| require_trimmed_text | require_nonempty_text | 696 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance | 623 | `isinstance(value, str)` |
| require_nonempty_text | value.strip | 625 | `value.strip(data not statically known)` |
| require_nonempty_text | contains_control_character | 631 | `contains_control_character(parsed, reject_delete_character=reject_delete_character)` |
| contains_control_character | pattern.search | 685 | `pattern.search(value)` |
| require_choice | frozenset | 1078 | `frozenset(choices)` |
| require_choice | choice_error | 1080 | `choice_error(allowed)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_nonempty_text` | `isinstance` | 623 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 625 |
| unresolved_call | `contains_control_character` | `pattern.search` | 685 |
| external_call | `require_choice` | `frozenset` | 1078 |
| unresolved_call | `require_choice` | `choice_error` | 1080 |

## Behavior

This flow starts at `require_choice` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
