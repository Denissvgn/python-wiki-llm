# flow_for_entrypoint

**Entry point:** `flow_for_entrypoint` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [common](../modules/common.md), [config](../modules/config.md), [context_packet](../modules/context_packet.md), and 20 more

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

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as flow_for_entrypoint
    participant p1 as _normalize_query_input
    participant p2 as normalize_documentation_query_text
    participant p3 as _effective_query_limit
    participant p4 as _run_query
    participant p5 as _query_service
    participant p6 as _normalize_query_limit
    participant p7 as build_documentation_query_service
    participant p8 as normalize_documentation_query_limit
    participant p9 as validate_source_root
    participant p10 as _validate_wiki_dir
    participant p11 as build_live_documentation_query_service
    participant p12 as validate_path
    participant p13 as normalize_supplied_paths
    participant p14 as resolve_source_selection
    participant p15 as capture_source_selection_inputs
    participant p16 as validate_live_query_source_selection
    participant p17 as windows_current_user_sid
    participant p18 as _source_anchor
    participant p19 as _wiki_anchor
    participant p20 as source_path_diagnostics
    participant p21 as _live_source_selection_identity
    participant p22 as confirmed_missing_source_paths (src/llm_wiki_cli/services/context_packet.py)
    participant p23 as attach_implementation_read_view
    participant p24 as analysis_identity
    participant p25 as read_guarded
    participant p26 as attach_maintenance_view_from_inputs
    participant p27 as _assert_source_unchanged
    participant p28 as _assert_wiki_unchanged
    participant p29 as cast
    participant p30 as _query_service(…).flow_for_entrypoint
    p0->>p1: _normalize_query_input
    p0->>p2: normalize_documentation_query_text
    p0->>p3: _effective_query_limit
    p0->>p4: _run_query
    p0->>p5: _query_service
    p3->>p6: _normalize_query_limit
    p5->>p7: build_documentation_query_service
    p6->>p8: normalize_documentation_query_limit
    p7->>p9: validate_source_root
    p7->>p10: _validate_wiki_dir
    p7->>p11: build_live_documentation_query_service
    p9->>p12: validate_path
    p11->>p13: normalize_supplied_paths
    p11->>p14: resolve_source_selection
    p11->>p15: capture_source_selection_inputs
    p11->>p16: validate_live_query_source_selection
    p9->>p17: windows_current_user_sid
    p11->>p18: _source_anchor
    p11->>p19: _wiki_anchor
    p11->>p20: source_path_diagnostics
    p11->>p21: _live_source_selection_identity
    p11->>p22: confirmed_missing_source_paths (src/llm_wiki_cli/services/context_packet.py)
    p11->>p23: attach_implementation_read_view
    p11->>p24: analysis_identity
    p11->>p25: read_guarded
    p11->>p26: attach_maintenance_view_from_inputs
    p11->>p27: _assert_source_unchanged
    p11->>p28: _assert_wiki_unchanged
    p0-->>p29: cast(FlowForEntrypointResult, _run_query(...))
    p0-->>p30: _query_service(…).flow_for_entrypoint(query)
```

> Call sequence diagram shows 30 of 914 interactions; 884 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 374 (373 omitted); unresolved 1 of 201 (200 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/api.py:_normalize_query_input` | 2 | - | unresolved | 1 |
| `src/llm_wiki_cli/api.py:_normalize_query_input` | 2 | [src/llm_wiki_cli/api.py](../modules/api.md) | internal | 1 |
| `src/llm_wiki_cli/api.py:_normalize_query_input` | 2 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_query_builder.py:normalize_documentation_query_text` | 6 | - | external | 2 |
| `src/llm_wiki_cli/services/documentation_query_builder.py:normalize_documentation_query_text` | 6 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/documentation_query_builder.py:normalize_documentation_query_text` | 6 | [src/llm_wiki_cli/services/documentation_queries.py](../modules/documentation_queries.md) | internal | 2 |
| `src/llm_wiki_cli/api.py:_normalize_query_limit` | 15 | [src/llm_wiki_cli/api.py](../modules/api.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_query_builder.py:normalize_documentation_query_limit` | 17 | - | external | 3 |
> Omission summary shows 8 of 196 groups; 188 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 340; effect analysis evaluated: 214, partial: 18, unavailable: 108. Counts include steps omitted from the displayed trace.

Collector observations for 232 source steps with known totals: observed: 1479, emitted: 1374, omitted: 105. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `flow_for_entrypoint` | `available` | `evaluated` | `available` | `10` | `10` | `0` |
| `_normalize_query_input` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `callback (src/llm_wiki_cli/api.py:_normalize_query_input)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `InvalidRequestError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `str (src/llm_wiki_cli/api.py:_normalize_query_input)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `normalize_documentation_query_text` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `isinstance (src/llm_wiki_cli/services…_documentation_query_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `value.strip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `DocumentationQueryError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `value.strip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len (src/llm_wiki_cli/services…_documentation_query_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `selected.encode` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. flow_for_entrypoint"]
    s2["2. _normalize_query_input"]
    s3["3. callback (src/llm_wiki_cli/api.py:_normalize_query_input)"]
    s4["4. InvalidRequestError"]
    s5["5. str (src/llm_wiki_cli/api.py:_normalize_query_input)"]
    s6["6. normalize_documentation_query_text"]
    s7["7. isinstance (src/llm_wiki_cli/services…_documentation_query_text)"]
    s8["8. value.strip"]
    s9["9. DocumentationQueryError"]
    s10["10. value.strip"]
    s11["11. len (src/llm_wiki_cli/services…_documentation_query_text)"]
    s12["12. selected.encode"]
    s1 -->|"_normalize_query_input(...)"| s2
    s2 -. "callback (src/llm_wiki_cli/api.py:_normalize_query_input)(data not statically known)" .-> s3
    s2 -->|"InvalidRequestError(str(...), code='invalid-request', details={...})"| s4
    s2 -. "str (src/llm_wiki_cli/api.py:_normalize_query_input)(exc)" .-> s5
    s1 -->|"normalize_documentation_query_text(id_or_symbol, field='id_or_symbol')"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…_documentation_query_text)(value, str)" .-> s7
    s6 -. "value.strip(data not statically known)" .-> s8
    s6 -->|"DocumentationQueryError(...)"| s9
    s6 -. "value.strip(data not statically known)" .-> s10
    s6 -. "len (src/llm_wiki_cli/services…_documentation_query_text)(selected.encode(...))" .-> s11
    s6 -. "selected.encode('utf-8')" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
    click s4 "../modules/api.md"
    click s6 "../modules/documentation_query_builder.md"
    click s9 "../modules/documentation_queries.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `flow_for_entrypoint` | `id_or_symbol: object`, `service: DocumentationGraphQueryService \| None`, `src_dir: str`, `wiki_dir: str`, `limit: int`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None` | `FlowForEntrypointResult` | - | `cast(...)` |
| `_normalize_query_input` | `callback: Callable[[], _R]`, `field: str` | `DocumentationQueryError` | - | `callback(...)` |
| `callback (src/llm_wiki_cli/api.py:_normalize_query_input)` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `str (src/llm_wiki_cli/api.py:_normalize_query_input)` | - | - | - | - |
| `normalize_documentation_query_text` | `value: object`, `field: str` | `QUERY_IDENTITY_BYTE_LIMIT`, `QUERY_IDENTITY_BYTE_LIMIT` | - | `selected` |
| `isinstance (src/llm_wiki_cli/services…_documentation_query_text)` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `len (src/llm_wiki_cli/services…_documentation_query_text)` | - | - | - | - |
| `selected.encode` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| flow_for_entrypoint | _normalize_query_input | 2156 | `_normalize_query_input(...)` |
| _normalize_query_input | callback (src/llm_wiki_cli/api.py:_normalize_query_input) | 2013 | `callback(data not statically known)` |
| _normalize_query_input | InvalidRequestError | 2015 | `InvalidRequestError(str(...), code='invalid-request', details={...})` |
| _normalize_query_input | str (src/llm_wiki_cli/api.py:_normalize_query_input) | 2016 | `str(exc)` |
| flow_for_entrypoint | normalize_documentation_query_text | 2157 | `normalize_documentation_query_text(id_or_symbol, field='id_or_symbol')` |
| normalize_documentation_query_text | isinstance (src/llm_wiki_cli/services…_documentation_query_text) | 65 | `isinstance(value, str)` |
| normalize_documentation_query_text | value.strip | 65 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | DocumentationQueryError | 66 | `DocumentationQueryError(...)` |
| normalize_documentation_query_text | value.strip | 67 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | len (src/llm_wiki_cli/services…_documentation_query_text) | 68 | `len(selected.encode(...))` |
| normalize_documentation_query_text | selected.encode | 68 | `selected.encode('utf-8')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalize_query_input` | `callback` | 2013 |
| external_call | `normalize_documentation_query_text` | `isinstance` | 65 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 65 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 67 |
| unresolved_call | `normalize_documentation_query_text` | `selected.encode` | 68 |
| step_limit | `flow_for_entrypoint` | `first 12 steps` | 0 |
| truncated_flow | `flow_for_entrypoint` | `depth limit` | 0 |

## Behavior

This flow starts at `flow_for_entrypoint` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
