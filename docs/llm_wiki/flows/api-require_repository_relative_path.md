# require_repository_relative_path

**Entry point:** `require_repository_relative_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_repository_relative_path
    participant p1 as isinstance
    participant p2 as strip
    participant p3 as any
    participant p4 as ord
    participant p5 as startswith
    participant p6 as match
    participant p7 as split
    participant p8 as PurePosixPath
    participant p9 as normpath
    participant p10 as require_portable_relative_path
    participant p11 as _default_path_error
    participant p12 as SharedValidationError
    participant p13 as fspath
    participant p14 as encode
    participant p15 as replace
    participant p16 as is_absolute
    participant p17 as as_posix
    p0-->>p1: isinstance
    p0-->>p2: strip
    p0-->>p3: any
    p0-->>p4: ord
    p0-->>p4: ord
    p0-->>p5: startswith
    p0-->>p5: startswith
    p0-->>p6: match
    p0-->>p7: split
    p0-->>p8: PurePosixPath
    p0-->>p3: any
    p0-->>p9: normpath
    p0->>p10: require_portable_relative_path
    p10-->>p1: isinstance
    p10->>p11: _default_path_error
    p11->>p12: SharedValidationError
    p10-->>p13: fspath
    p10-->>p1: isinstance
    p10->>p11: _default_path_error
    p10-->>p14: encode
    p10->>p11: _default_path_error
    p10->>p11: _default_path_error
    p10-->>p15: replace
    p10-->>p8: PurePosixPath
    p10-->>p16: is_absolute
    p10-->>p6: match
    p10->>p11: _default_path_error
    p10->>p11: _default_path_error
    p10-->>p17: as_posix
    p10-->>p2: strip
```

> Call sequence diagram shows 30 of 55 interactions; 25 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_repository_relative_path"]
    s2["2. isinstance"]
    s3["3. strip"]
    s4["4. any"]
    s5["5. ord"]
    s6["6. ord"]
    s7["7. startswith"]
    s8["8. startswith"]
    s9["9. match"]
    s10["10. split"]
    s11["11. PurePosixPath"]
    s12["12. any"]
    s1 -. "isinstance(value, str)" .-> s2
    s1 -. "value.strip(data not statically known)" .-> s3
    s1 -. "any(...)" .-> s4
    s1 -. "ord(character)" .-> s5
    s1 -. "ord(character)" .-> s6
    s1 -. "value.startswith('/')" .-> s7
    s1 -. "value.startswith('\\')" .-> s8
    s1 -. "_WINDOWS_DRIVE_PREFIX_RE.match(value)" .-> s9
    s1 -. "value.split('/')" .-> s10
    s1 -. "PurePosixPath(value)" .-> s11
    s1 -. "any(...)" .-> s12
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `require_portable_relative_path(...)` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |
| `ord` | - | - | - | - |
| `startswith` | - | - | - | - |
| `startswith` | - | - | - | - |
| `match` | - | - | - | - |
| `split` | - | - | - | - |
| `PurePosixPath` | - | - | - | - |
| `any` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_repository_relative_path | isinstance | 256 | `isinstance(value, str)` |
| require_repository_relative_path | strip | 258 | `value.strip(data not statically known)` |
| require_repository_relative_path | any | 260 | `any(...)` |
| require_repository_relative_path | ord | 261 | `ord(character)` |
| require_repository_relative_path | ord | 262 | `ord(character)` |
| require_repository_relative_path | startswith | 268 | `value.startswith('/')` |
| require_repository_relative_path | startswith | 269 | `value.startswith('\\')` |
| require_repository_relative_path | match | 270 | `_WINDOWS_DRIVE_PREFIX_RE.match(value)` |
| require_repository_relative_path | split | 275 | `value.split('/')` |
| require_repository_relative_path | PurePosixPath | 277 | `PurePosixPath(value)` |
| require_repository_relative_path | any | 280 | `any(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_repository_relative_path` | `isinstance` | 256 |
| unresolved_call | `require_repository_relative_path` | `value.strip` | 258 |
| unresolved_call | `require_repository_relative_path` | `any` | 260 |
| unresolved_call | `require_repository_relative_path` | `ord` | 261 |
| unresolved_call | `require_repository_relative_path` | `ord` | 262 |
| unresolved_call | `require_repository_relative_path` | `value.startswith` | 268 |
| unresolved_call | `require_repository_relative_path` | `value.startswith` | 269 |
| unresolved_call | `require_repository_relative_path` | `_WINDOWS_DRIVE_PREFIX_RE.match` | 270 |
| unresolved_call | `require_repository_relative_path` | `value.split` | 275 |
| external_call | `require_repository_relative_path` | `PurePosixPath` | 277 |
| unresolved_call | `require_repository_relative_path` | `any` | 280 |
| step_limit | `require_repository_relative_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `require_repository_relative_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
