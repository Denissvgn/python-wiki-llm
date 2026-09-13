# build_budgeted_context

**Entry point:** `build_budgeted_context` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [change_selection](../modules/change_selection.md), [common](../modules/common.md), and 40 more

**Complete modules touched:**

- [api](../modules/api.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [change_selection](../modules/change_selection.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_budget](../modules/context_budget.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [go_calls](../modules/go_calls.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [python_calls](../modules/python_calls.md)
- [python_imports](../modules/python_imports.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [token_counting](../modules/token_counting.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_budgeted_context (src/llm_wiki_cli/api.py)
    participant p1 as build_budgeted_context (src/llm_wiki_cli/services/context_budget.py)
    participant p2 as validate_request
    participant p3 as set (src/llm_wiki_cli/services…udget.py:validate_request)
    participant p4 as ProtocolRequestError
    participant p5 as sorted (src/llm_wiki_cli/services…udget.py:validate_request)
    participant p6 as dict (src/llm_wiki_cli/services…udget.py:validate_request)
    participant p7 as data.get (src/llm_wiki_cli/services…udget.py:validate_request)
    participant p8 as legacy.pop
    participant p9 as _validate_protocol_request
    participant p10 as isinstance (src/llm_wiki_cli/services…validate_protocol_request)
    participant p11 as data.get (src/llm_wiki_cli/services…validate_protocol_request)
    participant p12 as _validate_protocol_request_impl
    participant p13 as isinstance (src/llm_wiki_cli/services…ate_protocol_request_impl)
    participant p14 as any (src/llm_wiki_cli/services…ate_protocol_request_impl)
    participant p15 as data.get (src/llm_wiki_cli/services…ate_protocol_request_impl)
    participant p16 as sorted (src/llm_wiki_cli/services…ate_protocol_request_impl)
    participant p17 as set (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p0->>p1: build_budgeted_context (src/llm_wiki_cli/services/context_budget.py)
    p1->>p2: validate_request
    p2-->>p3: set (src/llm_wiki_cli/services…udget.py:validate_request)
    p2->>p4: ProtocolRequestError
    p2-->>p5: sorted (src/llm_wiki_cli/services…udget.py:validate_request)
    p2-->>p6: dict (src/llm_wiki_cli/services…udget.py:validate_request)
    p2-->>p7: data.get (src/llm_wiki_cli/services…udget.py:validate_request)
    p2-->>p7: data.get (src/llm_wiki_cli/services…udget.py:validate_request)
    p2-->>p7: data.get (src/llm_wiki_cli/services…udget.py:validate_request)
    p2-->>p8: legacy.pop
    p2-->>p8: legacy.pop
    p2-->>p8: legacy.pop
    p2->>p9: _validate_protocol_request
    p9-->>p10: isinstance (src/llm_wiki_cli/services…validate_protocol_request)
    p9-->>p11: data.get (src/llm_wiki_cli/services…validate_protocol_request)
    p9->>p12: _validate_protocol_request_impl
    p12-->>p13: isinstance (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p12->>p4: ProtocolRequestError
    p12-->>p14: any (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p12-->>p13: isinstance (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p12->>p4: ProtocolRequestError
    p12-->>p15: data.get (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p12->>p2: validate_request
    p12->>p4: ProtocolRequestError
    p12-->>p16: sorted (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p12-->>p17: set (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p12->>p4: ProtocolRequestError
    p12->>p4: ProtocolRequestError
    p12-->>p13: isinstance (src/llm_wiki_cli/services…ate_protocol_request_impl)
    p12-->>p13: isinstance (src/llm_wiki_cli/services…ate_protocol_request_impl)
```

> Call sequence diagram shows 30 of 2769 interactions; 2739 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_budgeted_context (src/llm_wiki_cli/api.py)"]
    s2["2. build_budgeted_context (src/llm_wiki_cli/services/context_budget.py)"]
    s3["3. validate_request"]
    s4["4. set (src/llm_wiki_cli/services…udget.py:validate_request)"]
    s5["5. ProtocolRequestError"]
    s6["6. sorted (src/llm_wiki_cli/services…udget.py:validate_request)"]
    s7["7. dict (src/llm_wiki_cli/services…udget.py:validate_request)"]
    s8["8. data.get (src/llm_wiki_cli/services…udget.py:validate_request)"]
    s9["9. data.get (src/llm_wiki_cli/services…udget.py:validate_request)"]
    s10["10. data.get (src/llm_wiki_cli/services…udget.py:validate_request)"]
    s11["11. legacy.pop"]
    s12["12. legacy.pop"]
    s1 -->|"build_budgeted_context (src/llm_wiki_cli/services/context_budget.py)(…)"| s2
    s2 -->|"validate_request(...)"| s3
    s3 -. "set (src/llm_wiki_cli/services…udget.py:validate_request)(data)" .-> s4
    s3 -->|"ProtocolRequestError(...)"| s5
    s3 -. "sorted (src/llm_wiki_cli/services…udget.py:validate_request)(unknown)" .-> s6
    s3 -. "dict (src/llm_wiki_cli/services…udget.py:validate_request)(data)" .-> s7
    s3 -. "data.get (src/llm_wiki_cli/services…udget.py:validate_request)('knowledge_mode', 'off')" .-> s8
    s3 -. "data.get (src/llm_wiki_cli/services…udget.py:validate_request)('format')" .-> s9
    s3 -. "data.get (src/llm_wiki_cli/services…udget.py:validate_request)('format', 'json')" .-> s10
    s3 -. "legacy.pop('budget_mode', None)" .-> s11
    s3 -. "legacy.pop('counter_id', None)" .-> s12
    b0["mutation legacy.update"]
    s2 -. "mutation legacy.update" .-> b0
    b1["mutation legacy.pop"]
    s3 -. "mutation legacy.pop" .-> b1
    b2["mutation legacy.pop"]
    s3 -. "mutation legacy.pop" .-> b2
    b3["mutation legacy.pop"]
    s3 -. "mutation legacy.pop" .-> b3
    click s1 "../modules/api.md"
    click s2 "../modules/context_budget.md"
    click s3 "../modules/context_budget.md"
    click s5 "../modules/context_service.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_budgeted_context (src/llm_wiki_cli/api.py)` | `src_dir: str`, `wiki_dir: str`, `request: Mapping[str, Any] \| None`, `counter: TokenCounter \| None`, `allow_external_src: bool`, `source_selection: str \| Path \| None` | - | - | `build(...)` |
| `build_budgeted_context (src/llm_wiki_cli/services/context_budget.py)` | `src_dir`, `wiki_dir`, `request`, `counter: TokenCounter \| None`, `allow_external_src`, `source_selection` | `context`, `context` | `changes[...]` | `result` |
| `validate_request` | `data: Mapping[str, Any]` | `context`, `context`, `CONTEXT_BUDGET_PROTOCOL_VERSION` | `legacy[...]`, `legacy[...]`, `legacy[...]` | `{...}` |
| `set (src/llm_wiki_cli/services…udget.py:validate_request)` | - | - | - | - |
| `ProtocolRequestError` | - | - | - | - |
| `sorted (src/llm_wiki_cli/services…udget.py:validate_request)` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…udget.py:validate_request)` | - | - | - | - |
| `data.get (src/llm_wiki_cli/services…udget.py:validate_request)` | - | - | - | - |
| `data.get (src/llm_wiki_cli/services…udget.py:validate_request)` | - | - | - | - |
| `data.get (src/llm_wiki_cli/services…udget.py:validate_request)` | - | - | - | - |
| `legacy.pop` | - | - | - | - |
| `legacy.pop` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_budgeted_context (src/llm_wiki_cli/api.py) | build_budgeted_context (src/llm_wiki_cli/services/context_budget.py) | 897 | `build(src_dir, wiki_dir, request, counter=counter, allow_external_src=allow_external_src, source_selection=source_selection)` |
| build_budgeted_context (src/llm_wiki_cli/services/context_budget.py) | validate_request | 186 | `validate_request(...)` |
| validate_request | set (src/llm_wiki_cli/services…udget.py:validate_request) | 34 | `set(data)` |
| validate_request | ProtocolRequestError | 36 | `context.ProtocolRequestError(...)` |
| validate_request | sorted (src/llm_wiki_cli/services…udget.py:validate_request) | 37 | `sorted(unknown)` |
| validate_request | dict (src/llm_wiki_cli/services…udget.py:validate_request) | 39 | `dict(data)` |
| validate_request | data.get (src/llm_wiki_cli/services…udget.py:validate_request) | 41 | `data.get('knowledge_mode', 'off')` |
| validate_request | data.get (src/llm_wiki_cli/services…udget.py:validate_request) | 43 | `data.get('format')` |
| validate_request | data.get (src/llm_wiki_cli/services…udget.py:validate_request) | 43 | `data.get('format', 'json')` |
| validate_request | legacy.pop | 45 | `legacy.pop('budget_mode', None)` |
| validate_request | legacy.pop | 46 | `legacy.pop('counter_id', None)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `legacy.update` | `build_budgeted_context` | 227 |
| mutation | `legacy.pop` | `validate_request` | 45 |
| mutation | `legacy.pop` | `validate_request` | 46 |
| mutation | `legacy.pop` | `validate_request` | 47 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_request` | `sorted` | 37 |
| unresolved_call | `validate_request` | `data.get` | 41 |
| unresolved_call | `validate_request` | `data.get` | 43 |
| step_limit | `build_budgeted_context` | `first 12 steps` | 0 |
| truncated_flow | `build_budgeted_context` | `depth limit` | 0 |

## Behavior

This flow starts at `build_budgeted_context` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
