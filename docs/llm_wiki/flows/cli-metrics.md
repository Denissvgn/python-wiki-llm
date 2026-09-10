# metrics

**Entry point:** `run` (`cli`)
**Source:** [metrics_cmd](../modules/metrics_cmd.md)
**Modules touched:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [config](../modules/config.md), [documentation_queries](../modules/documentation_queries.md), and 20 more

**Complete modules touched:**

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [imports](../modules/imports.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [lint_service](../modules/lint_service.md)
- [metrics](../modules/metrics.md)
- [metrics_cmd](../modules/metrics_cmd.md)
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_contracts](../modules/python_contracts.md)
- [python_observations](../modules/python_observations.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)
    participant p2 as bool (src/llm_wiki_cli/commands/metrics_cmd.py:run)
    participant p3 as validate_source_root
    participant p4 as validate_path
    participant p5 as PathValidationError
    participant p6 as (…).resolve
    participant p7 as Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    participant p8 as Path.cwd().resolve
    participant p9 as resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    participant p10 as Path(…).expanduser
    participant p11 as Path (src/llm_wiki_cli/config.py:validate_source_root)
    participant p12 as candidate.is_absolute
    participant p13 as Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    participant p14 as candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    participant p15 as resolved.is_dir
    participant p16 as os.path.abspath (src/llm_wiki_cli/config.py:validate_source_root)
    participant p17 as windows_current_user_sid
    participant p18 as WindowsSecurityGuardError
    participant p19 as _current_windows_user_sid
    participant p20 as ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)
    p0-->>p2: bool (src/llm_wiki_cli/commands/metrics_cmd.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)
    p0->>p3: validate_source_root
    p3->>p4: validate_path
    p4->>p5: PathValidationError
    p4-->>p6: (…).resolve
    p4-->>p7: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p4-->>p8: Path.cwd().resolve
    p4-->>p7: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p4-->>p9: resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    p4->>p5: PathValidationError
    p3-->>p10: Path(…).expanduser
    p3-->>p11: Path (src/llm_wiki_cli/config.py:validate_source_root)
    p3-->>p12: candidate.is_absolute
    p3-->>p13: Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    p3-->>p14: candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    p3->>p5: PathValidationError
    p3-->>p15: resolved.is_dir
    p3->>p5: PathValidationError
    p3-->>p11: Path (src/llm_wiki_cli/config.py:validate_source_root)
    p3-->>p16: os.path.abspath (src/llm_wiki_cli/config.py:validate_source_root)
    p3->>p17: windows_current_user_sid
    p17->>p18: WindowsSecurityGuardError
    p17->>p19: _current_windows_user_sid
    p19-->>p20: ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)
    p19-->>p20: ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)
```

> Call sequence diagram shows 30 of 909 interactions; 879 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)"]
    s3["3. getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)"]
    s4["4. getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)"]
    s5["5. getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)"]
    s6["6. bool (src/llm_wiki_cli/commands/metrics_cmd.py:run)"]
    s7["7. getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)"]
    s8["8. validate_source_root"]
    s9["9. validate_path"]
    s10["10. PathValidationError"]
    s11["11. (…).resolve"]
    s12["12. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s1 -. "getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)(args, 'src_dir', '.')" .-> s2
    s1 -. "getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s3
    s1 -. "getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)(args, 'last', '30d')" .-> s4
    s1 -. "getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)(args, 'format', 'text')" .-> s5
    s1 -. "bool (src/llm_wiki_cli/commands/metrics_cmd.py:run)(getattr(...))" .-> s6
    s1 -. "getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)(args, 'allow_external_src', False)" .-> s7
    s1 -->|"validate_source_root(src_dir, '--src-dir', allow_external=allow_external)"| s8
    s8 -->|"validate_path(path, label)"| s9
    s9 -->|"PathValidationError(...)"| s10
    s9 -. "(…).resolve(data not statically known)" .-> s11
    s9 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    click s1 "../modules/metrics_cmd.md"
    click s8 "../modules/config.md"
    click s9 "../modules/config.md"
    click s10 "../modules/config.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `DEFAULT_WIKI_DIR` | - | - |
| `getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)` | - | - | - | - |
| `bool (src/llm_wiki_cli/commands/metrics_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run)` | - | - | - | - |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run) | 110 | `getattr(args, 'src_dir', '.')` |
| run | getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run) | 111 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run) | 112 | `getattr(args, 'last', '30d')` |
| run | getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run) | 113 | `getattr(args, 'format', 'text')` |
| run | bool (src/llm_wiki_cli/commands/metrics_cmd.py:run) | 115 | `bool(getattr(...))` |
| run | getattr (src/llm_wiki_cli/commands/metrics_cmd.py:run) | 115 | `getattr(args, 'allow_external_src', False)` |
| run | validate_source_root | 116 | `validate_source_root(src_dir, '--src-dir', allow_external=allow_external)` |
| validate_source_root | validate_path | 158 | `validate_path(path, label)` |
| validate_path | PathValidationError | 132 | `PathValidationError(...)` |
| validate_path | (…).resolve | 133 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 133 | `Path.cwd(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 134 |
| output | `print` | `run` | 136 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 110 |
| external_call | `run` | `getattr` | 111 |
| external_call | `run` | `getattr` | 112 |
| external_call | `run` | `getattr` | 113 |
| external_call | `run` | `getattr` | 115 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 133 |
| external_call | `validate_path` | `Path.cwd` | 133 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
