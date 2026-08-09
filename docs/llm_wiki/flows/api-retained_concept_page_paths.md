# retained_concept_page_paths

**Entry point:** `retained_concept_page_paths` (`api`)
**Source:** [sync_manifest](../modules/sync_manifest.md)
**Modules touched:** [sync_manifest](../modules/sync_manifest.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as retained_concept_page_paths
    participant p1 as is_dir
    participant p2 as extend
    participant p3 as glob
    participant p4 as is_file
    participant p5 as tuple
    participant p6 as sorted
    p0-->>p1: is_dir
    p0-->>p2: extend
    p0-->>p3: glob
    p0-->>p4: is_file
    p0-->>p5: tuple
    p0-->>p6: sorted
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. retained_concept_page_paths"]
    s2["2. is_dir"]
    s3["3. extend"]
    s4["4. glob"]
    s5["5. is_file"]
    s6["6. tuple"]
    s7["7. sorted"]
    s1 -. "root.is_dir(data not statically known)" .-> s2
    s1 -. "paths.extend(...)" .-> s3
    s1 -. "root.glob('*.md')" .-> s4
    s1 -. "path.is_file(data not statically known)" .-> s5
    s1 -. "tuple(sorted(...))" .-> s6
    s1 -. "sorted(paths)" .-> s7
    b0["mutation paths.extend"]
    s1 -. "mutation paths.extend" .-> b0
    click s1 "../modules/sync_manifest.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `retained_concept_page_paths` | `wiki_dir: Path` | - | - | `tuple(...)` |
| `is_dir` | - | - | - | - |
| `extend` | - | - | - | - |
| `glob` | - | - | - | - |
| `is_file` | - | - | - | - |
| `tuple` | - | - | - | - |
| `sorted` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| retained_concept_page_paths | is_dir | 706 | `root.is_dir(data not statically known)` |
| retained_concept_page_paths | extend | 708 | `paths.extend(...)` |
| retained_concept_page_paths | glob | 709 | `root.glob('*.md')` |
| retained_concept_page_paths | is_file | 709 | `path.is_file(data not statically known)` |
| retained_concept_page_paths | tuple | 711 | `tuple(sorted(...))` |
| retained_concept_page_paths | sorted | 711 | `sorted(paths)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `paths.extend` | `retained_concept_page_paths` | 708 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `retained_concept_page_paths` | `root.is_dir` | 706 |
| unresolved_call | `retained_concept_page_paths` | `root.glob` | 709 |
| unresolved_call | `retained_concept_page_paths` | `path.is_file` | 709 |
| unresolved_call | `retained_concept_page_paths` | `sorted` | 711 |

## Behavior

This flow starts at `retained_concept_page_paths` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
