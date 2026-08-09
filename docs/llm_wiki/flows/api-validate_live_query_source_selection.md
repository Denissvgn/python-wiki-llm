# validate_live_query_source_selection

**Entry point:** `validate_live_query_source_selection` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), [source_selection](../modules/source_selection.md), and 1 more

**Complete modules touched:**

- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [source_selection](../modules/source_selection.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_live_query_source_selection
    participant p1 as load
    participant p2 as _wiki_has_persisted_read_state
    participant p3 as is_dir
    participant p4 as walk
    participant p5 as is_symlink
    participant p6 as Path
    participant p7 as any
    participant p8 as DocumentationQueryError
    participant p9 as validate_persisted_source_selection_identity
    participant p10 as source_selection_identity_from_generation_inputs
    participant p11 as isinstance
    participant p12 as SourceSelectionError
    participant p13 as _validated_identity
    participant p14 as set
    participant p15 as sorted
    participant p16 as _selection_path
    participant p17 as _require_selection_path
    participant p18 as require_repository_relative_path
    p0-->>p1: load
    p0->>p2: _wiki_has_persisted_read_state
    p2-->>p3: is_dir
    p2-->>p4: walk
    p2-->>p5: is_symlink
    p2-->>p6: Path
    p2-->>p7: any
    p0->>p8: DocumentationQueryError
    p0->>p8: DocumentationQueryError
    p0->>p8: DocumentationQueryError
    p0->>p9: validate_persisted_source_selection_identity
    p9->>p10: source_selection_identity_from_generation_inputs
    p10-->>p11: isinstance
    p10-->>p7: any
    p10-->>p11: isinstance
    p10->>p12: SourceSelectionError
    p10->>p13: _validated_identity
    p13-->>p11: isinstance
    p13-->>p7: any
    p13-->>p11: isinstance
    p13->>p12: SourceSelectionError
    p13-->>p14: set
    p13-->>p15: sorted
    p13-->>p15: sorted
    p13->>p12: SourceSelectionError
    p13->>p12: SourceSelectionError
    p13->>p12: SourceSelectionError
    p13->>p16: _selection_path
    p16->>p17: _require_selection_path
    p17->>p18: require_repository_relative_path
```

> Call sequence diagram shows 30 of 88 interactions; 58 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_live_query_source_selection"]
    s2["2. load"]
    s3["3. _wiki_has_persisted_read_state"]
    s4["4. is_dir"]
    s5["5. walk"]
    s6["6. is_symlink"]
    s7["7. Path"]
    s8["8. any"]
    s9["9. DocumentationQueryError"]
    s10["10. DocumentationQueryError"]
    s11["11. DocumentationQueryError"]
    s12["12. validate_persisted_source_selection_identity"]
    s1 -. "SyncManifest.load(wiki_root)" .-> s2
    s1 -->|"_wiki_has_persisted_read_state(wiki_root)"| s3
    s3 -. "wiki_root.is_dir(data not statically known)" .-> s4
    s3 -. "os.walk(wiki_root, followlinks=False)" .-> s5
    s3 -. "(Path(root) / name).is_symlink(data not statically known)" .-> s6
    s3 -. "Path(root)" .-> s7
    s3 -. "any(...)" .-> s8
    s1 -->|"DocumentationQueryError(...)"| s9
    s1 -->|"DocumentationQueryError(...)"| s10
    s1 -->|"DocumentationQueryError(...)"| s11
    s1 -->|"validate_persisted_source_selection_identity(manifest.generation_inputs, live_identity, operation=operation)"| s12
    click s1 "../modules/documentation_query_builder.md"
    click s3 "../modules/documentation_query_builder.md"
    click s9 "../modules/documentation_queries.md"
    click s10 "../modules/documentation_queries.md"
    click s11 "../modules/documentation_queries.md"
    click s12 "../modules/source_selection.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_live_query_source_selection` | `source_root: Path`, `wiki_root: Path`, `live_identity: Mapping[str, object] \| None`, `live_selection_inputs: Mapping[str, object] \| None \| object`, `operation: str`, `allow_empty_wiki: bool` | `SyncManifestError`, `_UNSET_LIVE_SELECTION_INPUTS`, `SourceSelectionError` | - | `none` |
| `load` | - | - | - | - |
| `_wiki_has_persisted_read_state` | `wiki_root: Path` | - | - | `False`, `True`, `True`, `False` |
| `is_dir` | - | - | - | - |
| `walk` | - | - | - | - |
| `is_symlink` | - | - | - | - |
| `Path` | - | - | - | - |
| `any` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `validate_persisted_source_selection_identity` | `persisted_generation_inputs: Mapping[str, object] \| None`, `live_identity: Mapping[str, object] \| None`, `operation: str`, `explicit_path_authorized: bool`, `allow_same_path_update: bool`, `live_selection_inputs: Mapping[str, object] \| None \| object` | `_UNSET_SELECTION_INPUTS`, `SOURCE_SELECTION_PATH` | - | `none`, `none`, `none`, `none`, `none` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_live_query_source_selection | load | 69 | `SyncManifest.load(wiki_root)` |
| validate_live_query_source_selection | _wiki_has_persisted_read_state | 72 | `_wiki_has_persisted_read_state(wiki_root)` |
| _wiki_has_persisted_read_state | is_dir | 37 | `wiki_root.is_dir(data not statically known)` |
| _wiki_has_persisted_read_state | walk | 39 | `os.walk(wiki_root, followlinks=False)` |
| _wiki_has_persisted_read_state | is_symlink | 43 | `(Path(root) / name).is_symlink(data not statically known)` |
| _wiki_has_persisted_read_state | Path | 43 | `Path(root)` |
| _wiki_has_persisted_read_state | any | 45 | `any(...)` |
| validate_live_query_source_selection | DocumentationQueryError | 75 | `DocumentationQueryError(...)` |
| validate_live_query_source_selection | DocumentationQueryError | 81 | `DocumentationQueryError(...)` |
| validate_live_query_source_selection | DocumentationQueryError | 87 | `DocumentationQueryError(...)` |
| validate_live_query_source_selection | validate_persisted_source_selection_identity | 95 | `validate_persisted_source_selection_identity(manifest.generation_inputs, live_identity, operation=operation)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_live_query_source_selection` | `SyncManifest.load` | 69 |
| unresolved_call | `_wiki_has_persisted_read_state` | `wiki_root.is_dir` | 37 |
| external_call | `_wiki_has_persisted_read_state` | `os.walk` | 39 |
| unresolved_call | `_wiki_has_persisted_read_state` | `(Path(root) / name).is_symlink` | 43 |
| unresolved_call | `_wiki_has_persisted_read_state` | `any` | 45 |
| step_limit | `validate_live_query_source_selection` | `first 12 steps` | 0 |
| truncated_flow | `validate_live_query_source_selection` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_live_query_source_selection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
