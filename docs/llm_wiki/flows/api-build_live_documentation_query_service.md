# build_live_documentation_query_service

**Entry point:** `build_live_documentation_query_service` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), and 3 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_live_documentation_query_service
    participant p1 as resolve_source_selection
    participant p2 as resolve
    participant p3 as Path
    participant p4 as SourceSelectionError
    participant p5 as _override_text
    participant p6 as fspath
    participant p7 as isinstance
    participant p8 as _selection_path
    participant p9 as _require_selection_path
    participant p10 as require_repository_relative_path
    participant p11 as strip
    participant p12 as any
    participant p13 as ord
    participant p14 as startswith
    participant p15 as match
    participant p16 as split
    participant p17 as PurePosixPath
    participant p18 as normpath
    participant p19 as require_portable_relative_path
    p0->>p1: resolve_source_selection
    p1-->>p2: resolve
    p1-->>p3: Path
    p1->>p4: SourceSelectionError
    p1->>p5: _override_text
    p5-->>p6: fspath
    p5->>p4: SourceSelectionError
    p5-->>p7: isinstance
    p5->>p4: SourceSelectionError
    p5->>p8: _selection_path
    p8->>p9: _require_selection_path
    p9->>p10: require_repository_relative_path
    p10-->>p7: isinstance
    p10-->>p11: strip
    p10-->>p12: any
    p10-->>p13: ord
    p10-->>p13: ord
    p10-->>p14: startswith
    p10-->>p14: startswith
    p10-->>p15: match
    p10-->>p16: split
    p10-->>p17: PurePosixPath
    p10-->>p12: any
    p10-->>p18: normpath
    p10->>p19: require_portable_relative_path
    p9->>p4: SourceSelectionError
    p9->>p4: SourceSelectionError
    p9->>p4: SourceSelectionError
    p9->>p4: SourceSelectionError
    p9->>p4: SourceSelectionError
```

> Call sequence diagram shows 30 of 384 interactions; 354 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_live_documentation_query_service"]
    s2["2. resolve_source_selection"]
    s3["3. resolve"]
    s4["4. Path"]
    s5["5. SourceSelectionError"]
    s6["6. _override_text"]
    s7["7. fspath"]
    s8["8. SourceSelectionError"]
    s9["9. isinstance"]
    s10["10. SourceSelectionError"]
    s11["11. _selection_path"]
    s12["12. _require_selection_path"]
    s1 -->|"resolve_source_selection(source_root, source_selection)"| s2
    s2 -. "Path(root).resolve(data not statically known)" .-> s3
    s2 -. "Path(root)" .-> s4
    s2 -->|"SourceSelectionError('source_root', 'must resolve to a repository path')"| s5
    s2 -->|"_override_text(override)"| s6
    s6 -. "os.fspath(override)" .-> s7
    s6 -->|"SourceSelectionError('source_selection', 'override must be a repository-relative path')"| s8
    s6 -. "isinstance(value, str)" .-> s9
    s6 -->|"SourceSelectionError('source_selection', 'override must be a repository-relative text path')"| s10
    s6 -->|"_selection_path(value, 'source_selection', reject_glob=True)"| s11
    s11 -->|"_require_selection_path(value, field)"| s12
    click s1 "../modules/documentation_query_builder.md"
    click s2 "../modules/source_selection.md"
    click s5 "../modules/source_selection.md"
    click s6 "../modules/source_selection.md"
    click s8 "../modules/source_selection.md"
    click s10 "../modules/source_selection.md"
    click s11 "../modules/source_selection.md"
    click s12 "../modules/source_selection.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_live_documentation_query_service` | `source_root: Path`, `wiki_root: Path`, `limit: int`, `read_only: bool`, `helper_cache_dir: Path \| None`, `include_plugins: bool`, `source_plugins_only: bool`, `require_live_freshness: bool` | `build_source_snapshot`, `SourceSelectionError`, `SourceSelectionError`, `KnowledgeReadView`, `KnowledgeReadView` | `extract_options[...]`, `extract_options[...]`, `extract_options[...]`, `extract_options[...]`, `extract_options[...]` | `assemble_documentation_query_service(...)` |
| `resolve_source_selection` | `root: str \| Path`, `override: str \| Path \| None` | `SOURCE_SELECTION_PATH` | - | `None`, `None`, `policy` |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `SourceSelectionError` | - | - | - | - |
| `_override_text` | `override: str \| Path` | - | - | `_selection_path(...)` |
| `fspath` | - | - | - | - |
| `SourceSelectionError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `SourceSelectionError` | - | - | - | - |
| `_selection_path` | `value: object`, `field: str`, `reject_glob: bool` | `SourceSelectionError`, `_MAX_PATH_BYTES`, `_MAX_PATH_BYTES`, `_GLOB_CHARACTERS` | - | `path` |
| `_require_selection_path` | `value: object`, `field: str` | - | - | `require_repository_relative_path(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_live_documentation_query_service | resolve_source_selection | 255 | `resolve_source_selection(source_root, source_selection)` |
| resolve_source_selection | resolve | 606 | `Path(root).resolve(data not statically known)` |
| resolve_source_selection | Path | 606 | `Path(root)` |
| resolve_source_selection | SourceSelectionError | 608 | `SourceSelectionError('source_root', 'must resolve to a repository path')` |
| resolve_source_selection | _override_text | 615 | `_override_text(override)` |
| _override_text | fspath | 583 | `os.fspath(override)` |
| _override_text | SourceSelectionError | 585 | `SourceSelectionError('source_selection', 'override must be a repository-relative path')` |
| _override_text | isinstance | 588 | `isinstance(value, str)` |
| _override_text | SourceSelectionError | 589 | `SourceSelectionError('source_selection', 'override must be a repository-relative text path')` |
| _override_text | _selection_path | 592 | `_selection_path(value, 'source_selection', reject_glob=True)` |
| _selection_path | _require_selection_path | 81 | `_require_selection_path(value, field)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `resolve_source_selection` | `Path(root).resolve` | 606 |
| external_call | `_override_text` | `os.fspath` | 583 |
| unresolved_call | `_override_text` | `isinstance` | 588 |
| step_limit | `build_live_documentation_query_service` | `first 12 steps` | 0 |
| truncated_flow | `build_live_documentation_query_service` | `depth limit` | 0 |

## Behavior

This flow starts at `build_live_documentation_query_service` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
