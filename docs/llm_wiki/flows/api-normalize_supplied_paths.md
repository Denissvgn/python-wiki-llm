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
    participant p4 as isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p5 as _default_path_error
    participant p6 as SharedValidationError
    participant p7 as os.fspath
    participant p8 as raw.encode
    participant p9 as raw.replace
    participant p10 as PurePosixPath
    participant p11 as path.is_absolute
    participant p12 as _WINDOWS_ABSOLUTE_RE.match
    participant p13 as path.as_posix
    participant p14 as normalized.strip
    participant p15 as canonical.casefold().endswith
    participant p16 as canonical.casefold
    participant p17 as required_suffix.casefold
    participant p18 as require_portable_path_component
    participant p19 as component.encode
    participant p20 as unicodedata.normalize (src/llm_wiki_cli/services…re_portable_path_component)
    participant p21 as any
    p0->>p1: _portable_supplied_path
    p1->>p2: DocumentationQueryError
    p1->>p3: require_portable_relative_path
    p3-->>p4: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    p3->>p5: _default_path_error
    p5->>p6: SharedValidationError
    p3-->>p7: os.fspath
    p3-->>p4: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    p3->>p5: _default_path_error
    p3-->>p8: raw.encode
    p3->>p5: _default_path_error
    p3->>p5: _default_path_error
    p3-->>p9: raw.replace
    p3-->>p10: PurePosixPath
    p3-->>p11: path.is_absolute
    p3-->>p12: _WINDOWS_ABSOLUTE_RE.match
    p3->>p5: _default_path_error
    p3->>p5: _default_path_error
    p3-->>p13: path.as_posix
    p3-->>p14: normalized.strip
    p3-->>p15: canonical.casefold().endswith
    p3-->>p16: canonical.casefold
    p3-->>p17: required_suffix.casefold
    p3->>p5: _default_path_error
    p3->>p18: require_portable_path_component
    p18-->>p19: component.encode
    p18->>p6: SharedValidationError
    p18-->>p20: unicodedata.normalize (src/llm_wiki_cli/services…re_portable_path_component)
    p18->>p6: SharedValidationError
    p18-->>p21: any
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
    s5["5. isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)"]
    s6["6. _default_path_error"]
    s7["7. SharedValidationError"]
    s8["8. os.fspath"]
    s9["9. isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)"]
    s10["10. _default_path_error"]
    s11["11. raw.encode"]
    s12["12. _default_path_error"]
    s1 -->|"_portable_supplied_path(value)"| s2
    s2 -->|"DocumentationQueryError('paths must contain normalized portable relative source paths.')"| s3
    s2 -->|"require_portable_relative_path(…)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(value, (...))" .-> s5
    s4 -->|"_default_path_error(value)"| s6
    s6 -->|"SharedValidationError(...)"| s7
    s4 -. "os.fspath(value)" .-> s8
    s4 -. "isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(raw, str)" .-> s9
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
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `SharedValidationError` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `raw.encode` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| normalize_supplied_paths | _portable_supplied_path | 135 | `_portable_supplied_path(value)` |
| _portable_supplied_path | DocumentationQueryError | 113 | `DocumentationQueryError('paths must contain normalized portable relative source paths.')` |
| _portable_supplied_path | require_portable_relative_path | 116 | `require_portable_relative_path(value, text_error=error, relative_error=error, escape_error=error, traversal_error=error, separator_error=error, utf8_error=error, control_error=error, non_nfc_error=error, nonportable_error=error, reserved_error=error)` |
| require_portable_relative_path | isinstance (src/llm_wiki_cli/services…ire_portable_relative_path) | 170 | `isinstance(value, (...))` |
| require_portable_relative_path | _default_path_error | 171 | `_default_path_error(value)` |
| _default_path_error | SharedValidationError | 67 | `SharedValidationError(...)` |
| require_portable_relative_path | os.fspath | 172 | `os.fspath(value)` |
| require_portable_relative_path | isinstance (src/llm_wiki_cli/services…ire_portable_relative_path) | 173 | `isinstance(raw, str)` |
| require_portable_relative_path | _default_path_error | 174 | `_default_path_error(value)` |
| require_portable_relative_path | raw.encode | 176 | `raw.encode('utf-8')` |
| require_portable_relative_path | _default_path_error | 179 | `_default_path_error(raw)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_portable_relative_path` | `isinstance` | 170 |
| external_call | `require_portable_relative_path` | `os.fspath` | 172 |
| external_call | `require_portable_relative_path` | `isinstance` | 173 |
| unresolved_call | `require_portable_relative_path` | `raw.encode` | 176 |
| step_limit | `normalize_supplied_paths` | `first 12 steps` | 0 |

## Behavior

This flow starts at `normalize_supplied_paths` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
