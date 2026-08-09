# status

**Entry point:** `run` (`cli`)
**Source:** [status_cmd](../modules/status_cmd.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [filesystem_guard](../modules/filesystem_guard.md), [io](../modules/io.md), and 20 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [section_ownership](../modules/section_ownership.md)
- [skills](../modules/skills.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [status_cmd](../modules/status_cmd.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

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
    participant p18 as POINTER
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
    p16-->>p18: POINTER
    p16-->>p18: POINTER
```

> Call sequence diagram shows 30 of 1119 interactions; 1089 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. getattr"]
    s4["4. bool"]
    s5["5. getattr"]
    s6["6. validate_source_root"]
    s7["7. validate_path"]
    s8["8. PathValidationError"]
    s9["9. resolve"]
    s10["10. cwd"]
    s11["11. resolve"]
    s12["12. cwd"]
    s1 -. "getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s2
    s1 -. "getattr(args, 'src_dir', '.')" .-> s3
    s1 -. "bool(getattr(...))" .-> s4
    s1 -. "getattr(args, 'allow_external_src', False)" .-> s5
    s1 -->|"validate_source_root(src_dir, '--src-dir', allow_external=allow_external)"| s6
    s6 -->|"validate_path(path, label)"| s7
    s7 -->|"PathValidationError(...)"| s8
    s7 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s9
    s7 -. "Path.cwd(data not statically known)" .-> s10
    s7 -. "Path.cwd().resolve(data not statically known)" .-> s11
    s7 -. "Path.cwd(data not statically known)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["output print"]
    s1 -. "output print" .-> b4
    b5["output print"]
    s1 -. "output print" .-> b5
    b6["output print"]
    s1 -. "output print" .-> b6
    b7["output print"]
    s1 -. "output print" .-> b7
    click s1 "../modules/status_cmd.md"
    click s6 "../modules/config.md"
    click s7 "../modules/config.md"
    click s8 "../modules/config.md"
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
| `run` | `args` | `DEFAULT_WIKI_DIR`, `IDE_AGENTS` | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `bool` | - | - | - | - |
| `getattr` | - | - | - | - |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 89 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | getattr | 90 | `getattr(args, 'src_dir', '.')` |
| run | bool | 91 | `bool(getattr(...))` |
| run | getattr | 91 | `getattr(args, 'allow_external_src', False)` |
| run | validate_source_root | 92 | `validate_source_root(src_dir, '--src-dir', allow_external=allow_external)` |
| validate_source_root | validate_path | 156 | `validate_path(path, label)` |
| validate_path | PathValidationError | 128 | `PathValidationError(...)` |
| validate_path | resolve | 131 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 131 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 132 | `Path.cwd().resolve(data not statically known)` |
| validate_path | cwd | 132 | `Path.cwd(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 102 |
| output | `print` | `run` | 103 |
| output | `print` | `run` | 107 |
| output | `print` | `run` | 111 |
| output | `print` | `run` | 112 |
| output | `print` | `run` | 114 |
| output | `print` | `run` | 128 |
| output | `print` | `run` | 130 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 89 |
| unresolved_call | `run` | `getattr` | 90 |
| unresolved_call | `run` | `getattr` | 91 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 131 |
| external_call | `validate_path` | `Path.cwd` | 131 |
| external_call | `validate_path` | `Path.cwd().resolve` | 132 |
| external_call | `validate_path` | `Path.cwd` | 132 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
