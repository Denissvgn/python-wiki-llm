# build_documentation_agent_packet

**Entry point:** `build_documentation_agent_packet` (`api`)
**Source:** [packet](../modules/packet.md)
**Modules touched:** [config](../modules/config.md), [documentation_policy](../modules/documentation_policy.md), [documentation_run_contracts](../modules/documentation_run_contracts.md), and 8 more

**Complete modules touched:**

- [config](../modules/config.md)
- [documentation_policy](../modules/documentation_policy.md)
- [documentation_run_contracts](../modules/documentation_run_contracts.md)
- [documentation_run_schema](../modules/documentation_run_schema.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [integrity](../modules/integrity.md)
- [io](../modules/io.md)
- [packet](../modules/packet.md)
- [source_selection](../modules/source_selection.md)
- [validation](../modules/validation.md)
- [workspace](../modules/workspace.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_documentation_agent_packet
    participant p1 as DocumentationSchemaError
    participant p2 as _resolve_workspace_root_argument
    participant p3 as Path
    participant p4 as abspath
    participant p5 as fspath
    participant p6 as expanduser
    participant p7 as lexists
    participant p8 as lstat
    participant p9 as DocumentationIntegrityError
    participant p10 as bool
    participant p11 as getattr
    participant p12 as S_ISLNK
    participant p13 as S_ISDIR
    participant p14 as resolve
    participant p15 as _assert_existing_workspace_layout_safe
    participant p16 as _assert_safe_workspace_directory
    p0->>p1: DocumentationSchemaError
    p0->>p2: _resolve_workspace_root_argument
    p2-->>p3: Path
    p2-->>p4: abspath
    p2-->>p5: fspath
    p2-->>p6: expanduser
    p2-->>p3: Path
    p2-->>p7: lexists
    p2-->>p8: lstat
    p2->>p9: DocumentationIntegrityError
    p2-->>p10: bool
    p2-->>p11: getattr
    p2-->>p10: bool
    p2-->>p11: getattr
    p2-->>p12: S_ISLNK
    p2->>p9: DocumentationIntegrityError
    p2-->>p13: S_ISDIR
    p2->>p9: DocumentationIntegrityError
    p2-->>p14: resolve
    p2-->>p7: lexists
    p2->>p15: _assert_existing_workspace_layout_safe
    p15-->>p7: lexists
    p15->>p16: _assert_safe_workspace_directory
    p16-->>p8: lstat
    p16->>p9: DocumentationIntegrityError
    p16-->>p10: bool
    p16-->>p11: getattr
    p16-->>p10: bool
    p16-->>p11: getattr
    p16-->>p12: S_ISLNK
```

> Call sequence diagram shows 30 of 1413 interactions; 1383 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_documentation_agent_packet"]
    s2["2. DocumentationSchemaError"]
    s3["3. _resolve_workspace_root_argument"]
    s4["4. Path"]
    s5["5. abspath"]
    s6["6. fspath"]
    s7["7. expanduser"]
    s8["8. Path"]
    s9["9. lexists"]
    s10["10. lstat"]
    s11["11. DocumentationIntegrityError"]
    s12["12. bool"]
    s1 -->|"DocumentationSchemaError(...)"| s2
    s1 -->|"_resolve_workspace_root_argument(workspace)"| s3
    s3 -. "Path(os.path.abspath(...))" .-> s4
    s3 -. "os.path.abspath(os.fspath(...))" .-> s5
    s3 -. "os.fspath(...)" .-> s6
    s3 -. "Path(workspace).expanduser(data not statically known)" .-> s7
    s3 -. "Path(workspace)" .-> s8
    s3 -. "os.path.lexists(requested)" .-> s9
    s3 -. "requested.lstat(data not statically known)" .-> s10
    s3 -->|"DocumentationIntegrityError(...)"| s11
    s3 -. "bool(getattr(...))" .-> s12
    b0["filesystem_read before_path.read_bytes"]
    s1 -. "filesystem_read before_path.read_bytes" .-> b0
    b1["filesystem_read attempt_packet_path.read_bytes"]
    s1 -. "filesystem_read attempt_packet_path.read_bytes" .-> b1
    b2["filesystem_read run_path.read_bytes"]
    s1 -. "filesystem_read run_path.read_bytes" .-> b2
    click s1 "../modules/packet.md"
    click s2 "../modules/documentation_run_contracts.md"
    click s3 "../modules/workspace.md"
    click s11 "../modules/documentation_run_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_documentation_agent_packet` | `workspace: str \| Path`, `stage: str` | - | `run.current_stage`, `run.stage_attempts[...]` | `packet` |
| `DocumentationSchemaError` | - | - | - | - |
| `_resolve_workspace_root_argument` | `workspace: str \| Path` | - | - | `resolved` |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `fspath` | - | - | - | - |
| `expanduser` | - | - | - | - |
| `Path` | - | - | - | - |
| `lexists` | - | - | - | - |
| `lstat` | - | - | - | - |
| `DocumentationIntegrityError` | - | - | - | - |
| `bool` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_documentation_agent_packet | DocumentationSchemaError | 86 | `DocumentationSchemaError(...)` |
| build_documentation_agent_packet | _resolve_workspace_root_argument | 87 | `_resolve_workspace_root_argument(workspace)` |
| _resolve_workspace_root_argument | Path | 102 | `Path(os.path.abspath(...))` |
| _resolve_workspace_root_argument | abspath | 102 | `os.path.abspath(os.fspath(...))` |
| _resolve_workspace_root_argument | fspath | 102 | `os.fspath(...)` |
| _resolve_workspace_root_argument | expanduser | 102 | `Path(workspace).expanduser(data not statically known)` |
| _resolve_workspace_root_argument | Path | 102 | `Path(workspace)` |
| _resolve_workspace_root_argument | lexists | 103 | `os.path.lexists(requested)` |
| _resolve_workspace_root_argument | lstat | 105 | `requested.lstat(data not statically known)` |
| _resolve_workspace_root_argument | DocumentationIntegrityError | 107 | `DocumentationIntegrityError(...)` |
| _resolve_workspace_root_argument | bool | 110 | `bool(getattr(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `before_path.read_bytes` | `build_documentation_agent_packet` | 129 |
| filesystem_read | `attempt_packet_path.read_bytes` | `build_documentation_agent_packet` | 270 |
| filesystem_read | `run_path.read_bytes` | `build_documentation_agent_packet` | 274 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_resolve_workspace_root_argument` | `os.path.abspath` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `os.fspath` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `Path(workspace).expanduser` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `os.path.lexists` | 103 |
| unresolved_call | `_resolve_workspace_root_argument` | `requested.lstat` | 105 |
| step_limit | `build_documentation_agent_packet` | `first 12 steps` | 0 |
| truncated_flow | `build_documentation_agent_packet` | `depth limit` | 0 |

## Behavior

This flow starts at `build_documentation_agent_packet` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
