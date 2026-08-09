# source_plugin_tree_baseline

**Entry point:** `source_plugin_tree_baseline` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as source_plugin_tree_baseline
    participant p1 as Path
    participant p2 as lexists
    participant p3 as TreeBaseline
    participant p4 as _hash_labeled_hashes
    participant p5 as sha256
    participant p6 as sorted
    participant p7 as items
    participant p8 as update
    participant p9 as encode
    participant p10 as replace
    participant p11 as hexdigest
    participant p12 as _lstat
    participant p13 as lstat
    participant p14 as DocumentationPolicyError
    participant p15 as _assert_safe_directory
    participant p16 as S_ISLNK
    participant p17 as _is_windows_reparse_point
    participant p18 as int
    participant p19 as getattr
    participant p20 as bool
    participant p21 as S_ISDIR
    p0-->>p1: Path
    p0-->>p2: lexists
    p0->>p3: TreeBaseline
    p0->>p4: _hash_labeled_hashes
    p4-->>p5: sha256
    p4-->>p6: sorted
    p4-->>p7: items
    p4-->>p8: update
    p4-->>p9: encode
    p4-->>p10: replace
    p4-->>p8: update
    p4-->>p8: update
    p4-->>p9: encode
    p4-->>p8: update
    p4-->>p11: hexdigest
    p0->>p12: _lstat
    p12-->>p13: lstat
    p12->>p14: DocumentationPolicyError
    p0->>p15: _assert_safe_directory
    p15-->>p16: S_ISLNK
    p15->>p14: DocumentationPolicyError
    p15->>p17: _is_windows_reparse_point
    p17-->>p18: int
    p17-->>p19: getattr
    p17-->>p18: int
    p17-->>p19: getattr
    p17-->>p20: bool
    p15->>p14: DocumentationPolicyError
    p15-->>p21: S_ISDIR
    p15->>p14: DocumentationPolicyError
```

> Call sequence diagram shows 30 of 336 interactions; 306 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. source_plugin_tree_baseline"]
    s2["2. Path"]
    s3["3. lexists"]
    s4["4. TreeBaseline"]
    s5["5. _hash_labeled_hashes"]
    s6["6. sha256"]
    s7["7. sorted"]
    s8["8. items"]
    s9["9. update"]
    s10["10. encode"]
    s11["11. replace"]
    s12["12. update"]
    s1 -. "Path(root)" .-> s2
    s1 -. "os.path.lexists(plugin_home)" .-> s3
    s1 -->|"TreeBaseline(root_display='source_plugins', tree_hash=_hash_labeled_hashes(...), file_hashes=file_hashes)"| s4
    s1 -->|"_hash_labeled_hashes(file_hashes)"| s5
    s5 -. "hashlib.sha256(data not statically known)" .-> s6
    s5 -. "sorted(file_hashes.items(...))" .-> s7
    s5 -. "file_hashes.items(data not statically known)" .-> s8
    s5 -. "digest.update(...)" .-> s9
    s5 -. "path.replace('\\', '/').encode('utf-8')" .-> s10
    s5 -. "path.replace('\\', '/')" .-> s11
    s5 -. "digest.update(b'\x00')" .-> s12
    b0["mutation file_hashes.update"]
    s1 -. "mutation file_hashes.update" .-> b0
    b1["mutation digest.update"]
    s5 -. "mutation digest.update" .-> b1
    b2["mutation digest.update"]
    s5 -. "mutation digest.update" .-> b2
    b3["mutation digest.update"]
    s5 -. "mutation digest.update" .-> b3
    b4["mutation digest.update"]
    s5 -. "mutation digest.update" .-> b4
    click s1 "../modules/documentation_policy.md"
    click s4 "../modules/documentation_policy.md"
    click s5 "../modules/documentation_policy.md"
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
| `update` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| _hash_labeled_hashes | update | 908 | `digest.update(b'\x00')` |

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
| step_limit | `source_plugin_tree_baseline` | `first 12 steps` | 0 |
| truncated_flow | `source_plugin_tree_baseline` | `depth limit` | 0 |

## Behavior

This flow starts at `source_plugin_tree_baseline` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
