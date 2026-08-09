# team

**Entry point:** `run` (`cli`)
**Source:** [team_cmd](../modules/team_cmd.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [extraction_jobs](../modules/extraction_jobs.md), [extraction_service](../modules/extraction_service.md), and 10 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [resource_diagnostics](../modules/resource_diagnostics.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [team_cmd](../modules/team_cmd.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as _run_init
    participant p3 as validate_path
    participant p4 as PathValidationError
    participant p5 as resolve
    participant p6 as cwd
    participant p7 as relative_to
    participant p8 as team_config_path
    participant p9 as exists
    participant p10 as print
    participant p11 as write_default_team_config
    participant p12 as _run_check
    participant p13 as bool
    participant p14 as validate_source_root
    participant p15 as expanduser
    participant p16 as Path
    participant p17 as is_absolute
    p0-->>p1: getattr
    p0->>p2: _run_init
    p2-->>p1: getattr
    p2->>p3: validate_path
    p3->>p4: PathValidationError
    p3-->>p5: resolve
    p3-->>p6: cwd
    p3-->>p5: resolve
    p3-->>p6: cwd
    p3-->>p7: relative_to
    p3->>p4: PathValidationError
    p2-->>p8: team_config_path
    p2-->>p9: exists
    p2-->>p10: print
    p2-->>p11: write_default_team_config
    p2-->>p10: print
    p0->>p12: _run_check
    p12-->>p1: getattr
    p12-->>p1: getattr
    p12-->>p1: getattr
    p12-->>p13: bool
    p12-->>p1: getattr
    p12->>p14: validate_source_root
    p14->>p3: validate_path
    p14-->>p15: expanduser
    p14-->>p16: Path
    p14-->>p17: is_absolute
    p14-->>p6: cwd
    p14-->>p5: resolve
    p14->>p4: PathValidationError
```

> Call sequence diagram shows 30 of 929 interactions; 899 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. _run_init"]
    s4["4. getattr"]
    s5["5. validate_path"]
    s6["6. PathValidationError"]
    s7["7. resolve"]
    s8["8. cwd"]
    s9["9. resolve"]
    s10["10. cwd"]
    s11["11. relative_to"]
    s12["12. PathValidationError"]
    s1 -. "getattr(args, 'team_action', None)" .-> s2
    s1 -->|"_run_init(args)"| s3
    s3 -. "getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s4
    s3 -->|"validate_path(wiki_dir, '--wiki-dir')"| s5
    s5 -->|"PathValidationError(...)"| s6
    s5 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s7
    s5 -. "Path.cwd(data not statically known)" .-> s8
    s5 -. "Path.cwd().resolve(data not statically known)" .-> s9
    s5 -. "Path.cwd(data not statically known)" .-> s10
    s5 -. "resolved.relative_to(cwd)" .-> s11
    s5 -->|"PathValidationError(...)"| s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s3 -. "output print" .-> b1
    b2["output print"]
    s3 -. "output print" .-> b2
    click s1 "../modules/team_cmd.md"
    click s3 "../modules/team_cmd.md"
    click s5 "../modules/config.md"
    click s6 "../modules/config.md"
    click s12 "../modules/config.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `sys` | - | - |
| `getattr` | - | - | - | - |
| `_run_init` | `args` | `DEFAULT_WIKI_DIR` | - | `none` |
| `getattr` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `relative_to` | - | - | - | - |
| `PathValidationError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 192 | `getattr(args, 'team_action', None)` |
| run | _run_init | 194 | `_run_init(args)` |
| _run_init | getattr | 59 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| _run_init | validate_path | 60 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 128 | `PathValidationError(...)` |
| validate_path | resolve | 131 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 131 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 132 | `Path.cwd().resolve(data not statically known)` |
| validate_path | cwd | 132 | `Path.cwd(data not statically known)` |
| validate_path | relative_to | 134 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 136 | `PathValidationError(...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 200 |
| output | `print` | `_run_init` | 63 |
| output | `print` | `_run_init` | 66 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 192 |
| unresolved_call | `_run_init` | `getattr` | 59 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 131 |
| external_call | `validate_path` | `Path.cwd` | 131 |
| external_call | `validate_path` | `Path.cwd().resolve` | 132 |
| external_call | `validate_path` | `Path.cwd` | 132 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 134 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
