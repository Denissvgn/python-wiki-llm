# data_flow_for_entrypoint

**Entry point:** `data_flow_for_entrypoint` (`api`)
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
    participant p0 as data_flow_for_entrypoint
    participant p1 as _normalize_query_input
    participant p2 as callback
    participant p3 as InvalidRequestError
    participant p4 as str
    participant p5 as normalize_documentation_query_text
    participant p6 as isinstance
    participant p7 as strip
    participant p8 as DocumentationQueryError
    participant p9 as len
    participant p10 as encode
    participant p11 as _effective_query_limit
    participant p12 as _normalize_query_limit
    participant p13 as normalize_documentation_query_limit
    participant p14 as min
    participant p15 as cast
    participant p16 as _run_query
    participant p17 as _query_service
    participant p18 as build_documentation_query_service
    p0->>p1: _normalize_query_input
    p1-->>p2: callback
    p1->>p3: InvalidRequestError
    p1-->>p4: str
    p0->>p5: normalize_documentation_query_text
    p5-->>p6: isinstance
    p5-->>p7: strip
    p5->>p8: DocumentationQueryError
    p5-->>p7: strip
    p5-->>p9: len
    p5-->>p10: encode
    p5->>p8: DocumentationQueryError
    p0->>p11: _effective_query_limit
    p11->>p12: _normalize_query_limit
    p12->>p1: _normalize_query_input
    p12->>p13: normalize_documentation_query_limit
    p13-->>p6: isinstance
    p13-->>p6: isinstance
    p13->>p8: DocumentationQueryError
    p13-->>p14: min
    p0-->>p15: cast
    p0->>p16: _run_query
    p16-->>p2: callback
    p16->>p3: InvalidRequestError
    p16-->>p4: str
    p0-->>p0: data_flow_for_entrypoint
    p0->>p17: _query_service
    p17->>p3: InvalidRequestError
    p17->>p18: build_documentation_query_service
    p18->>p13: normalize_documentation_query_limit
```

> Call sequence diagram shows 30 of 347 interactions; 317 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. data_flow_for_entrypoint"]
    s2["2. _normalize_query_input"]
    s3["3. callback"]
    s4["4. InvalidRequestError"]
    s5["5. str"]
    s6["6. normalize_documentation_query_text"]
    s7["7. isinstance"]
    s8["8. strip"]
    s9["9. DocumentationQueryError"]
    s10["10. strip"]
    s11["11. len"]
    s12["12. encode"]
    s1 -->|"_normalize_query_input(...)"| s2
    s2 -. "callback(data not statically known)" .-> s3
    s2 -->|"InvalidRequestError(str(...), code='invalid-request', details={...})"| s4
    s2 -. "str(exc)" .-> s5
    s1 -->|"normalize_documentation_query_text(id_or_symbol, field='id_or_symbol')"| s6
    s6 -. "isinstance(value, str)" .-> s7
    s6 -. "value.strip(data not statically known)" .-> s8
    s6 -->|"DocumentationQueryError(...)"| s9
    s6 -. "value.strip(data not statically known)" .-> s10
    s6 -. "len(selected.encode(...))" .-> s11
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
| `data_flow_for_entrypoint` | `id_or_symbol: object`, `service: DocumentationGraphQueryService \| None`, `src_dir: str`, `wiki_dir: str`, `limit: int`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None` | `DataFlowForEntrypointResult` | - | `cast(...)` |
| `_normalize_query_input` | `callback: Callable[[], _R]`, `field: str` | `DocumentationQueryError` | - | `callback(...)` |
| `callback` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `str` | - | - | - | - |
| `normalize_documentation_query_text` | `value: object`, `field: str` | `QUERY_IDENTITY_BYTE_LIMIT`, `QUERY_IDENTITY_BYTE_LIMIT` | - | `selected` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `strip` | - | - | - | - |
| `len` | - | - | - | - |
| `encode` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| data_flow_for_entrypoint | _normalize_query_input | 1291 | `_normalize_query_input(...)` |
| _normalize_query_input | callback | 1137 | `callback(data not statically known)` |
| _normalize_query_input | InvalidRequestError | 1139 | `InvalidRequestError(str(...), code='invalid-request', details={...})` |
| _normalize_query_input | str | 1140 | `str(exc)` |
| data_flow_for_entrypoint | normalize_documentation_query_text | 1292 | `normalize_documentation_query_text(id_or_symbol, field='id_or_symbol')` |
| normalize_documentation_query_text | isinstance | 60 | `isinstance(value, str)` |
| normalize_documentation_query_text | strip | 60 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | DocumentationQueryError | 61 | `DocumentationQueryError(...)` |
| normalize_documentation_query_text | strip | 62 | `value.strip(data not statically known)` |
| normalize_documentation_query_text | len | 63 | `len(selected.encode(...))` |
| normalize_documentation_query_text | encode | 63 | `selected.encode('utf-8')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalize_query_input` | `callback` | 1137 |
| unresolved_call | `normalize_documentation_query_text` | `isinstance` | 60 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 60 |
| unresolved_call | `normalize_documentation_query_text` | `value.strip` | 62 |
| unresolved_call | `normalize_documentation_query_text` | `selected.encode` | 63 |
| step_limit | `data_flow_for_entrypoint` | `first 12 steps` | 0 |
| truncated_flow | `data_flow_for_entrypoint` | `depth limit` | 0 |

## Behavior

This flow starts at `data_flow_for_entrypoint` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
