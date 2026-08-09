# install-hook

**Entry point:** `run` (`cli`)
**Source:** [hook_cmd](../modules/hook_cmd.md)
**Modules touched:** [config](../modules/config.md), [hook_cmd](../modules/hook_cmd.md), [paths](../modules/paths.md), [source_selection](../modules/source_selection.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as Path
    participant p2 as exists
    participant p3 as print
    participant p4 as exit
    participant p5 as mkdir
    participant p6 as getattr
    participant p7 as validate_path
    participant p8 as PathValidationError
    participant p9 as resolve
    participant p10 as cwd
    participant p11 as relative_to
    participant p12 as read_config
    participant p13 as get_agent_config_path
    participant p14 as is_dir
    participant p15 as dict
    participant p16 as strip
    participant p17 as read_text
    participant p18 as startswith
    participant p19 as loads
    participant p20 as items
    participant p21 as setdefault
    p0-->>p1: Path
    p0-->>p2: exists
    p0-->>p3: print
    p0-->>p4: exit
    p0-->>p5: mkdir
    p0-->>p6: getattr
    p0->>p7: validate_path
    p7->>p8: PathValidationError
    p7-->>p9: resolve
    p7-->>p10: cwd
    p7-->>p9: resolve
    p7-->>p10: cwd
    p7-->>p11: relative_to
    p7->>p8: PathValidationError
    p0->>p12: read_config
    p12->>p13: get_agent_config_path
    p13-->>p14: is_dir
    p13-->>p1: Path
    p13-->>p1: Path
    p13-->>p1: Path
    p12-->>p2: exists
    p12-->>p15: dict
    p12-->>p16: strip
    p12-->>p17: read_text
    p12-->>p18: startswith
    p12-->>p15: dict
    p12-->>p19: loads
    p12-->>p15: dict
    p12-->>p20: items
    p12-->>p21: setdefault
```

> Call sequence diagram shows 30 of 227 interactions; 197 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. Path"]
    s3["3. exists"]
    s4["4. print"]
    s5["5. exit"]
    s6["6. mkdir"]
    s7["7. getattr"]
    s8["8. validate_path"]
    s9["9. PathValidationError"]
    s10["10. resolve"]
    s11["11. cwd"]
    s12["12. resolve"]
    s1 -. "Path('.git')" .-> s2
    s1 -. "git_dir.exists(data not statically known)" .-> s3
    s1 -. "print('Error: No .git directory found. Are you in the root of a git repository?')" .-> s4
    s1 -. "sys.exit(1)" .-> s5
    s1 -. "hooks_dir.mkdir(exist_ok=True)" .-> s6
    s1 -. "getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s7
    s1 -->|"validate_path(wiki_dir, '--wiki-dir')"| s8
    s8 -->|"PathValidationError(...)"| s9
    s8 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s10
    s8 -. "Path.cwd(data not statically known)" .-> s11
    s8 -. "Path.cwd().resolve(data not statically known)" .-> s12
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
    click s1 "../modules/hook_cmd.md"
    click s8 "../modules/config.md"
    click s9 "../modules/config.md"
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
| `run` | `args` | `DEFAULT_WIKI_DIR`, `sys`, `SourceSelectionError`, `sys` | `stored[...]` | - |
| `Path` | - | - | - | - |
| `exists` | - | - | - | - |
| `print` | - | - | - | - |
| `exit` | - | - | - | - |
| `mkdir` | - | - | - | - |
| `getattr` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | Path | 140 | `Path('.git')` |
| run | exists | 141 | `git_dir.exists(data not statically known)` |
| run | print | 142 | `print('Error: No .git directory found. Are you in the root of a git repository?')` |
| run | exit | 145 | `sys.exit(1)` |
| run | mkdir | 148 | `hooks_dir.mkdir(exist_ok=True)` |
| run | getattr | 150 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | validate_path | 151 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 128 | `PathValidationError(...)` |
| validate_path | resolve | 131 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 131 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 132 | `Path.cwd().resolve(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 142 |
| output | `print` | `run` | 156 |
| output | `print` | `run` | 166 |
| output | `print` | `run` | 201 |
| output | `print` | `run` | 203 |
| output | `print` | `run` | 209 |
| output | `print` | `run` | 217 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `git_dir.exists` | 141 |
| external_call | `run` | `sys.exit` | 145 |
| unresolved_call | `run` | `hooks_dir.mkdir` | 148 |
| unresolved_call | `run` | `getattr` | 150 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 131 |
| external_call | `validate_path` | `Path.cwd` | 131 |
| external_call | `validate_path` | `Path.cwd().resolve` | 132 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
