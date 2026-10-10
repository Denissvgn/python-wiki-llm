# compare_source_plugin_tree_baseline

**Entry point:** `compare_source_plugin_tree_baseline` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_source_plugin_tree_baseline
    participant p1 as source_plugin_tree_baseline
    participant p2 as IntegrityDifference
    participant p3 as tuple (src/llm_wiki_cli/services…urce_plugin_tree_baseline)
    participant p4 as sorted (src/llm_wiki_cli/services…urce_plugin_tree_baseline)
    participant p5 as set
    participant p6 as Path (src/llm_wiki_cli/services…urce_plugin_tree_baseline)
    participant p7 as os.path.lexists (src/llm_wiki_cli/services…urce_plugin_tree_baseline)
    participant p8 as TreeBaseline
    participant p9 as _hash_labeled_hashes
    participant p10 as _lstat
    participant p11 as _assert_safe_directory
    participant p12 as sorted (src/llm_wiki_cli/services…e_plugin_tree_baseline, 1)
    participant p13 as path.relative_to(…).as_posix
    participant p14 as path.relative_to
    participant p15 as store.rglob
    participant p16 as DocumentationPolicyError
    participant p17 as capture_tree_baseline
    participant p18 as file_hashes.update
    p0->>p1: source_plugin_tree_baseline
    p0->>p2: IntegrityDifference
    p0-->>p3: tuple (src/llm_wiki_cli/services…urce_plugin_tree_baseline)(sorted(...))
    p0-->>p4: sorted (src/llm_wiki_cli/services…urce_plugin_tree_baseline)(...)
    p0-->>p5: set(after)
    p0-->>p5: set(before)
    p0-->>p3: tuple (src/llm_wiki_cli/services…urce_plugin_tree_baseline)(sorted(...))
    p0-->>p4: sorted (src/llm_wiki_cli/services…urce_plugin_tree_baseline)(...)
    p0-->>p5: set(before)
    p0-->>p5: set(after)
    p0-->>p3: tuple (src/llm_wiki_cli/services…urce_plugin_tree_baseline)(sorted(...))
    p0-->>p4: sorted (src/llm_wiki_cli/services…urce_plugin_tree_baseline)(...)
    p0-->>p5: set(before)
    p0-->>p5: set(after)
    p1-->>p6: Path (src/llm_wiki_cli/services…urce_plugin_tree_baseline)(root)
    p1-->>p7: os.path.lexists (src/llm_wiki_cli/services…urce_plugin_tree_baseline)(plugin_home)
    p1->>p8: TreeBaseline
    p1->>p9: _hash_labeled_hashes
    p1->>p10: _lstat
    p1->>p11: _assert_safe_directory
    p1-->>p7: os.path.lexists (src/llm_wiki_cli/services…urce_plugin_tree_baseline)(store)
    p1-->>p12: sorted (src/llm_wiki_cli/services…e_plugin_tree_baseline, 1)(...)
    p1-->>p13: path.relative_to(…).as_posix
    p1-->>p14: path.relative_to(store)
    p1-->>p15: store.rglob('*.py')
    p1-->>p14: path.relative_to(store)
    p1->>p16: DocumentationPolicyError
    p1->>p16: DocumentationPolicyError
    p1->>p17: capture_tree_baseline
    p1-->>p18: file_hashes.update(...)
```

> Call sequence diagram shows 30 of 273 interactions; 243 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 16 of 110 (94 omitted); unresolved 5 of 40 (35 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_policy.py:_hash_labeled_hashes` | 6 | - | external | 2 |
| `src/llm_wiki_cli/services/documentation_policy.py:_hash_labeled_hashes` | 6 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 18 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 18 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_assert_safe_directory` | 21 | - | external | 2 |
| `src/llm_wiki_cli/services/documentation_policy.py:_assert_safe_directory` | 21 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 4 |
| `src/llm_wiki_cli/services/documentation_policy.py:_is_windows_reparse_point` | 24 | - | external | 5 |
| `src/llm_wiki_cli/services/documentation_policy.py:capture_tree_baseline` | 41 | - | unresolved | 1 |
> Omission summary shows 8 of 52 groups; 44 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
