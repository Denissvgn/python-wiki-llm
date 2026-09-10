# normalize_concept_coordinate

**Entry point:** `normalize_concept_coordinate` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as normalize_concept_coordinate
    participant p1 as normalize_documentation_query_text
    participant p2 as isinstance (src/llm_wiki_cli/services…e_documentation_query_text)
    participant p3 as value.strip (src/llm_wiki_cli/services…e_documentation_query_text)
    participant p4 as DocumentationQueryError
    participant p5 as len (src/llm_wiki_cli/services…e_documentation_query_text)
    participant p6 as selected.encode
    participant p7 as validate_exact_page_coordinate
    participant p8 as isinstance (src/llm_wiki_cli/services…date_exact_page_coordinate)
    participant p9 as value.strip (src/llm_wiki_cli/services…date_exact_page_coordinate)
    participant p10 as WikiSurfaceError
    participant p11 as any (src/llm_wiki_cli/services…date_exact_page_coordinate)
    participant p12 as ord (src/llm_wiki_cli/services…date_exact_page_coordinate)
    participant p13 as _matches_directory_path
    participant p14 as coordinate.startswith (src/llm_wiki_cli/services…py:_matches_directory_path)
    participant p15 as coordinate.endswith
    participant p16 as len (src/llm_wiki_cli/services…py:_matches_directory_path)
    participant p17 as bool (src/llm_wiki_cli/services…py:_matches_directory_path)
    participant p18 as is_safe_page_id
    participant p19 as isinstance (src/llm_wiki_cli/services…surface.py:is_safe_page_id)
    participant p20 as bool (src/llm_wiki_cli/services…surface.py:is_safe_page_id)
    participant p21 as page_id.startswith
    participant p22 as _PAGE_ID_RE.fullmatch
    participant p23 as is_portable_path_component
    p0->>p1: normalize_documentation_query_text
    p1-->>p2: isinstance (src/llm_wiki_cli/services…e_documentation_query_text)
    p1-->>p3: value.strip (src/llm_wiki_cli/services…e_documentation_query_text)
    p1->>p4: DocumentationQueryError
    p1-->>p3: value.strip (src/llm_wiki_cli/services…e_documentation_query_text)
    p1-->>p5: len (src/llm_wiki_cli/services…e_documentation_query_text)
    p1-->>p6: selected.encode
    p1->>p4: DocumentationQueryError
    p0->>p7: validate_exact_page_coordinate
    p7-->>p8: isinstance (src/llm_wiki_cli/services…date_exact_page_coordinate)
    p7-->>p9: value.strip (src/llm_wiki_cli/services…date_exact_page_coordinate)
    p7->>p10: WikiSurfaceError
    p7-->>p9: value.strip (src/llm_wiki_cli/services…date_exact_page_coordinate)
    p7-->>p11: any (src/llm_wiki_cli/services…date_exact_page_coordinate)
    p7-->>p12: ord (src/llm_wiki_cli/services…date_exact_page_coordinate)
    p7-->>p12: ord (src/llm_wiki_cli/services…date_exact_page_coordinate)
    p7->>p10: WikiSurfaceError
    p7->>p13: _matches_directory_path
    p13-->>p14: coordinate.startswith (src/llm_wiki_cli/services…py:_matches_directory_path)
    p13-->>p15: coordinate.endswith
    p13-->>p16: len (src/llm_wiki_cli/services…py:_matches_directory_path)
    p13-->>p16: len (src/llm_wiki_cli/services…py:_matches_directory_path)
    p13-->>p17: bool (src/llm_wiki_cli/services…py:_matches_directory_path)
    p13->>p18: is_safe_page_id
    p18-->>p19: isinstance (src/llm_wiki_cli/services…surface.py:is_safe_page_id)
    p18-->>p20: bool (src/llm_wiki_cli/services…surface.py:is_safe_page_id)
    p18-->>p21: page_id.startswith
    p18-->>p20: bool (src/llm_wiki_cli/services…surface.py:is_safe_page_id)
    p18-->>p22: _PAGE_ID_RE.fullmatch
    p18->>p23: is_portable_path_component
```

> Call sequence diagram shows 30 of 74 interactions; 44 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. normalize_concept_coordinate"]
    s2["2. normalize_documentation_query_text"]
    s3["3. isinstance (src/llm_wiki_cli/services…e_documentation_query_text)"]
    s4["4. value.strip (src/llm_wiki_cli/services…e_documentation_query_text)"]
    s5["5. DocumentationQueryError"]
    s6["6. value.strip (src/llm_wiki_cli/services…e_documentation_query_text)"]
    s7["7. len (src/llm_wiki_cli/services…e_documentation_query_text)"]
    s8["8. selected.encode"]
    s9["9. DocumentationQueryError"]
    s10["10. validate_exact_page_coordinate"]
    s11["11. isinstance (src/llm_wiki_cli/services…date_exact_page_coordinate)"]
    s12["12. value.strip (src/llm_wiki_cli/services…date_exact_page_coordinate)"]
    s1 -->|"normalize_documentation_query_text(value, field='locator_or_exact_route')"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…e_documentation_query_text)(value, str)" .-> s3
    s2 -. "value.strip (src/llm_wiki_cli/services…e_documentation_query_text)(data not statically known)" .-> s4
    s2 -->|"DocumentationQueryError(...)"| s5
    s2 -. "value.strip (src/llm_wiki_cli/services…e_documentation_query_text)(data not statically known)" .-> s6
    s2 -. "len (src/llm_wiki_cli/services…e_documentation_query_text)(selected.encode(...))" .-> s7
    s2 -. "selected.encode('utf-8')" .-> s8
    s2 -->|"DocumentationQueryError(...)"| s9
    s1 -->|"validate_exact_page_coordinate(selected)"| s10
    s10 -. "isinstance (src/llm_wiki_cli/services…date_exact_page_coordinate)(value, str)" .-> s11
    s10 -. "value.strip (src/llm_wiki_cli/services…date_exact_page_coordinate)(data not statically known)" .-> s12
    click s1 "../modules/documentation_query_builder.md"
    click s2 "../modules/documentation_query_builder.md"
    click s5 "../modules/documentation_queries.md"
    click s9 "../modules/documentation_queries.md"
    click s10 "../modules/wiki_surface.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `normalize_concept_coordinate` | `value: object` | `wiki_surface`, `validate_concept_uid`, `validate_natural_key`, `ConceptIdentityError` | - | `wiki_surface.validate_exact_page_coordinate(...)`, `validator(...)` |
| `normalize_documentation_query_text` | `value: object`, `field: str` | `QUERY_IDENTITY_BYTE_LIMIT`, `QUERY_IDENTITY_BYTE_LIMIT` | - | `selected` |
| `isinstance (src/llm_wiki_cli/services…e_documentation_query_text)` | - | - | - | - |
| `value.strip (src/llm_wiki_cli/services…e_documentation_query_text)` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `value.strip (src/llm_wiki_cli/services…e_documentation_query_text)` | - | - | - | - |
| `len (src/llm_wiki_cli/services…e_documentation_query_text)` | - | - | - | - |
| `selected.encode` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `validate_exact_page_coordinate` | `value: object` | `_PAGE_KINDS` | - | `coordinate`, `coordinate` |
| `isinstance (src/llm_wiki_cli/services…date_exact_page_coordinate)` | - | - | - | - |
| `value.strip (src/llm_wiki_cli/services…date_exact_page_coordinate)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| normalize_concept_coordinate | normalize_documentation_query_text | 73 | `normalize_documentation_query_text(value, field='locator_or_exact_route')` |
| normalize_documentation_query_text | isinstance (src/llm_wiki_cli/services…e_documentation_query_text) | 60 | `isinstance(value, str)` |
| normalize_documentation_query_text | value.strip (src/llm_wiki_cli/services…e_documentation_query_text) | 60 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | DocumentationQueryError | 61 | `DocumentationQueryError(...)` |
| normalize_documentation_query_text | value.strip (src/llm_wiki_cli/services…e_documentation_query_text) | 62 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | len (src/llm_wiki_cli/services…e_documentation_query_text) | 63 | `len(selected.encode(...))` |
| normalize_documentation_query_text | selected.encode | 63 | `selected.encode('utf-8')` |
| normalize_documentation_query_text | DocumentationQueryError | 64 | `DocumentationQueryError(...)` |
| normalize_concept_coordinate | validate_exact_page_coordinate | 78 | `wiki_surface.validate_exact_page_coordinate(selected)` |
| validate_exact_page_coordinate | isinstance (src/llm_wiki_cli/services…date_exact_page_coordinate) | 263 | `isinstance(value, str)` |
| validate_exact_page_coordinate | value.strip (src/llm_wiki_cli/services…date_exact_page_coordinate) | 263 | `value.strip(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `normalize_documentation_query_text` | `isinstance` | 60 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 60 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 62 |
| unresolved_call | `normalize_documentation_query_text` | `selected.encode` | 63 |
| external_call | `validate_exact_page_coordinate` | `isinstance` | 263 |
| unresolved_call | `validate_exact_page_coordinate` | `value.strip` | 263 |
| step_limit | `normalize_concept_coordinate` | `first 12 steps` | 0 |

## Behavior

This flow starts at `normalize_concept_coordinate` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
