# dependency_neighborhood

**Entry point:** `dependency_neighborhood` (`api`)
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
    participant p0 as dependency_neighborhood
    participant p1 as _normalize_query_input
    participant p2 as callback
    participant p3 as InvalidRequestError
    participant p4 as str
    participant p5 as normalize_supplied_paths
    participant p6 as _portable_supplied_path
    participant p7 as DocumentationQueryError
    participant p8 as require_portable_relative_path
    participant p9 as isinstance
    participant p10 as _default_path_error
    participant p11 as SharedValidationError
    participant p12 as fspath
    participant p13 as encode
    participant p14 as replace
    participant p15 as PurePosixPath
    participant p16 as is_absolute
    participant p17 as match
    participant p18 as as_posix
    participant p19 as strip
    participant p20 as endswith
    participant p21 as casefold
    participant p22 as require_portable_path_component
    p0->>p1: _normalize_query_input
    p1-->>p2: callback
    p1->>p3: InvalidRequestError
    p1-->>p4: str
    p0->>p5: normalize_supplied_paths
    p5->>p6: _portable_supplied_path
    p6->>p7: DocumentationQueryError
    p6->>p8: require_portable_relative_path
    p8-->>p9: isinstance
    p8->>p10: _default_path_error
    p10->>p11: SharedValidationError
    p8-->>p12: fspath
    p8-->>p9: isinstance
    p8->>p10: _default_path_error
    p8-->>p13: encode
    p8->>p10: _default_path_error
    p8->>p10: _default_path_error
    p8-->>p14: replace
    p8-->>p15: PurePosixPath
    p8-->>p16: is_absolute
    p8-->>p17: match
    p8->>p10: _default_path_error
    p8->>p10: _default_path_error
    p8-->>p18: as_posix
    p8-->>p19: strip
    p8-->>p20: endswith
    p8-->>p21: casefold
    p8-->>p21: casefold
    p8->>p10: _default_path_error
    p8->>p22: require_portable_path_component
```

> Call sequence diagram shows 30 of 382 interactions; 352 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. dependency_neighborhood"]
    s2["2. _normalize_query_input"]
    s3["3. callback"]
    s4["4. InvalidRequestError"]
    s5["5. str"]
    s6["6. normalize_supplied_paths"]
    s7["7. _portable_supplied_path"]
    s8["8. DocumentationQueryError"]
    s9["9. require_portable_relative_path"]
    s10["10. isinstance"]
    s11["11. _default_path_error"]
    s12["12. SharedValidationError"]
    s1 -->|"_normalize_query_input(...)"| s2
    s2 -. "callback(data not statically known)" .-> s3
    s2 -->|"InvalidRequestError(str(...), code='invalid-request', details={...})"| s4
    s2 -. "str(exc)" .-> s5
    s1 -->|"normalize_supplied_paths((...))"| s6
    s6 -->|"_portable_supplied_path(value)"| s7
    s7 -->|"DocumentationQueryError('paths must contain normalized portable relative source paths.')"| s8
    s7 -->|"require_portable_relative_path(value, text_error=error, relative_error=error, escape_error=error, traversal_error=error, separator_error=error, utf8_error=erro…"| s9
    s9 -. "isinstance(value, (...))" .-> s10
    s9 -->|"_default_path_error(value)"| s11
    s11 -->|"SharedValidationError(...)"| s12
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
    click s4 "../modules/api.md"
    click s6 "../modules/documentation_query_builder.md"
    click s7 "../modules/documentation_query_builder.md"
    click s8 "../modules/documentation_queries.md"
    click s9 "../modules/validation.md"
    click s11 "../modules/validation.md"
    click s12 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `dependency_neighborhood` | `path: object`, `service: DocumentationGraphQueryService \| None`, `src_dir: str`, `wiki_dir: str`, `limit: int`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None` | `DependencyNeighborhoodResult` | - | `cast(...)` |
| `_normalize_query_input` | `callback: Callable[[], _R]`, `field: str` | `DocumentationQueryError` | - | `callback(...)` |
| `callback` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `str` | - | - | - | - |
| `normalize_supplied_paths` | `values: object` | - | - | `tuple(...)` |
| `_portable_supplied_path` | `value: object` | - | - | `require_portable_relative_path(...)` |
| `DocumentationQueryError` | - | - | - | - |
| `require_portable_relative_path` | `value: object`, `normalize_backslashes: bool`, `normalize_posix_spelling: bool`, `required_suffix: str \| None`, `defer_non_nfc_error: bool`, `reject_delete_character: bool`, `text_error: Exception \| None`, `relative_error: Exception \| None` | `os` | - | `canonical` |
| `isinstance` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `SharedValidationError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| dependency_neighborhood | _normalize_query_input | 1393 | `_normalize_query_input(...)` |
| _normalize_query_input | callback | 1137 | `callback(data not statically known)` |
| _normalize_query_input | InvalidRequestError | 1139 | `InvalidRequestError(str(...), code='invalid-request', details={...})` |
| _normalize_query_input | str | 1140 | `str(exc)` |
| dependency_neighborhood | normalize_supplied_paths | 1393 | `normalize_supplied_paths((...))` |
| normalize_supplied_paths | _portable_supplied_path | 135 | `_portable_supplied_path(value)` |
| _portable_supplied_path | DocumentationQueryError | 113 | `DocumentationQueryError('paths must contain normalized portable relative source paths.')` |
| _portable_supplied_path | require_portable_relative_path | 116 | `require_portable_relative_path(value, text_error=error, relative_error=error, escape_error=error, traversal_error=error, separator_error=error, utf8_error=error, control_error=error, non_nfc_error=error, nonportable_error=error, reserved_error=error)` |
| require_portable_relative_path | isinstance | 170 | `isinstance(value, (...))` |
| require_portable_relative_path | _default_path_error | 171 | `_default_path_error(value)` |
| _default_path_error | SharedValidationError | 67 | `SharedValidationError(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalize_query_input` | `callback` | 1137 |
| unresolved_call | `require_portable_relative_path` | `isinstance` | 170 |
| step_limit | `dependency_neighborhood` | `first 12 steps` | 0 |
| truncated_flow | `dependency_neighborhood` | `depth limit` | 0 |

## Behavior

This flow starts at `dependency_neighborhood` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
