# portable_page_component

**Entry point:** `portable_page_component` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as portable_page_component
    participant p1 as portable_page_component.<locals>.sanitize
    participant p2 as str(…).strip
    participant p3 as str
    participant p4 as unicodedata.normalize (src/llm_wiki_cli/services…omponent.<locals>.sanitize)
    participant p5 as _UNSAFE_PAGE_COMPONENT_RE.sub(…).strip
    participant p6 as _UNSAFE_PAGE_COMPONENT_RE.sub
    participant p7 as re.sub(…).lstrip(…).rstrip
    participant p8 as re.sub(…).lstrip
    participant p9 as re.sub
    participant p10 as safe.replace
    participant p11 as is_portable_path_component
    participant p12 as require_portable_path_component
    participant p13 as component.encode
    participant p14 as SharedValidationError
    participant p15 as unicodedata.normalize (src/llm_wiki_cli/services…re_portable_path_component)
    participant p16 as any
    participant p17 as ord
    participant p18 as component.endswith
    participant p19 as component.split(…)[…].casefold
    participant p20 as component.split
    p0->>p1: portable_page_component.<locals>.sanitize
    p0->>p1: portable_page_component.<locals>.sanitize
    p1-->>p2: str(…).strip
    p1-->>p3: str(candidate)
    p1-->>p4: unicodedata.normalize (src/llm_wiki_cli/services…omponent.<locals>.sanitize)('NFC', raw)
    p1-->>p5: _UNSAFE_PAGE_COMPONENT_RE.sub(…).strip('_')
    p1-->>p6: _UNSAFE_PAGE_COMPONENT_RE.sub('_', normalized)
    p1-->>p7: re.sub(…).lstrip(…).rstrip('. ')
    p1-->>p8: re.sub(…).lstrip('.')
    p1-->>p9: re.sub('_+', '_', safe)
    p1-->>p10: safe.replace('..', '._')
    p1->>p11: is_portable_path_component
    p11->>p12: require_portable_path_component
    p12-->>p13: component.encode('utf-8')
    p12->>p14: SharedValidationError
    p12-->>p15: unicodedata.normalize (src/llm_wiki_cli/services…re_portable_path_component)('NFC', component)
    p12->>p14: SharedValidationError
    p12-->>p16: any(...)
    p12-->>p17: ord(character)
    p12-->>p17: ord(character)
    p12->>p14: SharedValidationError
    p12-->>p18: component.endswith((...))
    p12-->>p16: any(...)
    p12->>p14: SharedValidationError
    p12-->>p19: component.split(…)[…].casefold
    p12-->>p20: component.split('.', 1)
    p12->>p14: SharedValidationError
```

> Call sequence diagram shows 27 of 27 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 8 (0 omitted); unresolved 10 of 10 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 10; effect analysis evaluated: 4, partial: 1, unavailable: 5. Counts include steps omitted from the displayed trace.

Collector observations for 5 source steps with known totals: observed: 23, emitted: 22, omitted: 1. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `portable_page_component` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `portable_page_component.<locals>.sanitize` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `str(…).strip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `str` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `unicodedata.normalize (src/llm_wiki_cli/services…omponent.<locals>.sanitize)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_UNSAFE_PAGE_COMPONENT_RE.sub(…).strip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_UNSAFE_PAGE_COMPONENT_RE.sub` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `re.sub(…).lstrip(…).rstrip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `re.sub(…).lstrip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `re.sub` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `safe.replace` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `is_portable_path_component` | `available` | `evaluated` | `available` | `4` | `4` | `0` |

```mermaid
flowchart LR
    s1["1. portable_page_component"]
    s2["2. portable_page_component.#60;locals#62;.sanitize"]
    s3["3. str(…).strip"]
    s4["4. str"]
    s5["5. unicodedata.normalize (src/llm_wiki_cli/services…omponent.#60;locals#62;.sanitize)"]
    s6["6. _UNSAFE_PAGE_COMPONENT_RE.sub(…).strip"]
    s7["7. _UNSAFE_PAGE_COMPONENT_RE.sub"]
    s8["8. re.sub(…).lstrip(…).rstrip"]
    s9["9. re.sub(…).lstrip"]
    s10["10. re.sub"]
    s11["11. safe.replace"]
    s12["12. is_portable_path_component"]
    s1 -->|"portable_page_component.#60;locals#62;.sanitize(value)"| s2
    s2 -. "str(…).strip(data not statically known)" .-> s3
    s2 -. "str(candidate)" .-> s4
    s2 -. "unicodedata.normalize (src/llm_wiki_cli/services…omponent.#60;locals#62;.sanitize)('NFC', raw)" .-> s5
    s2 -. "_UNSAFE_PAGE_COMPONENT_RE.sub(…).strip('_')" .-> s6
    s2 -. "_UNSAFE_PAGE_COMPONENT_RE.sub('_', normalized)" .-> s7
    s2 -. "re.sub(…).lstrip(…).rstrip('. ')" .-> s8
    s2 -. "re.sub(…).lstrip('.')" .-> s9
    s2 -. "re.sub('_+', '_', safe)" .-> s10
    s2 -. "safe.replace('..', '._')" .-> s11
    s2 -->|"is_portable_path_component(safe)"| s12
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s12 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `portable_page_component` | `value: object`, `fallback: str` | - | - | `...` |
| `portable_page_component.<locals>.sanitize` | `candidate: object` | - | - | `safe` |
| `str(…).strip` | - | - | - | - |
| `str` | - | - | - | - |
| `unicodedata.normalize (src/llm_wiki_cli/services…omponent.<locals>.sanitize)` | - | - | - | - |
| `_UNSAFE_PAGE_COMPONENT_RE.sub(…).strip` | - | - | - | - |
| `_UNSAFE_PAGE_COMPONENT_RE.sub` | - | - | - | - |
| `re.sub(…).lstrip(…).rstrip` | - | - | - | - |
| `re.sub(…).lstrip` | - | - | - | - |
| `re.sub` | - | - | - | - |
| `safe.replace` | - | - | - | - |
| `is_portable_path_component` | `component: str` | `SharedValidationError` | - | `False`, `True` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| portable_page_component | portable_page_component.<locals>.sanitize | 616 | `sanitize(value)` |
| portable_page_component.<locals>.sanitize | str(…).strip | 606 | `str(candidate).strip(data not statically known)` |
| portable_page_component.<locals>.sanitize | str | 606 | `str(candidate)` |
| portable_page_component.<locals>.sanitize | unicodedata.normalize (src/llm_wiki_cli/services…omponent.<locals>.sanitize) | 607 | `unicodedata.normalize('NFC', raw)` |
| portable_page_component.<locals>.sanitize | _UNSAFE_PAGE_COMPONENT_RE.sub(…).strip | 608 | `_UNSAFE_PAGE_COMPONENT_RE.sub('_', normalized).strip('_')` |
| portable_page_component.<locals>.sanitize | _UNSAFE_PAGE_COMPONENT_RE.sub | 608 | `_UNSAFE_PAGE_COMPONENT_RE.sub('_', normalized)` |
| portable_page_component.<locals>.sanitize | re.sub(…).lstrip(…).rstrip | 609 | `re.sub('_+', '_', safe).lstrip('.').rstrip('. ')` |
| portable_page_component.<locals>.sanitize | re.sub(…).lstrip | 609 | `re.sub('_+', '_', safe).lstrip('.')` |
| portable_page_component.<locals>.sanitize | re.sub | 609 | `re.sub('_+', '_', safe)` |
| portable_page_component.<locals>.sanitize | safe.replace | 611 | `safe.replace('..', '._')` |
| portable_page_component.<locals>.sanitize | is_portable_path_component | 612 | `is_portable_path_component(safe)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `portable_page_component.<locals>.sanitize` | `str(candidate).strip` | 606 |
| external_call | `portable_page_component.<locals>.sanitize` | `unicodedata.normalize` | 607 |
| unresolved_call | `portable_page_component.<locals>.sanitize` | `_UNSAFE_PAGE_COMPONENT_RE.sub('_', normalized).strip` | 608 |
| unresolved_call | `portable_page_component.<locals>.sanitize` | `_UNSAFE_PAGE_COMPONENT_RE.sub` | 608 |
| unresolved_call | `portable_page_component.<locals>.sanitize` | `re.sub('_+', '_', safe).lstrip('.').rstrip` | 609 |
| unresolved_call | `portable_page_component.<locals>.sanitize` | `re.sub('_+', '_', safe).lstrip` | 609 |
| external_call | `portable_page_component.<locals>.sanitize` | `re.sub` | 609 |
| unresolved_call | `portable_page_component.<locals>.sanitize` | `safe.replace` | 611 |
| step_limit | `portable_page_component` | `first 12 steps` | 0 |

## Behavior

This flow starts at `portable_page_component` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
