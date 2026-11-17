# validate_engine_event

**Entry point:** `validate_engine_event` (`api`)
**Source:** [engine_events](../modules/engine_events.md)
**Modules touched:** [engine_events](../modules/engine_events.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_engine_event
    participant p1 as _json_value
    participant p2 as _text
    participant p3 as isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event)
    participant p4 as ', '.join
    participant p5 as set
    participant p6 as ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)
    participant p7 as sorted
    participant p8 as data.get
    participant p9 as exit_code.is_integer
    participant p10 as isinstance (src/llm_wiki_engine/engine_events.py:_text)
    participant p11 as isinstance (src/llm_wiki_engine/engine_events.py:_json_value)
    participant p12 as ValueError (src/llm_wiki_engine/engine_events.py:_text)
    participant p13 as float
    p0->>p1: _json_value
    p0->>p2: _text
    p0-->>p3: isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event)(document, Mapping)
    p0-->>p4: ', '.join(sorted(...))
    p0-->>p5: set(document)
    p0-->>p6: ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)(...)
    p0-->>p7: sorted(_EVENT_FIELDS)
    p0-->>p6: ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)(...)
    p0-->>p6: ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)(...)
    p0-->>p3: isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event)(data, Mapping)
    p0-->>p6: ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)('data must be an object')
    p0-->>p5: set(data)
    p0-->>p6: ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)(...)
    p0-->>p4: ', '.join(sorted(...))
    p0-->>p7: sorted(...)
    p0-->>p6: ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)("data.stream must be 'stdout' or 'stderr'")
    p0-->>p3: isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event)(data[...], Mapping)
    p0-->>p6: ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)('data.result must be an object')
    p0-->>p8: data.get('exit_code', 0)
    p0-->>p3: isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event)(exit_code, bool)
    p0-->>p3: isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event)(exit_code, int)
    p0-->>p3: isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event)(exit_code, float)
    p0-->>p9: exit_code.is_integer
    p0-->>p6: ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)('data.exit_code must be an integer')
    p2-->>p10: isinstance (src/llm_wiki_engine/engine_events.py:_text)(value, str)
    p1-->>p11: isinstance (src/llm_wiki_engine/engine_events.py:_json_value)(value, (...))
    p2-->>p12: ValueError (src/llm_wiki_engine/engine_events.py:_text)(...)
    p1-->>p11: isinstance (src/llm_wiki_engine/engine_events.py:_json_value)(value, int)
    p1-->>p11: isinstance (src/llm_wiki_engine/engine_events.py:_json_value)(value, float)
    p1-->>p13: float('inf')
```

> Call sequence diagram shows 30 of 46 interactions; 16 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 24 of 32 (8 omitted); unresolved 4 of 5 (1 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_engine/engine_events.py:validate_engine_event` | 1 | [src/llm_wiki_engine/engine_events.py](../modules/engine_events.md) | internal | 5 |
| `src/llm_wiki_engine/engine_events.py:_json_value` | 19 | - | external | 8 |
| `src/llm_wiki_engine/engine_events.py:_json_value` | 19 | [src/llm_wiki_engine/engine_events.py](../modules/engine_events.md) | internal | 2 |
| `src/llm_wiki_engine/engine_events.py:_json_value` | 19 | - | unresolved | 1 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 10; effect analysis evaluated: 9, partial: 1, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 10 source steps with known totals: observed: 52, emitted: 51, omitted: 1. Unavailable totals are excluded.

- Effect collector omitted observations before flow assembly; displayed effects are partial.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `validate_engine_event` | `available` | `partial` | `available` | `10` | `9` | `1` |
| `isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `set` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `', '.join` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `sorted` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_text` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `isinstance (src/llm_wiki_engine/engine_events.py:_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ValueError (src/llm_wiki_engine/engine_events.py:_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_text` | `available` | `evaluated` | `available` | `3` | `3` | `0` |

```mermaid
flowchart LR
    s1["1. validate_engine_event"]
    s2["2. isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event)"]
    s3["3. set"]
    s4["4. ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)"]
    s5["5. ', '.join"]
    s6["6. sorted"]
    s7["7. ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)"]
    s8["8. ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)"]
    s9["9. _text"]
    s10["10. isinstance (src/llm_wiki_engine/engine_events.py:_text)"]
    s11["11. ValueError (src/llm_wiki_engine/engine_events.py:_text)"]
    s12["12. _text"]
    s1 -. "isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event)(document, Mapping)" .-> s2
    s1 -. "set(document)" .-> s3
    s1 -. "ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)(...)" .-> s4
    s1 -. "', '.join(sorted(...))" .-> s5
    s1 -. "sorted(_EVENT_FIELDS)" .-> s6
    s1 -. "ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)(...)" .-> s7
    s1 -. "ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)(...)" .-> s8
    s1 -->|"_text(document[...], 'operation')"| s9
    s9 -. "isinstance (src/llm_wiki_engine/engine_events.py:_text)(value, str)" .-> s10
    s9 -. "ValueError (src/llm_wiki_engine/engine_events.py:_text)(...)" .-> s11
    s1 -->|"_text(document[...], 'operation_id')"| s12
    click s1 "../modules/engine_events.md"
    click s9 "../modules/engine_events.md"
    click s12 "../modules/engine_events.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_engine_event` | `document: object` | `Mapping`, `_EVENT_FIELDS`, `_EVENT_FIELDS`, `ENGINE_EVENT_SCHEMA_VERSION`, `ENGINE_EVENT_SCHEMA_VERSION`, `EVENT_KINDS`, `Mapping`, `_DATA_FIELDS` | - | - |
| `isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event)` | - | - | - | - |
| `set` | - | - | - | - |
| `ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)` | - | - | - | - |
| `', '.join` | - | - | - | - |
| `sorted` | - | - | - | - |
| `ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)` | - | - | - | - |
| `ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event)` | - | - | - | - |
| `_text` | `value: object`, `path: str`, `empty: bool` | - | - | - |
| `isinstance (src/llm_wiki_engine/engine_events.py:_text)` | - | - | - | - |
| `ValueError (src/llm_wiki_engine/engine_events.py:_text)` | - | - | - | - |
| `_text` | `value: object`, `path: str`, `empty: bool` | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_engine_event | isinstance (src/llm_wiki_engine/engin…s.py:validate_engine_event) | 125 | `isinstance(document, Mapping)` |
| validate_engine_event | set | 125 | `set(document)` |
| validate_engine_event | ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event) | 126 | `ValueError(...)` |
| validate_engine_event | ', '.join | 126 | `', '.join(sorted(...))` |
| validate_engine_event | sorted | 126 | `sorted(_EVENT_FIELDS)` |
| validate_engine_event | ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event) | 128 | `ValueError(...)` |
| validate_engine_event | ValueError (src/llm_wiki_engine/engin…s.py:validate_engine_event) | 131 | `ValueError(...)` |
| validate_engine_event | _text | 132 | `_text(document[...], 'operation')` |
| _text | isinstance (src/llm_wiki_engine/engine_events.py:_text) | 119 | `isinstance(value, str)` |
| _text | ValueError (src/llm_wiki_engine/engine_events.py:_text) | 120 | `ValueError(...)` |
| validate_engine_event | _text | 133 | `_text(document[...], 'operation_id')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_engine_event` | `isinstance` | 125 |
| external_call | `validate_engine_event` | `ValueError` | 126 |
| unresolved_call | `validate_engine_event` | `', '.join` | 126 |
| external_call | `validate_engine_event` | `sorted` | 126 |
| external_call | `validate_engine_event` | `ValueError` | 128 |
| external_call | `validate_engine_event` | `ValueError` | 131 |
| external_call | `_text` | `isinstance` | 119 |
| external_call | `_text` | `ValueError` | 120 |
| step_limit | `validate_engine_event` | `first 12 steps` | 0 |

## Behavior

This flow starts at `validate_engine_event` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
