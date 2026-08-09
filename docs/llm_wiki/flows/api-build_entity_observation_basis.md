# build_entity_observation_basis

**Entry point:** `build_entity_observation_basis` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_entity_observation_basis
    participant p1 as _validate_basis_inputs
    participant p2 as _validate_source_path
    participant p3 as require_repository_relative_path
    participant p4 as isinstance
    participant p5 as strip
    participant p6 as any
    participant p7 as ord
    participant p8 as startswith
    participant p9 as match
    participant p10 as split
    participant p11 as PurePosixPath
    participant p12 as normpath
    participant p13 as require_portable_relative_path
    participant p14 as _default_path_error
    participant p15 as SharedValidationError
    participant p16 as fspath
    participant p17 as encode
    participant p18 as replace
    participant p19 as is_absolute
    p0->>p1: _validate_basis_inputs
    p1->>p2: _validate_source_path
    p2->>p3: require_repository_relative_path
    p3-->>p4: isinstance
    p3-->>p5: strip
    p3-->>p6: any
    p3-->>p7: ord
    p3-->>p7: ord
    p3-->>p8: startswith
    p3-->>p8: startswith
    p3-->>p9: match
    p3-->>p10: split
    p3-->>p11: PurePosixPath
    p3-->>p6: any
    p3-->>p12: normpath
    p3->>p13: require_portable_relative_path
    p13-->>p4: isinstance
    p13->>p14: _default_path_error
    p14->>p15: SharedValidationError
    p13-->>p16: fspath
    p13-->>p4: isinstance
    p13->>p14: _default_path_error
    p13-->>p17: encode
    p13->>p14: _default_path_error
    p13->>p14: _default_path_error
    p13-->>p18: replace
    p13-->>p11: PurePosixPath
    p13-->>p19: is_absolute
    p13-->>p9: match
    p13->>p14: _default_path_error
```

> Call sequence diagram shows 30 of 199 interactions; 169 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_entity_observation_basis"]
    s2["2. _validate_basis_inputs"]
    s3["3. _validate_source_path"]
    s4["4. require_repository_relative_path"]
    s5["5. isinstance"]
    s6["6. strip"]
    s7["7. any"]
    s8["8. ord"]
    s9["9. ord"]
    s10["10. startswith"]
    s11["11. startswith"]
    s12["12. match"]
    s1 -->|"_validate_basis_inputs(source_path, source_content_hash, extractor_ref, inventory_complete)"| s2
    s2 -->|"_validate_source_path(source_path)"| s3
    s3 -->|"require_repository_relative_path(source_path, text_error=ValueError(...), posix_error=ValueError(...), normalized_error=ValueError(...))"| s4
    s4 -. "isinstance(value, str)" .-> s5
    s4 -. "value.strip(data not statically known)" .-> s6
    s4 -. "any(...)" .-> s7
    s4 -. "ord(character)" .-> s8
    s4 -. "ord(character)" .-> s9
    s4 -. "value.startswith('/')" .-> s10
    s4 -. "value.startswith('\\')" .-> s11
    s4 -. "_WINDOWS_DRIVE_PREFIX_RE.match(value)" .-> s12
    click s1 "../modules/knowledge_evidence.md"
    click s2 "../modules/knowledge_evidence.md"
    click s3 "../modules/knowledge_evidence.md"
    click s4 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_entity_observation_basis` | `source_path: str`, `file_data: Mapping[str, Any] \| None`, `entity_name: str`, `occurrence: int`, `source_content_hash: str`, `extractor_ref: str`, `inventory_complete: bool` | `ENTITY_OBSERVATION_SCOPE`, `UNKNOWN_INSUFFICIENT_INVENTORY`, `_InventoryNormalizationError`, `ENTITY_OBSERVATION_SCOPE`, `ENTITY_OBSERVATION_SCOPE`, `UNKNOWN_INVALID_INVENTORY`, `ENTITY_OBSERVATION_SCOPE` | - | `_unknown_basis(...)`, `_unknown_basis(...)`, `_unknown_basis(...)`, `ConceptObservationBasis(...)` |
| `_validate_basis_inputs` | `source_path: object`, `source_content_hash: object`, `extractor_ref: object`, `inventory_complete: object` | - | - | - |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_entity_observation_basis | _validate_basis_inputs | 351 | `_validate_basis_inputs(source_path, source_content_hash, extractor_ref, inventory_complete)` |
| _validate_basis_inputs | _validate_source_path | 844 | `_validate_source_path(source_path)` |
| _validate_source_path | require_repository_relative_path | 872 | `require_repository_relative_path(source_path, text_error=ValueError(...), posix_error=ValueError(...), normalized_error=ValueError(...))` |
| require_repository_relative_path | isinstance | 256 | `isinstance(value, str)` |
| require_repository_relative_path | strip | 258 | `value.strip(data not statically known)` |
| require_repository_relative_path | any | 260 | `any(...)` |
| require_repository_relative_path | ord | 261 | `ord(character)` |
| require_repository_relative_path | ord | 262 | `ord(character)` |
| require_repository_relative_path | startswith | 268 | `value.startswith('/')` |
| require_repository_relative_path | startswith | 269 | `value.startswith('\\')` |
| require_repository_relative_path | match | 270 | `_WINDOWS_DRIVE_PREFIX_RE.match(value)` |

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
| step_limit | `build_entity_observation_basis` | `first 12 steps` | 0 |
| truncated_flow | `build_entity_observation_basis` | `depth limit` | 0 |

## Behavior

This flow starts at `build_entity_observation_basis` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
