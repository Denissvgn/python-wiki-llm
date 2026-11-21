# normalize_concept_coordinate

**Entry point:** `normalize_concept_coordinate` (`api`)
**Source:** [query_request_format](../modules/query_request_format.md)
**Modules touched:** [query_request_format](../modules/query_request_format.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as normalize_concept_coordinate
    participant p1 as normalize_documentation_query_text
    participant p2 as wiki_surface.validate_exact_page_coordinate
    participant p3 as validator
    participant p4 as DocumentationQueryError
    participant p5 as isinstance
    participant p6 as value.strip
    participant p7 as len
    participant p8 as selected.encode
    p0->>p1: normalize_documentation_query_text
    p0-->>p2: wiki_surface.validate_exact_page_coordinate(selected)
    p0-->>p3: validator(selected)
    p0->>p4: DocumentationQueryError
    p1-->>p5: isinstance(value, str)
    p1-->>p6: value.strip
    p1->>p4: DocumentationQueryError
    p1-->>p6: value.strip
    p1-->>p7: len(selected.encode(...))
    p1-->>p8: selected.encode('utf-8')
    p1->>p4: DocumentationQueryError
```

> Call sequence diagram shows 11 of 11 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 2 of 2 (0 omitted); unresolved 5 of 5 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 5; effect analysis evaluated: 2, partial: 0, unavailable: 3. Counts include steps omitted from the displayed trace.

Collector observations for 2 source steps with known totals: observed: 12, emitted: 12, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `normalize_concept_coordinate` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `normalize_documentation_query_text` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `isinstance` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `value.strip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `DocumentationQueryError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `value.strip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `selected.encode` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `DocumentationQueryError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `wiki_surface.validate_exact_page_coordinate` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `validator` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `DocumentationQueryError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. normalize_concept_coordinate"]
    s2["2. normalize_documentation_query_text"]
    s3["3. isinstance"]
    s4["4. value.strip"]
    s5["5. DocumentationQueryError"]
    s6["6. value.strip"]
    s7["7. len"]
    s8["8. selected.encode"]
    s9["9. DocumentationQueryError"]
    s10["10. wiki_surface.validate_exact_page_coordinate"]
    s11["11. validator"]
    s12["12. DocumentationQueryError"]
    s1 -->|"normalize_documentation_query_text(value, field='locator_or_exact_route')"| s2
    s2 -. "isinstance(value, str)" .-> s3
    s2 -. "value.strip(data not statically known)" .-> s4
    s2 -->|"DocumentationQueryError(...)"| s5
    s2 -. "value.strip(data not statically known)" .-> s6
    s2 -. "len(selected.encode(...))" .-> s7
    s2 -. "selected.encode('utf-8')" .-> s8
    s2 -->|"DocumentationQueryError(...)"| s9
    s1 -. "wiki_surface.validate_exact_page_coordinate(selected)" .-> s10
    s1 -. "validator(selected)" .-> s11
    s1 -->|"DocumentationQueryError('locator_or_exact_route must be an exact canonical wiki path or llm-wiki URI, durable concept UID, or natural-key alias.')"| s12
    click s1 "../modules/query_request_format.md"
    click s2 "../modules/query_request_format.md"
    click s5 "../modules/query_request_format.md"
    click s9 "../modules/query_request_format.md"
    click s12 "../modules/query_request_format.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `normalize_concept_coordinate` | `value: object` | `wiki_surface`, `validate_concept_uid`, `validate_natural_key`, `ConceptIdentityError` | - | `wiki_surface.validate_exact_page_coordinate(...)`, `validator(...)` |
| `normalize_documentation_query_text` | `value: object`, `field: str` | `QUERY_IDENTITY_BYTE_LIMIT`, `QUERY_IDENTITY_BYTE_LIMIT` | - | `selected` |
| `isinstance` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `len` | - | - | - | - |
| `selected.encode` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `wiki_surface.validate_exact_page_coordinate` | - | - | - | - |
| `validator` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| normalize_concept_coordinate | normalize_documentation_query_text | 62 | `normalize_documentation_query_text(value, field='locator_or_exact_route')` |
| normalize_documentation_query_text | isinstance | 49 | `isinstance(value, str)` |
| normalize_documentation_query_text | value.strip | 49 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | DocumentationQueryError | 50 | `DocumentationQueryError(...)` |
| normalize_documentation_query_text | value.strip | 51 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | len | 52 | `len(selected.encode(...))` |
| normalize_documentation_query_text | selected.encode | 52 | `selected.encode('utf-8')` |
| normalize_documentation_query_text | DocumentationQueryError | 53 | `DocumentationQueryError(...)` |
| normalize_concept_coordinate | wiki_surface.validate_exact_page_coordinate | 67 | `wiki_surface.validate_exact_page_coordinate(selected)` |
| normalize_concept_coordinate | validator | 72 | `validator(selected)` |
| normalize_concept_coordinate | DocumentationQueryError | 75 | `DocumentationQueryError('locator_or_exact_route must be an exact canonical wiki path or llm-wiki URI, durable concept UID, or natural-key alias.')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `normalize_documentation_query_text` | `isinstance` | 49 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 49 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 51 |
| unresolved_call | `normalize_documentation_query_text` | `selected.encode` | 52 |
| unresolved_call | `normalize_concept_coordinate` | `wiki_surface.validate_exact_page_coordinate` | 67 |
| unresolved_call | `normalize_concept_coordinate` | `validator` | 72 |

## Behavior

This flow starts at `normalize_concept_coordinate` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
