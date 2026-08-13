# explain_evidence

**Entry point:** `explain_evidence` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [common](../modules/common.md), [config](../modules/config.md), [documentation_queries](../modules/documentation_queries.md), and 6 more

**Complete modules touched:**

- [api](../modules/api.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as explain_evidence
    participant p1 as _normalize_query_input
    participant p2 as callback
    participant p3 as InvalidRequestError
    participant p4 as str
    participant p5 as normalize_concept_coordinate
    participant p6 as normalize_documentation_query_text
    participant p7 as isinstance
    participant p8 as strip
    participant p9 as DocumentationQueryError
    participant p10 as len
    participant p11 as encode
    participant p12 as validate_exact_page_coordinate
    participant p13 as validator
    participant p14 as _effective_query_limit
    participant p15 as _normalize_query_limit
    participant p16 as normalize_documentation_query_limit
    participant p17 as min
    participant p18 as cast
    participant p19 as _run_query
    p0->>p1: _normalize_query_input
    p1-->>p2: callback
    p1->>p3: InvalidRequestError
    p1-->>p4: str
    p0->>p5: normalize_concept_coordinate
    p5->>p6: normalize_documentation_query_text
    p6-->>p7: isinstance
    p6-->>p8: strip
    p6->>p9: DocumentationQueryError
    p6-->>p8: strip
    p6-->>p10: len
    p6-->>p11: encode
    p6->>p9: DocumentationQueryError
    p5-->>p12: validate_exact_page_coordinate
    p5-->>p13: validator
    p5->>p9: DocumentationQueryError
    p0->>p14: _effective_query_limit
    p14->>p15: _normalize_query_limit
    p15->>p1: _normalize_query_input
    p15->>p16: normalize_documentation_query_limit
    p16-->>p7: isinstance
    p16-->>p7: isinstance
    p16->>p9: DocumentationQueryError
    p16-->>p17: min
    p0-->>p18: cast
    p0->>p19: _run_query
    p19-->>p2: callback
    p19->>p3: InvalidRequestError
    p19-->>p4: str
    p0-->>p0: explain_evidence
```

> Call sequence diagram shows 30 of 351 interactions; 321 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. explain_evidence"]
    s2["2. _normalize_query_input"]
    s3["3. callback"]
    s4["4. InvalidRequestError"]
    s5["5. str"]
    s6["6. normalize_concept_coordinate"]
    s7["7. normalize_documentation_query_text"]
    s8["8. isinstance"]
    s9["9. strip"]
    s10["10. DocumentationQueryError"]
    s11["11. strip"]
    s12["12. len"]
    s1 -->|"_normalize_query_input(...)"| s2
    s2 -. "callback(data not statically known)" .-> s3
    s2 -->|"InvalidRequestError(str(...), code='invalid-request', details={...})"| s4
    s2 -. "str(exc)" .-> s5
    s1 -->|"normalize_concept_coordinate(locator_or_exact_route)"| s6
    s6 -->|"normalize_documentation_query_text(value, field='locator_or_exact_route')"| s7
    s7 -. "isinstance(value, str)" .-> s8
    s7 -. "value.strip(data not statically known)" .-> s9
    s7 -->|"DocumentationQueryError(...)"| s10
    s7 -. "value.strip(data not statically known)" .-> s11
    s7 -. "len(selected.encode(...))" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
    click s4 "../modules/api.md"
    click s6 "../modules/documentation_query_builder.md"
    click s7 "../modules/documentation_query_builder.md"
    click s10 "../modules/documentation_queries.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `explain_evidence` | `locator_or_exact_route: object`, `service: DocumentationGraphQueryService \| None`, `src_dir: str`, `wiki_dir: str`, `limit: int`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None` | `EvidenceExplanationResult` | - | `cast(...)` |
| `_normalize_query_input` | `callback: Callable[[], _R]`, `field: str` | `DocumentationQueryError` | - | `callback(...)` |
| `callback` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `str` | - | - | - | - |
| `normalize_concept_coordinate` | `value: object` | `wiki_surface`, `validate_concept_uid`, `validate_natural_key`, `ConceptIdentityError` | - | `wiki_surface.validate_exact_page_coordinate(...)`, `validator(...)` |
| `normalize_documentation_query_text` | `value: object`, `field: str` | `QUERY_IDENTITY_BYTE_LIMIT`, `QUERY_IDENTITY_BYTE_LIMIT` | - | `selected` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `strip` | - | - | - | - |
| `len` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| explain_evidence | _normalize_query_input | 1649 | `_normalize_query_input(...)` |
| _normalize_query_input | callback | 1137 | `callback(data not statically known)` |
| _normalize_query_input | InvalidRequestError | 1139 | `InvalidRequestError(str(...), code='invalid-request', details={...})` |
| _normalize_query_input | str | 1140 | `str(exc)` |
| explain_evidence | normalize_concept_coordinate | 1650 | `normalize_concept_coordinate(locator_or_exact_route)` |
| normalize_concept_coordinate | normalize_documentation_query_text | 73 | `normalize_documentation_query_text(value, field='locator_or_exact_route')` |
| normalize_documentation_query_text | isinstance | 60 | `isinstance(value, str)` |
| normalize_documentation_query_text | strip | 60 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | DocumentationQueryError | 61 | `DocumentationQueryError(...)` |
| normalize_documentation_query_text | strip | 62 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | len | 63 | `len(selected.encode(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalize_query_input` | `callback` | 1137 |
| unresolved_call | `normalize_documentation_query_text` | `isinstance` | 60 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 60 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 62 |
| step_limit | `explain_evidence` | `first 12 steps` | 0 |
| truncated_flow | `explain_evidence` | `depth limit` | 0 |

## Behavior

This flow starts at `explain_evidence` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
