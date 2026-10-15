# is_pristine_wiki_target

**Entry point:** `is_pristine_wiki_target` (`api`)
**Source:** [wiki_lifecycle](../modules/wiki_lifecycle.md)
**Modules touched:** [current_contracts](../modules/current_contracts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [wiki_lifecycle](../modules/wiki_lifecycle.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_pristine_wiki_target
    participant p1 as formatted_json_bytes
    participant p2 as iter_page_kinds
    participant p3 as current_contract_defaults
    participant p4 as formatted_json_text
    participant p5 as Path
    participant p6 as root.is_symlink
    participant p7 as root.exists
    participant p8 as root.is_dir
    participant p9 as sorted
    participant p10 as root.rglob
    participant p11 as path.is_symlink
    participant p12 as path.relative_to(…).as_posix
    participant p13 as path.relative_to
    participant p14 as set
    participant p15 as paths_by_relative.items
    participant p16 as path.is_dir
    participant p17 as path.is_file
    participant p18 as path.stat
    participant p19 as path.read_text
    participant p20 as json.loads
    participant p21 as isinstance
    participant p22 as frozenset
    participant p23 as any
    participant p24 as type
    p0->>p1: formatted_json_bytes
    p0->>p2: iter_page_kinds
    p0->>p3: current_contract_defaults
    p1->>p4: formatted_json_text
    p0-->>p5: Path(wiki_dir)
    p0-->>p6: root.is_symlink
    p0-->>p7: root.exists
    p0-->>p8: root.is_dir
    p0-->>p9: sorted(root.rglob(...))
    p0-->>p10: root.rglob('*')
    p0-->>p11: path.is_symlink
    p0-->>p12: path.relative_to(…).as_posix
    p0-->>p13: path.relative_to(root)
    p0-->>p14: set(paths_by_relative)
    p0-->>p15: paths_by_relative.items
    p0-->>p16: path.is_dir
    p0-->>p17: path.is_file
    p0-->>p18: path.stat
    p0-->>p19: path.read_text(encoding='utf-8')
    p0-->>p19: path.read_text(encoding='utf-8')
    p0-->>p19: path.read_text(encoding='utf-8')
    p0-->>p20: json.loads(raw_config)
    p0-->>p21: isinstance(config, dict)
    p0-->>p22: frozenset(config)
    p0-->>p22: frozenset(legacy_fields)
    p0-->>p22: frozenset(profiled_fields)
    p0-->>p22: frozenset(current_fields)
    p0-->>p23: any(...)
    p0-->>p24: type(config[...])
    p0-->>p21: isinstance(config[...], str)
```

> Call sequence diagram shows 30 of 37 interactions; 7 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 12 of 15 (3 omitted); unresolved 14 of 17 (3 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/wiki_lifecycle.py:is_pristine_wiki_target` | 1 | - | external | 2 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:formatted_json_bytes` | 31 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:formatted_json_text` | 33 | - | external | 1 |
| `src/llm_wiki_cli/services/wiki_lifecycle.py:is_pristine_wiki_target` | 1 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/wiki_lifecycle.py:is_pristine_wiki_target` | 1 | [src/llm_wiki_cli/services/knowledge_evidence.py](../modules/knowledge_evidence.md) | internal | 1 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. is_pristine_wiki_target"]
    s2["2. Path"]
    s3["3. root.is_symlink"]
    s4["4. root.exists"]
    s5["5. root.is_dir"]
    s6["6. iter_page_kinds"]
    s7["7. sorted"]
    s8["8. root.rglob"]
    s9["9. path.is_symlink"]
    s10["10. path.relative_to(…).as_posix"]
    s11["11. path.relative_to"]
    s12["12. set"]
    s1 -. "Path(wiki_dir)" .-> s2
    s1 -. "root.is_symlink(data not statically known)" .-> s3
    s1 -. "root.exists(data not statically known)" .-> s4
    s1 -. "root.is_dir(data not statically known)" .-> s5
    s1 -->|"iter_page_kinds(data not statically known)"| s6
    s1 -. "sorted(root.rglob(...))" .-> s7
    s1 -. "root.rglob('*')" .-> s8
    s1 -. "path.is_symlink(data not statically known)" .-> s9
    s1 -. "path.relative_to(…).as_posix(data not statically known)" .-> s10
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
| `root.is_symlink` | - | - | - | - |
| `root.exists` | - | - | - | - |
| `root.is_dir` | - | - | - | - |
| `iter_page_kinds` | - | `_PAGE_KINDS` | - | `_PAGE_KINDS` |
| `sorted` | - | - | - | - |
| `root.rglob` | - | - | - | - |
| `path.is_symlink` | - | - | - | - |
| `path.relative_to(…).as_posix` | - | - | - | - |
| `path.relative_to` | - | - | - | - |
| `set` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_pristine_wiki_target | Path | 156 | `Path(wiki_dir)` |
| is_pristine_wiki_target | root.is_symlink | 157 | `root.is_symlink(data not statically known)` |
| is_pristine_wiki_target | root.exists | 159 | `root.exists(data not statically known)` |
| is_pristine_wiki_target | root.is_dir | 161 | `root.is_dir(data not statically known)` |
| is_pristine_wiki_target | iter_page_kinds | 165 | `iter_page_kinds(data not statically known)` |
| is_pristine_wiki_target | sorted | 177 | `sorted(root.rglob(...))` |
| is_pristine_wiki_target | root.rglob | 177 | `root.rglob('*')` |
| is_pristine_wiki_target | path.is_symlink | 185 | `path.is_symlink(data not statically known)` |
| is_pristine_wiki_target | path.relative_to(…).as_posix | 188 | `path.relative_to(root).as_posix(data not statically known)` |
| is_pristine_wiki_target | path.relative_to | 188 | `path.relative_to(root)` |
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
| external_call | `is_pristine_wiki_target` | `sorted` | 177 |
| unresolved_call | `is_pristine_wiki_target` | `root.rglob` | 177 |
| unresolved_call | `is_pristine_wiki_target` | `path.is_symlink` | 185 |
| unresolved_call | `is_pristine_wiki_target` | `path.relative_to(root).as_posix` | 188 |
| unresolved_call | `is_pristine_wiki_target` | `path.relative_to` | 188 |
| step_limit | `is_pristine_wiki_target` | `first 12 steps` | 0 |

## Behavior

This flow starts at `is_pristine_wiki_target` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
