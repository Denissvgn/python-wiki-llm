# context

**Entry point:** `run` (`cli`)
**Source:** [context_service](../modules/context_service.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [context_packet](../modules/context_packet.md), [context_service](../modules/context_service.md), and 24 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [io](../modules/io.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [plugins](../modules/plugins.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr (src/llm_wiki_cli/services/context_service.py:run)
    participant p2 as _run_protocol
    participant p3 as getattr (src/llm_wiki_cli/services…_service.py:_run_protocol)
    participant p4 as _read_protocol_request
    participant p5 as sys.stdin.read
    participant p6 as Path(…).read_text
    participant p7 as Path (src/llm_wiki_cli/services…py:_read_protocol_request)
    participant p8 as ProtocolRequestError
    participant p9 as json.loads (src/llm_wiki_cli/services…py:_read_protocol_request)
    participant p10 as _validate_protocol_request
    participant p11 as isinstance (src/llm_wiki_cli/services…validate_protocol_request)
    participant p12 as data.get (src/llm_wiki_cli/services…validate_protocol_request)
    participant p13 as _validate_protocol_request_impl
    participant p14 as isinstance (src/llm_wiki_cli/services…ate_protocol_request_impl)
    participant p15 as any (src/llm_wiki_cli/services…ate_protocol_request_impl)
    participant p16 as data.get (src/llm_wiki_cli/services…ate_protocol_request_impl)
    participant p17 as sorted (src/llm_wiki_cli/services…ate_protocol_request_impl)
    participant p18 as set (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p0-->>p1: getattr (src/llm_wiki_cli/services/context_service.py:run)
    p0->>p2: _run_protocol
    p2-->>p3: getattr (src/llm_wiki_cli/services…_service.py:_run_protocol)
    p2->>p4: _read_protocol_request
    p4-->>p5: sys.stdin.read
    p4-->>p6: Path(…).read_text
    p4-->>p7: Path (src/llm_wiki_cli/services…py:_read_protocol_request)
    p4->>p8: ProtocolRequestError
    p4-->>p9: json.loads (src/llm_wiki_cli/services…py:_read_protocol_request)
    p4->>p8: ProtocolRequestError
    p4->>p10: _validate_protocol_request
    p10-->>p11: isinstance (src/llm_wiki_cli/services…validate_protocol_request)
    p10-->>p12: data.get (src/llm_wiki_cli/services…validate_protocol_request)
    p10->>p13: _validate_protocol_request_impl
    p13-->>p14: isinstance (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p13->>p8: ProtocolRequestError
    p13-->>p15: any (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p13-->>p14: isinstance (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p13->>p8: ProtocolRequestError
    p13-->>p16: data.get (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p13->>p8: ProtocolRequestError
    p13-->>p17: sorted (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p13-->>p18: set (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p13->>p8: ProtocolRequestError
    p13->>p8: ProtocolRequestError
    p13-->>p14: isinstance (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p13-->>p14: isinstance (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p13->>p8: ProtocolRequestError
    p13-->>p16: data.get (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p13-->>p14: isinstance (src/llm_wiki_cli/services…ate_protocol_request_impl)
```

> Call sequence diagram shows 30 of 1683 interactions; 1653 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/services/context_service.py:run)"]
    s3["3. _run_protocol"]
    s4["4. getattr (src/llm_wiki_cli/services…_service.py:_run_protocol)"]
    s5["5. _read_protocol_request"]
    s6["6. sys.stdin.read"]
    s7["7. Path(…).read_text"]
    s8["8. Path (src/llm_wiki_cli/services…py:_read_protocol_request)"]
    s9["9. ProtocolRequestError"]
    s10["10. json.loads (src/llm_wiki_cli/services…py:_read_protocol_request)"]
    s11["11. ProtocolRequestError"]
    s12["12. _validate_protocol_request"]
    s1 -. "getattr (src/llm_wiki_cli/services/context_service.py:run)(args, 'request', None)" .-> s2
    s1 -->|"_run_protocol(args)"| s3
    s3 -. "getattr (src/llm_wiki_cli/services…_service.py:_run_protocol)(args, 'output', None)" .-> s4
    s3 -->|"_read_protocol_request(args.request)"| s5
    s5 -. "sys.stdin.read(data not statically known)" .-> s6
    s5 -. "Path(…).read_text(encoding='utf-8')" .-> s7
    s5 -. "Path (src/llm_wiki_cli/services…py:_read_protocol_request)(source)" .-> s8
    s5 -->|"ProtocolRequestError(..., 'request')"| s9
    s5 -. "json.loads (src/llm_wiki_cli/services…py:_read_protocol_request)(raw)" .-> s10
    s5 -->|"ProtocolRequestError(..., 'request')"| s11
    s5 -->|"_validate_protocol_request(data)"| s12
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
    click s1 "../modules/context_service.md"
    click s3 "../modules/context_service.md"
    click s5 "../modules/context_service.md"
    click s9 "../modules/context_service.md"
    click s11 "../modules/context_service.md"
    click s12 "../modules/context_service.md"
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
| `run` | `args` | `DEFAULT_WIKI_DIR`, `sys`, `sys`, `print_extraction_job_plan`, `ProtocolRequestError`, `sys`, `KnowledgeRequiredUnavailableError`, `sys` | - | `none`, `none`, `none` |
| `getattr (src/llm_wiki_cli/services/context_service.py:run)` | - | - | - | - |
| `_run_protocol` | `args` | `DEFAULT_WIKI_DIR`, `KNOWLEDGE_PROTOCOL_VERSION`, `print_extraction_job_plan`, `ProtocolRequestError`, `KnowledgeRequiredUnavailableError`, `sys` | `exc.protocol` | `none` |
| `getattr (src/llm_wiki_cli/services…_service.py:_run_protocol)` | - | - | - | - |
| `_read_protocol_request` | `source: str` | `json` | - | `_validate_protocol_request(...)` |
| `sys.stdin.read` | - | - | - | - |
| `Path(…).read_text` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…py:_read_protocol_request)` | - | - | - | - |
| `ProtocolRequestError` | - | - | - | - |
| `json.loads (src/llm_wiki_cli/services…py:_read_protocol_request)` | - | - | - | - |
| `ProtocolRequestError` | - | - | - | - |
| `_validate_protocol_request` | `data: object` | `PROTOCOL_VERSION`, `ProtocolRequestError`, `PROTOCOL_VERSION`, `KNOWLEDGE_PROTOCOL_VERSION` | `exc.protocol` | `_validate_protocol_request_impl(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/services/context_service.py:run) | 3445 | `getattr(args, 'request', None)` |
| run | _run_protocol | 3446 | `_run_protocol(args)` |
| _run_protocol | getattr (src/llm_wiki_cli/services…_service.py:_run_protocol) | 3334 | `getattr(args, 'output', None)` |
| _run_protocol | _read_protocol_request | 3337 | `_read_protocol_request(args.request)` |
| _read_protocol_request | sys.stdin.read | 1053 | `sys.stdin.read(data not statically known)` |
| _read_protocol_request | Path(…).read_text | 1055 | `Path(source).read_text(encoding='utf-8')` |
| _read_protocol_request | Path (src/llm_wiki_cli/services…py:_read_protocol_request) | 1055 | `Path(source)` |
| _read_protocol_request | ProtocolRequestError | 1058 | `ProtocolRequestError(..., 'request')` |
| _read_protocol_request | json.loads (src/llm_wiki_cli/services…py:_read_protocol_request) | 1061 | `json.loads(raw)` |
| _read_protocol_request | ProtocolRequestError | 1063 | `ProtocolRequestError(..., 'request')` |
| _read_protocol_request | _validate_protocol_request | 1065 | `_validate_protocol_request(data)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 3462 |
| output | `print` | `run` | 3465 |
| output | `print` | `run` | 3499 |
| output | `print` | `run` | 3502 |
| output | `print` | `run` | 3509 |
| output | `print` | `run` | 3511 |
| output | `print` | `run` | 3520 |
| output | `print` | `run` | 3522 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 3445 |
| external_call | `_run_protocol` | `getattr` | 3334 |
| external_call | `_read_protocol_request` | `sys.stdin.read` | 1053 |
| unresolved_call | `_read_protocol_request` | `Path(source).read_text` | 1055 |
| external_call | `_read_protocol_request` | `json.loads` | 1061 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
