# obsidian

**Entry point:** `run` (`cli`)
**Source:** [obsidian_cmd](../modules/obsidian_cmd.md)
**Modules touched:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), [config](../modules/config.md), and 30 more

**Complete modules touched:**

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [inventory_cache](../modules/inventory_cache.md)
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
- [knowledge_projection](../modules/knowledge_projection.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [obsidian](../modules/obsidian.md)
- [obsidian_cmd](../modules/obsidian_cmd.md)
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [section_ownership](../modules/section_ownership.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as validate_path
    participant p3 as PathValidationError
    participant p4 as resolve
    participant p5 as cwd
    participant p6 as relative_to
    participant p7 as bool
    participant p8 as validate_source_root
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
    p0->>p2: validate_path
    p2->>p3: PathValidationError
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p6: relative_to
    p2->>p3: PathValidationError
    p0-->>p7: bool
    p0-->>p1: getattr
    p0->>p8: validate_source_root
    p8->>p2: validate_path
    p8-->>p9: expanduser
    p8-->>p10: Path
    p8-->>p11: is_absolute
    p8-->>p5: cwd
    p8-->>p4: resolve
    p8->>p3: PathValidationError
    p8-->>p12: is_dir
    p8->>p3: PathValidationError
    p8-->>p10: Path
    p8-->>p13: abspath
    p8->>p14: windows_current_user_sid
    p14->>p15: WindowsSecurityGuardError
    p14->>p16: _current_windows_user_sid
    p16-->>p17: WinDLL
```

> Call sequence diagram shows 30 of 2653 interactions; 2623 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

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
    s6["6. validate_path"]
    s7["7. PathValidationError"]
    s8["8. resolve"]
    s9["9. cwd"]
    s10["10. resolve"]
    s11["11. cwd"]
    s12["12. relative_to"]
    s1 -. "getattr(args, 'obsidian_action', None)" .-> s2
    s1 -. "getattr(args, 'format', 'text')" .-> s3
    s1 -. "getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s4
    s1 -. "getattr(args, 'src_dir', '.')" .-> s5
    s1 -->|"validate_path(wiki_dir, '--wiki-dir')"| s6
    s6 -->|"PathValidationError(...)"| s7
    s6 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s8
    s6 -. "Path.cwd(data not statically known)" .-> s9
    s6 -. "Path.cwd().resolve(data not statically known)" .-> s10
    s6 -. "Path.cwd(data not statically known)" .-> s11
    s6 -. "resolved.relative_to(cwd)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    click s1 "../modules/obsidian_cmd.md"
    click s6 "../modules/config.md"
    click s7 "../modules/config.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `DEFAULT_WIKI_DIR`, `DEFAULT_NOTES_DIR`, `DEFAULT_WIKI_DIR`, `DEFAULT_PLUGIN_SOURCE`, `ObsidianError`, `sys`, `sys` | - | `none`, `none`, `none` |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `relative_to` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 74 | `getattr(args, 'obsidian_action', None)` |
| run | getattr | 75 | `getattr(args, 'format', 'text')` |
| run | getattr | 79 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | getattr | 80 | `getattr(args, 'src_dir', '.')` |
| run | validate_path | 81 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 132 | `PathValidationError(...)` |
| validate_path | resolve | 133 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 133 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 134 | `Path.cwd().resolve(data not statically known)` |
| validate_path | cwd | 134 | `Path.cwd(data not statically known)` |
| validate_path | relative_to | 136 | `resolved.relative_to(cwd)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 132 |
| output | `print` | `run` | 135 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 74 |
| unresolved_call | `run` | `getattr` | 75 |
| unresolved_call | `run` | `getattr` | 79 |
| unresolved_call | `run` | `getattr` | 80 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 133 |
| external_call | `validate_path` | `Path.cwd` | 133 |
| external_call | `validate_path` | `Path.cwd().resolve` | 134 |
| external_call | `validate_path` | `Path.cwd` | 134 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 136 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

Dispatches one of three explicit actions. `export` validates the current source
selection and writes or previews a derived vault mirror; `check` compares an
existing mirror and exits nonzero on mismatches; `install-plugin` copies the
packaged plugin into the vault. Optional knowledge metadata is projected under
the selected disclosure profile before export, and the canonical wiki is never
replaced by mirror content.
