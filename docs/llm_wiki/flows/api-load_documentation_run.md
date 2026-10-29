# load_documentation_run

**Entry point:** `load_documentation_run` (`api`)
**Source:** [workspace](../modules/workspace.md)
**Modules touched:** [workspace](../modules/workspace.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_documentation_run
    participant p1 as documentation_run_path
    participant p2 as _resolve_workspace_root_argument
    participant p3 as _assert_existing_workspace_layout_safe
    participant p4 as _assert_safe_workspace_directory
    participant p5 as _assert_workspace_control_tree_safe
    participant p6 as _assert_workspace_output_tree_safe
    participant p7 as json.loads
    participant p8 as path.read_text
    participant p9 as DocumentationRunError
    participant p10 as DocumentationPersistedStateError
    participant p11 as isinstance
    participant p12 as DocumentationRun.from_dict
    participant p13 as str
    participant p14 as Path (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p15 as os.path.abspath
    participant p16 as os.fspath
    participant p17 as Path(…).expanduser
    participant p18 as os.path.lexists (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p19 as requested.lstat
    participant p20 as DocumentationIntegrityError (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p21 as bool (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p22 as getattr (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p23 as stat.S_ISLNK (src/llm_wiki_cli/services…ve_workspace_root_argument)
    participant p24 as stat.S_ISDIR (src/llm_wiki_cli/services…ve_workspace_root_argument)
    p0->>p1: documentation_run_path
    p1->>p2: _resolve_workspace_root_argument
    p2->>p3: _assert_existing_workspace_layout_safe
    p3->>p4: _assert_safe_workspace_directory
    p3->>p5: _assert_workspace_control_tree_safe
    p3->>p6: _assert_workspace_output_tree_safe
    p0-->>p7: json.loads(path.read_text(...))
    p0-->>p8: path.read_text(encoding='utf-8')
    p0-->>p9: DocumentationRunError(...)
    p0-->>p10: DocumentationPersistedStateError(...)
    p0-->>p11: isinstance(payload, dict)
    p0-->>p10: DocumentationPersistedStateError('Documentation run payload must be an object.')
    p0-->>p12: DocumentationRun.from_dict(payload)
    p0-->>p10: DocumentationPersistedStateError(str(...))
    p0-->>p13: str(exc)
    p2-->>p14: Path (src/llm_wiki_cli/services…ve_workspace_root_argument)(os.path.abspath(...))
    p2-->>p15: os.path.abspath(os.fspath(...))
    p2-->>p16: os.fspath(...)
    p2-->>p17: Path(…).expanduser
    p2-->>p14: Path (src/llm_wiki_cli/services…ve_workspace_root_argument)(workspace)
    p2-->>p18: os.path.lexists (src/llm_wiki_cli/services…ve_workspace_root_argument)(requested)
    p2-->>p19: requested.lstat
    p2-->>p20: DocumentationIntegrityError (src/llm_wiki_cli/services…ve_workspace_root_argument)(...)
    p2-->>p21: bool (src/llm_wiki_cli/services…ve_workspace_root_argument)(getattr(...))
    p2-->>p22: getattr (src/llm_wiki_cli/services…ve_workspace_root_argument)(entry_stat, 'st_reparse_tag', 0)
    p2-->>p21: bool (src/llm_wiki_cli/services…ve_workspace_root_argument)(...)
    p2-->>p22: getattr (src/llm_wiki_cli/services…ve_workspace_root_argument)(entry_stat, 'st_file_attributes', 0)
    p2-->>p23: stat.S_ISLNK (src/llm_wiki_cli/services…ve_workspace_root_argument)(entry_stat.st_mode)
    p2-->>p20: DocumentationIntegrityError (src/llm_wiki_cli/services…ve_workspace_root_argument)('Requested workspace root must not be a symlink or reparse point.')
    p2-->>p24: stat.S_ISDIR (src/llm_wiki_cli/services…ve_workspace_root_argument)(entry_stat.st_mode)
```

> Call sequence diagram shows 30 of 92 interactions; 62 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 24 of 85 (61 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_resolve_workspace_root_argument` | 3 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_existing_workspace_layout_safe` | 22 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_safe_workspace_directory` | 24 | - | unresolved | 14 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_existing_workspace_layout_safe` | 22 | [src/llm_wiki_cli/services/documentation_run/workspace.py](../modules/workspace.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_workspace_control_tree_safe` | 41 | - | unresolved | 21 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_workspace_output_tree_safe` | 63 | - | unresolved | 21 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 8; effect analysis evaluated: 8, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

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
