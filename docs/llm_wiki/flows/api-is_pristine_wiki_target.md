# is_pristine_wiki_target

**Entry point:** `is_pristine_wiki_target` (`api`)
**Source:** [wiki_lifecycle](../modules/wiki_lifecycle.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [wiki_lifecycle](../modules/wiki_lifecycle.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_pristine_wiki_target
    participant p1 as Path
    participant p2 as is_symlink
    participant p3 as exists
    participant p4 as is_dir
    participant p5 as iter_page_kinds
    participant p6 as sorted
    participant p7 as rglob
    participant p8 as as_posix
    participant p9 as relative_to
    participant p10 as set
    participant p11 as items
    participant p12 as is_file
    participant p13 as stat
    participant p14 as read_text
    participant p15 as loads
    participant p16 as isinstance
    participant p17 as frozenset
    participant p18 as any
    participant p19 as type
    participant p20 as encode
    participant p21 as dumps
    participant p22 as formatted_json_bytes
    p0-->>p1: Path
    p0-->>p2: is_symlink
    p0-->>p3: exists
    p0-->>p4: is_dir
    p0->>p5: iter_page_kinds
    p0-->>p6: sorted
    p0-->>p7: rglob
    p0-->>p2: is_symlink
    p0-->>p8: as_posix
    p0-->>p9: relative_to
    p0-->>p10: set
    p0-->>p11: items
    p0-->>p4: is_dir
    p0-->>p12: is_file
    p0-->>p13: stat
    p0-->>p14: read_text
    p0-->>p14: read_text
    p0-->>p14: read_text
    p0-->>p15: loads
    p0-->>p16: isinstance
    p0-->>p17: frozenset
    p0-->>p17: frozenset
    p0-->>p17: frozenset
    p0-->>p18: any
    p0-->>p19: type
    p0-->>p10: set
    p0-->>p20: encode
    p0-->>p21: dumps
    p0->>p22: formatted_json_bytes
    p22-->>p20: encode
```

> Call sequence diagram shows 30 of 33 interactions; 3 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. is_pristine_wiki_target"]
    s2["2. Path"]
    s3["3. is_symlink"]
    s4["4. exists"]
    s5["5. is_dir"]
    s6["6. iter_page_kinds"]
    s7["7. sorted"]
    s8["8. rglob"]
    s9["9. is_symlink"]
    s10["10. as_posix"]
    s11["11. relative_to"]
    s12["12. set"]
    s1 -. "Path(wiki_dir)" .-> s2
    s1 -. "root.is_symlink(data not statically known)" .-> s3
    s1 -. "root.exists(data not statically known)" .-> s4
    s1 -. "root.is_dir(data not statically known)" .-> s5
    s1 -->|"iter_page_kinds(data not statically known)"| s6
    s1 -. "sorted(root.rglob(...))" .-> s7
    s1 -. "root.rglob('*')" .-> s8
    s1 -. "path.is_symlink(data not statically known)" .-> s9
    s1 -. "path.relative_to(root).as_posix(data not statically known)" .-> s10
    s1 -. "path.relative_to(root)" .-> s11
    s1 -. "set(paths_by_relative)" .-> s12
    b0["filesystem_read path.read_text"]
    s1 -. "filesystem_read path.read_text" .-> b0
    b1["filesystem_read path.read_text"]
    s1 -. "filesystem_read path.read_text" .-> b1
    b2["filesystem_read path.read_text"]
    s1 -. "filesystem_read path.read_text" .-> b2
    click s1 "../modules/wiki_lifecycle.md"
    click s6 "../modules/wiki_surface.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_pristine_wiki_target` | `wiki_dir: Union[str, Path]` | `INITIAL_WIKI_INDEX_MARKDOWN`, `INITIAL_WIKI_LOG_MARKDOWN`, `AGENT_CHOICES`, `SchemaRenderProfile`, `SCHEMA_BLOCK_VERSION`, `RenderReason` | `paths_by_relative[...]` | `False`, `True`, `False`, `False`, `True`, `False`, `False`, `False` |
| `Path` | - | - | - | - |
| `is_symlink` | - | - | - | - |
| `exists` | - | - | - | - |
| `is_dir` | - | - | - | - |
| `iter_page_kinds` | - | `_PAGE_KINDS` | - | `_PAGE_KINDS` |
| `sorted` | - | - | - | - |
| `rglob` | - | - | - | - |
| `is_symlink` | - | - | - | - |
| `as_posix` | - | - | - | - |
| `relative_to` | - | - | - | - |
| `set` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_pristine_wiki_target | Path | 156 | `Path(wiki_dir)` |
| is_pristine_wiki_target | is_symlink | 157 | `root.is_symlink(data not statically known)` |
| is_pristine_wiki_target | exists | 159 | `root.exists(data not statically known)` |
| is_pristine_wiki_target | is_dir | 161 | `root.is_dir(data not statically known)` |
| is_pristine_wiki_target | iter_page_kinds | 165 | `iter_page_kinds(data not statically known)` |
| is_pristine_wiki_target | sorted | 177 | `sorted(root.rglob(...))` |
| is_pristine_wiki_target | rglob | 177 | `root.rglob('*')` |
| is_pristine_wiki_target | is_symlink | 185 | `path.is_symlink(data not statically known)` |
| is_pristine_wiki_target | as_posix | 188 | `path.relative_to(root).as_posix(data not statically known)` |
| is_pristine_wiki_target | relative_to | 188 | `path.relative_to(root)` |
| is_pristine_wiki_target | set | 193 | `set(paths_by_relative)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `path.read_text` | `is_pristine_wiki_target` | 212 |
| filesystem_read | `path.read_text` | `is_pristine_wiki_target` | 215 |
| filesystem_read | `path.read_text` | `is_pristine_wiki_target` | 218 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `is_pristine_wiki_target` | `root.is_symlink` | 157 |
| unresolved_call | `is_pristine_wiki_target` | `root.exists` | 159 |
| unresolved_call | `is_pristine_wiki_target` | `root.is_dir` | 161 |
| unresolved_call | `is_pristine_wiki_target` | `sorted` | 177 |
| unresolved_call | `is_pristine_wiki_target` | `root.rglob` | 177 |
| unresolved_call | `is_pristine_wiki_target` | `path.is_symlink` | 185 |
| unresolved_call | `is_pristine_wiki_target` | `path.relative_to(root).as_posix` | 188 |
| unresolved_call | `is_pristine_wiki_target` | `path.relative_to` | 188 |
| step_limit | `is_pristine_wiki_target` | `first 12 steps` | 0 |

## Behavior

This flow starts at `is_pristine_wiki_target` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
