# build_infrastructure_observation_basis

**Entry point:** `build_infrastructure_observation_basis` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_infrastructure_observation_basis
    participant p1 as _validate_source_path
    participant p2 as require_repository_relative_path
    participant p3 as isinstance
    participant p4 as strip
    participant p5 as any
    participant p6 as ord
    participant p7 as startswith
    participant p8 as match
    participant p9 as split
    participant p10 as PurePosixPath
    participant p11 as normpath
    participant p12 as require_portable_relative_path
    participant p13 as _default_path_error
    participant p14 as SharedValidationError
    participant p15 as fspath
    participant p16 as encode
    participant p17 as replace
    participant p18 as is_absolute
    p0->>p1: _validate_source_path
    p1->>p2: require_repository_relative_path
    p2-->>p3: isinstance
    p2-->>p4: strip
    p2-->>p5: any
    p2-->>p6: ord
    p2-->>p6: ord
    p2-->>p7: startswith
    p2-->>p7: startswith
    p2-->>p8: match
    p2-->>p9: split
    p2-->>p10: PurePosixPath
    p2-->>p5: any
    p2-->>p11: normpath
    p2->>p12: require_portable_relative_path
    p12-->>p3: isinstance
    p12->>p13: _default_path_error
    p13->>p14: SharedValidationError
    p12-->>p15: fspath
    p12-->>p3: isinstance
    p12->>p13: _default_path_error
    p12-->>p16: encode
    p12->>p13: _default_path_error
    p12->>p13: _default_path_error
    p12-->>p17: replace
    p12-->>p10: PurePosixPath
    p12-->>p18: is_absolute
    p12-->>p8: match
    p12->>p13: _default_path_error
    p12->>p13: _default_path_error
```

> Call sequence diagram shows 30 of 81 interactions; 51 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_infrastructure_observation_basis"]
    s2["2. _validate_source_path"]
    s3["3. require_repository_relative_path"]
    s4["4. isinstance"]
    s5["5. strip"]
    s6["6. any"]
    s7["7. ord"]
    s8["8. ord"]
    s9["9. startswith"]
    s10["10. startswith"]
    s11["11. match"]
    s12["12. split"]
    s1 -->|"_validate_source_path(source_path)"| s2
    s2 -->|"require_repository_relative_path(source_path, text_error=ValueError(...), posix_error=ValueError(...), normalized_error=ValueError(...))"| s3
    s3 -. "isinstance(value, str)" .-> s4
    s3 -. "value.strip(data not statically known)" .-> s5
    s3 -. "any(...)" .-> s6
    s3 -. "ord(character)" .-> s7
    s3 -. "ord(character)" .-> s8
    s3 -. "value.startswith('/')" .-> s9
    s3 -. "value.startswith('\\')" .-> s10
    s3 -. "_WINDOWS_DRIVE_PREFIX_RE.match(value)" .-> s11
    s3 -. "value.split('/')" .-> s12
    click s1 "../modules/knowledge_evidence.md"
    click s2 "../modules/knowledge_evidence.md"
    click s3 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_infrastructure_observation_basis` | `source_path: str`, `source_content_hash: str`, `observation_hash: str`, `extractor_ref: str` | `INFRASTRUCTURE_OBSERVATION_SCOPE` | - | `ConceptObservationBasis(...)` |
| `_validate_source_path` | `source_path: object` | - | - | - |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_infrastructure_observation_basis | _validate_source_path | 409 | `_validate_source_path(source_path)` |
| _validate_source_path | require_repository_relative_path | 872 | `require_repository_relative_path(source_path, text_error=ValueError(...), posix_error=ValueError(...), normalized_error=ValueError(...))` |
| require_repository_relative_path | isinstance | 256 | `isinstance(value, str)` |
| require_repository_relative_path | strip | 258 | `value.strip(data not statically known)` |
| require_repository_relative_path | any | 260 | `any(...)` |
| require_repository_relative_path | ord | 261 | `ord(character)` |
| require_repository_relative_path | ord | 262 | `ord(character)` |
| require_repository_relative_path | startswith | 268 | `value.startswith('/')` |
| require_repository_relative_path | startswith | 269 | `value.startswith('\\')` |
| require_repository_relative_path | match | 270 | `_WINDOWS_DRIVE_PREFIX_RE.match(value)` |
| require_repository_relative_path | split | 275 | `value.split('/')` |

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
| step_limit | `build_infrastructure_observation_basis` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_infrastructure_observation_basis` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
