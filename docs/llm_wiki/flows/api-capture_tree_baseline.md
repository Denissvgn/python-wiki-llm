# capture_tree_baseline

**Entry point:** `capture_tree_baseline` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as capture_tree_baseline
    participant p1 as limits.items
    participant p2 as isinstance
    participant p3 as DocumentationPolicyError
    participant p4 as _resolve_existing_directory
    participant p5 as frozenset
    participant p6 as str (src/llm_wiki_cli/services….py:capture_tree_baseline)
    participant p7 as _walk_regular_files
    participant p8 as len (src/llm_wiki_cli/services….py:capture_tree_baseline)
    participant p9 as int (src/llm_wiki_cli/services….py:capture_tree_baseline)
    participant p10 as _hash_file
    participant p11 as min
    participant p12 as TreeBaseline
    participant p13 as _hash_labeled_hashes
    participant p14 as tuple
    participant p15 as sorted (src/llm_wiki_cli/services….py:capture_tree_baseline)
    participant p16 as Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)
    participant p17 as _lstat
    participant p18 as Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file)
    participant p19 as hashlib.sha256 (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    participant p20 as Path (src/llm_wiki_cli/services…esolve_existing_directory)
    participant p21 as _assert_safe_directory
    participant p22 as os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)
    participant p23 as sorted (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    participant p24 as Path (src/llm_wiki_cli/services…cy.py:_walk_regular_files)
    participant p25 as os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)
    p0-->>p1: limits.items
    p0-->>p2: isinstance(value, bool)
    p0-->>p2: isinstance(value, int)
    p0->>p3: DocumentationPolicyError
    p0->>p4: _resolve_existing_directory
    p0-->>p5: frozenset(...)
    p0-->>p6: str (src/llm_wiki_cli/services….py:capture_tree_baseline)(value)
    p0->>p7: _walk_regular_files
    p0-->>p8: len (src/llm_wiki_cli/services….py:capture_tree_baseline)(file_hashes)
    p0->>p3: DocumentationPolicyError
    p0-->>p9: int (src/llm_wiki_cli/services….py:capture_tree_baseline)(inspected.st_size)
    p0->>p3: DocumentationPolicyError
    p0->>p3: DocumentationPolicyError
    p0->>p10: _hash_file
    p0-->>p11: min(max_file_bytes, ...)
    p0->>p12: TreeBaseline
    p0->>p13: _hash_labeled_hashes
    p0-->>p14: tuple(sorted(...))
    p0-->>p15: sorted (src/llm_wiki_cli/services….py:capture_tree_baseline)(excluded)
    p4-->>p16: Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)
    p7->>p17: _lstat
    p10-->>p18: Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file)(os.path.abspath(...))
    p13-->>p19: hashlib.sha256 (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)
    p4-->>p20: Path (src/llm_wiki_cli/services…esolve_existing_directory)(path)
    p7->>p21: _assert_safe_directory
    p10-->>p22: os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)(os.fspath(...))
    p13-->>p23: sorted (src/llm_wiki_cli/services…y.py:_hash_labeled_hashes)(file_hashes.items(...))
    p4->>p17: _lstat
    p7-->>p24: Path (src/llm_wiki_cli/services…cy.py:_walk_regular_files)
    p10-->>p25: os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)(path)
```

> Call sequence diagram shows 30 of 412 interactions; 382 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 16 of 199 (183 omitted); unresolved 2 of 54 (52 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 9 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 9 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_existing_directory` | 6 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 8 |
| `src/llm_wiki_cli/services/documentation_policy.py:_assert_safe_directory` | 12 | - | external | 2 |
| `src/llm_wiki_cli/services/documentation_policy.py:_assert_safe_directory` | 12 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 4 |
| `src/llm_wiki_cli/services/documentation_policy.py:_is_windows_reparse_point` | 15 | - | external | 5 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_path` | 24 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_path` | 24 | - | external | 1 |
> Omission summary shows 8 of 69 groups; 61 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. capture_tree_baseline"]
    s2["2. limits.items"]
    s3["3. isinstance"]
    s4["4. isinstance"]
    s5["5. DocumentationPolicyError"]
    s6["6. _resolve_existing_directory"]
    s7["7. Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)"]
    s8["8. Path (src/llm_wiki_cli/services…esolve_existing_directory)"]
    s9["9. _lstat"]
    s10["10. os.lstat (src/llm_wiki_cli/services…entation_policy.py:_lstat)"]
    s11["11. DocumentationPolicyError"]
    s12["12. _assert_safe_directory"]
    s1 -. "limits.items(data not statically known)" .-> s2
    s1 -. "isinstance(value, bool)" .-> s3
    s1 -. "isinstance(value, int)" .-> s4
    s1 -->|"DocumentationPolicyError(...)"| s5
    s1 -->|"_resolve_existing_directory(root, display)"| s6
    s6 -. "Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)(data not statically known)" .-> s7
    s6 -. "Path (src/llm_wiki_cli/services…esolve_existing_directory)(path)" .-> s8
    s6 -->|"_lstat(candidate, context=label)"| s9
    s9 -. "os.lstat (src/llm_wiki_cli/services…entation_policy.py:_lstat)(path)" .-> s10
    s9 -->|"DocumentationPolicyError(...)"| s11
    s6 -->|"_assert_safe_directory(candidate, inspected, context=label)"| s12
    click s1 "../modules/documentation_policy.md"
    click s5 "../modules/documentation_policy.md"
    click s6 "../modules/documentation_policy.md"
    click s9 "../modules/documentation_policy.md"
    click s11 "../modules/documentation_policy.md"
    click s12 "../modules/documentation_policy.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `_assert_safe_directory` | `path: Path`, `result: os.stat_result`, `context: str` | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| _resolve_existing_directory | _assert_safe_directory | 950 | `_assert_safe_directory(candidate, inspected, context=label)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `capture_tree_baseline` | `limits.items` | 304 |
| external_call | `capture_tree_baseline` | `isinstance` | 305 |
| unresolved_call | `_resolve_existing_directory` | `Path(path).expanduser` | 948 |
| external_call | `_lstat` | `os.lstat` | 782 |
| step_limit | `capture_tree_baseline` | `first 12 steps` | 0 |
| truncated_flow | `capture_tree_baseline` | `depth limit` | 0 |

## Behavior

This flow starts at `capture_tree_baseline` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
