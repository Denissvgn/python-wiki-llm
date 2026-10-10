# load_documentation_run

**Entry point:** `load_documentation_run` (`api`)
**Source:** [workspace](../modules/workspace.md)
**Modules touched:** [workspace](../modules/workspace.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_documentation_run
    participant p1 as documentation_run_path
    participant p2 as json.loads
    participant p3 as path.read_text
    participant p4 as DocumentationRunError
    participant p5 as DocumentationPersistedStateError
    participant p6 as isinstance
    participant p7 as DocumentationRun.from_dict
    participant p8 as str
    participant p9 as _resolve_workspace_root_argument
    participant p10 as Path (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p11 as os.path.abspath
    participant p12 as os.fspath
    participant p13 as Path(…).expanduser
    participant p14 as os.path.lexists (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p15 as requested.lstat
    participant p16 as DocumentationIntegrityError (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p17 as bool (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p18 as getattr (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p19 as stat.S_ISLNK (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p20 as stat.S_ISDIR (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p21 as requested.resolve
    participant p22 as _assert_existing_workspace_layout_safe
    p0->>p1: documentation_run_path
    p0-->>p2: json.loads(path.read_text(...))
    p0-->>p3: path.read_text(encoding='utf-8')
    p0-->>p4: DocumentationRunError(...)
    p0-->>p5: DocumentationPersistedStateError(...)
    p0-->>p6: isinstance(payload, dict)
    p0-->>p5: DocumentationPersistedStateError('Documentation run payload must be an object.')
    p0-->>p7: DocumentationRun.from_dict(payload)
    p0-->>p5: DocumentationPersistedStateError(str(...))
    p0-->>p8: str(exc)
    p1->>p9: _resolve_workspace_root_argument
    p9-->>p10: Path (src/llm_wiki_cli/services…ve_workspace_root_argument)(os.path.abspath(...))
    p9-->>p11: os.path.abspath(os.fspath(...))
    p9-->>p12: os.fspath(...)
    p9-->>p13: Path(…).expanduser
    p9-->>p10: Path (src/llm_wiki_cli/services…ve_workspace_root_argument)(workspace)
    p9-->>p14: os.path.lexists (src/llm_wiki_cli/services…ve_workspace_root_argument)(requested)
    p9-->>p15: requested.lstat
    p9-->>p16: DocumentationIntegrityError (src/llm_wiki_cli/services…ve_workspace_root_argument)(...)
    p9-->>p17: bool (src/llm_wiki_cli/services…ve_workspace_root_argument)(getattr(...))
    p9-->>p18: getattr (src/llm_wiki_cli/services…ve_workspace_root_argument)(entry_stat, 'st_reparse_tag', 0)
    p9-->>p17: bool (src/llm_wiki_cli/services…ve_workspace_root_argument)(...)
    p9-->>p18: getattr (src/llm_wiki_cli/services…ve_workspace_root_argument)(entry_stat, 'st_file_attributes', 0)
    p9-->>p19: stat.S_ISLNK (src/llm_wiki_cli/services…ve_workspace_root_argument)(entry_stat.st_mode)
    p9-->>p16: DocumentationIntegrityError (src/llm_wiki_cli/services…ve_workspace_root_argument)('Requested workspace root must not be a symlink or reparse point.')
    p9-->>p20: stat.S_ISDIR (src/llm_wiki_cli/services…ve_workspace_root_argument)(entry_stat.st_mode)
    p9-->>p16: DocumentationIntegrityError (src/llm_wiki_cli/services…ve_workspace_root_argument)('Requested workspace root must be a directory.')
    p9-->>p21: requested.resolve
    p9-->>p14: os.path.lexists (src/llm_wiki_cli/services…ve_workspace_root_argument)(resolved)
    p9->>p22: _assert_existing_workspace_layout_safe
```

> Call sequence diagram shows 30 of 92 interactions; 62 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 27 of 85 (58 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_existing_workspace_layout_safe` | 22 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_existing_workspace_layout_safe` | 22 | [src/llm_wiki_cli/services/documentation_run/workspace.py](../modules/workspace.md) | internal | 4 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_safe_workspace_directory` | 24 | - | unresolved | 14 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_workspace_control_tree_safe` | 41 | - | unresolved | 21 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_workspace_output_tree_safe` | 63 | - | unresolved | 21 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_documentation_run"]
    s2["2. documentation_run_path"]
    s3["3. _resolve_workspace_root_argument"]
    s4["4. Path (src/llm_wiki_cli/services…ve_workspace_root_argument)"]
    s5["5. os.path.abspath"]
    s6["6. os.fspath"]
    s7["7. Path(…).expanduser"]
    s8["8. Path (src/llm_wiki_cli/services…ve_workspace_root_argument)"]
    s9["9. os.path.lexists (src/llm_wiki_cli/services…ve_workspace_root_argument)"]
    s10["10. requested.lstat"]
    s11["11. DocumentationIntegrityError (src/llm_wiki_cli/services…ve_workspace_root_argument)"]
    s12["12. bool (src/llm_wiki_cli/services…ve_workspace_root_argument)"]
    s1 -->|"documentation_run_path(workspace)"| s2
    s2 -->|"_resolve_workspace_root_argument(workspace)"| s3
    s3 -. "Path (src/llm_wiki_cli/services…ve_workspace_root_argument)(os.path.abspath(...))" .-> s4
    s3 -. "os.path.abspath(os.fspath(...))" .-> s5
    s3 -. "os.fspath(...)" .-> s6
    s3 -. "Path(…).expanduser(data not statically known)" .-> s7
    s3 -. "Path (src/llm_wiki_cli/services…ve_workspace_root_argument)(workspace)" .-> s8
    s3 -. "os.path.lexists (src/llm_wiki_cli/services…ve_workspace_root_argument)(requested)" .-> s9
    s3 -. "requested.lstat(data not statically known)" .-> s10
    s3 -. "DocumentationIntegrityError (src/llm_wiki_cli/services…ve_workspace_root_argument)(...)" .-> s11
    s3 -. "bool (src/llm_wiki_cli/services…ve_workspace_root_argument)(getattr(...))" .-> s12
    b0["filesystem_read path.read_text"]
    s1 -. "filesystem_read path.read_text" .-> b0
    click s1 "../modules/workspace.md"
    click s2 "../modules/workspace.md"
    click s3 "../modules/workspace.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `load_documentation_run` | `workspace: str \| Path` | - | - | `DocumentationRun.from_dict(...)` |
| `documentation_run_path` | `workspace: str \| Path` | - | - | `...` |
| `_resolve_workspace_root_argument` | `workspace: str \| Path` | - | - | `resolved` |
| `Path (src/llm_wiki_cli/services…ve_workspace_root_argument)` | - | - | - | - |
| `os.path.abspath` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `Path(…).expanduser` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…ve_workspace_root_argument)` | - | - | - | - |
| `os.path.lexists (src/llm_wiki_cli/services…ve_workspace_root_argument)` | - | - | - | - |
| `requested.lstat` | - | - | - | - |
| `DocumentationIntegrityError (src/llm_wiki_cli/services…ve_workspace_root_argument)` | - | - | - | - |
| `bool (src/llm_wiki_cli/services…ve_workspace_root_argument)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_documentation_run | documentation_run_path | 14 | `documentation_run_path(workspace)` |
| documentation_run_path | _resolve_workspace_root_argument | 10 | `_resolve_workspace_root_argument(workspace)` |
| _resolve_workspace_root_argument | Path (src/llm_wiki_cli/services…ve_workspace_root_argument) | 102 | `Path(os.path.abspath(...))` |
| _resolve_workspace_root_argument | os.path.abspath | 102 | `os.path.abspath(os.fspath(...))` |
| _resolve_workspace_root_argument | os.fspath | 102 | `os.fspath(...)` |
| _resolve_workspace_root_argument | Path(…).expanduser | 102 | `Path(workspace).expanduser(data not statically known)` |
| _resolve_workspace_root_argument | Path (src/llm_wiki_cli/services…ve_workspace_root_argument) | 102 | `Path(workspace)` |
| _resolve_workspace_root_argument | os.path.lexists (src/llm_wiki_cli/services…ve_workspace_root_argument) | 103 | `os.path.lexists(requested)` |
| _resolve_workspace_root_argument | requested.lstat | 105 | `requested.lstat(data not statically known)` |
| _resolve_workspace_root_argument | DocumentationIntegrityError (src/llm_wiki_cli/services…ve_workspace_root_argument) | 107 | `DocumentationIntegrityError(...)` |
| _resolve_workspace_root_argument | bool (src/llm_wiki_cli/services…ve_workspace_root_argument) | 110 | `bool(getattr(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `path.read_text` | `load_documentation_run` | 16 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_resolve_workspace_root_argument` | `os.path.abspath` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `os.fspath` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `Path(workspace).expanduser` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `os.path.lexists` | 103 |
| unresolved_call | `_resolve_workspace_root_argument` | `requested.lstat` | 105 |
| unresolved_call | `_resolve_workspace_root_argument` | `DocumentationIntegrityError` | 107 |
| step_limit | `load_documentation_run` | `first 12 steps` | 0 |

## Behavior

This flow starts at `load_documentation_run` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
