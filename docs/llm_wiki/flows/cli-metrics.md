# metrics

**Entry point:** `run` (`cli`)
**Source:** [metrics_cmd](../modules/metrics_cmd.md)
**Modules touched:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [config](../modules/config.md), [documentation_queries](../modules/documentation_queries.md), and 15 more

**Complete modules touched:**

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [lint_service](../modules/lint_service.md)
- [metrics](../modules/metrics.md)
- [metrics_cmd](../modules/metrics_cmd.md)
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as bool
    participant p3 as validate_source_root
    participant p4 as validate_path
    participant p5 as PathValidationError
    participant p6 as resolve
    participant p7 as cwd
    participant p8 as relative_to
    participant p9 as expanduser
    participant p10 as Path
    participant p11 as is_absolute
    participant p12 as is_dir
    participant p13 as abspath
    participant p14 as windows_current_user_sid
    participant p15 as WindowsSecurityGuardError
    participant p16 as _current_windows_user_sid
    participant p17 as WinDLL
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p2: bool
    p0-->>p1: getattr
    p0->>p3: validate_source_root
    p3->>p4: validate_path
    p4->>p5: PathValidationError
    p4-->>p6: resolve
    p4-->>p7: cwd
    p4-->>p6: resolve
    p4-->>p7: cwd
    p4-->>p8: relative_to
    p4->>p5: PathValidationError
    p3-->>p9: expanduser
    p3-->>p10: Path
    p3-->>p11: is_absolute
    p3-->>p7: cwd
    p3-->>p6: resolve
    p3->>p5: PathValidationError
    p3-->>p12: is_dir
    p3->>p5: PathValidationError
    p3-->>p10: Path
    p3-->>p13: abspath
    p3->>p14: windows_current_user_sid
    p14->>p15: WindowsSecurityGuardError
    p14->>p16: _current_windows_user_sid
    p16-->>p17: WinDLL
    p16-->>p17: WinDLL
```

> Call sequence diagram shows 30 of 842 interactions; 812 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. getattr"]
    s4["4. getattr"]
    s5["5. getattr"]
    s6["6. bool"]
    s7["7. getattr"]
    s8["8. validate_source_root"]
    s9["9. validate_path"]
    s10["10. PathValidationError"]
    s11["11. resolve"]
    s12["12. cwd"]
    s1 -. "getattr(args, 'src_dir', '.')" .-> s2
    s1 -. "getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s3
    s1 -. "getattr(args, 'last', '30d')" .-> s4
    s1 -. "getattr(args, 'format', 'text')" .-> s5
    s1 -. "bool(getattr(...))" .-> s6
    s1 -. "getattr(args, 'allow_external_src', False)" .-> s7
    s1 -->|"validate_source_root(src_dir, '--src-dir', allow_external=allow_external)"| s8
    s8 -->|"validate_path(path, label)"| s9
    s9 -->|"PathValidationError(...)"| s10
    s9 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s11
    s9 -. "Path.cwd(data not statically known)" .-> s12
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
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `bool` | - | - | - | - |
| `getattr` | - | - | - | - |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 110 | `getattr(args, 'src_dir', '.')` |
| run | getattr | 111 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | getattr | 112 | `getattr(args, 'last', '30d')` |
| run | getattr | 113 | `getattr(args, 'format', 'text')` |
| run | bool | 115 | `bool(getattr(...))` |
| run | getattr | 115 | `getattr(args, 'allow_external_src', False)` |
| run | validate_source_root | 116 | `validate_source_root(src_dir, '--src-dir', allow_external=allow_external)` |
| validate_source_root | validate_path | 158 | `validate_path(path, label)` |
| validate_path | PathValidationError | 132 | `PathValidationError(...)` |
| validate_path | resolve | 133 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 133 | `Path.cwd(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 134 |
| output | `print` | `run` | 136 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 110 |
| unresolved_call | `run` | `getattr` | 111 |
| unresolved_call | `run` | `getattr` | 112 |
| unresolved_call | `run` | `getattr` | 113 |
| unresolved_call | `run` | `getattr` | 115 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 133 |
| external_call | `validate_path` | `Path.cwd` | 133 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
