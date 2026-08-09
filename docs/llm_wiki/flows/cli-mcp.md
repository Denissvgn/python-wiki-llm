# mcp

**Entry point:** `run` (`cli`)
**Source:** [mcp_cmd](../modules/mcp_cmd.md)
**Modules touched:** [config](../modules/config.md), [filesystem_guard](../modules/filesystem_guard.md), [io](../modules/io.md), [mcp_cmd](../modules/mcp_cmd.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as _mcp_service_export
    participant p2 as get
    participant p3 as globals
    participant p4 as getattr
    participant p5 as bool
    participant p6 as validate_source_root
    participant p7 as validate_path
    participant p8 as PathValidationError
    participant p9 as resolve
    participant p10 as cwd
    participant p11 as relative_to
    participant p12 as expanduser
    participant p13 as Path
    participant p14 as is_absolute
    participant p15 as is_dir
    participant p16 as abspath
    p0->>p1: _mcp_service_export
    p1-->>p2: get
    p1-->>p3: globals
    p1-->>p4: getattr
    p1-->>p3: globals
    p0->>p1: _mcp_service_export
    p0->>p1: _mcp_service_export
    p0->>p1: _mcp_service_export
    p0-->>p4: getattr
    p0-->>p5: bool
    p0-->>p4: getattr
    p0->>p6: validate_source_root
    p6->>p7: validate_path
    p7->>p8: PathValidationError
    p7-->>p9: resolve
    p7-->>p10: cwd
    p7-->>p9: resolve
    p7-->>p10: cwd
    p7-->>p11: relative_to
    p7->>p8: PathValidationError
    p6-->>p12: expanduser
    p6-->>p13: Path
    p6-->>p14: is_absolute
    p6-->>p10: cwd
    p6-->>p9: resolve
    p6->>p8: PathValidationError
    p6-->>p15: is_dir
    p6->>p8: PathValidationError
    p6-->>p13: Path
    p6-->>p16: abspath
```

> Call sequence diagram shows 30 of 127 interactions; 97 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. _mcp_service_export"]
    s3["3. get"]
    s4["4. globals"]
    s5["5. getattr"]
    s6["6. globals"]
    s7["7. _mcp_service_export"]
    s8["8. _mcp_service_export"]
    s9["9. _mcp_service_export"]
    s10["10. getattr"]
    s11["11. bool"]
    s12["12. getattr"]
    s1 -->|"_mcp_service_export('McpServerConfig')"| s2
    s2 -. "globals().get(name, _MISSING)" .-> s3
    s2 -. "globals(data not statically known)" .-> s4
    s2 -. "getattr(mcp_server, name)" .-> s5
    s2 -. "globals(data not statically known)" .-> s6
    s1 -->|"_mcp_service_export('MCPDependencyError')"| s7
    s1 -->|"_mcp_service_export('McpWikiError')"| s8
    s1 -->|"_mcp_service_export('run_mcp_server')"| s9
    s1 -. "getattr(args, 'src_dir', '.')" .-> s10
    s1 -. "bool(getattr(...))" .-> s11
    s1 -. "getattr(args, 'allow_external_src', False)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    click s1 "../modules/mcp_cmd.md"
    click s2 "../modules/mcp_cmd.md"
    click s7 "../modules/mcp_cmd.md"
    click s8 "../modules/mcp_cmd.md"
    click s9 "../modules/mcp_cmd.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `sys` | - | - |
| `_mcp_service_export` | `name: str` | `_MISSING`, `_MISSING` | - | `value`, `value` |
| `get` | - | - | - | - |
| `globals` | - | - | - | - |
| `getattr` | - | - | - | - |
| `globals` | - | - | - | - |
| `_mcp_service_export` | `name: str` | `_MISSING`, `_MISSING` | - | `value`, `value` |
| `_mcp_service_export` | `name: str` | `_MISSING`, `_MISSING` | - | `value`, `value` |
| `_mcp_service_export` | `name: str` | `_MISSING`, `_MISSING` | - | `value`, `value` |
| `getattr` | - | - | - | - |
| `bool` | - | - | - | - |
| `getattr` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | _mcp_service_export | 45 | `_mcp_service_export('McpServerConfig')` |
| _mcp_service_export | get | 23 | `globals().get(name, _MISSING)` |
| _mcp_service_export | globals | 23 | `globals(data not statically known)` |
| _mcp_service_export | getattr | 28 | `getattr(mcp_server, name)` |
| _mcp_service_export | globals | 29 | `globals(data not statically known)` |
| run | _mcp_service_export | 46 | `_mcp_service_export('MCPDependencyError')` |
| run | _mcp_service_export | 47 | `_mcp_service_export('McpWikiError')` |
| run | _mcp_service_export | 48 | `_mcp_service_export('run_mcp_server')` |
| run | getattr | 50 | `getattr(args, 'src_dir', '.')` |
| run | bool | 51 | `bool(getattr(...))` |
| run | getattr | 51 | `getattr(args, 'allow_external_src', False)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 72 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_mcp_service_export` | `globals().get` | 23 |
| unresolved_call | `_mcp_service_export` | `globals` | 23 |
| unresolved_call | `_mcp_service_export` | `getattr` | 28 |
| unresolved_call | `_mcp_service_export` | `globals` | 29 |
| unresolved_call | `run` | `getattr` | 50 |
| unresolved_call | `run` | `getattr` | 51 |
| step_limit | `run` | `first 12 steps` | 0 |

## Behavior

Loads the optional MCP service only after command dispatch, validates the
source root, and constructs the server configuration. Stdio is the default;
HTTP configuration is checked again by the service for loopback host, port,
path, and origin safety. Missing optional packages and invalid wiki or
transport state are reported as command errors without changing the wiki.
