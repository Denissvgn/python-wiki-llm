# remove_guarded_tree

**Entry point:** `remove_guarded_tree` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as remove_guarded_tree
    participant p1 as Path (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)
    participant p2 as target.is_absolute
    participant p3 as OSError (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)
    participant p4 as uuid.uuid4 (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)
    participant p5 as guard_windows_directory_chain
    participant p6 as create_private_windows_directory
    participant p7 as move_windows_path_write_through
    participant p8 as claimed.lstat
    participant p9 as windows_object_identity
    participant p10 as str (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)
    participant p11 as getattr (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)
    participant p12 as stat.S_ISDIR (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)
    participant p13 as WindowsDirectoryGuardError
    participant p14 as _guarded_tree_manifest_windows_path
    participant p15 as any
    participant p16 as clear_windows
    participant p17 as claimed.rmdir
    participant p18 as quarantine.rmdir
    p0-->>p1: Path (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(path)
    p0-->>p2: target.is_absolute
    p0-->>p3: OSError (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(...)
    p0-->>p4: uuid.uuid4 (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)
    p0->>p5: guard_windows_directory_chain
    p0-->>p1: Path (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(target.parent.anchor)
    p0->>p6: create_private_windows_directory
    p0->>p7: move_windows_path_write_through
    p0-->>p8: claimed.lstat
    p0->>p9: windows_object_identity
    p0-->>p10: str (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(claimed)
    p0-->>p11: getattr (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(metadata, 'st_file_attributes', 0)
    p0-->>p12: stat.S_ISDIR (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(metadata.st_mode)
    p0->>p13: WindowsDirectoryGuardError
    p0->>p13: WindowsDirectoryGuardError
    p0->>p14: _guarded_tree_manifest_windows_path
    p0->>p13: WindowsDirectoryGuardError
    p0-->>p15: any(...)
    p0-->>p12: stat.S_ISDIR (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(entry[...])
    p0->>p13: WindowsDirectoryGuardError
    p0-->>p16: clear_windows(claimed)
    p0->>p9: windows_object_identity
    p0-->>p8: claimed.lstat
    p0-->>p10: str (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(claimed)
    p0->>p13: WindowsDirectoryGuardError
    p0-->>p17: claimed.rmdir
    p0->>p7: move_windows_path_write_through
    p0-->>p18: quarantine.rmdir
    p0-->>p11: getattr (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(os, 'O_NOFOLLOW', None)
    p0-->>p11: getattr (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(os, 'O_DIRECTORY', None)
```

> Call sequence diagram shows 30 of 385 interactions; 355 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 12 of 236 (224 omitted); unresolved 6 of 53 (47 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 6 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 6 | - | external | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 6 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 14 | - | external | 14 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 14 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 14 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 17 | - | external | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 17 | - | unresolved | 2 |
> Omission summary shows 8 of 52 groups; 44 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. remove_guarded_tree"]
    s2["2. Path (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)"]
    s3["3. target.is_absolute"]
    s4["4. OSError (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)"]
    s5["5. uuid.uuid4 (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)"]
    s6["6. guard_windows_directory_chain"]
    s7["7. WindowsDirectoryGuardError"]
    s8["8. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s9["9. os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s10["10. os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s11["11. WindowsDirectoryGuardError"]
    s12["12. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s1 -. "Path (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(path)" .-> s2
    s1 -. "target.is_absolute(data not statically known)" .-> s3
    s1 -. "OSError (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(...)" .-> s4
    s1 -. "uuid.uuid4 (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)(data not statically known)" .-> s5
    s1 -->|"guard_windows_directory_chain(Path(...), ...)"| s6
    s6 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s7
    s6 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(os.path.abspath(...))" .-> s8
    s6 -. "os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)(os.fspath(...))" .-> s9
    s6 -. "os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)(root)" .-> s10
    s6 -->|"WindowsDirectoryGuardError(...)"| s11
    s6 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(root_path.anchor)" .-> s12
    b0["filesystem_write claimed.rmdir"]
    s1 -. "filesystem_write claimed.rmdir" .-> b0
    b1["filesystem_write quarantine.rmdir"]
    s1 -. "filesystem_write quarantine.rmdir" .-> b1
    b2["filesystem_write os.rmdir"]
    s1 -. "filesystem_write os.rmdir" .-> b2
    b3["filesystem_write os.rmdir"]
    s1 -. "filesystem_write os.rmdir" .-> b3
    b4["filesystem_write os.rmdir"]
    s1 -. "filesystem_write os.rmdir" .-> b4
    b5["filesystem_write os.rmdir"]
    s1 -. "filesystem_write os.rmdir" .-> b5
    b6["filesystem_write os.rmdir"]
    s1 -. "filesystem_write os.rmdir" .-> b6
    b7["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b7
    click s1 "../modules/filesystem_guard.md"
    click s6 "../modules/filesystem_guard.md"
    click s7 "../modules/filesystem_guard.md"
    click s11 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
    class b7 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `remove_guarded_tree` | `path: Path`, `expected_identity: tuple[int, int] \| None`, `expected_manifest: GuardedTreeManifest \| None` | `os`, `os`, `os`, `os` | - | `none` |
| `Path (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)` | - | - | - | - |
| `target.is_absolute` | - | - | - | - |
| `OSError (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)` | - | - | - | - |
| `uuid.uuid4 (src/llm_wiki_cli/services…rd.py:remove_guarded_tree)` | - | - | - | - |
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
| remove_guarded_tree | Path (src/llm_wiki_cli/services…rd.py:remove_guarded_tree) | 1804 | `Path(path)` |
| remove_guarded_tree | target.is_absolute | 1805 | `target.is_absolute(data not statically known)` |
| remove_guarded_tree | OSError (src/llm_wiki_cli/services…rd.py:remove_guarded_tree) | 1806 | `OSError(...)` |
| remove_guarded_tree | uuid.uuid4 (src/llm_wiki_cli/services…rd.py:remove_guarded_tree) | 1808 | `uuid.uuid4(data not statically known)` |
| remove_guarded_tree | guard_windows_directory_chain | 1925 | `guard_windows_directory_chain(Path(...), ...)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.fspath(root)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 176 | `WindowsDirectoryGuardError(...)` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 179 | `Path(root_path.anchor)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `claimed.rmdir` | `remove_guarded_tree` | 1977 |
| filesystem_write | `quarantine.rmdir` | `remove_guarded_tree` | 1990 |
| filesystem_write | `os.rmdir` | `remove_guarded_tree` | 2194 |
| filesystem_write | `os.rmdir` | `remove_guarded_tree` | 2200 |
| filesystem_write | `os.rmdir` | `remove_guarded_tree` | 2219 |
| filesystem_write | `os.rmdir` | `remove_guarded_tree` | 2229 |
| filesystem_write | `os.rmdir` | `remove_guarded_tree` | 2241 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `remove_guarded_tree` | `target.is_absolute` | 1805 |
| external_call | `remove_guarded_tree` | `OSError` | 1806 |
| external_call | `remove_guarded_tree` | `uuid.uuid4` | 1808 |
| external_call | `guard_windows_directory_chain` | `os.path.abspath` | 174 |
| external_call | `guard_windows_directory_chain` | `os.fspath` | 174 |
| step_limit | `remove_guarded_tree` | `first 12 steps` | 0 |

## Behavior

This flow starts at `remove_guarded_tree` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
