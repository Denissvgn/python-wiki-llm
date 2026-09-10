# classify_wiki_lifecycle

**Entry point:** `classify_wiki_lifecycle` (`api`)
**Source:** [wiki_lifecycle](../modules/wiki_lifecycle.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [wiki_lifecycle](../modules/wiki_lifecycle.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as classify_wiki_lifecycle
    participant p1 as Path (src/llm_wiki_cli/services…py:classify_wiki_lifecycle)
    participant p2 as manifest.exists
    participant p3 as manifest.is_symlink
    participant p4 as is_pristine_wiki_target
    participant p5 as Path (src/llm_wiki_cli/services…py:is_pristine_wiki_target)
    participant p6 as root.is_symlink
    participant p7 as root.exists
    participant p8 as root.is_dir (src/llm_wiki_cli/services…py:is_pristine_wiki_target)
    participant p9 as iter_page_kinds
    participant p10 as sorted
    participant p11 as root.rglob
    participant p12 as path.is_symlink
    participant p13 as path.relative_to(…).as_posix
    participant p14 as path.relative_to
    participant p15 as set
    participant p16 as paths_by_relative.items
    participant p17 as path.is_dir
    participant p18 as path.is_file
    participant p19 as path.stat
    participant p20 as path.read_text
    participant p21 as json.loads
    participant p22 as isinstance
    participant p23 as frozenset
    participant p24 as any
    participant p25 as type
    p0-->>p1: Path (src/llm_wiki_cli/services…py:classify_wiki_lifecycle)
    p0-->>p2: manifest.exists
    p0-->>p3: manifest.is_symlink
    p0->>p4: is_pristine_wiki_target
    p4-->>p5: Path (src/llm_wiki_cli/services…py:is_pristine_wiki_target)
    p4-->>p6: root.is_symlink
    p4-->>p7: root.exists
    p4-->>p8: root.is_dir (src/llm_wiki_cli/services…py:is_pristine_wiki_target)
    p4->>p9: iter_page_kinds
    p4-->>p10: sorted
    p4-->>p11: root.rglob
    p4-->>p12: path.is_symlink
    p4-->>p13: path.relative_to(…).as_posix
    p4-->>p14: path.relative_to
    p4-->>p15: set
    p4-->>p16: paths_by_relative.items
    p4-->>p17: path.is_dir
    p4-->>p18: path.is_file
    p4-->>p19: path.stat
    p4-->>p20: path.read_text
    p4-->>p20: path.read_text
    p4-->>p20: path.read_text
    p4-->>p21: json.loads
    p4-->>p22: isinstance
    p4-->>p23: frozenset
    p4-->>p23: frozenset
    p4-->>p23: frozenset
    p4-->>p24: any
    p4-->>p25: type
    p4-->>p15: set
```

> Call sequence diagram shows 30 of 40 interactions; 10 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. classify_wiki_lifecycle"]
    s2["2. Path (src/llm_wiki_cli/services…py:classify_wiki_lifecycle)"]
    s3["3. manifest.exists"]
    s4["4. manifest.is_symlink"]
    s5["5. is_pristine_wiki_target"]
    s6["6. Path (src/llm_wiki_cli/services…py:is_pristine_wiki_target)"]
    s7["7. root.is_symlink"]
    s8["8. root.exists"]
    s9["9. root.is_dir (src/llm_wiki_cli/services…py:is_pristine_wiki_target)"]
    s10["10. iter_page_kinds"]
    s11["11. sorted"]
    s12["12. root.rglob"]
    s1 -. "Path (src/llm_wiki_cli/services…py:classify_wiki_lifecycle)(wiki_dir)" .-> s2
    s1 -. "manifest.exists(data not statically known)" .-> s3
    s1 -. "manifest.is_symlink(data not statically known)" .-> s4
    s1 -->|"is_pristine_wiki_target(root)"| s5
    s5 -. "Path (src/llm_wiki_cli/services…py:is_pristine_wiki_target)(wiki_dir)" .-> s6
    s5 -. "root.is_symlink(data not statically known)" .-> s7
    s5 -. "root.exists(data not statically known)" .-> s8
    s5 -. "root.is_dir (src/llm_wiki_cli/services…py:is_pristine_wiki_target)(data not statically known)" .-> s9
    s5 -->|"iter_page_kinds(data not statically known)"| s10
    s5 -. "sorted(root.rglob(...))" .-> s11
    s5 -. "root.rglob('*')" .-> s12
    b0["filesystem_read path.read_text"]
    s5 -. "filesystem_read path.read_text" .-> b0
    b1["filesystem_read path.read_text"]
    s5 -. "filesystem_read path.read_text" .-> b1
    b2["filesystem_read path.read_text"]
    s5 -. "filesystem_read path.read_text" .-> b2
    click s1 "../modules/wiki_lifecycle.md"
    click s5 "../modules/wiki_lifecycle.md"
    click s10 "../modules/wiki_surface.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `classify_wiki_lifecycle` | `wiki_dir: Union[str, Path]` | `MANIFEST_FILENAME`, `WikiLifecycleState`, `WikiLifecycleState`, `WikiLifecycleState`, `WikiLifecycleState` | - | `WikiLifecycleState.MANAGED`, `WikiLifecycleState.FIRST_USE`, `WikiLifecycleState.SYNC_SEEDABLE`, `WikiLifecycleState.MIGRATION_REQUIRED` |
| `Path (src/llm_wiki_cli/services…py:classify_wiki_lifecycle)` | - | - | - | - |
| `manifest.exists` | - | - | - | - |
| `manifest.is_symlink` | - | - | - | - |
| `is_pristine_wiki_target` | `wiki_dir: Union[str, Path]` | `INITIAL_WIKI_INDEX_MARKDOWN`, `INITIAL_WIKI_LOG_MARKDOWN`, `AGENT_CHOICES`, `SchemaRenderProfile`, `SCHEMA_BLOCK_VERSION`, `RenderReason` | `paths_by_relative[...]` | `False`, `True`, `False`, `False`, `True`, `False`, `False`, `False` |
| `Path (src/llm_wiki_cli/services…py:is_pristine_wiki_target)` | - | - | - | - |
| `root.is_symlink` | - | - | - | - |
| `root.exists` | - | - | - | - |
| `root.is_dir (src/llm_wiki_cli/services…py:is_pristine_wiki_target)` | - | - | - | - |
| `iter_page_kinds` | - | `_PAGE_KINDS` | - | `_PAGE_KINDS` |
| `sorted` | - | - | - | - |
| `root.rglob` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| classify_wiki_lifecycle | Path (src/llm_wiki_cli/services…py:classify_wiki_lifecycle) | 276 | `Path(wiki_dir)` |
| classify_wiki_lifecycle | manifest.exists | 278 | `manifest.exists(data not statically known)` |
| classify_wiki_lifecycle | manifest.is_symlink | 278 | `manifest.is_symlink(data not statically known)` |
| classify_wiki_lifecycle | is_pristine_wiki_target | 280 | `is_pristine_wiki_target(root)` |
| is_pristine_wiki_target | Path (src/llm_wiki_cli/services…py:is_pristine_wiki_target) | 156 | `Path(wiki_dir)` |
| is_pristine_wiki_target | root.is_symlink | 157 | `root.is_symlink(data not statically known)` |
| is_pristine_wiki_target | root.exists | 159 | `root.exists(data not statically known)` |
| is_pristine_wiki_target | root.is_dir (src/llm_wiki_cli/services…py:is_pristine_wiki_target) | 161 | `root.is_dir(data not statically known)` |
| is_pristine_wiki_target | iter_page_kinds | 165 | `iter_page_kinds(data not statically known)` |
| is_pristine_wiki_target | sorted | 177 | `sorted(root.rglob(...))` |
| is_pristine_wiki_target | root.rglob | 177 | `root.rglob('*')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `path.read_text` | `is_pristine_wiki_target` | 212 |
| filesystem_read | `path.read_text` | `is_pristine_wiki_target` | 215 |
| filesystem_read | `path.read_text` | `is_pristine_wiki_target` | 218 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `classify_wiki_lifecycle` | `manifest.exists` | 278 |
| unresolved_call | `classify_wiki_lifecycle` | `manifest.is_symlink` | 278 |
| unresolved_call | `is_pristine_wiki_target` | `root.is_symlink` | 157 |
| unresolved_call | `is_pristine_wiki_target` | `root.exists` | 159 |
| unresolved_call | `is_pristine_wiki_target` | `root.is_dir` | 161 |
| external_call | `is_pristine_wiki_target` | `sorted` | 177 |
| unresolved_call | `is_pristine_wiki_target` | `root.rglob` | 177 |
| step_limit | `classify_wiki_lifecycle` | `first 12 steps` | 0 |

## Behavior

This flow starts at `classify_wiki_lifecycle` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
