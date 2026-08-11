# compare_source_plugin_tree_baseline

**Entry point:** `compare_source_plugin_tree_baseline` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_source_plugin_tree_baseline
    participant p1 as source_plugin_tree_baseline
    participant p2 as Path
    participant p3 as lexists
    participant p4 as TreeBaseline
    participant p5 as _hash_labeled_hashes
    participant p6 as sha256
    participant p7 as sorted
    participant p8 as items
    participant p9 as update
    participant p10 as encode
    participant p11 as replace
    participant p12 as hexdigest
    participant p13 as _lstat
    participant p14 as lstat
    participant p15 as DocumentationPolicyError
    participant p16 as _assert_safe_directory
    participant p17 as S_ISLNK
    participant p18 as _is_windows_reparse_point
    participant p19 as int
    participant p20 as getattr
    participant p21 as bool
    participant p22 as S_ISDIR
    p0->>p1: source_plugin_tree_baseline
    p1-->>p2: Path
    p1-->>p3: lexists
    p1->>p4: TreeBaseline
    p1->>p5: _hash_labeled_hashes
    p5-->>p6: sha256
    p5-->>p7: sorted
    p5-->>p8: items
    p5-->>p9: update
    p5-->>p10: encode
    p5-->>p11: replace
    p5-->>p9: update
    p5-->>p9: update
    p5-->>p10: encode
    p5-->>p9: update
    p5-->>p12: hexdigest
    p1->>p13: _lstat
    p13-->>p14: lstat
    p13->>p15: DocumentationPolicyError
    p1->>p16: _assert_safe_directory
    p16-->>p17: S_ISLNK
    p16->>p15: DocumentationPolicyError
    p16->>p18: _is_windows_reparse_point
    p18-->>p19: int
    p18-->>p20: getattr
    p18-->>p19: int
    p18-->>p20: getattr
    p18-->>p21: bool
    p16->>p15: DocumentationPolicyError
    p16-->>p22: S_ISDIR
```

> Call sequence diagram shows 30 of 273 interactions; 243 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. compare_source_plugin_tree_baseline"]
    s2["2. source_plugin_tree_baseline"]
    s3["3. Path"]
    s4["4. lexists"]
    s5["5. TreeBaseline"]
    s6["6. _hash_labeled_hashes"]
    s7["7. sha256"]
    s8["8. sorted"]
    s9["9. items"]
    s10["10. update"]
    s11["11. encode"]
    s12["12. replace"]
    s1 -->|"source_plugin_tree_baseline(root)"| s2
    s2 -. "Path(root)" .-> s3
    s2 -. "os.path.lexists(plugin_home)" .-> s4
    s2 -->|"TreeBaseline(root_display='source_plugins', tree_hash=_hash_labeled_hashes(...), file_hashes=file_hashes)"| s5
    s2 -->|"_hash_labeled_hashes(file_hashes)"| s6
    s6 -. "hashlib.sha256(data not statically known)" .-> s7
    s6 -. "sorted(file_hashes.items(...))" .-> s8
    s6 -. "file_hashes.items(data not statically known)" .-> s9
    s6 -. "digest.update(...)" .-> s10
    s6 -. "path.replace('\\', '/').encode('utf-8')" .-> s11
    s6 -. "path.replace('\\', '/')" .-> s12
    b0["mutation file_hashes.update"]
    s2 -. "mutation file_hashes.update" .-> b0
    b1["mutation digest.update"]
    s6 -. "mutation digest.update" .-> b1
    b2["mutation digest.update"]
    s6 -. "mutation digest.update" .-> b2
    b3["mutation digest.update"]
    s6 -. "mutation digest.update" .-> b3
    b4["mutation digest.update"]
    s6 -. "mutation digest.update" .-> b4
    click s1 "../modules/documentation_policy.md"
    click s2 "../modules/documentation_policy.md"
    click s5 "../modules/documentation_policy.md"
    click s6 "../modules/documentation_policy.md"
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
| `compare_source_plugin_tree_baseline` | `baseline: TreeBaseline`, `root: str \| Path` | - | - | `IntegrityDifference(...)` |
| `source_plugin_tree_baseline` | `root: str \| Path` | `DEFAULT_MAX_BASELINE_FILE_BYTES`, `DEFAULT_MAX_BASELINE_FILE_BYTES`, `DEFAULT_MAX_BASELINE_FILES` | `file_hashes[...]` | `TreeBaseline(...)`, `TreeBaseline(...)` |
| `Path` | - | - | - | - |
| `lexists` | - | - | - | - |
| `TreeBaseline` | - | - | - | - |
| `_hash_labeled_hashes` | `file_hashes: dict[str, str]` | - | - | `...` |
| `sha256` | - | - | - | - |
| `sorted` | - | - | - | - |
| `items` | - | - | - | - |
| `update` | - | - | - | - |
| `encode` | - | - | - | - |
| `replace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compare_source_plugin_tree_baseline | source_plugin_tree_baseline | 500 | `source_plugin_tree_baseline(root)` |
| source_plugin_tree_baseline | Path | 427 | `Path(root)` |
| source_plugin_tree_baseline | lexists | 432 | `os.path.lexists(plugin_home)` |
| source_plugin_tree_baseline | TreeBaseline | 433 | `TreeBaseline(root_display='source_plugins', tree_hash=_hash_labeled_hashes(...), file_hashes=file_hashes)` |
| source_plugin_tree_baseline | _hash_labeled_hashes | 435 | `_hash_labeled_hashes(file_hashes)` |
| _hash_labeled_hashes | sha256 | 905 | `hashlib.sha256(data not statically known)` |
| _hash_labeled_hashes | sorted | 906 | `sorted(file_hashes.items(...))` |
| _hash_labeled_hashes | items | 906 | `file_hashes.items(data not statically known)` |
| _hash_labeled_hashes | update | 907 | `digest.update(...)` |
| _hash_labeled_hashes | encode | 907 | `path.replace('\\', '/').encode('utf-8')` |
| _hash_labeled_hashes | replace | 907 | `path.replace('\\', '/')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `file_hashes.update` | `source_plugin_tree_baseline` | 467 |
| mutation | `digest.update` | `_hash_labeled_hashes` | 907 |
| mutation | `digest.update` | `_hash_labeled_hashes` | 908 |
| mutation | `digest.update` | `_hash_labeled_hashes` | 909 |
| mutation | `digest.update` | `_hash_labeled_hashes` | 910 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `source_plugin_tree_baseline` | `os.path.lexists` | 432 |
| external_call | `_hash_labeled_hashes` | `hashlib.sha256` | 905 |
| unresolved_call | `_hash_labeled_hashes` | `sorted` | 906 |
| unresolved_call | `_hash_labeled_hashes` | `file_hashes.items` | 906 |
| step_limit | `compare_source_plugin_tree_baseline` | `first 12 steps` | 0 |
| truncated_flow | `compare_source_plugin_tree_baseline` | `depth limit` | 0 |

## Behavior

This flow starts at `compare_source_plugin_tree_baseline` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
