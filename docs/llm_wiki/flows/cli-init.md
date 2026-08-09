# init

**Entry point:** `run` (`cli`)
**Source:** [init_cmd](../modules/init_cmd.md)
**Modules touched:** [config](../modules/config.md), [init_cmd](../modules/init_cmd.md), [io](../modules/io.md), [paths](../modules/paths.md), and 5 more

**Complete modules touched:**

- [config](../modules/config.md)
- [init_cmd](../modules/init_cmd.md)
- [io](../modules/io.md)
- [paths](../modules/paths.md)
- [services_schema](../modules/services_schema.md)
- [skills](../modules/skills.md)
- [source_selection](../modules/source_selection.md)
- [validation](../modules/validation.md)
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
    participant p7 as read_config
    participant p8 as get_agent_config_path
    participant p9 as is_dir
    participant p10 as Path
    participant p11 as exists
    participant p12 as dict
    participant p13 as strip
    participant p14 as read_text
    participant p15 as startswith
    participant p16 as loads
    participant p17 as items
    participant p18 as setdefault
    participant p19 as get
    participant p20 as isinstance
    participant p21 as print
    participant p22 as SystemExit
    p0-->>p1: getattr
    p0->>p2: validate_path
    p2->>p3: PathValidationError
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p6: relative_to
    p2->>p3: PathValidationError
    p0->>p7: read_config
    p7->>p8: get_agent_config_path
    p8-->>p9: is_dir
    p8-->>p10: Path
    p8-->>p10: Path
    p8-->>p10: Path
    p7-->>p11: exists
    p7-->>p12: dict
    p7-->>p13: strip
    p7-->>p14: read_text
    p7-->>p15: startswith
    p7-->>p12: dict
    p7-->>p16: loads
    p7-->>p12: dict
    p7-->>p17: items
    p7-->>p18: setdefault
    p0-->>p1: getattr
    p0-->>p19: get
    p0-->>p20: isinstance
    p0-->>p21: print
    p0-->>p22: SystemExit
```

> Call sequence diagram shows 30 of 334 interactions; 304 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

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
    s11["11. read_config"]
    s12["12. get_agent_config_path"]
    s1 -. "getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s2
    s1 -->|"validate_path(wiki_dir, '--wiki-dir')"| s3
    s3 -->|"PathValidationError(...)"| s4
    s3 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s5
    s3 -. "Path.cwd(data not statically known)" .-> s6
    s3 -. "Path.cwd().resolve(data not statically known)" .-> s7
    s3 -. "Path.cwd(data not statically known)" .-> s8
    s3 -. "resolved.relative_to(cwd)" .-> s9
    s3 -->|"PathValidationError(...)"| s10
    s1 -->|"read_config(wiki_dir)"| s11
    s11 -->|"get_agent_config_path(wiki_dir)"| s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["mutation directories.extend"]
    s1 -. "mutation directories.extend" .-> b4
    b5["output print"]
    s1 -. "output print" .-> b5
    b6["output print"]
    s1 -. "output print" .-> b6
    b7["output print"]
    s1 -. "output print" .-> b7
    click s1 "../modules/init_cmd.md"
    click s3 "../modules/config.md"
    click s4 "../modules/config.md"
    click s10 "../modules/config.md"
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
| `run` | `args` | `DEFAULT_WIKI_DIR`, `sys`, `SourceSelectionError`, `sys`, `INITIAL_WIKI_INDEX_MARKDOWN`, `INITIAL_WIKI_LOG_MARKDOWN`, `_CONSTRAINT_START`, `SkillsError` | `config[...]` | - |
| `getattr` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `relative_to` | - | - | - | - |
| `PathValidationError` | - | - | - | - |
| `read_config` | `wiki_dir: 'str \| Path'` | `_DEFAULT_CONFIG`, `_DEFAULT_CONFIG`, `json`, `_DEFAULT_CONFIG` | `result[...]` | `dict(...)`, `result`, `result`, `data` |
| `get_agent_config_path` | `wiki_dir: 'str \| Path'` | - | - | `...`, `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 43 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | validate_path | 44 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 128 | `PathValidationError(...)` |
| validate_path | resolve | 131 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 131 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 132 | `Path.cwd().resolve(data not statically known)` |
| validate_path | cwd | 132 | `Path.cwd(data not statically known)` |
| validate_path | relative_to | 134 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 136 | `PathValidationError(...)` |
| run | read_config | 45 | `read_config(wiki_dir)` |
| read_config | get_agent_config_path | 537 | `get_agent_config_path(wiki_dir)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 49 |
| output | `print` | `run` | 59 |
| output | `print` | `run` | 66 |
| output | `print` | `run` | 71 |
| mutation | `directories.extend` | `run` | 81 |
| output | `print` | `run` | 93 |
| output | `print` | `run` | 96 |
| output | `print` | `run` | 138 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 43 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 131 |
| external_call | `validate_path` | `Path.cwd` | 131 |
| external_call | `validate_path` | `Path.cwd().resolve` | 132 |
| external_call | `validate_path` | `Path.cwd` | 132 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 134 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
