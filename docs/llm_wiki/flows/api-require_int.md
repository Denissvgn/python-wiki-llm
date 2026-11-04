# require_int

**Entry point:** `require_int` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_int
    participant p1 as isinstance (src/llm_wiki_cli/services/validation.py:require_int)
    participant p2 as _validation_error
    participant p3 as isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)
    participant p4 as error
    p0-->>p1: isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, bool)
    p0-->>p1: isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, int)
    p0->>p2: _validation_error
    p2-->>p3: isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)
    p2-->>p4: error(context)
```

> Call sequence diagram shows 5 of 5 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 3 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 2; effect analysis evaluated: 2, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 2 source steps with known totals: observed: 7, emitted: 7, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. require_int"]
    s2["2. isinstance (src/llm_wiki_cli/services/validation.py:require_int)"]
    s3["3. isinstance (src/llm_wiki_cli/services/validation.py:require_int)"]
    s4["4. _validation_error"]
    s5["5. isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)"]
    s6["6. error"]
    s1 -. "isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, bool)" .-> s2
    s1 -. "isinstance (src/llm_wiki_cli/services/validation.py:require_int)(value, int)" .-> s3
    s1 -->|"_validation_error(error, error_context)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)(error, Exception)" .-> s5
    s4 -. "error(context)" .-> s6
    click s1 "../modules/validation.md"
    click s4 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_int` | `value: object`, `error: _ValidationError`, `error_context: str` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services/validation.py:require_int)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services/validation.py:require_int)` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `isinstance (src/llm_wiki_cli/services…ation.py:_validation_error)` | - | - | - | - |
| `error` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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

This flow starts at `require_int` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
