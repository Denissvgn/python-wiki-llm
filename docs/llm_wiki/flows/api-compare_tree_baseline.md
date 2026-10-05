# compare_tree_baseline

**Entry point:** `compare_tree_baseline` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_tree_baseline
    participant p1 as capture_tree_baseline
    participant p2 as IntegrityDifference
    participant p3 as tuple (src/llm_wiki_cli/services….py:compare_tree_baseline)
    participant p4 as sorted (src/llm_wiki_cli/services….py:compare_tree_baseline)
    participant p5 as set
    participant p6 as limits.items
    participant p7 as isinstance
    participant p8 as DocumentationPolicyError
    participant p9 as _resolve_existing_directory
    participant p10 as frozenset
    participant p11 as str (src/llm_wiki_cli/services….py:capture_tree_baseline)
    participant p12 as _walk_regular_files
    participant p13 as len (src/llm_wiki_cli/services….py:capture_tree_baseline)
    participant p14 as int (src/llm_wiki_cli/services….py:capture_tree_baseline)
    participant p15 as _hash_file
    participant p16 as min
    participant p17 as TreeBaseline
    p0->>p1: capture_tree_baseline
    p0->>p2: IntegrityDifference
    p0-->>p3: tuple (src/llm_wiki_cli/services….py:compare_tree_baseline)(sorted(...))
    p0-->>p4: sorted (src/llm_wiki_cli/services….py:compare_tree_baseline)(...)
    p0-->>p5: set(after)
    p0-->>p5: set(before)
    p0-->>p3: tuple (src/llm_wiki_cli/services….py:compare_tree_baseline)(sorted(...))
    p0-->>p4: sorted (src/llm_wiki_cli/services….py:compare_tree_baseline)(...)
    p0-->>p5: set(before)
    p0-->>p5: set(after)
    p0-->>p3: tuple (src/llm_wiki_cli/services….py:compare_tree_baseline)(sorted(...))
    p0-->>p4: sorted (src/llm_wiki_cli/services….py:compare_tree_baseline)(...)
    p0-->>p5: set(before)
    p0-->>p5: set(after)
    p1-->>p6: limits.items
    p1-->>p7: isinstance(value, bool)
    p1-->>p7: isinstance(value, int)
    p1->>p8: DocumentationPolicyError
    p1->>p9: _resolve_existing_directory
    p1-->>p10: frozenset(...)
    p1-->>p11: str (src/llm_wiki_cli/services….py:capture_tree_baseline)(value)
    p1->>p12: _walk_regular_files
    p1-->>p13: len (src/llm_wiki_cli/services….py:capture_tree_baseline)(file_hashes)
    p1->>p8: DocumentationPolicyError
    p1-->>p14: int (src/llm_wiki_cli/services….py:capture_tree_baseline)(inspected.st_size)
    p1->>p8: DocumentationPolicyError
    p1->>p8: DocumentationPolicyError
    p1->>p15: _hash_file
    p1-->>p16: min(max_file_bytes, ...)
    p1->>p17: TreeBaseline
```

> Call sequence diagram shows 30 of 323 interactions; 293 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 19 of 141 (122 omitted); unresolved 1 of 42 (41 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_existing_directory` | 7 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_existing_directory` | 7 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_existing_directory` | 7 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 9 |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 10 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 10 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_assert_safe_directory` | 13 | - | external | 2 |
| `src/llm_wiki_cli/services/documentation_policy.py:_assert_safe_directory` | 13 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 4 |
| `src/llm_wiki_cli/services/documentation_policy.py:_is_windows_reparse_point` | 16 | - | external | 5 |
> Omission summary shows 8 of 61 groups; 53 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. compare_tree_baseline"]
    s2["2. capture_tree_baseline"]
    s3["3. limits.items"]
    s4["4. isinstance"]
    s5["5. isinstance"]
    s6["6. DocumentationPolicyError"]
    s7["7. _resolve_existing_directory"]
    s8["8. Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)"]
    s9["9. Path (src/llm_wiki_cli/services…esolve_existing_directory)"]
    s10["10. _lstat"]
    s11["11. os.lstat (src/llm_wiki_cli/services…entation_policy.py:_lstat)"]
    s12["12. DocumentationPolicyError"]
    s1 -->|"capture_tree_baseline(…)"| s2
    s2 -. "limits.items(data not statically known)" .-> s3
    s2 -. "isinstance(value, bool)" .-> s4
    s2 -. "isinstance(value, int)" .-> s5
    s2 -->|"DocumentationPolicyError(...)"| s6
    s2 -->|"_resolve_existing_directory(root, display)"| s7
    s7 -. "Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)(data not statically known)" .-> s8
    s7 -. "Path (src/llm_wiki_cli/services…esolve_existing_directory)(path)" .-> s9
    s7 -->|"_lstat(candidate, context=label)"| s10
    s10 -. "os.lstat (src/llm_wiki_cli/services…entation_policy.py:_lstat)(path)" .-> s11
    s10 -->|"DocumentationPolicyError(...)"| s12
    click s1 "../modules/documentation_policy.md"
    click s2 "../modules/documentation_policy.md"
    click s6 "../modules/documentation_policy.md"
    click s7 "../modules/documentation_policy.md"
    click s10 "../modules/documentation_policy.md"
    click s12 "../modules/documentation_policy.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compare_tree_baseline` | `baseline: TreeBaseline`, `root: str \| Path`, `max_files: int`, `max_file_bytes: int`, `max_total_bytes: int` | - | - | `IntegrityDifference(...)` |
| `capture_tree_baseline` | `root: str \| Path`, `display: str`, `excluded_directories: Iterable[str]`, `max_files: int`, `max_file_bytes: int`, `max_total_bytes: int` | - | `file_hashes[...]` | `TreeBaseline(...)` |
| `limits.items` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `DocumentationPolicyError` | - | - | - | - |
| `_resolve_existing_directory` | `path: str \| Path`, `label: str` | - | - | `resolved` |
| `Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…esolve_existing_directory)` | - | - | - | - |
| `_lstat` | `path: Path`, `context: str` | - | - | `os.lstat(...)` |
| `os.lstat (src/llm_wiki_cli/services…entation_policy.py:_lstat)` | - | - | - | - |
| `DocumentationPolicyError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compare_tree_baseline | capture_tree_baseline | 351 | `capture_tree_baseline(root, display=baseline.root_display, excluded_directories=baseline.excluded_directories, max_files=max_files, max_file_bytes=max_file_bytes, max_total_bytes=max_total_bytes)` |
| capture_tree_baseline | limits.items | 304 | `limits.items(data not statically known)` |
| capture_tree_baseline | isinstance | 305 | `isinstance(value, bool)` |
| capture_tree_baseline | isinstance | 305 | `isinstance(value, int)` |
| capture_tree_baseline | DocumentationPolicyError | 306 | `DocumentationPolicyError(...)` |
| capture_tree_baseline | _resolve_existing_directory | 308 | `_resolve_existing_directory(root, display)` |
| _resolve_existing_directory | Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory) | 948 | `Path(path).expanduser(data not statically known)` |
| _resolve_existing_directory | Path (src/llm_wiki_cli/services…esolve_existing_directory) | 948 | `Path(path)` |
| _resolve_existing_directory | _lstat | 949 | `_lstat(candidate, context=label)` |
| _lstat | os.lstat (src/llm_wiki_cli/services…entation_policy.py:_lstat) | 782 | `os.lstat(path)` |
| _lstat | DocumentationPolicyError | 784 | `DocumentationPolicyError(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `capture_tree_baseline` | `limits.items` | 304 |
| external_call | `capture_tree_baseline` | `isinstance` | 305 |
| unresolved_call | `_resolve_existing_directory` | `Path(path).expanduser` | 948 |
| external_call | `_lstat` | `os.lstat` | 782 |
| step_limit | `compare_tree_baseline` | `first 12 steps` | 0 |
| truncated_flow | `compare_tree_baseline` | `depth limit` | 0 |

## Behavior

This flow starts at `compare_tree_baseline` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
