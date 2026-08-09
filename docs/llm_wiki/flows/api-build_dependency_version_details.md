# build_dependency_version_details

**Entry point:** `build_dependency_version_details` (`api`)
**Source:** [dependency_versions](../modules/dependency_versions.md)
**Modules touched:** [config](../modules/config.md), [dependency_versions](../modules/dependency_versions.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_dependency_version_details
    participant p1 as resolve
    participant p2 as Path
    participant p3 as _snapshot_sources
    participant p4 as set
    participant p5 as relative_to
    participant p6 as _dependency_source_names
    participant p7 as startswith
    participant p8 as endswith
    participant p9 as add
    participant p10 as sorted
    participant p11 as _source_path
    participant p12 as as_posix
    participant p13 as get
    participant p14 as is_file
    participant p15 as list
    participant p16 as _walk_sources
    participant p17 as walk
    participant p18 as is_agent_worktree_path
    participant p19 as _normalized_rel_parts
    participant p20 as isinstance
    p0-->>p1: resolve
    p0-->>p2: Path
    p0->>p3: _snapshot_sources
    p3-->>p4: set
    p3-->>p5: relative_to
    p3->>p6: _dependency_source_names
    p6-->>p7: startswith
    p6-->>p8: endswith
    p3-->>p9: add
    p3-->>p10: sorted
    p3->>p11: _source_path
    p11-->>p12: as_posix
    p11-->>p5: relative_to
    p3-->>p13: get
    p3-->>p9: add
    p3-->>p14: is_file
    p3-->>p9: add
    p3-->>p15: list
    p3-->>p7: startswith
    p3-->>p14: is_file
    p3-->>p9: add
    p3-->>p10: sorted
    p3->>p11: _source_path
    p0->>p16: _walk_sources
    p16-->>p17: walk
    p16-->>p2: Path
    p16->>p18: is_agent_worktree_path
    p18->>p19: _normalized_rel_parts
    p19-->>p20: isinstance
    p19-->>p12: as_posix
```

> Call sequence diagram shows 30 of 119 interactions; 89 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_dependency_version_details"]
    s2["2. resolve"]
    s3["3. Path"]
    s4["4. _snapshot_sources"]
    s5["5. set"]
    s6["6. relative_to"]
    s7["7. _dependency_source_names"]
    s8["8. startswith"]
    s9["9. endswith"]
    s10["10. add"]
    s11["11. sorted"]
    s12["12. _source_path"]
    s1 -. "Path(project_root).resolve(data not statically known)" .-> s2
    s1 -. "Path(project_root)" .-> s3
    s1 -->|"_snapshot_sources(root, source_snapshot)"| s4
    s4 -. "set(data not statically known)" .-> s5
    s4 -. "marker.abs_path.relative_to(root)" .-> s6
    s4 -->|"_dependency_source_names([...])"| s7
    s7 -. "value.startswith('requirements')" .-> s8
    s7 -. "value.endswith('.txt')" .-> s9
    s4 -. "paths.add(marker.abs_path)" .-> s10
    s4 -. "sorted(paths, key=...)" .-> s11
    s4 -->|"_source_path(root, path)"| s12
    b0["mutation reasons.add"]
    s1 -. "mutation reasons.add" .-> b0
    b1["mutation diagnostics.append"]
    s1 -. "mutation diagnostics.append" .-> b1
    b2["mutation limitations.append"]
    s1 -. "mutation limitations.append" .-> b2
    b3["mutation limitations.append"]
    s1 -. "mutation limitations.append" .-> b3
    b4["mutation paths.add"]
    s4 -. "mutation paths.add" .-> b4
    b5["mutation candidate_directories.add"]
    s4 -. "mutation candidate_directories.add" .-> b5
    b6["mutation paths.add"]
    s4 -. "mutation paths.add" .-> b6
    b7["mutation paths.add"]
    s4 -. "mutation paths.add" .-> b7
    click s1 "../modules/dependency_versions.md"
    click s4 "../modules/dependency_versions.md"
    click s7 "../modules/dependency_versions.md"
    click s12 "../modules/dependency_versions.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
    class b7 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_dependency_version_details` | `project_root: str \| Path`, `source_snapshot: SourceSnapshot \| None` | `DEPENDENCY_VERSION_DETAILS_SCHEMA_VERSION` | - | `{...}` |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `_snapshot_sources` | `root: Path`, `snapshot: SourceSnapshot` | - | - | `sorted(...)`, `sorted(...)` |
| `set` | - | - | - | - |
| `relative_to` | - | - | - | - |
| `_dependency_source_names` | `files: Iterable[str]` | `_SOURCE_NAMES` | - | `...` |
| `startswith` | - | - | - | - |
| `endswith` | - | - | - | - |
| `add` | - | - | - | - |
| `sorted` | - | - | - | - |
| `_source_path` | `root: Path`, `path: Path` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_dependency_version_details | resolve | 1437 | `Path(project_root).resolve(data not statically known)` |
| build_dependency_version_details | Path | 1437 | `Path(project_root)` |
| build_dependency_version_details | _snapshot_sources | 1439 | `_snapshot_sources(root, source_snapshot)` |
| _snapshot_sources | set | 161 | `set(data not statically known)` |
| _snapshot_sources | relative_to | 164 | `marker.abs_path.relative_to(root)` |
| _snapshot_sources | _dependency_source_names | 167 | `_dependency_source_names([...])` |
| _dependency_source_names | startswith | 156 | `value.startswith('requirements')` |
| _dependency_source_names | endswith | 156 | `value.endswith('.txt')` |
| _snapshot_sources | add | 170 | `paths.add(marker.abs_path)` |
| _snapshot_sources | sorted | 173 | `sorted(paths, key=...)` |
| _snapshot_sources | _source_path | 173 | `_source_path(root, path)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `reasons.add` | `build_dependency_version_details` | 1521 |
| mutation | `diagnostics.append` | `build_dependency_version_details` | 1523 |
| mutation | `limitations.append` | `build_dependency_version_details` | 1541 |
| mutation | `limitations.append` | `build_dependency_version_details` | 1553 |
| mutation | `paths.add` | `_snapshot_sources` | 170 |
| mutation | `candidate_directories.add` | `_snapshot_sources` | 180 |
| mutation | `paths.add` | `_snapshot_sources` | 187 |
| mutation | `paths.add` | `_snapshot_sources` | 206 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_dependency_version_details` | `Path(project_root).resolve` | 1437 |
| unresolved_call | `_snapshot_sources` | `marker.abs_path.relative_to` | 164 |
| unresolved_call | `_dependency_source_names` | `value.startswith` | 156 |
| unresolved_call | `_dependency_source_names` | `value.endswith` | 156 |
| unresolved_call | `_snapshot_sources` | `sorted` | 173 |
| step_limit | `build_dependency_version_details` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_dependency_version_details` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
