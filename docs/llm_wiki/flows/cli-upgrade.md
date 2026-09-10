# upgrade

**Entry point:** `run` (`cli`)
**Source:** [upgrade_cmd](../modules/upgrade_cmd.md)
**Modules touched:** [config](../modules/config.md), [filesystem_guard](../modules/filesystem_guard.md), [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), and 11 more

**Complete modules touched:**

- [config](../modules/config.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [legacy_hooks](../modules/legacy_hooks.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [rendering_lifecycle](../modules/rendering_lifecycle.md)
- [services_schema](../modules/services_schema.md)
- [skills](../modules/skills.md)
- [source_selection](../modules/source_selection.md)
- [upgrade_cmd](../modules/upgrade_cmd.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr (src/llm_wiki_cli/commands/upgrade_cmd.py:run)
    participant p2 as validate_path
    participant p3 as PathValidationError
    participant p4 as (…).resolve
    participant p5 as Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    participant p6 as Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)
    participant p7 as resolved.relative_to
    participant p8 as require_safe_wiki_scaffold
    participant p9 as Path (src/llm_wiki_cli/services…equire_safe_wiki_scaffold)
    participant p10 as tuple (src/llm_wiki_cli/services…equire_safe_wiki_scaffold)
    participant p11 as iter_directory_kinds
    participant p12 as tuple (src/llm_wiki_cli/services…e.py:iter_directory_kinds)
    participant p13 as first_unsafe_path_component
    participant p14 as Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p15 as os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p16 as os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p17 as lexical.is_absolute
    participant p18 as Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p19 as list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p20 as pending_parts.pop
    participant p21 as current.lstat (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p22 as getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p23 as stat.S_ISLNK (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p24 as bool (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/upgrade_cmd.py:run)
    p0->>p2: validate_path
    p2->>p3: PathValidationError
    p2-->>p4: (…).resolve
    p2-->>p5: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p2-->>p6: Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)
    p2-->>p5: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p2-->>p7: resolved.relative_to
    p2->>p3: PathValidationError
    p0->>p8: require_safe_wiki_scaffold
    p8-->>p9: Path (src/llm_wiki_cli/services…equire_safe_wiki_scaffold)
    p8-->>p10: tuple (src/llm_wiki_cli/services…equire_safe_wiki_scaffold)
    p8->>p11: iter_directory_kinds
    p11-->>p12: tuple (src/llm_wiki_cli/services…e.py:iter_directory_kinds)
    p8-->>p10: tuple (src/llm_wiki_cli/services…equire_safe_wiki_scaffold)
    p8->>p13: first_unsafe_path_component
    p13-->>p14: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p15: os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p14: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p16: os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p17: lexical.is_absolute
    p13-->>p18: Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p14: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p19: list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p20: pending_parts.pop
    p13-->>p21: current.lstat (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p22: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p22: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p23: stat.S_ISLNK (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p24: bool (src/llm_wiki_cli/services…rst_unsafe_path_component)
```

> Call sequence diagram shows 30 of 1774 interactions; 1744 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/upgrade_cmd.py:run)"]
    s3["3. validate_path"]
    s4["4. PathValidationError"]
    s5["5. (…).resolve"]
    s6["6. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s7["7. Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)"]
    s8["8. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s9["9. resolved.relative_to"]
    s10["10. PathValidationError"]
    s11["11. require_safe_wiki_scaffold"]
    s12["12. Path (src/llm_wiki_cli/services…equire_safe_wiki_scaffold)"]
    s1 -. "getattr (src/llm_wiki_cli/commands/upgrade_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s2
    s1 -->|"validate_path(wiki_dir, '--wiki-dir')"| s3
    s3 -->|"PathValidationError(...)"| s4
    s3 -. "(…).resolve(data not statically known)" .-> s5
    s3 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s6
    s3 -. "Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s7
    s3 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s8
    s3 -. "resolved.relative_to(cwd)" .-> s9
    s3 -->|"PathValidationError(...)"| s10
    s1 -->|"require_safe_wiki_scaffold(wiki_dir)"| s11
    s11 -. "Path (src/llm_wiki_cli/services…equire_safe_wiki_scaffold)(wiki_dir)" .-> s12
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
    click s1 "../modules/upgrade_cmd.md"
    click s3 "../modules/config.md"
    click s4 "../modules/config.md"
    click s10 "../modules/config.md"
    click s11 "../modules/wiki_lifecycle.md"
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
| `run` | `args` | `DEFAULT_WIKI_DIR`, `WikiScaffoldPathError`, `sys`, `LegacyHookError`, `sys`, `AgentConfigState`, `sys`, `AgentConfigState` | `config[...]`, `config[...]`, `config[...]` | - |
| `getattr (src/llm_wiki_cli/commands/upgrade_cmd.py:run)` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `resolved.relative_to` | - | - | - | - |
| `PathValidationError` | - | - | - | - |
| `require_safe_wiki_scaffold` | `wiki_dir: Union[str, Path]` | - | - | - |
| `Path (src/llm_wiki_cli/services…equire_safe_wiki_scaffold)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/upgrade_cmd.py:run) | 585 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | validate_path | 586 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 132 | `PathValidationError(...)` |
| validate_path | (…).resolve | 133 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 133 | `Path.cwd(data not statically known)` |
| validate_path | Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path) | 134 | `Path.cwd().resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 134 | `Path.cwd(data not statically known)` |
| validate_path | resolved.relative_to | 136 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 138 | `PathValidationError(...)` |
| run | require_safe_wiki_scaffold | 588 | `require_safe_wiki_scaffold(wiki_dir)` |
| require_safe_wiki_scaffold | Path (src/llm_wiki_cli/services…equire_safe_wiki_scaffold) | 43 | `Path(wiki_dir)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 591 |
| output | `print` | `run` | 596 |
| output | `print` | `run` | 600 |
| output | `print` | `run` | 602 |
| output | `print` | `run` | 619 |
| output | `print` | `run` | 631 |
| output | `print` | `run` | 642 |
| output | `print` | `run` | 650 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 585 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 133 |
| external_call | `validate_path` | `Path.cwd` | 133 |
| unresolved_call | `validate_path` | `Path.cwd().resolve` | 134 |
| external_call | `validate_path` | `Path.cwd` | 134 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 136 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
