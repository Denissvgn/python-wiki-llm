# normalize_concept_coordinate

**Entry point:** `normalize_concept_coordinate` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as normalize_concept_coordinate
    participant p1 as normalize_documentation_query_text
    participant p2 as isinstance
    participant p3 as strip
    participant p4 as DocumentationQueryError
    participant p5 as len
    participant p6 as encode
    participant p7 as validate_exact_page_coordinate
    participant p8 as validator
    p0->>p1: normalize_documentation_query_text
    p1-->>p2: isinstance
    p1-->>p3: strip
    p1->>p4: DocumentationQueryError
    p1-->>p3: strip
    p1-->>p5: len
    p1-->>p6: encode
    p1->>p4: DocumentationQueryError
    p0-->>p7: validate_exact_page_coordinate
    p0-->>p8: validator
    p0->>p4: DocumentationQueryError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. normalize_concept_coordinate"]
    s2["2. normalize_documentation_query_text"]
    s3["3. isinstance"]
    s4["4. strip"]
    s5["5. DocumentationQueryError"]
    s6["6. strip"]
    s7["7. len"]
    s8["8. encode"]
    s9["9. DocumentationQueryError"]
    s10["10. validate_exact_page_coordinate"]
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
    click s1 "../modules/documentation_query_builder.md"
    click s2 "../modules/documentation_query_builder.md"
    click s5 "../modules/documentation_queries.md"
    click s9 "../modules/documentation_queries.md"
    click s12 "../modules/documentation_queries.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `normalize_concept_coordinate` | `value: object` | `wiki_surface`, `validate_concept_uid`, `validate_natural_key`, `ConceptIdentityError` | - | `wiki_surface.validate_exact_page_coordinate(...)`, `validator(...)` |
| `normalize_documentation_query_text` | `value: object`, `field: str` | `QUERY_IDENTITY_BYTE_LIMIT`, `QUERY_IDENTITY_BYTE_LIMIT` | - | `selected` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `strip` | - | - | - | - |
| `len` | - | - | - | - |
| `encode` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `validate_exact_page_coordinate` | - | - | - | - |
| `validator` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| normalize_concept_coordinate | normalize_documentation_query_text | 73 | `normalize_documentation_query_text(value, field='locator_or_exact_route')` |
| normalize_documentation_query_text | isinstance | 60 | `isinstance(value, str)` |
| normalize_documentation_query_text | strip | 60 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | DocumentationQueryError | 61 | `DocumentationQueryError(...)` |
| normalize_documentation_query_text | strip | 62 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | len | 63 | `len(selected.encode(...))` |
| normalize_documentation_query_text | encode | 63 | `selected.encode('utf-8')` |
| normalize_documentation_query_text | DocumentationQueryError | 64 | `DocumentationQueryError(...)` |
| normalize_concept_coordinate | validate_exact_page_coordinate | 78 | `wiki_surface.validate_exact_page_coordinate(selected)` |
| normalize_concept_coordinate | validator | 83 | `validator(selected)` |
| normalize_concept_coordinate | DocumentationQueryError | 86 | `DocumentationQueryError('locator_or_exact_route must be an exact canonical wiki path or llm-wiki URI, durable concept UID, or natural-key alias.')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `normalize_documentation_query_text` | `isinstance` | 60 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 60 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 62 |
| unresolved_call | `normalize_documentation_query_text` | `selected.encode` | 63 |
| external_call | `normalize_concept_coordinate` | `wiki_surface.validate_exact_page_coordinate` | 78 |
| unresolved_call | `normalize_concept_coordinate` | `validator` | 83 |

## Behavior

This flow starts at `normalize_concept_coordinate` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
