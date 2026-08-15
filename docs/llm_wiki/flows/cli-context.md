# context

**Entry point:** `run` (`cli`)
**Source:** [context_service](../modules/context_service.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [context_packet](../modules/context_packet.md), [context_service](../modules/context_service.md), and 22 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [entrypoints](../modules/entrypoints.md)
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
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as _run_protocol
    participant p3 as _read_protocol_request
    participant p4 as read
    participant p5 as read_text
    participant p6 as Path
    participant p7 as ProtocolRequestError
    participant p8 as loads
    participant p9 as _validate_protocol_request
    participant p10 as isinstance
    participant p11 as get
    participant p12 as _validate_protocol_request_impl
    participant p13 as any
    participant p14 as sorted
    participant p15 as set
    p0-->>p1: getattr
    p0->>p2: _run_protocol
    p2-->>p1: getattr
    p2->>p3: _read_protocol_request
    p3-->>p4: read
    p3-->>p5: read_text
    p3-->>p6: Path
    p3->>p7: ProtocolRequestError
    p3-->>p8: loads
    p3->>p7: ProtocolRequestError
    p3->>p9: _validate_protocol_request
    p9-->>p10: isinstance
    p9-->>p11: get
    p9->>p12: _validate_protocol_request_impl
    p12-->>p10: isinstance
    p12->>p7: ProtocolRequestError
    p12-->>p13: any
    p12-->>p10: isinstance
    p12->>p7: ProtocolRequestError
    p12-->>p11: get
    p12->>p7: ProtocolRequestError
    p12-->>p14: sorted
    p12-->>p15: set
    p12->>p7: ProtocolRequestError
    p12->>p7: ProtocolRequestError
    p12-->>p10: isinstance
    p12-->>p10: isinstance
    p12->>p7: ProtocolRequestError
    p12-->>p11: get
    p12-->>p10: isinstance
```

> Call sequence diagram shows 30 of 1669 interactions; 1639 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. _run_protocol"]
    s4["4. getattr"]
    s5["5. _read_protocol_request"]
    s6["6. read"]
    s7["7. read_text"]
    s8["8. Path"]
    s9["9. ProtocolRequestError"]
    s10["10. loads"]
    s11["11. ProtocolRequestError"]
    s12["12. _validate_protocol_request"]
    s1 -. "getattr(args, 'request', None)" .-> s2
    s1 -->|"_run_protocol(args)"| s3
    s3 -. "getattr(args, 'output', None)" .-> s4
    s3 -->|"_read_protocol_request(args.request)"| s5
    s5 -. "sys.stdin.read(data not statically known)" .-> s6
    s5 -. "Path(source).read_text(encoding='utf-8')" .-> s7
    s5 -. "Path(source)" .-> s8
    s5 -->|"ProtocolRequestError(..., 'request')"| s9
    s5 -. "json.loads(raw)" .-> s10
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
| `getattr` | - | - | - | - |
| `_run_protocol` | `args` | `DEFAULT_WIKI_DIR`, `KNOWLEDGE_PROTOCOL_VERSION`, `print_extraction_job_plan`, `ProtocolRequestError`, `KnowledgeRequiredUnavailableError`, `sys` | `exc.protocol` | `none` |
| `getattr` | - | - | - | - |
| `_read_protocol_request` | `source: str` | `json` | - | `_validate_protocol_request(...)` |
| `read` | - | - | - | - |
| `read_text` | - | - | - | - |
| `Path` | - | - | - | - |
| `ProtocolRequestError` | - | - | - | - |
| `loads` | - | - | - | - |
| `ProtocolRequestError` | - | - | - | - |
| `_validate_protocol_request` | `data: object` | `PROTOCOL_VERSION`, `ProtocolRequestError`, `PROTOCOL_VERSION`, `KNOWLEDGE_PROTOCOL_VERSION` | `exc.protocol` | `_validate_protocol_request_impl(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 3403 | `getattr(args, 'request', None)` |
| run | _run_protocol | 3404 | `_run_protocol(args)` |
| _run_protocol | getattr | 3292 | `getattr(args, 'output', None)` |
| _run_protocol | _read_protocol_request | 3295 | `_read_protocol_request(args.request)` |
| _read_protocol_request | read | 1011 | `sys.stdin.read(data not statically known)` |
| _read_protocol_request | read_text | 1013 | `Path(source).read_text(encoding='utf-8')` |
| _read_protocol_request | Path | 1013 | `Path(source)` |
| _read_protocol_request | ProtocolRequestError | 1016 | `ProtocolRequestError(..., 'request')` |
| _read_protocol_request | loads | 1019 | `json.loads(raw)` |
| _read_protocol_request | ProtocolRequestError | 1021 | `ProtocolRequestError(..., 'request')` |
| _read_protocol_request | _validate_protocol_request | 1023 | `_validate_protocol_request(data)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 3420 |
| output | `print` | `run` | 3423 |
| output | `print` | `run` | 3457 |
| output | `print` | `run` | 3460 |
| output | `print` | `run` | 3467 |
| output | `print` | `run` | 3469 |
| output | `print` | `run` | 3478 |
| output | `print` | `run` | 3480 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 3403 |
| unresolved_call | `_run_protocol` | `getattr` | 3292 |
| external_call | `_read_protocol_request` | `sys.stdin.read` | 1011 |
| unresolved_call | `_read_protocol_request` | `Path(source).read_text` | 1013 |
| external_call | `_read_protocol_request` | `json.loads` | 1019 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
