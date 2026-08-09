# capture_tree_baseline

**Entry point:** `capture_tree_baseline` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as capture_tree_baseline
    participant p1 as items
    participant p2 as isinstance
    participant p3 as DocumentationPolicyError
    participant p4 as _resolve_existing_directory
    participant p5 as expanduser
    participant p6 as Path
    participant p7 as _lstat
    participant p8 as lstat
    participant p9 as _assert_safe_directory
    participant p10 as S_ISLNK
    participant p11 as _is_windows_reparse_point
    participant p12 as int
    participant p13 as getattr
    participant p14 as bool
    participant p15 as S_ISDIR
    participant p16 as _resolve_path
    participant p17 as resolve
    participant p18 as _assert_same_file_identity
    p0-->>p1: items
    p0-->>p2: isinstance
    p0-->>p2: isinstance
    p0->>p3: DocumentationPolicyError
    p0->>p4: _resolve_existing_directory
    p4-->>p5: expanduser
    p4-->>p6: Path
    p4->>p7: _lstat
    p7-->>p8: lstat
    p7->>p3: DocumentationPolicyError
    p4->>p9: _assert_safe_directory
    p9-->>p10: S_ISLNK
    p9->>p3: DocumentationPolicyError
    p9->>p11: _is_windows_reparse_point
    p11-->>p12: int
    p11-->>p13: getattr
    p11-->>p12: int
    p11-->>p13: getattr
    p11-->>p14: bool
    p9->>p3: DocumentationPolicyError
    p9-->>p15: S_ISDIR
    p9->>p3: DocumentationPolicyError
    p4->>p16: _resolve_path
    p16-->>p17: resolve
    p16-->>p5: expanduser
    p16-->>p6: Path
    p16->>p3: DocumentationPolicyError
    p4->>p7: _lstat
    p4->>p9: _assert_safe_directory
    p4->>p18: _assert_same_file_identity
```

> Call sequence diagram shows 30 of 410 interactions; 380 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. capture_tree_baseline"]
    s2["2. items"]
    s3["3. isinstance"]
    s4["4. isinstance"]
    s5["5. DocumentationPolicyError"]
    s6["6. _resolve_existing_directory"]
    s7["7. expanduser"]
    s8["8. Path"]
    s9["9. _lstat"]
    s10["10. lstat"]
    s11["11. DocumentationPolicyError"]
    s12["12. _assert_safe_directory"]
    s1 -. "limits.items(data not statically known)" .-> s2
    s1 -. "isinstance(value, bool)" .-> s3
    s1 -. "isinstance(value, int)" .-> s4
    s1 -->|"DocumentationPolicyError(...)"| s5
    s1 -->|"_resolve_existing_directory(root, display)"| s6
    s6 -. "Path(path).expanduser(data not statically known)" .-> s7
    s6 -. "Path(path)" .-> s8
    s6 -->|"_lstat(candidate, context=label)"| s9
    s9 -. "os.lstat(path)" .-> s10
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
| `items` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `DocumentationPolicyError` | - | - | - | - |
| `_resolve_existing_directory` | `path: str \| Path`, `label: str` | - | - | `resolved` |
| `expanduser` | - | - | - | - |
| `Path` | - | - | - | - |
| `_lstat` | `path: Path`, `context: str` | - | - | `os.lstat(...)` |
| `lstat` | - | - | - | - |
| `DocumentationPolicyError` | - | - | - | - |
| `_assert_safe_directory` | `path: Path`, `result: os.stat_result`, `context: str` | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| capture_tree_baseline | items | 304 | `limits.items(data not statically known)` |
| capture_tree_baseline | isinstance | 305 | `isinstance(value, bool)` |
| capture_tree_baseline | isinstance | 305 | `isinstance(value, int)` |
| capture_tree_baseline | DocumentationPolicyError | 306 | `DocumentationPolicyError(...)` |
| capture_tree_baseline | _resolve_existing_directory | 308 | `_resolve_existing_directory(root, display)` |
| _resolve_existing_directory | expanduser | 948 | `Path(path).expanduser(data not statically known)` |
| _resolve_existing_directory | Path | 948 | `Path(path)` |
| _resolve_existing_directory | _lstat | 949 | `_lstat(candidate, context=label)` |
| _lstat | lstat | 782 | `os.lstat(path)` |
| _lstat | DocumentationPolicyError | 784 | `DocumentationPolicyError(...)` |
| _resolve_existing_directory | _assert_safe_directory | 950 | `_assert_safe_directory(candidate, inspected, context=label)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `capture_tree_baseline` | `limits.items` | 304 |
| unresolved_call | `capture_tree_baseline` | `isinstance` | 305 |
| unresolved_call | `_resolve_existing_directory` | `Path(path).expanduser` | 948 |
| external_call | `_lstat` | `os.lstat` | 782 |
| step_limit | `capture_tree_baseline` | `first 12 steps` | 0 |
| truncated_flow | `capture_tree_baseline` | `depth limit` | 0 |

## Behavior

This flow starts at `capture_tree_baseline` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
