# require_int_at_least

**Entry point:** `require_int_at_least` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_int_at_least
    participant p1 as require_int
    participant p2 as isinstance (src/llm_wiki_cli/services/validation.py:require_int)
    participant p3 as _validation_error
    participant p4 as isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)
    participant p5 as error
    p0->>p1: require_int
    p1-->>p2: isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, bool)
    p1-->>p2: isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, int)
    p1->>p3: _validation_error
    p3-->>p4: isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)
    p3-->>p5: error(context)
```

> Call sequence diagram shows 6 of 6 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 3 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 3; effect analysis evaluated: 3, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 3 source steps with known totals: observed: 11, emitted: 11, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. require_int_at_least"]
    s2["2. require_int"]
    s3["3. isinstance (src/llm_wiki_cli/services/validation.py:require_int)"]
    s4["4. isinstance (src/llm_wiki_cli/services/validation.py:require_int)"]
    s5["5. _validation_error"]
    s6["6. isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)"]
    s7["7. error"]
    s1 -->|"require_int(value, error=error)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, bool)" .-> s3
    s2 -. "isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, int)" .-> s4
    s2 -->|"_validation_error(error, error_context)"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)" .-> s6
    s5 -. "error(context)" .-> s7
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s5 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_int_at_least` | `value: object`, `minimum: int`, `error: Exception` | - | - | `parsed` |
| `require_int` | `value: object`, `error: _ValidationError`, `error_context: str` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services/validation.py:require_int)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services/validation.py:require_int)` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)` | - | - | - | - |
| `error` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_int_at_least | require_int | 881 | `require_int(value, error=error)` |
| require_int | isinstance (src/llm_wiki_cli/services/validation.py:require_int) | 836 | `isinstance(value, bool)` |
| require_int | isinstance (src/llm_wiki_cli/services/validation.py:require_int) | 836 | `isinstance(value, int)` |
| require_int | _validation_error | 837 | `_validation_error(error, error_context)` |
| _validation_error | isinstance (src/llm_wiki_cli/services…ation.py:_validation_error) | 95 | `isinstance(error, Exception)` |
| _validation_error | error | 95 | `error(context)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_int` | `isinstance` | 836 |
| external_call | `_validation_error` | `isinstance` | 95 |
| unresolved_call | `_validation_error` | `error` | 95 |

## Behavior

This flow starts at `require_int_at_least` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
