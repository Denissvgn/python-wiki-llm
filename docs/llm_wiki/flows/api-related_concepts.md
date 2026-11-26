# related_concepts

**Entry point:** `related_concepts` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [canonical_json](../modules/canonical_json.md), [common](../modules/common.md), [context_packet](../modules/context_packet.md), and 24 more

**Complete modules touched:**

- [api](../modules/api.md)
- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
- [context_packet](../modules/context_packet.md)
- [context_packet_builder](../modules/context_packet_builder.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [domain_pack](../modules/domain_pack.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [gitignore](../modules/gitignore.md)
- [host](../modules/host.md)
- [integrations](../modules/integrations.md)
- [io](../modules/io.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [path_policy](../modules/path_policy.md)
- [python_implementation](../modules/python_implementation.md)
- [query_request_format](../modules/query_request_format.md)
- [source_path_diagnostics](../modules/source_path_diagnostics.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as related_concepts
    participant p1 as _normalize_query_input
    participant p2 as normalize_concept_coordinate
    participant p3 as _normalize_query_choice
    participant p4 as _normalize_query_values
    participant p5 as _effective_query_limit
    participant p6 as _run_query
    participant p7 as _query_service
    participant p8 as normalize_documentation_query_text
    participant p9 as _normalize_query_limit
    participant p10 as build_documentation_query_service
    participant p11 as normalize_documentation_query_limit
    participant p12 as validate_source_root
    participant p13 as _validate_wiki_dir
    participant p14 as build_live_documentation_query_service
    participant p15 as validate_path
    participant p16 as normalize_supplied_paths
    participant p17 as resolve_source_selection
    participant p18 as capture_source_selection_inputs
    participant p19 as validate_live_query_source_selection
    participant p20 as windows_current_user_sid
    participant p21 as _source_anchor
    participant p22 as _wiki_anchor
    participant p23 as source_path_diagnostics
    participant p24 as first_unsafe_path_component
    participant p25 as _live_source_selection_identity
    participant p26 as confirmed_missing_source_paths (src/llm_wiki_cli/services/context_packet_builder.py)
    participant p27 as attach_implementation_read_view
    participant p28 as analysis_identity (src/llm_wiki_cli/services/python_implementation.py)
    participant p29 as cast
    participant p30 as _query_service(…).related_concepts
    p0->>p1: _normalize_query_input
    p0->>p2: normalize_concept_coordinate
    p0->>p3: _normalize_query_choice
    p0->>p4: _normalize_query_values
    p0->>p5: _effective_query_limit
    p0->>p6: _run_query
    p0->>p7: _query_service
    p2->>p8: normalize_documentation_query_text
    p5->>p9: _normalize_query_limit
    p7->>p10: build_documentation_query_service
    p9->>p11: normalize_documentation_query_limit
    p10->>p12: validate_source_root
    p10->>p13: _validate_wiki_dir
    p10->>p14: build_live_documentation_query_service
    p12->>p15: validate_path
    p14->>p16: normalize_supplied_paths
    p14->>p17: resolve_source_selection
    p14->>p18: capture_source_selection_inputs
    p14->>p19: validate_live_query_source_selection
    p12->>p20: windows_current_user_sid
    p14->>p21: _source_anchor
    p14->>p22: _wiki_anchor
    p14->>p23: source_path_diagnostics
    p12->>p24: first_unsafe_path_component
    p14->>p25: _live_source_selection_identity
    p14->>p26: confirmed_missing_source_paths (src/llm_wiki_cli/services/context_packet_builder.py)
    p14->>p27: attach_implementation_read_view
    p14->>p28: analysis_identity (src/llm_wiki_cli/services/python_implementation.py)
    p0-->>p29: cast(RelatedConceptsResult, _run_query(...))
    p0-->>p30: _query_service(…).related_concepts(query, direction=selected_direction, kinds=selected_kinds)
```

> Call sequence diagram shows 30 of 900 interactions; 870 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 357 (356 omitted); unresolved 1 of 195 (194 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/api.py:_normalize_query_input` | 2 | - | unresolved | 1 |
| `src/llm_wiki_cli/api.py:_normalize_query_input` | 2 | [src/llm_wiki_cli/api.py](../modules/api.md) | internal | 1 |
| `src/llm_wiki_cli/api.py:_normalize_query_input` | 2 | - | external | 1 |
| `src/llm_wiki_engine/query_request_format.py:normalize_documentation_query_text` | 7 | - | external | 2 |
| `src/llm_wiki_engine/query_request_format.py:normalize_documentation_query_text` | 7 | - | unresolved | 3 |
| `src/llm_wiki_engine/query_request_format.py:normalize_documentation_query_text` | 7 | [src/llm_wiki_engine/query_request_format.py](../modules/query_request_format.md) | internal | 2 |
| `src/llm_wiki_engine/query_request_format.py:normalize_concept_coordinate` | 6 | - | unresolved | 2 |
| `src/llm_wiki_engine/query_request_format.py:normalize_concept_coordinate` | 6 | [src/llm_wiki_engine/query_request_format.py](../modules/query_request_format.md) | internal | 1 |
> Omission summary shows 8 of 215 groups; 207 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 349; effect analysis evaluated: 224, partial: 14, unavailable: 111. Counts include steps omitted from the displayed trace.

Collector observations for 238 source steps with known totals: observed: 1397, emitted: 1313, omitted: 84. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `related_concepts` | `available` | `partial` | `available` | `14` | `12` | `2` |
| `_normalize_query_input` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `callback (src/llm_wiki_cli/api.py:_normalize_query_input)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `InvalidRequestError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `str (src/llm_wiki_cli/api.py:_normalize_query_input)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `normalize_concept_coordinate` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `normalize_documentation_query_text` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `isinstance (src/llm_wiki_engine/query…_documentation_query_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `value.strip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `DocumentationQueryError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `value.strip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len (src/llm_wiki_engine/query…_documentation_query_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. related_concepts"]
    s2["2. _normalize_query_input"]
    s3["3. callback (src/llm_wiki_cli/api.py:_normalize_query_input)"]
    s4["4. InvalidRequestError"]
    s5["5. str (src/llm_wiki_cli/api.py:_normalize_query_input)"]
    s6["6. normalize_concept_coordinate"]
    s7["7. normalize_documentation_query_text"]
    s8["8. isinstance (src/llm_wiki_engine/query…_documentation_query_text)"]
    s9["9. value.strip"]
    s10["10. DocumentationQueryError"]
    s11["11. value.strip"]
    s12["12. len (src/llm_wiki_engine/query…_documentation_query_text)"]
    s1 -->|"_normalize_query_input(...)"| s2
    s2 -. "callback (src/llm_wiki_cli/api.py:_normalize_query_input)(data not statically known)" .-> s3
    s2 -->|"InvalidRequestError(str(...), code='invalid-request', details={...})"| s4
    s2 -. "str (src/llm_wiki_cli/api.py:_normalize_query_input)(exc)" .-> s5
    s1 -->|"normalize_concept_coordinate(locator_or_exact_route)"| s6
    s6 -->|"normalize_documentation_query_text(value, field='locator_or_exact_route')"| s7
    s7 -. "isinstance (src/llm_wiki_engine/query…_documentation_query_text)(value, str)" .-> s8
    s7 -. "value.strip(data not statically known)" .-> s9
    s7 -->|"DocumentationQueryError(...)"| s10
    s7 -. "value.strip(data not statically known)" .-> s11
    s7 -. "len (src/llm_wiki_engine/query…_documentation_query_text)(selected.encode(...))" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
    click s4 "../modules/api.md"
    click s6 "../modules/query_request_format.md"
    click s7 "../modules/query_request_format.md"
    click s10 "../modules/query_request_format.md"
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
| `isinstance (src/llm_wiki_engine/query…_documentation_query_text)` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `len (src/llm_wiki_engine/query…_documentation_query_text)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| related_concepts | _normalize_query_input | 2706 | `_normalize_query_input(...)` |
| _normalize_query_input | callback (src/llm_wiki_cli/api.py:_normalize_query_input) | 2288 | `callback(data not statically known)` |
| _normalize_query_input | InvalidRequestError | 2290 | `InvalidRequestError(str(...), code='invalid-request', details={...})` |
| _normalize_query_input | str (src/llm_wiki_cli/api.py:_normalize_query_input) | 2291 | `str(exc)` |
| related_concepts | normalize_concept_coordinate | 2707 | `normalize_concept_coordinate(locator_or_exact_route)` |
| normalize_concept_coordinate | normalize_documentation_query_text | 62 | `normalize_documentation_query_text(value, field='locator_or_exact_route')` |
| normalize_documentation_query_text | isinstance (src/llm_wiki_engine/query…_documentation_query_text) | 49 | `isinstance(value, str)` |
| normalize_documentation_query_text | value.strip | 49 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | DocumentationQueryError | 50 | `DocumentationQueryError(...)` |
| normalize_documentation_query_text | value.strip | 51 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | len (src/llm_wiki_engine/query…_documentation_query_text) | 52 | `len(selected.encode(...))` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalize_query_input` | `callback` | 2288 |
| external_call | `normalize_documentation_query_text` | `isinstance` | 49 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 49 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 51 |
| step_limit | `related_concepts` | `first 12 steps` | 0 |
| truncated_flow | `related_concepts` | `depth limit` | 0 |

## Behavior

This flow starts at `related_concepts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
