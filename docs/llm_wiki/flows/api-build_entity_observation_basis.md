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
    participant p4 as isinstance (src/llm_wiki_cli/services…_repository_relative_path)
    participant p5 as value.strip (src/llm_wiki_cli/services…_repository_relative_path)
    participant p6 as any (src/llm_wiki_cli/services…_repository_relative_path)
    participant p7 as ord (src/llm_wiki_cli/services…_repository_relative_path)
    participant p8 as value.startswith
    participant p9 as _WINDOWS_DRIVE_PREFIX_RE.match
    participant p10 as value.split
    participant p11 as PurePosixPath (src/llm_wiki_cli/services…_repository_relative_path)
    participant p12 as posixpath.normpath
    participant p13 as require_portable_relative_path
    participant p14 as isinstance (src/llm_wiki_cli/services…re_portable_relative_path)
    participant p15 as _default_path_error
    participant p16 as SharedValidationError
    participant p17 as os.fspath
    participant p18 as raw.encode
    participant p19 as raw.replace
    participant p20 as PurePosixPath (src/llm_wiki_cli/services…re_portable_relative_path)
    participant p21 as path.is_absolute
    participant p22 as _WINDOWS_ABSOLUTE_RE.match
    p0->>p1: _validate_basis_inputs
    p1->>p2: _validate_source_path
    p2->>p3: require_repository_relative_path
    p3-->>p4: isinstance (src/llm_wiki_cli/services…_repository_relative_path)
    p3-->>p5: value.strip (src/llm_wiki_cli/services…_repository_relative_path)
    p3-->>p6: any (src/llm_wiki_cli/services…_repository_relative_path)
    p3-->>p7: ord (src/llm_wiki_cli/services…_repository_relative_path)
    p3-->>p7: ord (src/llm_wiki_cli/services…_repository_relative_path)
    p3-->>p8: value.startswith
    p3-->>p8: value.startswith
    p3-->>p9: _WINDOWS_DRIVE_PREFIX_RE.match
    p3-->>p10: value.split
    p3-->>p11: PurePosixPath (src/llm_wiki_cli/services…_repository_relative_path)
    p3-->>p6: any (src/llm_wiki_cli/services…_repository_relative_path)
    p3-->>p12: posixpath.normpath
    p3->>p13: require_portable_relative_path
    p13-->>p14: isinstance (src/llm_wiki_cli/services…re_portable_relative_path)
    p13->>p15: _default_path_error
    p15->>p16: SharedValidationError
    p13-->>p17: os.fspath
    p13-->>p14: isinstance (src/llm_wiki_cli/services…re_portable_relative_path)
    p13->>p15: _default_path_error
    p13-->>p18: raw.encode
    p13->>p15: _default_path_error
    p13->>p15: _default_path_error
    p13-->>p19: raw.replace
    p13-->>p20: PurePosixPath (src/llm_wiki_cli/services…re_portable_relative_path)
    p13-->>p21: path.is_absolute
    p13-->>p22: _WINDOWS_ABSOLUTE_RE.match
    p13->>p15: _default_path_error
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
    s5["5. isinstance (src/llm_wiki_cli/services…_repository_relative_path)"]
    s6["6. value.strip (src/llm_wiki_cli/services…_repository_relative_path)"]
    s7["7. any (src/llm_wiki_cli/services…_repository_relative_path)"]
    s8["8. ord (src/llm_wiki_cli/services…_repository_relative_path)"]
    s9["9. ord (src/llm_wiki_cli/services…_repository_relative_path)"]
    s10["10. value.startswith"]
    s11["11. value.startswith"]
    s12["12. _WINDOWS_DRIVE_PREFIX_RE.match"]
    s1 -->|"_validate_basis_inputs(source_path, source_content_hash, extractor_ref, inventory_complete)"| s2
    s2 -->|"_validate_source_path(source_path)"| s3
    s3 -->|"require_repository_relative_path(source_path, text_error=ValueError(...), posix_error=ValueError(...), normalized_error=ValueError(...))"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…_repository_relative_path)(value, str)" .-> s5
    s4 -. "value.strip (src/llm_wiki_cli/services…_repository_relative_path)(data not statically known)" .-> s6
    s4 -. "any (src/llm_wiki_cli/services…_repository_relative_path)(...)" .-> s7
    s4 -. "ord (src/llm_wiki_cli/services…_repository_relative_path)(character)" .-> s8
    s4 -. "ord (src/llm_wiki_cli/services…_repository_relative_path)(character)" .-> s9
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
| `isinstance (src/llm_wiki_cli/services…_repository_relative_path)` | - | - | - | - |
| `value.strip (src/llm_wiki_cli/services…_repository_relative_path)` | - | - | - | - |
| `any (src/llm_wiki_cli/services…_repository_relative_path)` | - | - | - | - |
| `ord (src/llm_wiki_cli/services…_repository_relative_path)` | - | - | - | - |
| `ord (src/llm_wiki_cli/services…_repository_relative_path)` | - | - | - | - |
| `value.startswith` | - | - | - | - |
| `value.startswith` | - | - | - | - |
| `_WINDOWS_DRIVE_PREFIX_RE.match` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_entity_observation_basis | _validate_basis_inputs | 352 | `_validate_basis_inputs(source_path, source_content_hash, extractor_ref, inventory_complete)` |
| _validate_basis_inputs | _validate_source_path | 845 | `_validate_source_path(source_path)` |
| _validate_source_path | require_repository_relative_path | 873 | `require_repository_relative_path(source_path, text_error=ValueError(...), posix_error=ValueError(...), normalized_error=ValueError(...))` |
| require_repository_relative_path | isinstance (src/llm_wiki_cli/services…_repository_relative_path) | 256 | `isinstance(value, str)` |
| require_repository_relative_path | value.strip (src/llm_wiki_cli/services…_repository_relative_path) | 258 | `value.strip(data not statically known)` |
| require_repository_relative_path | any (src/llm_wiki_cli/services…_repository_relative_path) | 260 | `any(...)` |
| require_repository_relative_path | ord (src/llm_wiki_cli/services…_repository_relative_path) | 261 | `ord(character)` |
| require_repository_relative_path | ord (src/llm_wiki_cli/services…_repository_relative_path) | 262 | `ord(character)` |
| require_repository_relative_path | value.startswith | 268 | `value.startswith('/')` |
| require_repository_relative_path | value.startswith | 269 | `value.startswith('\\')` |
| require_repository_relative_path | _WINDOWS_DRIVE_PREFIX_RE.match | 270 | `_WINDOWS_DRIVE_PREFIX_RE.match(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_repository_relative_path` | `isinstance` | 256 |
| unresolved_call | `require_repository_relative_path` | `value.strip` | 258 |
| external_call | `require_repository_relative_path` | `any` | 260 |
| external_call | `require_repository_relative_path` | `ord` | 261 |
| external_call | `require_repository_relative_path` | `ord` | 262 |
| unresolved_call | `require_repository_relative_path` | `value.startswith` | 268 |
| unresolved_call | `require_repository_relative_path` | `value.startswith` | 269 |
| unresolved_call | `require_repository_relative_path` | `_WINDOWS_DRIVE_PREFIX_RE.match` | 270 |
| step_limit | `build_entity_observation_basis` | `first 12 steps` | 0 |
| truncated_flow | `build_entity_observation_basis` | `depth limit` | 0 |

## Behavior

This flow starts at `build_entity_observation_basis` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
