# source_tree_baseline

**Entry point:** `source_tree_baseline` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as source_tree_baseline
    participant p1 as capture_tree_baseline
    participant p2 as limits.items
    participant p3 as isinstance
    participant p4 as DocumentationPolicyError
    participant p5 as _resolve_existing_directory
    participant p6 as Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)
    participant p7 as Path (src/llm_wiki_cli/services…esolve_existing_directory)
    participant p8 as _lstat
    participant p9 as os.lstat (src/llm_wiki_cli/services…entation_policy.py:_lstat)
    participant p10 as _assert_safe_directory
    participant p11 as stat.S_ISLNK (src/llm_wiki_cli/services…py:_assert_safe_directory)
    participant p12 as _is_windows_reparse_point
    participant p13 as int (src/llm_wiki_cli/services…_is_windows_reparse_point)
    participant p14 as getattr (src/llm_wiki_cli/services…_is_windows_reparse_point)
    participant p15 as bool
    participant p16 as stat.S_ISDIR (src/llm_wiki_cli/services…py:_assert_safe_directory)
    participant p17 as _resolve_path
    participant p18 as Path(…).expanduser().resolve
    participant p19 as Path(…).expanduser (src/llm_wiki_cli/services…n_policy.py:_resolve_path)
    participant p20 as Path (src/llm_wiki_cli/services…n_policy.py:_resolve_path)
    p0->>p1: capture_tree_baseline
    p1-->>p2: limits.items
    p1-->>p3: isinstance
    p1-->>p3: isinstance
    p1->>p4: DocumentationPolicyError
    p1->>p5: _resolve_existing_directory
    p5-->>p6: Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)
    p5-->>p7: Path (src/llm_wiki_cli/services…esolve_existing_directory)
    p5->>p8: _lstat
    p8-->>p9: os.lstat (src/llm_wiki_cli/services…entation_policy.py:_lstat)
    p8->>p4: DocumentationPolicyError
    p5->>p10: _assert_safe_directory
    p10-->>p11: stat.S_ISLNK (src/llm_wiki_cli/services…py:_assert_safe_directory)
    p10->>p4: DocumentationPolicyError
    p10->>p12: _is_windows_reparse_point
    p12-->>p13: int (src/llm_wiki_cli/services…_is_windows_reparse_point)
    p12-->>p14: getattr (src/llm_wiki_cli/services…_is_windows_reparse_point)
    p12-->>p13: int (src/llm_wiki_cli/services…_is_windows_reparse_point)
    p12-->>p14: getattr (src/llm_wiki_cli/services…_is_windows_reparse_point)
    p12-->>p15: bool
    p10->>p4: DocumentationPolicyError
    p10-->>p16: stat.S_ISDIR (src/llm_wiki_cli/services…py:_assert_safe_directory)
    p10->>p4: DocumentationPolicyError
    p5->>p17: _resolve_path
    p17-->>p18: Path(…).expanduser().resolve
    p17-->>p19: Path(…).expanduser (src/llm_wiki_cli/services…n_policy.py:_resolve_path)
    p17-->>p20: Path (src/llm_wiki_cli/services…n_policy.py:_resolve_path)
    p17->>p4: DocumentationPolicyError
    p5->>p8: _lstat
    p5->>p10: _assert_safe_directory
```

> Call sequence diagram shows 30 of 310 interactions; 280 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. source_tree_baseline"]
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
    s1 -->|"capture_tree_baseline(root, display='source', excluded_directories=SOURCE_BASELINE_EXCLUDED_DIRS)"| s2
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
| `source_tree_baseline` | `root: str \| Path` | `SOURCE_BASELINE_EXCLUDED_DIRS` | - | `capture_tree_baseline(...)` |
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
| source_tree_baseline | capture_tree_baseline | 374 | `capture_tree_baseline(root, display='source', excluded_directories=SOURCE_BASELINE_EXCLUDED_DIRS)` |
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
| step_limit | `source_tree_baseline` | `first 12 steps` | 0 |
| truncated_flow | `source_tree_baseline` | `depth limit` | 0 |

## Behavior

This flow starts at `source_tree_baseline` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
