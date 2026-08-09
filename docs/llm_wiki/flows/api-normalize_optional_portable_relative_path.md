# normalize_optional_portable_relative_path

**Entry point:** `normalize_optional_portable_relative_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as normalize_optional_portable_relative_path
    participant p1 as isinstance
    participant p2 as strip
    participant p3 as replace
    participant p4 as startswith
    participant p5 as require_portable_relative_path
    participant p6 as _default_path_error
    participant p7 as SharedValidationError
    participant p8 as fspath
    participant p9 as encode
    participant p10 as PurePosixPath
    participant p11 as is_absolute
    participant p12 as match
    participant p13 as as_posix
    participant p14 as endswith
    participant p15 as casefold
    participant p16 as require_portable_path_component
    p0-->>p1: isinstance
    p0-->>p2: strip
    p0-->>p3: replace
    p0-->>p2: strip
    p0-->>p4: startswith
    p0->>p5: require_portable_relative_path
    p5-->>p1: isinstance
    p5->>p6: _default_path_error
    p6->>p7: SharedValidationError
    p5-->>p8: fspath
    p5-->>p1: isinstance
    p5->>p6: _default_path_error
    p5-->>p9: encode
    p5->>p6: _default_path_error
    p5->>p6: _default_path_error
    p5-->>p3: replace
    p5-->>p10: PurePosixPath
    p5-->>p11: is_absolute
    p5-->>p12: match
    p5->>p6: _default_path_error
    p5->>p6: _default_path_error
    p5-->>p13: as_posix
    p5-->>p2: strip
    p5-->>p14: endswith
    p5-->>p15: casefold
    p5-->>p15: casefold
    p5->>p6: _default_path_error
    p5->>p16: require_portable_path_component
    p16-->>p9: encode
    p16->>p7: SharedValidationError
```

> Call sequence diagram shows 30 of 48 interactions; 18 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. normalize_optional_portable_relative_path"]
    s2["2. isinstance"]
    s3["3. strip"]
    s4["4. replace"]
    s5["5. strip"]
    s6["6. startswith"]
    s7["7. require_portable_relative_path"]
    s8["8. isinstance"]
    s9["9. _default_path_error"]
    s10["10. SharedValidationError"]
    s11["11. fspath"]
    s12["12. isinstance"]
    s1 -. "isinstance(value, str)" .-> s2
    s1 -. "value.strip(data not statically known)" .-> s3
    s1 -. "value.strip().replace('\\', '/')" .-> s4
    s1 -. "value.strip(data not statically known)" .-> s5
    s1 -. "normalized.startswith('./')" .-> s6
    s1 -->|"require_portable_relative_path(normalized)"| s7
    s7 -. "isinstance(value, (...))" .-> s8
    s7 -->|"_default_path_error(value)"| s9
    s9 -->|"SharedValidationError(...)"| s10
    s7 -. "os.fspath(value)" .-> s11
    s7 -. "isinstance(raw, str)" .-> s12
    click s1 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s9 "../modules/validation.md"
    click s10 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `normalize_optional_portable_relative_path` | `value: object` | `SharedValidationError` | - | `None`, `require_portable_relative_path(...)`, `None` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `replace` | - | - | - | - |
| `strip` | - | - | - | - |
| `startswith` | - | - | - | - |
| `require_portable_relative_path` | `value: object`, `normalize_backslashes: bool`, `normalize_posix_spelling: bool`, `required_suffix: str \| None`, `defer_non_nfc_error: bool`, `reject_delete_character: bool`, `text_error: Exception \| None`, `relative_error: Exception \| None` | `os` | - | `canonical` |
| `isinstance` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `SharedValidationError` | - | - | - | - |
| `fspath` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| normalize_optional_portable_relative_path | isinstance | 382 | `isinstance(value, str)` |
| normalize_optional_portable_relative_path | strip | 382 | `value.strip(data not statically known)` |
| normalize_optional_portable_relative_path | replace | 384 | `value.strip().replace('\\', '/')` |
| normalize_optional_portable_relative_path | strip | 384 | `value.strip(data not statically known)` |
| normalize_optional_portable_relative_path | startswith | 385 | `normalized.startswith('./')` |
| normalize_optional_portable_relative_path | require_portable_relative_path | 388 | `require_portable_relative_path(normalized)` |
| require_portable_relative_path | isinstance | 170 | `isinstance(value, (...))` |
| require_portable_relative_path | _default_path_error | 171 | `_default_path_error(value)` |
| _default_path_error | SharedValidationError | 67 | `SharedValidationError(...)` |
| require_portable_relative_path | fspath | 172 | `os.fspath(value)` |
| require_portable_relative_path | isinstance | 173 | `isinstance(raw, str)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `normalize_optional_portable_relative_path` | `isinstance` | 382 |
| unresolved_call | `normalize_optional_portable_relative_path` | `value.strip` | 382 |
| unresolved_call | `normalize_optional_portable_relative_path` | `value.strip().replace` | 384 |
| unresolved_call | `normalize_optional_portable_relative_path` | `value.strip` | 384 |
| unresolved_call | `normalize_optional_portable_relative_path` | `normalized.startswith` | 385 |
| unresolved_call | `require_portable_relative_path` | `isinstance` | 170 |
| external_call | `require_portable_relative_path` | `os.fspath` | 172 |
| unresolved_call | `require_portable_relative_path` | `isinstance` | 173 |
| step_limit | `normalize_optional_portable_relative_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `normalize_optional_portable_relative_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
