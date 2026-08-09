# collect_runtime_repository_evidence

**Entry point:** `collect_runtime_repository_evidence` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [common](../modules/common.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as collect_runtime_repository_evidence
    participant p1 as resolve
    participant p2 as Path
    participant p3 as isinstance
    participant p4 as TypeError
    participant p5 as ValueError
    participant p6 as add
    participant p7 as update
    participant p8 as items
    participant p9 as tuple
    participant p10 as sorted
    participant p11 as str
    participant p12 as set
    participant p13 as enumerate
    participant p14 as joinpath
    participant p15 as relative_to
    participant p16 as is_bundled_helper_implementation_path
    participant p17 as _normalize_path_text
    participant p18 as as_posix
    participant p19 as replace
    p0-->>p1: resolve
    p0-->>p2: Path
    p0-->>p1: resolve
    p0-->>p2: Path
    p0-->>p3: isinstance
    p0-->>p4: TypeError
    p0-->>p1: resolve
    p0-->>p5: ValueError
    p0-->>p6: add
    p0-->>p7: update
    p0-->>p8: items
    p0-->>p9: tuple
    p0-->>p10: sorted
    p0-->>p11: str
    p0-->>p12: set
    p0-->>p12: set
    p0-->>p12: set
    p0-->>p12: set
    p0-->>p2: Path
    p0-->>p13: enumerate
    p0-->>p6: add
    p0-->>p14: joinpath
    p0-->>p6: add
    p0-->>p15: relative_to
    p0-->>p2: Path
    p0->>p16: is_bundled_helper_implementation_path
    p16->>p17: _normalize_path_text
    p17-->>p3: isinstance
    p17-->>p18: as_posix
    p17-->>p19: replace
```

> Call sequence diagram shows 30 of 204 interactions; 174 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. collect_runtime_repository_evidence"]
    s2["2. resolve"]
    s3["3. Path"]
    s4["4. resolve"]
    s5["5. Path"]
    s6["6. isinstance"]
    s7["7. TypeError"]
    s8["8. resolve"]
    s9["9. ValueError"]
    s10["10. add"]
    s11["11. update"]
    s12["12. items"]
    s1 -. "Path(source_root).resolve(data not statically known)" .-> s2
    s1 -. "Path(source_root)" .-> s3
    s1 -. "Path(target_wiki_dir).resolve(data not statically known)" .-> s4
    s1 -. "Path(target_wiki_dir)" .-> s5
    s1 -. "isinstance(source_snapshot, SourceSnapshot)" .-> s6
    s1 -. "TypeError('source_snapshot must be a SourceSnapshot or None')" .-> s7
    s1 -. "source_snapshot.root.resolve(data not statically known)" .-> s8
    s1 -. "ValueError('source_snapshot root must match source_root')" .-> s9
    s1 -. "selected_paths.add(...)" .-> s10
    s1 -. "selected_paths.update(...)" .-> s11
    s1 -. "source_snapshot.captured_input_kinds.items(data not statically known)" .-> s12
    b0["mutation selected_paths.add"]
    s1 -. "mutation selected_paths.add" .-> b0
    b1["mutation selected_paths.update"]
    s1 -. "mutation selected_paths.update" .-> b1
    b2["mutation package_roots.add"]
    s1 -. "mutation package_roots.add" .-> b2
    b3["mutation package_roots.add"]
    s1 -. "mutation package_roots.add" .-> b3
    b4["mutation helper_excludes.add"]
    s1 -. "mutation helper_excludes.add" .-> b4
    click s1 "../modules/knowledge_orchestration.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `collect_runtime_repository_evidence` | `source_root: str \| Path`, `target_wiki_dir: str \| Path`, `source_snapshot: SourceSnapshot \| None` | `SourceSnapshot`, `ConsumedInputKind`, `BUNDLED_HELPER_IMPLEMENTATION_PATHS`, `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `MANIFEST_FILENAME`, `EXCLUDED_DIRS`, `AGENT_WORKTREE_DIR_PATTERNS` | - | `collect_git_repository_evidence(...)` |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `add` | - | - | - | - |
| `update` | - | - | - | - |
| `items` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| collect_runtime_repository_evidence | resolve | 768 | `Path(source_root).resolve(data not statically known)` |
| collect_runtime_repository_evidence | Path | 768 | `Path(source_root)` |
| collect_runtime_repository_evidence | resolve | 769 | `Path(target_wiki_dir).resolve(data not statically known)` |
| collect_runtime_repository_evidence | Path | 769 | `Path(target_wiki_dir)` |
| collect_runtime_repository_evidence | isinstance | 774 | `isinstance(source_snapshot, SourceSnapshot)` |
| collect_runtime_repository_evidence | TypeError | 775 | `TypeError('source_snapshot must be a SourceSnapshot or None')` |
| collect_runtime_repository_evidence | resolve | 776 | `source_snapshot.root.resolve(data not statically known)` |
| collect_runtime_repository_evidence | ValueError | 777 | `ValueError('source_snapshot root must match source_root')` |
| collect_runtime_repository_evidence | add | 785 | `selected_paths.add(...)` |
| collect_runtime_repository_evidence | update | 786 | `selected_paths.update(...)` |
| collect_runtime_repository_evidence | items | 788 | `source_snapshot.captured_input_kinds.items(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `selected_paths.add` | `collect_runtime_repository_evidence` | 785 |
| mutation | `selected_paths.update` | `collect_runtime_repository_evidence` | 786 |
| mutation | `package_roots.add` | `collect_runtime_repository_evidence` | 801 |
| mutation | `package_roots.add` | `collect_runtime_repository_evidence` | 803 |
| mutation | `helper_excludes.add` | `collect_runtime_repository_evidence` | 809 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `collect_runtime_repository_evidence` | `Path(source_root).resolve` | 768 |
| unresolved_call | `collect_runtime_repository_evidence` | `Path(target_wiki_dir).resolve` | 769 |
| unresolved_call | `collect_runtime_repository_evidence` | `isinstance` | 774 |
| unresolved_call | `collect_runtime_repository_evidence` | `TypeError` | 775 |
| unresolved_call | `collect_runtime_repository_evidence` | `source_snapshot.root.resolve` | 776 |
| unresolved_call | `collect_runtime_repository_evidence` | `ValueError` | 777 |
| unresolved_call | `collect_runtime_repository_evidence` | `source_snapshot.captured_input_kinds.items` | 788 |
| step_limit | `collect_runtime_repository_evidence` | `first 12 steps` | 0 |
| truncated_flow | `collect_runtime_repository_evidence` | `depth limit` | 0 |

## Behavior

This flow starts at `collect_runtime_repository_evidence` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
