# normalize_supplied_paths

**Entry point:** `normalize_supplied_paths` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as normalize_supplied_paths
    participant p1 as _portable_supplied_path
    participant p2 as DocumentationQueryError
    participant p3 as require_portable_relative_path
    participant p4 as isinstance
    participant p5 as _default_path_error
    participant p6 as SharedValidationError
    participant p7 as fspath
    participant p8 as encode
    participant p9 as replace
    participant p10 as PurePosixPath
    participant p11 as is_absolute
    participant p12 as match
    participant p13 as as_posix
    participant p14 as strip
    participant p15 as endswith
    participant p16 as casefold
    participant p17 as require_portable_path_component
    participant p18 as normalize
    participant p19 as any
    p0->>p1: _portable_supplied_path
    p1->>p2: DocumentationQueryError
    p1->>p3: require_portable_relative_path
    p3-->>p4: isinstance
    p3->>p5: _default_path_error
    p5->>p6: SharedValidationError
    p3-->>p7: fspath
    p3-->>p4: isinstance
    p3->>p5: _default_path_error
    p3-->>p8: encode
    p3->>p5: _default_path_error
    p3->>p5: _default_path_error
    p3-->>p9: replace
    p3-->>p10: PurePosixPath
    p3-->>p11: is_absolute
    p3-->>p12: match
    p3->>p5: _default_path_error
    p3->>p5: _default_path_error
    p3-->>p13: as_posix
    p3-->>p14: strip
    p3-->>p15: endswith
    p3-->>p16: casefold
    p3-->>p16: casefold
    p3->>p5: _default_path_error
    p3->>p17: require_portable_path_component
    p17-->>p8: encode
    p17->>p6: SharedValidationError
    p17-->>p18: normalize
    p17->>p6: SharedValidationError
    p17-->>p19: any
```

> Call sequence diagram shows 30 of 58 interactions; 28 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. normalize_supplied_paths"]
    s2["2. _portable_supplied_path"]
    s3["3. DocumentationQueryError"]
    s4["4. require_portable_relative_path"]
    s5["5. isinstance"]
    s6["6. _default_path_error"]
    s7["7. SharedValidationError"]
    s8["8. fspath"]
    s9["9. isinstance"]
    s10["10. _default_path_error"]
    s11["11. encode"]
    s12["12. _default_path_error"]
    s1 -->|"_portable_supplied_path(value)"| s2
    s2 -->|"DocumentationQueryError('paths must contain normalized portable relative source paths.')"| s3
    s2 -->|"require_portable_relative_path(value, text_error=error, relative_error=error, escape_error=error, traversal_error=error, separator_error=error, utf8_error=erro…"| s4
    s4 -. "isinstance(value, (...))" .-> s5
    s4 -->|"_default_path_error(value)"| s6
    s6 -->|"SharedValidationError(...)"| s7
    s4 -. "os.fspath(value)" .-> s8
    s4 -. "isinstance(raw, str)" .-> s9
    s4 -->|"_default_path_error(value)"| s10
    s4 -. "raw.encode('utf-8')" .-> s11
    s4 -->|"_default_path_error(raw)"| s12
    click s1 "../modules/documentation_query_builder.md"
    click s2 "../modules/documentation_query_builder.md"
    click s3 "../modules/documentation_queries.md"
    click s4 "../modules/validation.md"
    click s6 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s10 "../modules/validation.md"
    click s12 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| require_portable_relative_path | _default_path_error | 179 | `_default_path_error(raw)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_portable_relative_path` | `isinstance` | 170 |
| external_call | `require_portable_relative_path` | `os.fspath` | 172 |
| unresolved_call | `require_portable_relative_path` | `isinstance` | 173 |
| unresolved_call | `require_portable_relative_path` | `raw.encode` | 176 |
| step_limit | `normalize_supplied_paths` | `first 12 steps` | 0 |

## Behavior

This flow starts at `normalize_supplied_paths` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
