# api-diff

**Entry point:** `run` (`cli`)
**Source:** [api_diff_cmd](../modules/api_diff_cmd.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [api_diff](../modules/api_diff.md), [api_diff_cmd](../modules/api_diff_cmd.md), [config](../modules/config.md), and 3 more

**Complete modules touched:**

- [api_contracts](../modules/api_contracts.md)
- [api_diff](../modules/api_diff.md)
- [api_diff_cmd](../modules/api_diff_cmd.md)
- [config](../modules/config.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [source_selection](../modules/source_selection.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as validate_source_root
    participant p2 as validate_path
    participant p3 as PathValidationError
    participant p4 as (…).resolve
    participant p5 as Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    participant p6 as Path.cwd().resolve
    participant p7 as resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    participant p8 as Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)
    participant p9 as Path (src/llm_wiki_cli/config.py:validate_source_root)
    participant p10 as candidate.is_absolute (src/llm_wiki_cli/config.py:validate_source_root)
    participant p11 as Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    participant p12 as candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    participant p13 as resolved.is_dir
    participant p14 as os.path.abspath (src/llm_wiki_cli/config.py:validate_source_root)
    participant p15 as windows_current_user_sid
    participant p16 as WindowsSecurityGuardError
    participant p17 as _current_windows_user_sid
    participant p18 as ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)
    participant p19 as ctypes.POINTER (src/llm_wiki_cli/services…_current_windows_user_sid)
    participant p20 as wintypes.HANDLE (src/llm_wiki_cli/services…_current_windows_user_sid)
    participant p21 as open_process_token
    participant p22 as get_current_process
    participant p23 as ctypes.byref (src/llm_wiki_cli/services…_current_windows_user_sid)
    p0->>p1: validate_source_root
    p1->>p2: validate_path
    p2->>p3: PathValidationError
    p2-->>p4: (…).resolve
    p2-->>p5: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p2-->>p6: Path.cwd().resolve
    p2-->>p5: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p2-->>p7: resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    p2->>p3: PathValidationError
    p1-->>p8: Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)
    p1-->>p9: Path (src/llm_wiki_cli/config.py:validate_source_root)
    p1-->>p10: candidate.is_absolute (src/llm_wiki_cli/config.py:validate_source_root)
    p1-->>p11: Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    p1-->>p12: candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    p1->>p3: PathValidationError
    p1-->>p13: resolved.is_dir
    p1->>p3: PathValidationError
    p1-->>p9: Path (src/llm_wiki_cli/config.py:validate_source_root)
    p1-->>p14: os.path.abspath (src/llm_wiki_cli/config.py:validate_source_root)
    p1->>p15: windows_current_user_sid
    p15->>p16: WindowsSecurityGuardError
    p15->>p17: _current_windows_user_sid
    p17-->>p18: ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)
    p17-->>p18: ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)
    p17-->>p19: ctypes.POINTER (src/llm_wiki_cli/services…_current_windows_user_sid)
    p17-->>p19: ctypes.POINTER (src/llm_wiki_cli/services…_current_windows_user_sid)
    p17-->>p20: wintypes.HANDLE (src/llm_wiki_cli/services…_current_windows_user_sid)
    p17-->>p21: open_process_token
    p17-->>p22: get_current_process
    p17-->>p23: ctypes.byref (src/llm_wiki_cli/services…_current_windows_user_sid)
```

> Call sequence diagram shows 30 of 495 interactions; 465 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. validate_source_root"]
    s3["3. validate_path"]
    s4["4. PathValidationError"]
    s5["5. (…).resolve"]
    s6["6. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s7["7. Path.cwd().resolve"]
    s8["8. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s9["9. resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)"]
    s10["10. PathValidationError"]
    s11["11. Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)"]
    s12["12. Path (src/llm_wiki_cli/config.py:validate_source_root)"]
    s1 -->|"validate_source_root(args.src_dir, '--src-dir', allow_external=args.allow_external_src)"| s2
    s2 -->|"validate_path(path, label)"| s3
    s3 -->|"PathValidationError(...)"| s4
    s3 -. "(…).resolve(data not statically known)" .-> s5
    s3 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s6
    s3 -. "Path.cwd().resolve(data not statically known)" .-> s7
    s3 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s8
    s3 -. "resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)(cwd)" .-> s9
    s3 -->|"PathValidationError(...)"| s10
    s2 -. "Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)(data not statically known)" .-> s11
    s2 -. "Path (src/llm_wiki_cli/config.py:validate_source_root)(path)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    click s1 "../modules/api_diff_cmd.md"
    click s2 "../modules/config.md"
    click s3 "../modules/config.md"
    click s4 "../modules/config.md"
    click s10 "../modules/config.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | - | - | - |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd().resolve` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `PathValidationError` | - | - | - | - |
| `Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)` | - | - | - | - |
| `Path (src/llm_wiki_cli/config.py:validate_source_root)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | validate_source_root | 10 | `validate_source_root(args.src_dir, '--src-dir', allow_external=args.allow_external_src)` |
| validate_source_root | validate_path | 160 | `validate_path(path, label)` |
| validate_path | PathValidationError | 134 | `PathValidationError(...)` |
| validate_path | (…).resolve | 135 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 135 | `Path.cwd(data not statically known)` |
| validate_path | Path.cwd().resolve | 136 | `Path.cwd().resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 136 | `Path.cwd(data not statically known)` |
| validate_path | resolved.relative_to (src/llm_wiki_cli/config.py:validate_path) | 138 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 140 | `PathValidationError(...)` |
| validate_source_root | Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root) | 163 | `Path(path).expanduser(data not statically known)` |
| validate_source_root | Path (src/llm_wiki_cli/config.py:validate_source_root) | 163 | `Path(path)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 14 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 135 |
| external_call | `validate_path` | `Path.cwd` | 135 |
| unresolved_call | `validate_path` | `Path.cwd().resolve` | 136 |
| external_call | `validate_path` | `Path.cwd` | 136 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 138 |
| unresolved_call | `validate_source_root` | `Path(path).expanduser` | 163 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
