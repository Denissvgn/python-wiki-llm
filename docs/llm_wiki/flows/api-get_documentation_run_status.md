# get_documentation_run_status

**Entry point:** `get_documentation_run_status` (`api`)
**Source:** [workspace](../modules/workspace.md)
**Modules touched:** [workspace](../modules/workspace.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_documentation_run_status
    participant p1 as _resolve_workspace_root_argument
    participant p2 as load_documentation_run
    participant p3 as _load_bound_runtime_policy
    participant p4 as str (src/llm_wiki_cli/services…_documentation_run_status)
    participant p5 as run.baseline.get (src/llm_wiki_cli/services…_documentation_run_status)
    participant p6 as DocumentationRunStatus
    participant p7 as bool (src/llm_wiki_cli/services…_documentation_run_status)
    participant p8 as run.source.get (src/llm_wiki_cli/services…_documentation_run_status)
    participant p9 as _next_actions
    participant p10 as tuple
    participant p11 as Path (src/llm_wiki_cli/services…e_workspace_root_argument)
    participant p12 as documentation_run_path
    participant p13 as _workspace_path
    participant p14 as os.path.abspath
    participant p15 as json.loads (src/llm_wiki_cli/services…py:load_documentation_run)
    participant p16 as _read_json
    participant p17 as os.fspath
    participant p18 as path.read_text (src/llm_wiki_cli/services…py:load_documentation_run)
    participant p19 as _require_exact_fields
    participant p20 as Path(…).expanduser (src/llm_wiki_cli/services…e_workspace_root_argument)
    participant p21 as DocumentationRunError
    participant p22 as payload.get
    participant p23 as DocumentationPersistedStateError
    participant p24 as DocumentationIntegrityError (src/llm_wiki_cli/services…load_bound_runtime_policy)
    participant p25 as os.path.lexists (src/llm_wiki_cli/services…e_workspace_root_argument)
    participant p26 as isinstance (src/llm_wiki_cli/services…py:load_documentation_run)
    participant p27 as requested.lstat
    p0->>p1: _resolve_workspace_root_argument
    p0->>p2: load_documentation_run
    p0->>p3: _load_bound_runtime_policy
    p0-->>p4: str (src/llm_wiki_cli/services…_documentation_run_status)(run.baseline.get(...))
    p0-->>p5: run.baseline.get (src/llm_wiki_cli/services…_documentation_run_status)('freshness', 'unverified')
    p0-->>p6: DocumentationRunStatus(…)
    p0-->>p7: bool (src/llm_wiki_cli/services…_documentation_run_status)(run.source.get(...))
    p0-->>p8: run.source.get (src/llm_wiki_cli/services…_documentation_run_status)('available')
    p0-->>p9: _next_actions(run)
    p0-->>p10: tuple(run.verdict_limitations)
    p1-->>p11: Path (src/llm_wiki_cli/services…e_workspace_root_argument)(os.path.abspath(...))
    p2->>p12: documentation_run_path
    p3->>p13: _workspace_path
    p1-->>p14: os.path.abspath(os.fspath(...))
    p2-->>p15: json.loads (src/llm_wiki_cli/services…py:load_documentation_run)(path.read_text(...))
    p3->>p16: _read_json
    p1-->>p17: os.fspath(...)
    p2-->>p18: path.read_text (src/llm_wiki_cli/services…py:load_documentation_run)(encoding='utf-8')
    p3-->>p19: _require_exact_fields(payload, allowed={...}, required={...}, label='runtime documentation policy')
    p1-->>p20: Path(…).expanduser (src/llm_wiki_cli/services…e_workspace_root_argument)
    p2-->>p21: DocumentationRunError(...)
    p3-->>p22: payload.get('schema_version')
    p1-->>p11: Path (src/llm_wiki_cli/services…e_workspace_root_argument)(workspace)
    p2-->>p23: DocumentationPersistedStateError(...)
    p3-->>p24: DocumentationIntegrityError (src/llm_wiki_cli/services…load_bound_runtime_policy)('Runtime documentation policy schema is unsupported or was changed.')
    p1-->>p25: os.path.lexists (src/llm_wiki_cli/services…e_workspace_root_argument)(requested)
    p2-->>p26: isinstance (src/llm_wiki_cli/services…py:load_documentation_run)(payload, dict)
    p3-->>p22: payload.get('portable_policy')
    p1-->>p27: requested.lstat
    p2-->>p23: DocumentationPersistedStateError('Documentation run payload must be an object.')
```

> Call sequence diagram shows 30 of 165 interactions; 135 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 24 of 150 (126 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_resolve_workspace_root_argument` | 2 | - | unresolved | 11 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_resolve_workspace_root_argument` | 2 | [src/llm_wiki_cli/services/documentation_run/workspace.py](../modules/workspace.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_existing_workspace_layout_safe` | 21 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_existing_workspace_layout_safe` | 21 | [src/llm_wiki_cli/services/documentation_run/workspace.py](../modules/workspace.md) | internal | 4 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_safe_workspace_directory` | 23 | - | unresolved | 14 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_workspace_control_tree_safe` | 40 | - | unresolved | 21 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_workspace_output_tree_safe` | 62 | - | unresolved | 21 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:documentation_run_path` | 85 | [src/llm_wiki_cli/services/documentation_run/workspace.py](../modules/workspace.md) | internal | 1 |
> Omission summary shows 8 of 16 groups; 8 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. get_documentation_run_status"]
    s2["2. _resolve_workspace_root_argument"]
    s3["3. Path (src/llm_wiki_cli/services…e_workspace_root_argument)"]
    s4["4. os.path.abspath"]
    s5["5. os.fspath"]
    s6["6. Path(…).expanduser (src/llm_wiki_cli/services…e_workspace_root_argument)"]
    s7["7. Path (src/llm_wiki_cli/services…e_workspace_root_argument)"]
    s8["8. os.path.lexists (src/llm_wiki_cli/services…e_workspace_root_argument)"]
    s9["9. requested.lstat"]
    s10["10. DocumentationIntegrityError (src/llm_wiki_cli/services…e_workspace_root_argument)"]
    s11["11. bool (src/llm_wiki_cli/services…e_workspace_root_argument)"]
    s12["12. getattr (src/llm_wiki_cli/services…e_workspace_root_argument)"]
    s1 -->|"_resolve_workspace_root_argument(workspace)"| s2
    s2 -. "Path (src/llm_wiki_cli/services…e_workspace_root_argument)(os.path.abspath(...))" .-> s3
    s2 -. "os.path.abspath(os.fspath(...))" .-> s4
    s2 -. "os.fspath(...)" .-> s5
    s2 -. "Path(…).expanduser (src/llm_wiki_cli/services…e_workspace_root_argument)(data not statically known)" .-> s6
    s2 -. "Path (src/llm_wiki_cli/services…e_workspace_root_argument)(workspace)" .-> s7
    s2 -. "os.path.lexists (src/llm_wiki_cli/services…e_workspace_root_argument)(requested)" .-> s8
    s2 -. "requested.lstat(data not statically known)" .-> s9
    s2 -. "DocumentationIntegrityError (src/llm_wiki_cli/services…e_workspace_root_argument)(...)" .-> s10
    s2 -. "bool (src/llm_wiki_cli/services…e_workspace_root_argument)(getattr(...))" .-> s11
    s2 -. "getattr (src/llm_wiki_cli/services…e_workspace_root_argument)(entry_stat, 'st_reparse_tag', 0)" .-> s12
    click s1 "../modules/workspace.md"
    click s2 "../modules/workspace.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_documentation_run_status` | `workspace: str \| Path` | - | - | `DocumentationRunStatus(...)` |
| `_resolve_workspace_root_argument` | `workspace: str \| Path` | - | - | `resolved` |
| `Path (src/llm_wiki_cli/services…e_workspace_root_argument)` | - | - | - | - |
| `os.path.abspath` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `Path(…).expanduser (src/llm_wiki_cli/services…e_workspace_root_argument)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…e_workspace_root_argument)` | - | - | - | - |
| `os.path.lexists (src/llm_wiki_cli/services…e_workspace_root_argument)` | - | - | - | - |
| `requested.lstat` | - | - | - | - |
| `DocumentationIntegrityError (src/llm_wiki_cli/services…e_workspace_root_argument)` | - | - | - | - |
| `bool (src/llm_wiki_cli/services…e_workspace_root_argument)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/services…e_workspace_root_argument)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_documentation_run_status | _resolve_workspace_root_argument | 74 | `_resolve_workspace_root_argument(workspace)` |
| _resolve_workspace_root_argument | Path (src/llm_wiki_cli/services…e_workspace_root_argument) | 102 | `Path(os.path.abspath(...))` |
| _resolve_workspace_root_argument | os.path.abspath | 102 | `os.path.abspath(os.fspath(...))` |
| _resolve_workspace_root_argument | os.fspath | 102 | `os.fspath(...)` |
| _resolve_workspace_root_argument | Path(…).expanduser (src/llm_wiki_cli/services…e_workspace_root_argument) | 102 | `Path(workspace).expanduser(data not statically known)` |
| _resolve_workspace_root_argument | Path (src/llm_wiki_cli/services…e_workspace_root_argument) | 102 | `Path(workspace)` |
| _resolve_workspace_root_argument | os.path.lexists (src/llm_wiki_cli/services…e_workspace_root_argument) | 103 | `os.path.lexists(requested)` |
| _resolve_workspace_root_argument | requested.lstat | 105 | `requested.lstat(data not statically known)` |
| _resolve_workspace_root_argument | DocumentationIntegrityError (src/llm_wiki_cli/services…e_workspace_root_argument) | 107 | `DocumentationIntegrityError(...)` |
| _resolve_workspace_root_argument | bool (src/llm_wiki_cli/services…e_workspace_root_argument) | 110 | `bool(getattr(...))` |
| _resolve_workspace_root_argument | getattr (src/llm_wiki_cli/services…e_workspace_root_argument) | 110 | `getattr(entry_stat, 'st_reparse_tag', 0)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_resolve_workspace_root_argument` | `os.path.abspath` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `os.fspath` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `Path(workspace).expanduser` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `os.path.lexists` | 103 |
| unresolved_call | `_resolve_workspace_root_argument` | `requested.lstat` | 105 |
| unresolved_call | `_resolve_workspace_root_argument` | `DocumentationIntegrityError` | 107 |
| unresolved_call | `_resolve_workspace_root_argument` | `getattr` | 110 |
| step_limit | `get_documentation_run_status` | `first 12 steps` | 0 |

## Behavior

This flow starts at `get_documentation_run_status` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
