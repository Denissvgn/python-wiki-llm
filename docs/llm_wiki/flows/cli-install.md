# install

**Entry point:** `run` (`cli`)
**Source:** [install_cmd](../modules/install_cmd.md)
**Modules touched:** [config](../modules/config.md), [install_cmd](../modules/install_cmd.md), [io](../modules/io.md), [plugins](../modules/plugins.md), and 2 more

**Complete modules touched:**

- [config](../modules/config.md)
- [install_cmd](../modules/install_cmd.md)
- [io](../modules/io.md)
- [plugins](../modules/plugins.md)
- [services_schema](../modules/services_schema.md)
- [validation](../modules/validation.md)

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
    participant p7 as install_plugin
    participant p8 as resolve_plugin_ref
    participant p9 as expanduser
    participant p10 as Path
    participant p11 as exists
    participant p12 as PluginError
    participant p13 as _load_catalog
    participant p14 as loads
    participant p15 as read_text
    participant p16 as isinstance
    participant p17 as get
    p0-->>p1: getattr
    p0->>p2: validate_path
    p2->>p3: PathValidationError
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p6: relative_to
    p2->>p3: PathValidationError
    p0->>p7: install_plugin
    p7->>p8: resolve_plugin_ref
    p8-->>p9: expanduser
    p8-->>p10: Path
    p8-->>p11: exists
    p8-->>p4: resolve
    p8-->>p4: resolve
    p8-->>p10: Path
    p8-->>p6: relative_to
    p8->>p12: PluginError
    p8-->>p10: Path
    p8-->>p10: Path
    p8->>p13: _load_catalog
    p13-->>p11: exists
    p13-->>p14: loads
    p13-->>p15: read_text
    p13->>p12: PluginError
    p13-->>p16: isinstance
    p13-->>p16: isinstance
    p13-->>p17: get
    p13-->>p16: isinstance
```

> Call sequence diagram shows 30 of 338 interactions; 308 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. validate_path"]
    s4["4. PathValidationError"]
    s5["5. resolve"]
    s6["6. cwd"]
    s7["7. resolve"]
    s8["8. cwd"]
    s9["9. relative_to"]
    s10["10. PathValidationError"]
    s11["11. install_plugin"]
    s12["12. resolve_plugin_ref"]
    s1 -. "getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s2
    s1 -->|"validate_path(wiki_dir, '--wiki-dir')"| s3
    s3 -->|"PathValidationError(...)"| s4
    s3 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s5
    s3 -. "Path.cwd(data not statically known)" .-> s6
    s3 -. "Path.cwd().resolve(data not statically known)" .-> s7
    s3 -. "Path.cwd(data not statically known)" .-> s8
    s3 -. "resolved.relative_to(cwd)" .-> s9
    s3 -->|"PathValidationError(...)"| s10
    s1 -->|"install_plugin(getattr(...), dry_run=bool(...), yes=bool(...))"| s11
    s11 -->|"resolve_plugin_ref(ref, root=root)"| s12
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
    b6["filesystem_write shutil.copytree"]
    s11 -. "filesystem_write shutil.copytree" .-> b6
    click s1 "../modules/install_cmd.md"
    click s3 "../modules/config.md"
    click s4 "../modules/config.md"
    click s10 "../modules/config.md"
    click s11 "../modules/plugins.md"
    click s12 "../modules/plugins.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `DEFAULT_WIKI_DIR`, `PluginError`, `sys` | - | `none` |
| `getattr` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `relative_to` | - | - | - | - |
| `PathValidationError` | - | - | - | - |
| `install_plugin` | `ref: str`, `root: str \| Path`, `dry_run: bool`, `yes: bool` | `_copy_ignore` | - | `entry`, `entry` |
| `resolve_plugin_ref` | `ref: str`, `root: str \| Path` | `PROJECT_CATALOG`, `USER_CATALOG` | - | `resolved`, `configured.resolve(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 20 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | validate_path | 21 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 128 | `PathValidationError(...)` |
| validate_path | resolve | 131 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 131 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 132 | `Path.cwd().resolve(data not statically known)` |
| validate_path | cwd | 132 | `Path.cwd(data not statically known)` |
| validate_path | relative_to | 134 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 136 | `PathValidationError(...)` |
| run | install_plugin | 24 | `install_plugin(getattr(...), dry_run=bool(...), yes=bool(...))` |
| install_plugin | resolve_plugin_ref | 449 | `resolve_plugin_ref(ref, root=root)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 30 |
| output | `print` | `run` | 34 |
| output | `print` | `run` | 37 |
| output | `print` | `run` | 42 |
| output | `print` | `run` | 43 |
| output | `print` | `run` | 45 |
| filesystem_write | `shutil.copytree` | `install_plugin` | 479 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 20 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 131 |
| external_call | `validate_path` | `Path.cwd` | 131 |
| external_call | `validate_path` | `Path.cwd().resolve` | 132 |
| external_call | `validate_path` | `Path.cwd` | 132 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 134 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
