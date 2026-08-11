# load_snapshot_knowledge_observability

**Entry point:** `load_snapshot_knowledge_observability` (`api`)
**Source:** [knowledge_observability](../modules/knowledge_observability.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [infrastructure_sync](../modules/infrastructure_sync.md), [io](../modules/io.md), and 19 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [paths](../modules/paths.md)
- [section_ownership](../modules/section_ownership.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_snapshot_knowledge_observability
    participant p1 as perf_counter
    participant p2 as Path
    participant p3 as resolve_source_selection
    participant p4 as resolve
    participant p5 as SourceSelectionError
    participant p6 as _override_text
    participant p7 as fspath
    participant p8 as isinstance
    participant p9 as _selection_path
    participant p10 as _require_selection_path
    participant p11 as require_repository_relative_path
    participant p12 as strip
    participant p13 as any
    participant p14 as ord
    participant p15 as startswith
    participant p16 as match
    participant p17 as split
    participant p18 as PurePosixPath
    participant p19 as normpath
    participant p20 as require_portable_relative_path
    p0-->>p1: perf_counter
    p0-->>p2: Path
    p0->>p3: resolve_source_selection
    p3-->>p4: resolve
    p3-->>p2: Path
    p3->>p5: SourceSelectionError
    p3->>p6: _override_text
    p6-->>p7: fspath
    p6->>p5: SourceSelectionError
    p6-->>p8: isinstance
    p6->>p5: SourceSelectionError
    p6->>p9: _selection_path
    p9->>p10: _require_selection_path
    p10->>p11: require_repository_relative_path
    p11-->>p8: isinstance
    p11-->>p12: strip
    p11-->>p13: any
    p11-->>p14: ord
    p11-->>p14: ord
    p11-->>p15: startswith
    p11-->>p15: startswith
    p11-->>p16: match
    p11-->>p17: split
    p11-->>p18: PurePosixPath
    p11-->>p13: any
    p11-->>p19: normpath
    p11->>p20: require_portable_relative_path
    p10->>p5: SourceSelectionError
    p10->>p5: SourceSelectionError
    p10->>p5: SourceSelectionError
```

> Call sequence diagram shows 30 of 1932 interactions; 1902 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_snapshot_knowledge_observability"]
    s2["2. perf_counter"]
    s3["3. Path"]
    s4["4. resolve_source_selection"]
    s5["5. resolve"]
    s6["6. Path"]
    s7["7. SourceSelectionError"]
    s8["8. _override_text"]
    s9["9. fspath"]
    s10["10. SourceSelectionError"]
    s11["11. isinstance"]
    s12["12. SourceSelectionError"]
    s1 -. "time.perf_counter(data not statically known)" .-> s2
    s1 -. "Path(wiki_dir)" .-> s3
    s1 -->|"resolve_source_selection(effective_src_dir, source_selection)"| s4
    s4 -. "Path(root).resolve(data not statically known)" .-> s5
    s4 -. "Path(root)" .-> s6
    s4 -->|"SourceSelectionError('source_root', 'must resolve to a repository path')"| s7
    s4 -->|"_override_text(override)"| s8
    s8 -. "os.fspath(override)" .-> s9
    s8 -->|"SourceSelectionError('source_selection', 'override must be a repository-relative path')"| s10
    s8 -. "isinstance(value, str)" .-> s11
    s8 -->|"SourceSelectionError('source_selection', 'override must be a repository-relative text path')"| s12
    click s1 "../modules/knowledge_observability.md"
    click s4 "../modules/source_selection.md"
    click s7 "../modules/source_selection.md"
    click s8 "../modules/source_selection.md"
    click s10 "../modules/source_selection.md"
    click s12 "../modules/source_selection.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `load_snapshot_knowledge_observability` | `wiki_dir: str \| Path`, `src_dir: str \| Path \| None`, `source_selection: str \| Path \| None` | `SourceSelectionError`, `KnowledgeLoadState`, `KnowledgeMismatchPolicy`, `KnowledgeStateLoadError` | - | `_snapshot_result(...)`, `_snapshot_result(...)`, `_snapshot_result(...)`, `_snapshot_result(...)`, `_snapshot_result(...)` |
| `perf_counter` | - | - | - | - |
| `Path` | - | - | - | - |
| `resolve_source_selection` | `root: str \| Path`, `override: str \| Path \| None` | `SOURCE_SELECTION_PATH` | - | `None`, `None`, `policy` |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `SourceSelectionError` | - | - | - | - |
| `_override_text` | `override: str \| Path` | - | - | `_selection_path(...)` |
| `fspath` | - | - | - | - |
| `SourceSelectionError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `SourceSelectionError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_snapshot_knowledge_observability | perf_counter | 525 | `time.perf_counter(data not statically known)` |
| load_snapshot_knowledge_observability | Path | 526 | `Path(wiki_dir)` |
| load_snapshot_knowledge_observability | resolve_source_selection | 531 | `resolve_source_selection(effective_src_dir, source_selection)` |
| resolve_source_selection | resolve | 606 | `Path(root).resolve(data not statically known)` |
| resolve_source_selection | Path | 606 | `Path(root)` |
| resolve_source_selection | SourceSelectionError | 608 | `SourceSelectionError('source_root', 'must resolve to a repository path')` |
| resolve_source_selection | _override_text | 615 | `_override_text(override)` |
| _override_text | fspath | 583 | `os.fspath(override)` |
| _override_text | SourceSelectionError | 585 | `SourceSelectionError('source_selection', 'override must be a repository-relative path')` |
| _override_text | isinstance | 588 | `isinstance(value, str)` |
| _override_text | SourceSelectionError | 589 | `SourceSelectionError('source_selection', 'override must be a repository-relative text path')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `load_snapshot_knowledge_observability` | `time.perf_counter` | 525 |
| unresolved_call | `resolve_source_selection` | `Path(root).resolve` | 606 |
| external_call | `_override_text` | `os.fspath` | 583 |
| unresolved_call | `_override_text` | `isinstance` | 588 |
| step_limit | `load_snapshot_knowledge_observability` | `first 12 steps` | 0 |
| truncated_flow | `load_snapshot_knowledge_observability` | `depth limit` | 0 |

## Behavior

This flow starts at `load_snapshot_knowledge_observability` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
