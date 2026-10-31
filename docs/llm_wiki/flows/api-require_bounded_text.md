# require_bounded_text

**Entry point:** `require_bounded_text` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_bounded_text
    participant p1 as isinstance
    participant p2 as len
    participant p3 as value.strip
    participant p4 as contains_control_character
    participant p5 as pattern.search
    p0-->>p1: isinstance(value, str)
    p0-->>p2: len(value)
    p0-->>p2: len(value)
    p0-->>p3: value.strip
    p0->>p4: contains_control_character
    p4-->>p5: pattern.search(value)
```

> Call sequence diagram shows 6 of 6 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 3 (0 omitted); unresolved 2 of 2 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 2; effect analysis evaluated: 2, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 2 source steps with known totals: observed: 14, emitted: 14, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. require_bounded_text"]
    s2["2. isinstance"]
    s3["3. len"]
    s4["4. len"]
    s5["5. value.strip"]
    s6["6. contains_control_character"]
    s7["7. pattern.search"]
    s1 -. "isinstance(value, str)" .-> s2
    s1 -. "len(value)" .-> s3
    s1 -. "len(value)" .-> s4
    s1 -. "value.strip(data not statically known)" .-> s5
    s1 -->|"contains_control_character(value, reject_delete_character=reject_delete_character)"| s6
    s6 -. "pattern.search(value)" .-> s7
    click s1 "../modules/validation.md"
    click s6 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_bounded_text` | `value: object`, `maximum: int`, `error: Exception`, `minimum: int`, `control_error: Exception \| None`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `len` | - | - | - | - |
| `len` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `contains_control_character` | `value: str`, `reject_delete_character: bool` | `_ASCII_CONTROL_DELETE`, `_ASCII_CONTROL` | - | `...` |
| `pattern.search` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_bounded_text | isinstance | 658 | `isinstance(value, str)` |
| require_bounded_text | len | 659 | `len(value)` |
| require_bounded_text | len | 660 | `len(value)` |
| require_bounded_text | value.strip | 661 | `value.strip(data not statically known)` |
| require_bounded_text | contains_control_character | 664 | `contains_control_character(value, reject_delete_character=reject_delete_character)` |
| contains_control_character | pattern.search | 693 | `pattern.search(value)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_bounded_text` | `isinstance` | 658 |
| unresolved_call | `require_bounded_text` | `value.strip` | 661 |
| unresolved_call | `contains_control_character` | `pattern.search` | 693 |

## Behavior

This flow starts at `require_bounded_text` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
