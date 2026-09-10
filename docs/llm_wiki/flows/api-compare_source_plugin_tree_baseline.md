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
    participant p2 as Path (src/llm_wiki_cli/services…urce_plugin_tree_baseline)
    participant p3 as os.path.lexists (src/llm_wiki_cli/services…urce_plugin_tree_baseline)
    participant p4 as TreeBaseline
    participant p5 as _hash_labeled_hashes
    participant p6 as hashlib.sha256 (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    participant p7 as sorted (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    participant p8 as file_hashes.items (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    participant p9 as digest.update (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    participant p10 as path.replace(…).encode
    participant p11 as path.replace
    participant p12 as file_hash.encode
    participant p13 as digest.hexdigest (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    participant p14 as _lstat
    participant p15 as os.lstat (src/llm_wiki_cli/services…entation_policy.py:_lstat)
    participant p16 as DocumentationPolicyError
    participant p17 as _assert_safe_directory
    participant p18 as stat.S_ISLNK (src/llm_wiki_cli/services…py:_assert_safe_directory)
    participant p19 as _is_windows_reparse_point
    participant p20 as int (src/llm_wiki_cli/services…_is_windows_reparse_point)
    participant p21 as getattr (src/llm_wiki_cli/services…_is_windows_reparse_point)
    participant p22 as bool
    participant p23 as stat.S_ISDIR (src/llm_wiki_cli/services…py:_assert_safe_directory)
    p0->>p1: source_plugin_tree_baseline
    p1-->>p2: Path (src/llm_wiki_cli/services…urce_plugin_tree_baseline)
    p1-->>p3: os.path.lexists (src/llm_wiki_cli/services…urce_plugin_tree_baseline)
    p1->>p4: TreeBaseline
    p1->>p5: _hash_labeled_hashes
    p5-->>p6: hashlib.sha256 (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    p5-->>p7: sorted (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    p5-->>p8: file_hashes.items (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    p5-->>p9: digest.update (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    p5-->>p10: path.replace(…).encode
    p5-->>p11: path.replace
    p5-->>p9: digest.update (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    p5-->>p9: digest.update (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    p5-->>p12: file_hash.encode
    p5-->>p9: digest.update (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    p5-->>p13: digest.hexdigest (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    p1->>p14: _lstat
    p14-->>p15: os.lstat (src/llm_wiki_cli/services…entation_policy.py:_lstat)
    p14->>p16: DocumentationPolicyError
    p1->>p17: _assert_safe_directory
    p17-->>p18: stat.S_ISLNK (src/llm_wiki_cli/services…py:_assert_safe_directory)
    p17->>p16: DocumentationPolicyError
    p17->>p19: _is_windows_reparse_point
    p19-->>p20: int (src/llm_wiki_cli/services…_is_windows_reparse_point)
    p19-->>p21: getattr (src/llm_wiki_cli/services…_is_windows_reparse_point)
    p19-->>p20: int (src/llm_wiki_cli/services…_is_windows_reparse_point)
    p19-->>p21: getattr (src/llm_wiki_cli/services…_is_windows_reparse_point)
    p19-->>p22: bool
    p17->>p16: DocumentationPolicyError
    p17-->>p23: stat.S_ISDIR (src/llm_wiki_cli/services…py:_assert_safe_directory)
```

> Call sequence diagram shows 30 of 273 interactions; 243 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. compare_source_plugin_tree_baseline"]
    s2["2. source_plugin_tree_baseline"]
    s3["3. Path (src/llm_wiki_cli/services…urce_plugin_tree_baseline)"]
    s4["4. os.path.lexists (src/llm_wiki_cli/services…urce_plugin_tree_baseline)"]
    s5["5. TreeBaseline"]
    s6["6. _hash_labeled_hashes"]
    s7["7. hashlib.sha256 (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)"]
    s8["8. sorted (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)"]
    s9["9. file_hashes.items (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)"]
    s10["10. digest.update (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)"]
    s11["11. path.replace(…).encode"]
    s12["12. path.replace"]
    s1 -->|"source_plugin_tree_baseline(root)"| s2
    s2 -. "Path (src/llm_wiki_cli/services…urce_plugin_tree_baseline)(root)" .-> s3
    s2 -. "os.path.lexists (src/llm_wiki_cli/services…urce_plugin_tree_baseline)(plugin_home)" .-> s4
    s2 -->|"TreeBaseline(root_display='source_plugins', tree_hash=_hash_labeled_hashes(...), file_hashes=file_hashes)"| s5
    s2 -->|"_hash_labeled_hashes(file_hashes)"| s6
    s6 -. "hashlib.sha256 (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)(data not statically known)" .-> s7
    s6 -. "sorted (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)(file_hashes.items(...))" .-> s8
    s6 -. "file_hashes.items (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)(data not statically known)" .-> s9
    s6 -. "digest.update (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)(...)" .-> s10
    s6 -. "path.replace(…).encode('utf-8')" .-> s11
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
| `Path (src/llm_wiki_cli/services…urce_plugin_tree_baseline)` | - | - | - | - |
| `os.path.lexists (src/llm_wiki_cli/services…urce_plugin_tree_baseline)` | - | - | - | - |
| `TreeBaseline` | - | - | - | - |
| `_hash_labeled_hashes` | `file_hashes: dict[str, str]` | - | - | `...` |
| `hashlib.sha256 (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)` | - | - | - | - |
| `sorted (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)` | - | - | - | - |
| `file_hashes.items (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)` | - | - | - | - |
| `digest.update (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)` | - | - | - | - |
| `path.replace(…).encode` | - | - | - | - |
| `path.replace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compare_source_plugin_tree_baseline | source_plugin_tree_baseline | 500 | `source_plugin_tree_baseline(root)` |
| source_plugin_tree_baseline | Path (src/llm_wiki_cli/services…urce_plugin_tree_baseline) | 427 | `Path(root)` |
| source_plugin_tree_baseline | os.path.lexists (src/llm_wiki_cli/services…urce_plugin_tree_baseline) | 432 | `os.path.lexists(plugin_home)` |
| source_plugin_tree_baseline | TreeBaseline | 433 | `TreeBaseline(root_display='source_plugins', tree_hash=_hash_labeled_hashes(...), file_hashes=file_hashes)` |
| source_plugin_tree_baseline | _hash_labeled_hashes | 435 | `_hash_labeled_hashes(file_hashes)` |
| _hash_labeled_hashes | hashlib.sha256 (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes) | 905 | `hashlib.sha256(data not statically known)` |
| _hash_labeled_hashes | sorted (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes) | 906 | `sorted(file_hashes.items(...))` |
| _hash_labeled_hashes | file_hashes.items (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes) | 906 | `file_hashes.items(data not statically known)` |
| _hash_labeled_hashes | digest.update (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes) | 907 | `digest.update(...)` |
| _hash_labeled_hashes | path.replace(…).encode | 907 | `path.replace('\\', '/').encode('utf-8')` |
| _hash_labeled_hashes | path.replace | 907 | `path.replace('\\', '/')` |

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
| external_call | `_hash_labeled_hashes` | `sorted` | 906 |
| unresolved_call | `_hash_labeled_hashes` | `file_hashes.items` | 906 |
| step_limit | `compare_source_plugin_tree_baseline` | `first 12 steps` | 0 |
| truncated_flow | `compare_source_plugin_tree_baseline` | `depth limit` | 0 |

## Behavior

This flow starts at `compare_source_plugin_tree_baseline` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
