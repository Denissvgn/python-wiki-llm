# migrate

**Entry point:** `run` (`cli`)
**Source:** [migrate_cmd](../modules/migrate_cmd.md)
**Modules touched:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), [config](../modules/config.md), and 28 more

**Complete modules touched:**

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [imports](../modules/imports.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [migrate_cmd](../modules/migrate_cmd.md)
- [packages](../modules/packages.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [resource_diagnostics](../modules/resource_diagnostics.md)
- [section_ownership](../modules/section_ownership.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as Path
    participant p3 as bool
    participant p4 as validate_source_root
    participant p5 as validate_path
    participant p6 as PathValidationError
    participant p7 as resolve
    participant p8 as cwd
    participant p9 as relative_to
    participant p10 as expanduser
    participant p11 as is_absolute
    participant p12 as is_dir
    participant p13 as abspath
    participant p14 as windows_current_user_sid
    participant p15 as WindowsSecurityGuardError
    p0-->>p1: getattr
    p0-->>p2: Path
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p3: bool
    p0-->>p1: getattr
    p0->>p4: validate_source_root
    p4->>p5: validate_path
    p5->>p6: PathValidationError
    p5-->>p7: resolve
    p5-->>p8: cwd
    p5-->>p7: resolve
    p5-->>p8: cwd
    p5-->>p9: relative_to
    p5->>p6: PathValidationError
    p4-->>p10: expanduser
    p4-->>p2: Path
    p4-->>p11: is_absolute
    p4-->>p8: cwd
    p4-->>p7: resolve
    p4->>p6: PathValidationError
    p4-->>p12: is_dir
    p4->>p6: PathValidationError
    p4-->>p2: Path
    p4-->>p13: abspath
    p4->>p14: windows_current_user_sid
    p14->>p15: WindowsSecurityGuardError
```

> Call sequence diagram shows 30 of 3212 interactions; 3182 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. Path"]
    s4["4. getattr"]
    s5["5. getattr"]
    s6["6. getattr"]
    s7["7. getattr"]
    s8["8. getattr"]
    s9["9. bool"]
    s10["10. getattr"]
    s11["11. validate_source_root"]
    s12["12. validate_path"]
    s1 -. "getattr(args, 'src_dir', '.')" .-> s2
    s1 -. "Path(getattr(...))" .-> s3
    s1 -. "getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s4
    s1 -. "getattr(args, 'dry_run', False)" .-> s5
    s1 -. "getattr(args, 'chunk_size', None)" .-> s6
    s1 -. "getattr(args, 'chunk', None)" .-> s7
    s1 -. "getattr(args, 'plan_chunks', False)" .-> s8
    s1 -. "bool(getattr(...))" .-> s9
    s1 -. "getattr(args, 'allow_external_src', False)" .-> s10
    s1 -->|"validate_source_root(src_dir, '--src-dir', allow_external=allow_external)"| s11
    s11 -->|"validate_path(path, label)"| s12
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
    click s1 "../modules/migrate_cmd.md"
    click s11 "../modules/config.md"
    click s12 "../modules/config.md"
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
| `run` | `args` | `DEFAULT_WIKI_DIR`, `sys`, `sys`, `sys` | - | `none`, `none`, `none` |
| `getattr` | - | - | - | - |
| `Path` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `bool` | - | - | - | - |
| `getattr` | - | - | - | - |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 1631 | `getattr(args, 'src_dir', '.')` |
| run | Path | 1632 | `Path(getattr(...))` |
| run | getattr | 1632 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | getattr | 1633 | `getattr(args, 'dry_run', False)` |
| run | getattr | 1634 | `getattr(args, 'chunk_size', None)` |
| run | getattr | 1635 | `getattr(args, 'chunk', None)` |
| run | getattr | 1636 | `getattr(args, 'plan_chunks', False)` |
| run | bool | 1637 | `bool(getattr(...))` |
| run | getattr | 1637 | `getattr(args, 'allow_external_src', False)` |
| run | validate_source_root | 1638 | `validate_source_root(src_dir, '--src-dir', allow_external=allow_external)` |
| validate_source_root | validate_path | 156 | `validate_path(path, label)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 1648 |
| output | `print` | `run` | 1652 |
| output | `print` | `run` | 1655 |
| output | `print` | `run` | 1656 |
| output | `print` | `run` | 1665 |
| output | `print` | `run` | 1673 |
| output | `print` | `run` | 1679 |
| output | `print` | `run` | 1684 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 1631 |
| unresolved_call | `run` | `getattr` | 1632 |
| unresolved_call | `run` | `getattr` | 1633 |
| unresolved_call | `run` | `getattr` | 1634 |
| unresolved_call | `run` | `getattr` | 1635 |
| unresolved_call | `run` | `getattr` | 1636 |
| unresolved_call | `run` | `getattr` | 1637 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
