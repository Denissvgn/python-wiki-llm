# build_dependency_version_details

**Entry point:** `build_dependency_version_details` (`api`)
**Source:** [dependency_versions](../modules/dependency_versions.md)
**Modules touched:** [config](../modules/config.md), [dependency_versions](../modules/dependency_versions.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_dependency_version_details
    participant p1 as _snapshot_sources
    participant p2 as _walk_sources
    participant p3 as _local_project_identities
    participant p4 as _source_path
    participant p5 as _deduplicate
    participant p6 as is_agent_worktree_path
    participant p7 as _load_toml
    participant p8 as _dependency_source_names
    participant p9 as _scope
    participant p10 as _normal_python
    participant p11 as _normal_rust
    participant p12 as _normalized_rel_parts
    participant p13 as Path (src/llm_wiki_cli/services…ependency_version_details)
    participant p14 as Path(…).resolve
    participant p15 as path.name.startswith
    participant p16 as path.name.endswith
    participant p17 as len (src/llm_wiki_cli/services…ependency_version_details)
    participant p18 as evaluate
    participant p19 as set (src/llm_wiki_cli/services…ependency_version_details)
    participant p20 as reasons.add
    participant p21 as diagnostics.append
    participant p22 as limitations.append
    participant p23 as any
    participant p24 as sorted (src/llm_wiki_cli/services…ependency_version_details)
    p0->>p1: _snapshot_sources
    p0->>p2: _walk_sources
    p0->>p3: _local_project_identities
    p0->>p4: _source_path
    p0->>p5: _deduplicate
    p2->>p6: is_agent_worktree_path
    p3->>p7: _load_toml
    p1->>p8: _dependency_source_names
    p3->>p9: _scope
    p3->>p10: _normal_python
    p3->>p11: _normal_rust
    p6->>p12: _normalized_rel_parts
    p0-->>p13: Path (src/llm_wiki_cli/services…ependency_version_details)(project_root)
    p0-->>p14: Path(…).resolve
    p0-->>p15: path.name.startswith('requirements')
    p0-->>p16: path.name.endswith('.txt')
    p0-->>p17: len (src/llm_wiki_cli/services…ependency_version_details)(records)
    p0-->>p18: evaluate(path, omission_reasons)
    p0-->>p19: set (src/llm_wiki_cli/services…ependency_version_details)(omission_reasons)
    p0-->>p17: len (src/llm_wiki_cli/services…ependency_version_details)(omission_reasons)
    p0-->>p20: reasons.add('unsupported-or-malformed-records')
    p0-->>p21: diagnostics.append({...})
    p0-->>p17: len (src/llm_wiki_cli/services…ependency_version_details)(records)
    p0-->>p22: limitations.append('malformed-or-unsupported-version-records')
    p0-->>p23: any(...)
    p0-->>p23: any(...)
    p0-->>p22: limitations.append('unknown-selection-without-lock-evidence')
    p0-->>p17: len (src/llm_wiki_cli/services…ependency_version_details)(normalized)
    p0-->>p24: sorted (src/llm_wiki_cli/services…ependency_version_details)(limitations)
    p0-->>p24: sorted (src/llm_wiki_cli/services…ependency_version_details)(diagnostics, key=...)
```

> Call sequence diagram shows 30 of 119 interactions; 89 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 10 of 42 (32 omitted); unresolved 8 of 58 (50 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/dependency_versions.py:_snapshot_sources` | 4 | - | external | 4 |
| `src/llm_wiki_cli/services/dependency_versions.py:_snapshot_sources` | 4 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/dependency_versions.py:_dependency_source_names` | 7 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/dependency_versions.py:_snapshot_sources` | 4 | [src/llm_wiki_cli/services/dependency_versions.py](../modules/dependency_versions.md) | internal | 2 |
| `src/llm_wiki_cli/services/dependency_versions.py:_source_path` | 12 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/dependency_versions.py:_walk_sources` | 25 | - | external | 3 |
| `src/llm_wiki_cli/config.py:_normalized_rel_parts` | 29 | - | external | 3 |
| `src/llm_wiki_cli/config.py:_normalized_rel_parts` | 29 | - | unresolved | 4 |
> Omission summary shows 8 of 23 groups; 15 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 20; effect analysis evaluated: 20, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. build_dependency_version_details"]
    s2["2. Path(…).resolve"]
    s3["3. Path (src/llm_wiki_cli/services…ependency_version_details)"]
    s4["4. _snapshot_sources"]
    s5["5. set (src/llm_wiki_cli/services…ions.py:_snapshot_sources)"]
    s6["6. marker.abs_path.relative_to"]
    s7["7. _dependency_source_names"]
    s8["8. value.startswith"]
    s9["9. value.endswith"]
    s10["10. paths.add"]
    s11["11. sorted (src/llm_wiki_cli/services…ions.py:_snapshot_sources)"]
    s12["12. _source_path"]
    s1 -. "Path(…).resolve(data not statically known)" .-> s2
    s1 -. "Path (src/llm_wiki_cli/services…ependency_version_details)(project_root)" .-> s3
    s1 -->|"_snapshot_sources(root, source_snapshot)"| s4
    s4 -. "set (src/llm_wiki_cli/services…ions.py:_snapshot_sources)(data not statically known)" .-> s5
    s4 -. "marker.abs_path.relative_to(root)" .-> s6
    s4 -->|"_dependency_source_names([...])"| s7
    s7 -. "value.startswith('requirements')" .-> s8
    s7 -. "value.endswith('.txt')" .-> s9
    s4 -. "paths.add(marker.abs_path)" .-> s10
    s4 -. "sorted (src/llm_wiki_cli/services…ions.py:_snapshot_sources)(paths, key=...)" .-> s11
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
| `Path(…).resolve` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…ependency_version_details)` | - | - | - | - |
| `_snapshot_sources` | `root: Path`, `snapshot: SourceSnapshot` | - | - | `sorted(...)`, `sorted(...)` |
| `set (src/llm_wiki_cli/services…ions.py:_snapshot_sources)` | - | - | - | - |
| `marker.abs_path.relative_to` | - | - | - | - |
| `_dependency_source_names` | `files: Iterable[str]` | `_SOURCE_NAMES` | - | `...` |
| `value.startswith` | - | - | - | - |
| `value.endswith` | - | - | - | - |
| `paths.add` | - | - | - | - |
| `sorted (src/llm_wiki_cli/services…ions.py:_snapshot_sources)` | - | - | - | - |
| `_source_path` | `root: Path`, `path: Path` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_dependency_version_details | Path(…).resolve | 1437 | `Path(project_root).resolve(data not statically known)` |
| build_dependency_version_details | Path (src/llm_wiki_cli/services…ependency_version_details) | 1437 | `Path(project_root)` |
| build_dependency_version_details | _snapshot_sources | 1439 | `_snapshot_sources(root, source_snapshot)` |
| _snapshot_sources | set (src/llm_wiki_cli/services…ions.py:_snapshot_sources) | 161 | `set(data not statically known)` |
| _snapshot_sources | marker.abs_path.relative_to | 164 | `marker.abs_path.relative_to(root)` |
| _snapshot_sources | _dependency_source_names | 167 | `_dependency_source_names([...])` |
| _dependency_source_names | value.startswith | 156 | `value.startswith('requirements')` |
| _dependency_source_names | value.endswith | 156 | `value.endswith('.txt')` |
| _snapshot_sources | paths.add | 170 | `paths.add(marker.abs_path)` |
| _snapshot_sources | sorted (src/llm_wiki_cli/services…ions.py:_snapshot_sources) | 173 | `sorted(paths, key=...)` |
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
| external_call | `_snapshot_sources` | `sorted` | 173 |
| step_limit | `build_dependency_version_details` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_dependency_version_details` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
