# related_concepts

**Entry point:** `related_concepts` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [common](../modules/common.md), [config](../modules/config.md), [context_packet](../modules/context_packet.md), and 21 more

**Complete modules touched:**

- [api](../modules/api.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [io](../modules/io.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [python_implementation](../modules/python_implementation.md)
- [source_path_diagnostics](../modules/source_path_diagnostics.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as related_concepts
    participant p1 as _normalize_query_input
    participant p2 as normalize_concept_coordinate
    participant p3 as _normalize_query_choice
    participant p4 as _normalize_query_values
    participant p5 as _effective_query_limit
    participant p6 as cast
    participant p7 as _run_query
    participant p8 as _query_service(…).related_concepts
    participant p9 as _query_service
    participant p10 as callback (src/llm_wiki_cli/api.py:_normalize_query_input)
    participant p11 as normalize_documentation_query_text
    participant p12 as isinstance (src/llm_wiki_cli/api.py:_normalize_query_choice)
    participant p13 as isinstance (src/llm_wiki_cli/api.py:_normalize_query_values)
    participant p14 as _normalize_query_limit
    participant p15 as callback (src/llm_wiki_cli/api.py:_run_query)
    participant p16 as InvalidRequestError
    participant p17 as validate_exact_page_coordinate
    participant p18 as ', '.join
    participant p19 as build_documentation_query_service
    participant p20 as str (src/llm_wiki_cli/api.py:_normalize_query_input)
    participant p21 as validator
    participant p22 as repr
    participant p23 as str (src/llm_wiki_cli/api.py:_run_query)
    participant p24 as DocumentationQueryError
    participant p25 as list (src/llm_wiki_cli/api.py:_normalize_query_values)
    p0->>p1: _normalize_query_input
    p0->>p2: normalize_concept_coordinate
    p0->>p3: _normalize_query_choice
    p0->>p4: _normalize_query_values
    p0->>p5: _effective_query_limit
    p0-->>p6: cast(RelatedConceptsResult, _run_query(...))
    p0->>p7: _run_query
    p0-->>p8: _query_service(…).related_concepts(query, direction=selected_direction, kinds=selected_kinds)
    p0->>p9: _query_service
    p1-->>p10: callback (src/llm_wiki_cli/api.py:_normalize_query_input)
    p2->>p11: normalize_documentation_query_text
    p3-->>p12: isinstance (src/llm_wiki_cli/api.py:_normalize_query_choice)(value, str)
    p4-->>p13: isinstance (src/llm_wiki_cli/api.py:_normalize_query_values)(values, (...))
    p5->>p14: _normalize_query_limit
    p7-->>p15: callback (src/llm_wiki_cli/api.py:_run_query)
    p9->>p16: InvalidRequestError
    p1->>p16: InvalidRequestError
    p2->>p17: validate_exact_page_coordinate
    p3-->>p18: ', '.join(...)
    p4-->>p13: isinstance (src/llm_wiki_cli/api.py:_normalize_query_values)(values, Iterable)
    p7->>p16: InvalidRequestError
    p9->>p19: build_documentation_query_service
    p1-->>p20: str (src/llm_wiki_cli/api.py:_normalize_query_input)(exc)
    p2-->>p21: validator(selected)
    p3-->>p22: repr(item)
    p4->>p16: InvalidRequestError
    p7-->>p23: str (src/llm_wiki_cli/api.py:_run_query)(exc)
    p2->>p24: DocumentationQueryError
    p3->>p16: InvalidRequestError
    p4-->>p25: list (src/llm_wiki_cli/api.py:_normalize_query_values)(islice(...))
```

> Call sequence diagram shows 30 of 984 interactions; 954 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 399 (391 omitted); unresolved 5 of 222 (217 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_query_builder.py:normalize_documentation_query_text` | 7 | - | external | 2 |
| `src/llm_wiki_cli/services/documentation_query_builder.py:normalize_documentation_query_text` | 7 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/documentation_query_builder.py:normalize_documentation_query_text` | 7 | [src/llm_wiki_cli/services/documentation_queries.py](../modules/documentation_queries.md) | internal | 2 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 15 | - | external | 4 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 15 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 15 | [src/llm_wiki_cli/services/wiki_surface.py](../modules/wiki_surface.md) | internal | 7 |
| `src/llm_wiki_cli/services/wiki_surface.py:_matches_directory_path` | 24 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/wiki_surface.py:_matches_directory_path` | 24 | - | external | 3 |
> Omission summary shows 8 of 223 groups; 215 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. related_concepts"]
    s2["2. _normalize_query_input"]
    s3["3. callback (src/llm_wiki_cli/api.py:_normalize_query_input)"]
    s4["4. InvalidRequestError"]
    s5["5. str (src/llm_wiki_cli/api.py:_normalize_query_input)"]
    s6["6. normalize_concept_coordinate"]
    s7["7. normalize_documentation_query_text"]
    s8["8. isinstance (src/llm_wiki_cli/services…_documentation_query_text)"]
    s9["9. value.strip (src/llm_wiki_cli/services…_documentation_query_text)"]
    s10["10. DocumentationQueryError"]
    s11["11. value.strip (src/llm_wiki_cli/services…_documentation_query_text)"]
    s12["12. len (src/llm_wiki_cli/services…_documentation_query_text)"]
    s1 -->|"_normalize_query_input(...)"| s2
    s2 -. "callback (src/llm_wiki_cli/api.py:_normalize_query_input)(data not statically known)" .-> s3
    s2 -->|"InvalidRequestError(str(...), code='invalid-request', details={...})"| s4
    s2 -. "str (src/llm_wiki_cli/api.py:_normalize_query_input)(exc)" .-> s5
    s1 -->|"normalize_concept_coordinate(locator_or_exact_route)"| s6
    s6 -->|"normalize_documentation_query_text(value, field='locator_or_exact_route')"| s7
    s7 -. "isinstance (src/llm_wiki_cli/services…_documentation_query_text)(value, str)" .-> s8
    s7 -. "value.strip (src/llm_wiki_cli/services…_documentation_query_text)(data not statically known)" .-> s9
    s7 -->|"DocumentationQueryError(...)"| s10
    s7 -. "value.strip (src/llm_wiki_cli/services…_documentation_query_text)(data not statically known)" .-> s11
    s7 -. "len (src/llm_wiki_cli/services…_documentation_query_text)(selected.encode(...))" .-> s12
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
| `related_concepts` | `locator_or_exact_route: object`, `direction: str`, `kinds: Iterable[str] \| None`, `service: DocumentationGraphQueryService \| None`, `src_dir: str`, `wiki_dir: str`, `limit: int`, `allow_external_src: bool` | `_KNOWLEDGE_QUERY_DIRECTIONS`, `_KNOWLEDGE_QUERY_KINDS`, `RelatedConceptsResult` | - | `cast(...)` |
| `_normalize_query_input` | `callback: Callable[[], _R]`, `field: str` | `DocumentationQueryError` | - | `callback(...)` |
| `callback (src/llm_wiki_cli/api.py:_normalize_query_input)` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `str (src/llm_wiki_cli/api.py:_normalize_query_input)` | - | - | - | - |
| `normalize_concept_coordinate` | `value: object` | `wiki_surface`, `validate_concept_uid`, `validate_natural_key`, `ConceptIdentityError` | - | `wiki_surface.validate_exact_page_coordinate(...)`, `validator(...)` |
| `normalize_documentation_query_text` | `value: object`, `field: str` | `QUERY_IDENTITY_BYTE_LIMIT`, `QUERY_IDENTITY_BYTE_LIMIT` | - | `selected` |
| `isinstance (src/llm_wiki_cli/services…_documentation_query_text)` | - | - | - | - |
| `value.strip (src/llm_wiki_cli/services…_documentation_query_text)` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `value.strip (src/llm_wiki_cli/services…_documentation_query_text)` | - | - | - | - |
| `len (src/llm_wiki_cli/services…_documentation_query_text)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| related_concepts | _normalize_query_input | 2391 | `_normalize_query_input(...)` |
| _normalize_query_input | callback (src/llm_wiki_cli/api.py:_normalize_query_input) | 1998 | `callback(data not statically known)` |
| _normalize_query_input | InvalidRequestError | 2000 | `InvalidRequestError(str(...), code='invalid-request', details={...})` |
| _normalize_query_input | str (src/llm_wiki_cli/api.py:_normalize_query_input) | 2001 | `str(exc)` |
| related_concepts | normalize_concept_coordinate | 2392 | `normalize_concept_coordinate(locator_or_exact_route)` |
| normalize_concept_coordinate | normalize_documentation_query_text | 77 | `normalize_documentation_query_text(value, field='locator_or_exact_route')` |
| normalize_documentation_query_text | isinstance (src/llm_wiki_cli/services…_documentation_query_text) | 64 | `isinstance(value, str)` |
| normalize_documentation_query_text | value.strip (src/llm_wiki_cli/services…_documentation_query_text) | 64 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | DocumentationQueryError | 65 | `DocumentationQueryError(...)` |
| normalize_documentation_query_text | value.strip (src/llm_wiki_cli/services…_documentation_query_text) | 66 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | len (src/llm_wiki_cli/services…_documentation_query_text) | 67 | `len(selected.encode(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalize_query_input` | `callback` | 1998 |
| external_call | `normalize_documentation_query_text` | `isinstance` | 64 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 64 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 66 |
| step_limit | `related_concepts` | `first 12 steps` | 0 |
| truncated_flow | `related_concepts` | `depth limit` | 0 |

## Behavior

This flow starts at `related_concepts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
