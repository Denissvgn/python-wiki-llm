# require_portable_relative_path

**Entry point:** `require_portable_relative_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_portable_relative_path
    participant p1 as isinstance
    participant p2 as _default_path_error
    participant p3 as SharedValidationError
    participant p4 as os.fspath
    participant p5 as raw.encode
    participant p6 as raw.replace
    participant p7 as PurePosixPath
    participant p8 as path.is_absolute
    participant p9 as _WINDOWS_ABSOLUTE_RE.match
    participant p10 as path.as_posix
    participant p11 as normalized.strip
    participant p12 as canonical.casefold().endswith
    participant p13 as canonical.casefold
    participant p14 as required_suffix.casefold
    participant p15 as require_portable_path_component
    participant p16 as component.encode
    participant p17 as unicodedata.normalize (src/llm_wiki_cli/services…re_portable_path_component)
    participant p18 as any
    participant p19 as ord
    p0-->>p1: isinstance
    p0->>p2: _default_path_error
    p2->>p3: SharedValidationError
    p0-->>p4: os.fspath
    p0-->>p1: isinstance
    p0->>p2: _default_path_error
    p0-->>p5: raw.encode
    p0->>p2: _default_path_error
    p0->>p2: _default_path_error
    p0-->>p6: raw.replace
    p0-->>p7: PurePosixPath
    p0-->>p8: path.is_absolute
    p0-->>p9: _WINDOWS_ABSOLUTE_RE.match
    p0->>p2: _default_path_error
    p0->>p2: _default_path_error
    p0-->>p10: path.as_posix
    p0-->>p11: normalized.strip
    p0-->>p12: canonical.casefold().endswith
    p0-->>p13: canonical.casefold
    p0-->>p14: required_suffix.casefold
    p0->>p2: _default_path_error
    p0->>p15: require_portable_path_component
    p15-->>p16: component.encode
    p15->>p3: SharedValidationError
    p15-->>p17: unicodedata.normalize (src/llm_wiki_cli/services…re_portable_path_component)
    p15->>p3: SharedValidationError
    p15-->>p18: any
    p15-->>p19: ord
    p15-->>p19: ord
    p15->>p3: SharedValidationError
```

> Call sequence diagram shows 30 of 42 interactions; 12 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_portable_relative_path"]
    s2["2. isinstance"]
    s3["3. _default_path_error"]
    s4["4. SharedValidationError"]
    s5["5. os.fspath"]
    s6["6. isinstance"]
    s7["7. _default_path_error"]
    s8["8. raw.encode"]
    s9["9. _default_path_error"]
    s10["10. _default_path_error"]
    s11["11. raw.replace"]
    s12["12. PurePosixPath"]
    s1 -. "isinstance(value, (...))" .-> s2
    s1 -->|"_default_path_error(value)"| s3
    s3 -->|"SharedValidationError(...)"| s4
    s1 -. "os.fspath(value)" .-> s5
    s1 -. "isinstance(raw, str)" .-> s6
    s1 -->|"_default_path_error(value)"| s7
    s1 -. "raw.encode('utf-8')" .-> s8
    s1 -->|"_default_path_error(raw)"| s9
    s1 -->|"_default_path_error(raw)"| s10
    s1 -. "raw.replace('\\', '/')" .-> s11
    s1 -. "PurePosixPath(normalized)" .-> s12
    click s1 "../modules/validation.md"
    click s3 "../modules/validation.md"
    click s4 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s9 "../modules/validation.md"
    click s10 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_portable_relative_path` | `value: object`, `normalize_backslashes: bool`, `normalize_posix_spelling: bool`, `required_suffix: str \| None`, `defer_non_nfc_error: bool`, `reject_delete_character: bool`, `text_error: Exception \| None`, `relative_error: Exception \| None` | `os` | - | `canonical` |
| `isinstance` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `SharedValidationError` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `raw.encode` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `raw.replace` | - | - | - | - |
| `PurePosixPath` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_portable_relative_path | isinstance | 170 | `isinstance(value, (...))` |
| require_portable_relative_path | _default_path_error | 171 | `_default_path_error(value)` |
| _default_path_error | SharedValidationError | 67 | `SharedValidationError(...)` |
| require_portable_relative_path | os.fspath | 172 | `os.fspath(value)` |
| require_portable_relative_path | isinstance | 173 | `isinstance(raw, str)` |
| require_portable_relative_path | _default_path_error | 174 | `_default_path_error(value)` |
| require_portable_relative_path | raw.encode | 176 | `raw.encode('utf-8')` |
| require_portable_relative_path | _default_path_error | 179 | `_default_path_error(raw)` |
| require_portable_relative_path | _default_path_error | 182 | `_default_path_error(raw)` |
| require_portable_relative_path | raw.replace | 183 | `raw.replace('\\', '/')` |
| require_portable_relative_path | PurePosixPath | 184 | `PurePosixPath(normalized)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_portable_relative_path` | `isinstance` | 170 |
| external_call | `require_portable_relative_path` | `os.fspath` | 172 |
| external_call | `require_portable_relative_path` | `isinstance` | 173 |
| unresolved_call | `require_portable_relative_path` | `raw.encode` | 176 |
| unresolved_call | `require_portable_relative_path` | `raw.replace` | 183 |
| external_call | `require_portable_relative_path` | `PurePosixPath` | 184 |
| step_limit | `require_portable_relative_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `require_portable_relative_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
