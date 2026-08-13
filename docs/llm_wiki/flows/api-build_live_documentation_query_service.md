# build_live_documentation_query_service

**Entry point:** `build_live_documentation_query_service` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), and 3 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_live_documentation_query_service
    participant p1 as normalize_supplied_paths
    participant p2 as _portable_supplied_path
    participant p3 as DocumentationQueryError
    participant p4 as require_portable_relative_path
    participant p5 as isinstance
    participant p6 as _default_path_error
    participant p7 as SharedValidationError
    participant p8 as fspath
    participant p9 as encode
    participant p10 as replace
    participant p11 as PurePosixPath
    participant p12 as is_absolute
    participant p13 as match
    participant p14 as as_posix
    participant p15 as strip
    participant p16 as endswith
    participant p17 as casefold
    participant p18 as require_portable_path_component
    participant p19 as normalize
    p0->>p1: normalize_supplied_paths
    p1->>p2: _portable_supplied_path
    p2->>p3: DocumentationQueryError
    p2->>p4: require_portable_relative_path
    p4-->>p5: isinstance
    p4->>p6: _default_path_error
    p6->>p7: SharedValidationError
    p4-->>p8: fspath
    p4-->>p5: isinstance
    p4->>p6: _default_path_error
    p4-->>p9: encode
    p4->>p6: _default_path_error
    p4->>p6: _default_path_error
    p4-->>p10: replace
    p4-->>p11: PurePosixPath
    p4-->>p12: is_absolute
    p4-->>p13: match
    p4->>p6: _default_path_error
    p4->>p6: _default_path_error
    p4-->>p14: as_posix
    p4-->>p15: strip
    p4-->>p16: endswith
    p4-->>p17: casefold
    p4-->>p17: casefold
    p4->>p6: _default_path_error
    p4->>p18: require_portable_path_component
    p18-->>p9: encode
    p18->>p7: SharedValidationError
    p18-->>p19: normalize
    p18->>p7: SharedValidationError
```

> Call sequence diagram shows 30 of 474 interactions; 444 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_live_documentation_query_service"]
    s2["2. normalize_supplied_paths"]
    s3["3. _portable_supplied_path"]
    s4["4. DocumentationQueryError"]
    s5["5. require_portable_relative_path"]
    s6["6. isinstance"]
    s7["7. _default_path_error"]
    s8["8. SharedValidationError"]
    s9["9. fspath"]
    s10["10. isinstance"]
    s11["11. _default_path_error"]
    s12["12. encode"]
    s1 -->|"normalize_supplied_paths(paths)"| s2
    s2 -->|"_portable_supplied_path(value)"| s3
    s3 -->|"DocumentationQueryError('paths must contain normalized portable relative source paths.')"| s4
    s3 -->|"require_portable_relative_path(value, text_error=error, relative_error=error, escape_error=error, traversal_error=error, separator_error=error, utf8_error=erro…"| s5
    s5 -. "isinstance(value, (...))" .-> s6
    s5 -->|"_default_path_error(value)"| s7
    s7 -->|"SharedValidationError(...)"| s8
    s5 -. "os.fspath(value)" .-> s9
    s5 -. "isinstance(raw, str)" .-> s10
    s5 -->|"_default_path_error(value)"| s11
    s5 -. "raw.encode('utf-8')" .-> s12
    click s1 "../modules/documentation_query_builder.md"
    click s2 "../modules/documentation_query_builder.md"
    click s3 "../modules/documentation_query_builder.md"
    click s4 "../modules/documentation_queries.md"
    click s5 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s8 "../modules/validation.md"
    click s11 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_live_documentation_query_service` | `source_root: Path`, `wiki_root: Path`, `limit: int`, `read_only: bool`, `helper_cache_dir: Path \| None`, `include_plugins: bool`, `source_plugins_only: bool`, `require_live_freshness: bool` | `build_source_snapshot`, `SourceSelectionError`, `SourceSelectionError`, `KnowledgeReadView`, `KnowledgeReadView`, `KnowledgeReadView`, `Mapping` | `stage_ns[...]`, `snapshot_options[...]`, `stage_ns[...]`, `extract_options[...]`, `extract_options[...]`, `extract_options[...]`, `extract_options[...]`, `extract_options[...]` | `service` |
| `normalize_supplied_paths` | `values: object` | - | - | `tuple(...)` |
| `_portable_supplied_path` | `value: object` | - | - | `require_portable_relative_path(...)` |
| `DocumentationQueryError` | - | - | - | - |
| `require_portable_relative_path` | `value: object`, `normalize_backslashes: bool`, `normalize_posix_spelling: bool`, `required_suffix: str \| None`, `defer_non_nfc_error: bool`, `reject_delete_character: bool`, `text_error: Exception \| None`, `relative_error: Exception \| None` | `os` | - | `canonical` |
| `isinstance` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `SharedValidationError` | - | - | - | - |
| `fspath` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `encode` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_live_documentation_query_service | normalize_supplied_paths | 477 | `normalize_supplied_paths(paths)` |
| normalize_supplied_paths | _portable_supplied_path | 135 | `_portable_supplied_path(value)` |
| _portable_supplied_path | DocumentationQueryError | 113 | `DocumentationQueryError('paths must contain normalized portable relative source paths.')` |
| _portable_supplied_path | require_portable_relative_path | 116 | `require_portable_relative_path(value, text_error=error, relative_error=error, escape_error=error, traversal_error=error, separator_error=error, utf8_error=error, control_error=error, non_nfc_error=error, nonportable_error=error, reserved_error=error)` |
| require_portable_relative_path | isinstance | 170 | `isinstance(value, (...))` |
| require_portable_relative_path | _default_path_error | 171 | `_default_path_error(value)` |
| _default_path_error | SharedValidationError | 67 | `SharedValidationError(...)` |
| require_portable_relative_path | fspath | 172 | `os.fspath(value)` |
| require_portable_relative_path | isinstance | 173 | `isinstance(raw, str)` |
| require_portable_relative_path | _default_path_error | 174 | `_default_path_error(value)` |
| require_portable_relative_path | encode | 176 | `raw.encode('utf-8')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_portable_relative_path` | `isinstance` | 170 |
| external_call | `require_portable_relative_path` | `os.fspath` | 172 |
| unresolved_call | `require_portable_relative_path` | `isinstance` | 173 |
| unresolved_call | `require_portable_relative_path` | `raw.encode` | 176 |
| step_limit | `build_live_documentation_query_service` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_live_documentation_query_service` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
