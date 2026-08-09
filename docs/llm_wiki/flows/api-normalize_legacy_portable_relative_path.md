# normalize_legacy_portable_relative_path

**Entry point:** `normalize_legacy_portable_relative_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as normalize_legacy_portable_relative_path
    participant p1 as isinstance
    participant p2 as strip
    participant p3 as replace
    participant p4 as PurePosixPath
    participant p5 as startswith
    participant p6 as is_absolute
    participant p7 as match
    participant p8 as as_posix
    participant p9 as require_portable_relative_path
    participant p10 as _default_path_error
    participant p11 as SharedValidationError
    participant p12 as fspath
    participant p13 as encode
    participant p14 as endswith
    participant p15 as casefold
    p0-->>p1: isinstance
    p0-->>p2: strip
    p0-->>p3: replace
    p0-->>p2: strip
    p0-->>p4: PurePosixPath
    p0-->>p5: startswith
    p0-->>p6: is_absolute
    p0-->>p7: match
    p0-->>p7: match
    p0-->>p8: as_posix
    p0->>p9: require_portable_relative_path
    p9-->>p1: isinstance
    p9->>p10: _default_path_error
    p10->>p11: SharedValidationError
    p9-->>p12: fspath
    p9-->>p1: isinstance
    p9->>p10: _default_path_error
    p9-->>p13: encode
    p9->>p10: _default_path_error
    p9->>p10: _default_path_error
    p9-->>p3: replace
    p9-->>p4: PurePosixPath
    p9-->>p6: is_absolute
    p9-->>p7: match
    p9->>p10: _default_path_error
    p9->>p10: _default_path_error
    p9-->>p8: as_posix
    p9-->>p2: strip
    p9-->>p14: endswith
    p9-->>p15: casefold
```

> Call sequence diagram shows 30 of 53 interactions; 23 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. normalize_legacy_portable_relative_path"]
    s2["2. isinstance"]
    s3["3. strip"]
    s4["4. replace"]
    s5["5. strip"]
    s6["6. PurePosixPath"]
    s7["7. startswith"]
    s8["8. is_absolute"]
    s9["9. match"]
    s10["10. match"]
    s11["11. as_posix"]
    s12["12. require_portable_relative_path"]
    s1 -. "isinstance(value, str)" .-> s2
    s1 -. "value.strip(data not statically known)" .-> s3
    s1 -. "value.strip().replace('\\', '/')" .-> s4
    s1 -. "value.strip(data not statically known)" .-> s5
    s1 -. "PurePosixPath(normalized_input)" .-> s6
    s1 -. "normalized_input.startswith('.//')" .-> s7
    s1 -. "path.is_absolute(data not statically known)" .-> s8
    s1 -. "_WINDOWS_ABSOLUTE_RE.match(normalized_input)" .-> s9
    s1 -. "_WINDOWS_DRIVE_PREFIX_RE.match(normalized_input)" .-> s10
    s1 -. "path.as_posix(data not statically known)" .-> s11
    s1 -->|"require_portable_relative_path(normalized)"| s12
    click s1 "../modules/validation.md"
    click s12 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `normalize_legacy_portable_relative_path` | `value: object`, `text_error: Exception \| None`, `absolute_error: Exception \| None`, `traversal_error: Exception \| None`, `empty_error: Exception \| None`, `invalid_error: Exception \| None`, `reject_dot_prefixed_absolute: bool` | `SharedValidationError` | - | `None`, `None`, `None`, `None`, `require_portable_relative_path(...)`, `None` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `replace` | - | - | - | - |
| `strip` | - | - | - | - |
| `PurePosixPath` | - | - | - | - |
| `startswith` | - | - | - | - |
| `is_absolute` | - | - | - | - |
| `match` | - | - | - | - |
| `match` | - | - | - | - |
| `as_posix` | - | - | - | - |
| `require_portable_relative_path` | `value: object`, `normalize_backslashes: bool`, `normalize_posix_spelling: bool`, `required_suffix: str \| None`, `defer_non_nfc_error: bool`, `reject_delete_character: bool`, `text_error: Exception \| None`, `relative_error: Exception \| None` | `os` | - | `canonical` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| normalize_legacy_portable_relative_path | isinstance | 338 | `isinstance(value, str)` |
| normalize_legacy_portable_relative_path | strip | 338 | `value.strip(data not statically known)` |
| normalize_legacy_portable_relative_path | replace | 342 | `value.strip().replace('\\', '/')` |
| normalize_legacy_portable_relative_path | strip | 342 | `value.strip(data not statically known)` |
| normalize_legacy_portable_relative_path | PurePosixPath | 343 | `PurePosixPath(normalized_input)` |
| normalize_legacy_portable_relative_path | startswith | 347 | `normalized_input.startswith('.//')` |
| normalize_legacy_portable_relative_path | is_absolute | 349 | `path.is_absolute(data not statically known)` |
| normalize_legacy_portable_relative_path | match | 350 | `_WINDOWS_ABSOLUTE_RE.match(normalized_input)` |
| normalize_legacy_portable_relative_path | match | 351 | `_WINDOWS_DRIVE_PREFIX_RE.match(normalized_input)` |
| normalize_legacy_portable_relative_path | as_posix | 360 | `path.as_posix(data not statically known)` |
| normalize_legacy_portable_relative_path | require_portable_relative_path | 366 | `require_portable_relative_path(normalized)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `normalize_legacy_portable_relative_path` | `isinstance` | 338 |
| unresolved_call | `normalize_legacy_portable_relative_path` | `value.strip` | 338 |
| unresolved_call | `normalize_legacy_portable_relative_path` | `value.strip().replace` | 342 |
| unresolved_call | `normalize_legacy_portable_relative_path` | `value.strip` | 342 |
| external_call | `normalize_legacy_portable_relative_path` | `PurePosixPath` | 343 |
| unresolved_call | `normalize_legacy_portable_relative_path` | `normalized_input.startswith` | 347 |
| unresolved_call | `normalize_legacy_portable_relative_path` | `path.is_absolute` | 349 |
| unresolved_call | `normalize_legacy_portable_relative_path` | `_WINDOWS_ABSOLUTE_RE.match` | 350 |
| unresolved_call | `normalize_legacy_portable_relative_path` | `_WINDOWS_DRIVE_PREFIX_RE.match` | 351 |
| unresolved_call | `normalize_legacy_portable_relative_path` | `path.as_posix` | 360 |
| step_limit | `normalize_legacy_portable_relative_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `normalize_legacy_portable_relative_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
