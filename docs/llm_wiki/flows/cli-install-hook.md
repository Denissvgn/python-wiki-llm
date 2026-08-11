# install-hook

**Entry point:** `run` (`cli`)
**Source:** [hook_cmd](../modules/hook_cmd.md)
**Modules touched:** [config](../modules/config.md), [filesystem_guard](../modules/filesystem_guard.md), [hook_cmd](../modules/hook_cmd.md), [io](../modules/io.md), and 4 more

**Complete modules touched:**

- [config](../modules/config.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [hook_cmd](../modules/hook_cmd.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [paths](../modules/paths.md)
- [source_selection](../modules/source_selection.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as Path
    participant p2 as exists
    participant p3 as is_symlink
    participant p4 as print
    participant p5 as exit
    participant p6 as getattr
    participant p7 as validate_path
    participant p8 as PathValidationError
    participant p9 as resolve
    participant p10 as cwd
    participant p11 as relative_to
    participant p12 as require_safe_hook_arguments
    participant p13 as str
    participant p14 as splitlines
    participant p15 as any
    participant p16 as ord
    participant p17 as ValueError
    participant p18 as require_safe_hook_paths
    participant p19 as first_unsafe_path_component
    participant p20 as fspath
    participant p21 as abspath
    p0-->>p1: Path
    p0-->>p2: exists
    p0-->>p3: is_symlink
    p0-->>p4: print
    p0-->>p5: exit
    p0-->>p6: getattr
    p0->>p7: validate_path
    p7->>p8: PathValidationError
    p7-->>p9: resolve
    p7-->>p10: cwd
    p7-->>p9: resolve
    p7-->>p10: cwd
    p7-->>p11: relative_to
    p7->>p8: PathValidationError
    p0->>p12: require_safe_hook_arguments
    p12-->>p13: str
    p12-->>p14: splitlines
    p12-->>p15: any
    p12-->>p16: ord
    p12-->>p16: ord
    p12-->>p17: ValueError
    p0->>p18: require_safe_hook_paths
    p18-->>p1: Path
    p18-->>p2: exists
    p18-->>p3: is_symlink
    p18->>p19: first_unsafe_path_component
    p19-->>p1: Path
    p19-->>p20: fspath
    p19-->>p1: Path
    p19-->>p21: abspath
```

> Call sequence diagram shows 30 of 954 interactions; 924 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. Path"]
    s3["3. exists"]
    s4["4. is_symlink"]
    s5["5. print"]
    s6["6. exit"]
    s7["7. getattr"]
    s8["8. validate_path"]
    s9["9. PathValidationError"]
    s10["10. resolve"]
    s11["11. cwd"]
    s12["12. resolve"]
    s1 -. "Path('.git')" .-> s2
    s1 -. "git_dir.exists(data not statically known)" .-> s3
    s1 -. "git_dir.is_symlink(data not statically known)" .-> s4
    s1 -. "print('Error: No .git directory found. Are you in the root of a git repository?')" .-> s5
    s1 -. "sys.exit(1)" .-> s6
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
    b7["output print"]
    s1 -. "output print" .-> b7
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
    class b7 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `DEFAULT_WIKI_DIR`, `sys`, `_EXPECTED_HOOK_UNSET`, `AgentConfigState`, `sys`, `sys`, `AgentConfigState`, `sys` | `stored[...]` | - |
| `Path` | - | - | - | - |
| `exists` | - | - | - | - |
| `is_symlink` | - | - | - | - |
| `print` | - | - | - | - |
| `exit` | - | - | - | - |
| `getattr` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | Path | 591 | `Path('.git')` |
| run | exists | 592 | `git_dir.exists(data not statically known)` |
| run | is_symlink | 592 | `git_dir.is_symlink(data not statically known)` |
| run | print | 593 | `print('Error: No .git directory found. Are you in the root of a git repository?')` |
| run | exit | 596 | `sys.exit(1)` |
| run | getattr | 598 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | validate_path | 599 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 132 | `PathValidationError(...)` |
| validate_path | resolve | 133 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 133 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 134 | `Path.cwd().resolve(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 593 |
| output | `print` | `run` | 604 |
| output | `print` | `run` | 624 |
| output | `print` | `run` | 632 |
| output | `print` | `run` | 660 |
| output | `print` | `run` | 664 |
| output | `print` | `run` | 672 |
| output | `print` | `run` | 678 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `git_dir.exists` | 592 |
| unresolved_call | `run` | `git_dir.is_symlink` | 592 |
| external_call | `run` | `sys.exit` | 596 |
| unresolved_call | `run` | `getattr` | 598 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 133 |
| external_call | `validate_path` | `Path.cwd` | 133 |
| external_call | `validate_path` | `Path.cwd().resolve` | 134 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
