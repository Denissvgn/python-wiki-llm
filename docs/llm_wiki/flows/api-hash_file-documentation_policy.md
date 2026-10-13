# hash_file

**Entry point:** `hash_file` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_file
    participant p1 as _hash_file
    participant p2 as guard_windows_directory_chain
    participant p3 as _hash_windows_file
    participant p4 as _lstat
    participant p5 as _assert_safe_regular_file
    participant p6 as _assert_same_file_identity
    participant p7 as open_windows_readonly_file
    participant p8 as _open_windows_directory_guard
    participant p9 as _assert_stable_windows_path_handle_metadata
    participant p10 as create_private_windows_directory
    participant p11 as _assert_stable_file_metadata
    participant p12 as windows_object_identity
    participant p13 as _windows_path_handle_metadata
    participant p14 as _open_windows_readonly_file_handle
    participant p15 as _private_windows_security_attributes
    participant p16 as move_windows_path_write_through
    participant p17 as _verify_windows_handle_restrictive_dacl
    participant p18 as windows_object_identity_from_values
    participant p19 as _current_windows_user_sid
    participant p20 as DocumentationPolicyError
    participant p21 as WindowsDirectoryGuardError
    participant p22 as fresh_no_follow_stat
    participant p23 as _close_windows_handle
    participant p24 as WindowsFileGuardError
    participant p25 as _stable_metadata_signature
    participant p26 as _windows_api_path
    participant p27 as _is_windows_reparse_point
    participant p28 as _WindowsDirectoryGuardUnavailableError
    participant p29 as Path (src/llm_wiki_cli/services…ation_policy.py:hash_file)
    participant p30 as digest.update (src/llm_wiki_cli/services…tion_policy.py:_hash_file)
    p0->>p1: _hash_file
    p1->>p2: guard_windows_directory_chain
    p1->>p3: _hash_windows_file
    p1->>p4: _lstat
    p3->>p5: _assert_safe_regular_file
    p3->>p6: _assert_same_file_identity
    p3->>p7: open_windows_readonly_file
    p2->>p8: _open_windows_directory_guard
    p3->>p9: _assert_stable_windows_path_handle_metadata
    p2->>p10: create_private_windows_directory
    p3->>p11: _assert_stable_file_metadata
    p6->>p12: windows_object_identity
    p9->>p13: _windows_path_handle_metadata
    p7->>p14: _open_windows_readonly_file_handle
    p10->>p15: _private_windows_security_attributes
    p10->>p16: move_windows_path_write_through
    p8->>p17: _verify_windows_handle_restrictive_dacl
    p12->>p18: windows_object_identity_from_values
    p17->>p19: _current_windows_user_sid
    p1->>p20: DocumentationPolicyError
    p2->>p21: WindowsDirectoryGuardError
    p3->>p22: fresh_no_follow_stat
    p2->>p23: _close_windows_handle
    p7->>p24: WindowsFileGuardError
    p11->>p25: _stable_metadata_signature
    p8->>p26: _windows_api_path
    p5->>p27: _is_windows_reparse_point
    p8->>p28: _WindowsDirectoryGuardUnavailableError
    p0-->>p29: Path (src/llm_wiki_cli/services…ation_policy.py:hash_file)(path)
    p1-->>p30: digest.update (src/llm_wiki_cli/services…tion_policy.py:_hash_file)(chunk)
```

> Call sequence diagram shows 30 of 356 interactions; 326 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 195 (194 omitted); unresolved 1 of 37 (36 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_policy.py:_hash_file` | 2 | - | external | 14 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 6 | - | external | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 6 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 5 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 6 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 14 | - | external | 14 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 14 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 17 | - | external | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 17 | - | unresolved | 2 |
> Omission summary shows 8 of 56 groups; 48 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_file"]
    s2["2. _hash_file"]
    s3["3. Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file)"]
    s4["4. os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)"]
    s5["5. os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)"]
    s6["6. guard_windows_directory_chain"]
    s7["7. WindowsDirectoryGuardError"]
    s8["8. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s9["9. os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s10["10. os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s11["11. WindowsDirectoryGuardError"]
    s12["12. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s1 -->|"_hash_file(Path(...))"| s2
    s2 -. "Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file)(os.path.abspath(...))" .-> s3
    s2 -. "os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)(os.fspath(...))" .-> s4
    s2 -. "os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)(path)" .-> s5
    s2 -->|"guard_windows_directory_chain(absolute_path.parent, (...))"| s6
    s6 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s7
    s6 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(os.path.abspath(...))" .-> s8
    s6 -. "os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)(os.fspath(...))" .-> s9
    s6 -. "os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)(root)" .-> s10
    s6 -->|"WindowsDirectoryGuardError(...)"| s11
    s6 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(root_path.anchor)" .-> s12
    b0["mutation digest.update"]
    s2 -. "mutation digest.update" .-> b0
    b1["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b1
    b2["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b2
    b3["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b3
    click s1 "../modules/documentation_policy.md"
    click s2 "../modules/documentation_policy.md"
    click s6 "../modules/filesystem_guard.md"
    click s7 "../modules/filesystem_guard.md"
    click s11 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_file` | `path: str \| Path` | - | - | `_hash_file(...)` |
| `_hash_file` | `path: Path`, `inspected: os.stat_result \| None`, `max_bytes: int \| None` | `os`, `WindowsDirectoryGuardError`, `os`, `os`, `os`, `os` | - | `_hash_windows_file(...)`, `...` |
| `Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)` | - | - | - | - |
| `guard_windows_directory_chain` | `root: Path`, `relative_components: Sequence[str]`, `create_missing: bool`, `require_restrictive_dacl: bool` | `os`, `WindowsDurabilityError` | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_file | _hash_file | 524 | `_hash_file(Path(...))` |
| _hash_file | Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file) | 626 | `Path(os.path.abspath(...))` |
| _hash_file | os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file) | 626 | `os.path.abspath(os.fspath(...))` |
| _hash_file | os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file) | 626 | `os.fspath(path)` |
| _hash_file | guard_windows_directory_chain | 628 | `guard_windows_directory_chain(absolute_path.parent, (...))` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.fspath(root)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 176 | `WindowsDirectoryGuardError(...)` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 179 | `Path(root_path.anchor)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `digest.update` | `_hash_file` | 677 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 189 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 216 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_hash_file` | `os.path.abspath` | 626 |
| external_call | `_hash_file` | `os.fspath` | 626 |
| external_call | `guard_windows_directory_chain` | `os.path.abspath` | 174 |
| external_call | `guard_windows_directory_chain` | `os.fspath` | 174 |
| step_limit | `hash_file` | `first 12 steps` | 0 |
| truncated_flow | `hash_file` | `depth limit` | 0 |

## Behavior

This flow starts at `hash_file` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
