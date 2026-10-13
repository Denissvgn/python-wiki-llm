# normalize_concept_coordinate

**Entry point:** `normalize_concept_coordinate` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as normalize_concept_coordinate
    participant p1 as normalize_documentation_query_text
    participant p2 as validate_exact_page_coordinate
    participant p3 as DocumentationQueryError
    participant p4 as _matches_directory_path
    participant p5 as _matches_directory_uri
    participant p6 as is_safe_page_id
    participant p7 as canonical_path
    participant p8 as mcp_uri
    participant p9 as _entry_for
    participant p10 as _validate_page_id
    participant p11 as is_portable_path_component
    participant p12 as require_portable_path_component
    participant p13 as WikiSurfaceError
    participant p14 as PageKind
    participant p15 as SharedValidationError
    participant p16 as isinstance (src/llm_wiki_cli/services…e_documentation_query_text)
    participant p17 as validator
    participant p18 as isinstance (src/llm_wiki_cli/services…date_exact_page_coordinate)
    participant p19 as value.strip (src/llm_wiki_cli/services…e_documentation_query_text)
    participant p20 as value.strip (src/llm_wiki_cli/services…date_exact_page_coordinate)
    participant p21 as len (src/llm_wiki_cli/services…e_documentation_query_text)
    participant p22 as any (src/llm_wiki_cli/services…date_exact_page_coordinate)
    participant p23 as selected.encode
    participant p24 as ord (src/llm_wiki_cli/services…date_exact_page_coordinate)
    participant p25 as coordinate.startswith (src/llm_wiki_cli/services…py:_matches_directory_path)
    participant p26 as coordinate.startswith (src/llm_wiki_cli/services….py:_matches_directory_uri)
    participant p27 as coordinate.endswith
    p0->>p1: normalize_documentation_query_text
    p0->>p2: validate_exact_page_coordinate
    p0->>p3: DocumentationQueryError
    p2->>p4: _matches_directory_path
    p2->>p5: _matches_directory_uri
    p4->>p6: is_safe_page_id
    p4->>p7: canonical_path
    p5->>p8: mcp_uri
    p7->>p9: _entry_for
    p7->>p10: _validate_page_id
    p6->>p11: is_portable_path_component
    p11->>p12: require_portable_path_component
    p2->>p13: WikiSurfaceError
    p9->>p14: PageKind
    p12->>p15: SharedValidationError
    p1-->>p16: isinstance (src/llm_wiki_cli/services…e_documentation_query_text)(value, str)
    p0-->>p17: validator(selected)
    p2-->>p18: isinstance (src/llm_wiki_cli/services…date_exact_page_coordinate)(value, str)
    p1-->>p19: value.strip (src/llm_wiki_cli/services…e_documentation_query_text)
    p2-->>p20: value.strip (src/llm_wiki_cli/services…date_exact_page_coordinate)
    p1-->>p19: value.strip (src/llm_wiki_cli/services…e_documentation_query_text)
    p2-->>p20: value.strip (src/llm_wiki_cli/services…date_exact_page_coordinate)
    p1-->>p21: len (src/llm_wiki_cli/services…e_documentation_query_text)(selected.encode(...))
    p2-->>p22: any (src/llm_wiki_cli/services…date_exact_page_coordinate)(...)
    p1-->>p23: selected.encode('utf-8')
    p2-->>p24: ord (src/llm_wiki_cli/services…date_exact_page_coordinate)(character)
    p2-->>p24: ord (src/llm_wiki_cli/services…date_exact_page_coordinate)(character)
    p4-->>p25: coordinate.startswith (src/llm_wiki_cli/services…py:_matches_directory_path)(prefix)
    p5-->>p26: coordinate.startswith (src/llm_wiki_cli/services….py:_matches_directory_uri)(prefix)
    p4-->>p27: coordinate.endswith('.md')
```

> Call sequence diagram shows 30 of 74 interactions; 44 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 6 of 23 (17 omitted); unresolved 9 of 16 (7 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_query_builder.py:normalize_documentation_query_text` | 2 | [src/llm_wiki_cli/services/documentation_queries.py](../modules/documentation_queries.md) | internal | 2 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 10 | [src/llm_wiki_cli/services/wiki_surface.py](../modules/wiki_surface.md) | internal | 4 |
| `src/llm_wiki_cli/services/wiki_surface.py:_matches_directory_path` | 19 | - | external | 3 |
| `src/llm_wiki_cli/services/wiki_surface.py:is_safe_page_id` | 25 | - | external | 3 |
| `src/llm_wiki_cli/services/wiki_surface.py:is_safe_page_id` | 25 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_portable_path_component` | 32 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_path_component` | 32 | - | external | 5 |
| `src/llm_wiki_cli/services/validation.py:require_portable_path_component` | 32 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 4 |
> Omission summary shows 8 of 17 groups; 9 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
| normalize_concept_coordinate | normalize_documentation_query_text | 77 | `normalize_documentation_query_text(value, field='locator_or_exact_route')` |
| normalize_documentation_query_text | isinstance (src/llm_wiki_cli/services…e_documentation_query_text) | 64 | `isinstance(value, str)` |
| normalize_documentation_query_text | value.strip (src/llm_wiki_cli/services…e_documentation_query_text) | 64 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | DocumentationQueryError | 65 | `DocumentationQueryError(...)` |
| normalize_documentation_query_text | value.strip (src/llm_wiki_cli/services…e_documentation_query_text) | 66 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | len (src/llm_wiki_cli/services…e_documentation_query_text) | 67 | `len(selected.encode(...))` |
| normalize_documentation_query_text | selected.encode | 67 | `selected.encode('utf-8')` |
| normalize_documentation_query_text | DocumentationQueryError | 68 | `DocumentationQueryError(...)` |
| normalize_concept_coordinate | validate_exact_page_coordinate | 82 | `wiki_surface.validate_exact_page_coordinate(selected)` |
| validate_exact_page_coordinate | isinstance (src/llm_wiki_cli/services…date_exact_page_coordinate) | 263 | `isinstance(value, str)` |
| validate_exact_page_coordinate | value.strip (src/llm_wiki_cli/services…date_exact_page_coordinate) | 263 | `value.strip(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `normalize_documentation_query_text` | `isinstance` | 64 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 64 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 66 |
| unresolved_call | `normalize_documentation_query_text` | `selected.encode` | 67 |
| external_call | `validate_exact_page_coordinate` | `isinstance` | 263 |
| unresolved_call | `validate_exact_page_coordinate` | `value.strip` | 263 |
| step_limit | `normalize_concept_coordinate` | `first 12 steps` | 0 |

## Behavior

This flow starts at `normalize_concept_coordinate` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
