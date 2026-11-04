# require_nonnegative_int

**Entry point:** `require_nonnegative_int` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_nonnegative_int
    participant p1 as require_int
    participant p2 as _validation_error
    participant p3 as isinstance (src/llm_wiki_cli/services/validation.py:require_int)
    participant p4 as isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)
    participant p5 as error
    p0->>p1: require_int
    p0->>p2: _validation_error
    p1-->>p3: isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, bool)
    p1-->>p3: isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, int)
    p1->>p2: _validation_error
    p2-->>p4: isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)
    p2-->>p5: error(context)
```

> Call sequence diagram shows 7 of 7 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 3 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 4; effect analysis evaluated: 4, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 4 source steps with known totals: observed: 14, emitted: 14, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. require_nonnegative_int"]
    s2["2. require_int"]
    s3["3. isinstance (src/llm_wiki_cli/services/validation.py:require_int)"]
    s4["4. isinstance (src/llm_wiki_cli/services/validation.py:require_int)"]
    s5["5. _validation_error"]
    s6["6. isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)"]
    s7["7. error"]
    s8["8. _validation_error"]
    s1 -->|"require_int(value, error=error, error_context=error_context)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, bool)" .-> s3
    s2 -. "isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, int)" .-> s4
    s2 -->|"_validation_error(error, error_context)"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)" .-> s6
    s5 -. "error(context)" .-> s7
    s1 -->|"_validation_error(error, error_context)"| s8
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s5 "../modules/validation.md"
    click s8 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_nonnegative_int` | `value: object`, `error: _ValidationError`, `error_context: str` | - | - | `parsed` |
| `require_int` | `value: object`, `error: _ValidationError`, `error_context: str` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services/validation.py:require_int)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services/validation.py:require_int)` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)` | - | - | - | - |
| `error` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_nonnegative_int | require_int | 844 | `require_int(value, error=error, error_context=error_context)` |
| require_int | isinstance (src/llm_wiki_cli/services/validation.py:require_int) | 836 | `isinstance(value, bool)` |
| require_int | isinstance (src/llm_wiki_cli/services/validation.py:require_int) | 836 | `isinstance(value, int)` |
| require_int | _validation_error | 837 | `_validation_error(error, error_context)` |
| _validation_error | isinstance (src/llm_wiki_cli/services…ation.py:_validation_error) | 95 | `isinstance(error, Exception)` |
| _validation_error | error | 95 | `error(context)` |
| require_nonnegative_int | _validation_error | 846 | `_validation_error(error, error_context)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_int` | `isinstance` | 836 |
| external_call | `_validation_error` | `isinstance` | 95 |
| unresolved_call | `_validation_error` | `error` | 95 |

## Behavior

This flow starts at `require_nonnegative_int` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
