# input_wiki_tree_baseline

**Entry point:** `input_wiki_tree_baseline` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as input_wiki_tree_baseline
    participant p1 as capture_tree_baseline
    participant p2 as _resolve_existing_directory
    participant p3 as _walk_regular_files
    participant p4 as _hash_file
    participant p5 as _lstat
    participant p6 as _assert_safe_directory
    participant p7 as _resolve_path
    participant p8 as _guard_baseline_directory
    participant p9 as _hash_windows_file
    participant p10 as _assert_same_file_identity
    participant p11 as windows_object_identity
    participant p12 as guard_windows_directory_chain
    participant p13 as _assert_safe_regular_file
    participant p14 as open_windows_readonly_file
    participant p15 as _assert_stable_windows_path_handle_metadata
    participant p16 as _assert_stable_file_metadata
    participant p17 as windows_object_identity_from_values
    participant p18 as _windows_path_handle_metadata
    participant p19 as _open_windows_readonly_file_handle
    participant p20 as _open_windows_directory_guard
    participant p21 as create_private_windows_directory
    participant p22 as DocumentationPolicyError
    participant p23 as TreeBaseline
    participant p24 as _hash_labeled_hashes
    participant p25 as fresh_no_follow_stat
    participant p26 as _is_windows_reparse_point
    participant p27 as _stable_metadata_signature
    participant p28 as WindowsDirectoryGuardError
    participant p29 as isinstance
    participant p30 as limits.items
    p0->>p1: capture_tree_baseline
    p1->>p2: _resolve_existing_directory
    p1->>p3: _walk_regular_files
    p1->>p4: _hash_file
    p2->>p5: _lstat
    p2->>p6: _assert_safe_directory
    p2->>p7: _resolve_path
    p3->>p8: _guard_baseline_directory
    p4->>p9: _hash_windows_file
    p2->>p10: _assert_same_file_identity
    p10->>p11: windows_object_identity
    p8->>p12: guard_windows_directory_chain
    p9->>p13: _assert_safe_regular_file
    p9->>p14: open_windows_readonly_file
    p9->>p15: _assert_stable_windows_path_handle_metadata
    p9->>p16: _assert_stable_file_metadata
    p11->>p17: windows_object_identity_from_values
    p15->>p18: _windows_path_handle_metadata
    p14->>p19: _open_windows_readonly_file_handle
    p12->>p20: _open_windows_directory_guard
    p12->>p21: create_private_windows_directory
    p1->>p22: DocumentationPolicyError
    p1->>p23: TreeBaseline
    p1->>p24: _hash_labeled_hashes
    p3->>p25: fresh_no_follow_stat
    p3->>p26: _is_windows_reparse_point
    p10->>p27: _stable_metadata_signature
    p12->>p28: WindowsDirectoryGuardError
    p1-->>p29: isinstance(value, bool)
    p1-->>p30: limits.items
```

> Call sequence diagram shows 30 of 310 interactions; 280 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 129 (128 omitted); unresolved 1 of 42 (41 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_policy.py:capture_tree_baseline` | 2 | - | external | 8 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_existing_directory` | 7 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_existing_directory` | 7 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 10 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 10 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_assert_safe_directory` | 13 | - | external | 2 |
| `src/llm_wiki_cli/services/documentation_policy.py:_assert_safe_directory` | 13 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 4 |
| `src/llm_wiki_cli/services/documentation_policy.py:_is_windows_reparse_point` | 16 | - | external | 5 |
> Omission summary shows 8 of 59 groups; 51 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. input_wiki_tree_baseline"]
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
    s1 -->|"capture_tree_baseline(root, display='input_wiki')"| s2
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
| `input_wiki_tree_baseline` | `root: str \| Path` | - | - | `capture_tree_baseline(...)` |
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
| input_wiki_tree_baseline | capture_tree_baseline | 516 | `capture_tree_baseline(root, display='input_wiki')` |
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
| step_limit | `input_wiki_tree_baseline` | `first 12 steps` | 0 |
| truncated_flow | `input_wiki_tree_baseline` | `depth limit` | 0 |

## Behavior

This flow starts at `input_wiki_tree_baseline` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
