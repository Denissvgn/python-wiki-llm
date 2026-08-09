# validate_portable_relative_path

**Entry point:** `validate_portable_relative_path` (`api`)
**Source:** [protected_artifacts](../modules/protected_artifacts.md)
**Modules touched:** [protected_artifacts](../modules/protected_artifacts.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_portable_relative_path
    participant p1 as fspath
    participant p2 as isinstance
    participant p3 as replace
    participant p4 as require_portable_relative_path
    participant p5 as _default_path_error
    participant p6 as SharedValidationError
    participant p7 as encode
    participant p8 as PurePosixPath
    participant p9 as is_absolute
    participant p10 as match
    participant p11 as as_posix
    participant p12 as strip
    participant p13 as endswith
    participant p14 as casefold
    participant p15 as require_portable_path_component
    participant p16 as normalize
    p0-->>p1: fspath
    p0-->>p2: isinstance
    p0-->>p3: replace
    p0->>p4: require_portable_relative_path
    p4-->>p2: isinstance
    p4->>p5: _default_path_error
    p5->>p6: SharedValidationError
    p4-->>p1: fspath
    p4-->>p2: isinstance
    p4->>p5: _default_path_error
    p4-->>p7: encode
    p4->>p5: _default_path_error
    p4->>p5: _default_path_error
    p4-->>p3: replace
    p4-->>p8: PurePosixPath
    p4-->>p9: is_absolute
    p4-->>p10: match
    p4->>p5: _default_path_error
    p4->>p5: _default_path_error
    p4-->>p11: as_posix
    p4-->>p12: strip
    p4-->>p13: endswith
    p4-->>p14: casefold
    p4-->>p14: casefold
    p4->>p5: _default_path_error
    p4->>p15: require_portable_path_component
    p15-->>p7: encode
    p15->>p6: SharedValidationError
    p15-->>p16: normalize
    p15->>p6: SharedValidationError
```

> Call sequence diagram shows 30 of 51 interactions; 21 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_portable_relative_path"]
    s2["2. fspath"]
    s3["3. isinstance"]
    s4["4. replace"]
    s5["5. require_portable_relative_path"]
    s6["6. isinstance"]
    s7["7. _default_path_error"]
    s8["8. SharedValidationError"]
    s9["9. fspath"]
    s10["10. isinstance"]
    s11["11. _default_path_error"]
    s12["12. encode"]
    s1 -. "os.fspath(relative)" .-> s2
    s1 -. "isinstance(raw, str)" .-> s3
    s1 -. "raw.replace('\\', '/')" .-> s4
    s1 -->|"require_portable_relative_path(raw, normalize_backslashes=normalize_backslashes, text_error=ProtectedArtifactIntegrityError(...), relative_error=ProtectedArtif…"| s5
    s5 -. "isinstance(value, (...))" .-> s6
    s5 -->|"_default_path_error(value)"| s7
    s7 -->|"SharedValidationError(...)"| s8
    s5 -. "os.fspath(value)" .-> s9
    s5 -. "isinstance(raw, str)" .-> s10
    s5 -->|"_default_path_error(value)"| s11
    s5 -. "raw.encode('utf-8')" .-> s12
    click s1 "../modules/protected_artifacts.md"
    click s5 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s8 "../modules/validation.md"
    click s11 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_portable_relative_path` | `relative: str \| Path`, `normalize_backslashes: bool` | - | - | `require_portable_relative_path(...)` |
| `fspath` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `replace` | - | - | - | - |
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
| validate_portable_relative_path | fspath | 106 | `os.fspath(relative)` |
| validate_portable_relative_path | isinstance | 107 | `isinstance(raw, str)` |
| validate_portable_relative_path | replace | 107 | `raw.replace('\\', '/')` |
| validate_portable_relative_path | require_portable_relative_path | 108 | `require_portable_relative_path(raw, normalize_backslashes=normalize_backslashes, text_error=ProtectedArtifactIntegrityError(...), relative_error=ProtectedArtifactIntegrityError(...), non_nfc_error=ProtectedArtifactIntegrityError(...), nonportable_error=ProtectedArtifactIntegrityError(...), reserved_error=ProtectedArtifactIntegrityError(...))` |
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
| external_call | `validate_portable_relative_path` | `os.fspath` | 106 |
| unresolved_call | `validate_portable_relative_path` | `isinstance` | 107 |
| unresolved_call | `validate_portable_relative_path` | `raw.replace` | 107 |
| unresolved_call | `require_portable_relative_path` | `isinstance` | 170 |
| external_call | `require_portable_relative_path` | `os.fspath` | 172 |
| unresolved_call | `require_portable_relative_path` | `isinstance` | 173 |
| unresolved_call | `require_portable_relative_path` | `raw.encode` | 176 |
| step_limit | `validate_portable_relative_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `validate_portable_relative_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
