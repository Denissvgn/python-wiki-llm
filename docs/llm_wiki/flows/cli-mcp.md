# mcp

**Entry point:** `run` (`cli`)
**Source:** [mcp_cmd](../modules/mcp_cmd.md)
**Modules touched:** [config](../modules/config.md), [filesystem_guard](../modules/filesystem_guard.md), [io](../modules/io.md), [mcp_cmd](../modules/mcp_cmd.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as _mcp_service_export
    participant p2 as getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)
    participant p3 as bool (src/llm_wiki_cli/commands/mcp_cmd.py:run)
    participant p4 as validate_source_root
    participant p5 as config_type
    participant p6 as str
    participant p7 as tuple
    participant p8 as runner
    participant p9 as print
    participant p10 as SystemExit
    participant p11 as globals().get
    participant p12 as validate_path
    participant p13 as globals (src/llm_wiki_cli/commands…md.py:_mcp_service_export)
    participant p14 as Path(…).expanduser
    participant p15 as getattr (src/llm_wiki_cli/commands…md.py:_mcp_service_export)
    participant p16 as Path (src/llm_wiki_cli/config.py:validate_source_root)
    p0->>p1: _mcp_service_export
    p0->>p1: _mcp_service_export
    p0->>p1: _mcp_service_export
    p0->>p1: _mcp_service_export
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'src_dir', '.')
    p0-->>p3: bool (src/llm_wiki_cli/commands/mcp_cmd.py:run)(getattr(...))
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'allow_external_src', False)
    p0->>p4: validate_source_root
    p0-->>p5: config_type(…)
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'comparison_policy', 'auto')
    p0-->>p6: str(source_root)
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'wiki_dir', 'docs/llm_wiki')
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'transport', 'stdio')
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'host', '127.0.0.1')
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'port', 8765)
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'path', '/mcp')
    p0-->>p7: tuple(...)
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'allowed_origin', None)
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'source_selection', None)
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'tokenizer', None)
    p0-->>p2: getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'enable_sessions', False)
    p0-->>p8: runner(config)
    p0-->>p9: print(..., file=sys.stderr)
    p0-->>p10: SystemExit(1)
    p1-->>p11: globals().get(name, _MISSING)
    p4->>p12: validate_path
    p1-->>p13: globals (src/llm_wiki_cli/commands…md.py:_mcp_service_export)
    p4-->>p14: Path(…).expanduser
    p1-->>p15: getattr (src/llm_wiki_cli/commands…md.py:_mcp_service_export)(mcp_server, name)
    p4-->>p16: Path (src/llm_wiki_cli/config.py:validate_source_root)(path)
```

> Call sequence diagram shows 30 of 130 interactions; 100 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 20 of 81 (61 omitted); unresolved 4 of 24 (20 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/commands/mcp_cmd.py:_mcp_service_export` | 2 | - | unresolved | 1 |
| `src/llm_wiki_cli/config.py:validate_path` | 14 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 14 | - | unresolved | 3 |
| `src/llm_wiki_cli/config.py:validate_path` | 14 | - | external | 2 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 13 | - | unresolved | 4 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 13 | - | external | 10 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 13 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 6 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 13 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 1 |
> Omission summary shows 8 of 20 groups; 12 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. _mcp_service_export"]
    s3["3. globals().get"]
    s4["4. globals (src/llm_wiki_cli/commands…md.py:_mcp_service_export)"]
    s5["5. getattr (src/llm_wiki_cli/commands…md.py:_mcp_service_export)"]
    s6["6. globals (src/llm_wiki_cli/commands…py:_mcp_service_export, 1)"]
    s7["7. _mcp_service_export"]
    s8["8. _mcp_service_export"]
    s9["9. _mcp_service_export"]
    s10["10. getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)"]
    s11["11. bool (src/llm_wiki_cli/commands/mcp_cmd.py:run)"]
    s12["12. getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)"]
    s1 -->|"_mcp_service_export('McpServerConfig')"| s2
    s2 -. "globals().get(name, _MISSING)" .-> s3
    s2 -. "globals (src/llm_wiki_cli/commands…md.py:_mcp_service_export)(data not statically known)" .-> s4
    s2 -. "getattr (src/llm_wiki_cli/commands…md.py:_mcp_service_export)(mcp_server, name)" .-> s5
    s2 -. "globals (src/llm_wiki_cli/commands…py:_mcp_service_export, 1)(data not statically known)" .-> s6
    s1 -->|"_mcp_service_export('MCPDependencyError')"| s7
    s1 -->|"_mcp_service_export('McpWikiError')"| s8
    s1 -->|"_mcp_service_export('run_mcp_server')"| s9
    s1 -. "getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'src_dir', '.')" .-> s10
    s1 -. "bool (src/llm_wiki_cli/commands/mcp_cmd.py:run)(getattr(...))" .-> s11
    s1 -. "getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)(args, 'allow_external_src', False)" .-> s12
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
| `globals().get` | - | - | - | - |
| `globals (src/llm_wiki_cli/commands…md.py:_mcp_service_export)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands…md.py:_mcp_service_export)` | - | - | - | - |
| `globals (src/llm_wiki_cli/commands…py:_mcp_service_export, 1)` | - | - | - | - |
| `_mcp_service_export` | `name: str` | `_MISSING`, `_MISSING` | - | `value`, `value` |
| `_mcp_service_export` | `name: str` | `_MISSING`, `_MISSING` | - | `value`, `value` |
| `_mcp_service_export` | `name: str` | `_MISSING`, `_MISSING` | - | `value`, `value` |
| `getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)` | - | - | - | - |
| `bool (src/llm_wiki_cli/commands/mcp_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | _mcp_service_export | 45 | `_mcp_service_export('McpServerConfig')` |
| _mcp_service_export | globals().get | 23 | `globals().get(name, _MISSING)` |
| _mcp_service_export | globals (src/llm_wiki_cli/commands…md.py:_mcp_service_export) | 23 | `globals(data not statically known)` |
| _mcp_service_export | getattr (src/llm_wiki_cli/commands…md.py:_mcp_service_export) | 28 | `getattr(mcp_server, name)` |
| _mcp_service_export | globals (src/llm_wiki_cli/commands…py:_mcp_service_export, 1) | 29 | `globals(data not statically known)` |
| run | _mcp_service_export | 46 | `_mcp_service_export('MCPDependencyError')` |
| run | _mcp_service_export | 47 | `_mcp_service_export('McpWikiError')` |
| run | _mcp_service_export | 48 | `_mcp_service_export('run_mcp_server')` |
| run | getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run) | 50 | `getattr(args, 'src_dir', '.')` |
| run | bool (src/llm_wiki_cli/commands/mcp_cmd.py:run) | 51 | `bool(getattr(...))` |
| run | getattr (src/llm_wiki_cli/commands/mcp_cmd.py:run) | 51 | `getattr(args, 'allow_external_src', False)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 75 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_mcp_service_export` | `globals().get` | 23 |
| external_call | `_mcp_service_export` | `globals` | 23 |
| external_call | `_mcp_service_export` | `getattr` | 28 |
| unresolved_call | `_mcp_service_export` | `globals` | 29 |
| external_call | `run` | `getattr` | 50 |
| external_call | `run` | `getattr` | 51 |
| step_limit | `run` | `first 12 steps` | 0 |

## Behavior

Loads the optional MCP service only after command dispatch, validates the
source root, and constructs the server configuration. Stdio is the default;
HTTP configuration is checked again by the service for loopback host, port,
path, and origin safety. Missing optional packages and invalid wiki or
transport state are reported as command errors without changing the wiki.
