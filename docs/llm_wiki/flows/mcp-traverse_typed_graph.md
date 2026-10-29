# traverse_typed_graph

**Entry point:** `traverse_typed_graph` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as traverse_typed_graph
    participant p1 as _native_tool_call
    participant p2 as callback
    participant p3 as str
    participant p4 as CallToolResult
    participant p5 as TextContent
    participant p6 as json.dumps
    p0->>p1: _native_tool_call
    p1-->>p2: callback(..., **=kwargs)
    p1-->>p3: str(exc)
    p1-->>p4: CallToolResult(isError=True, content=[...], structuredContent=failure)
    p1-->>p5: TextContent(type='text', text=json.dumps(...))
    p1-->>p6: json.dumps(failure, sort_keys=True)
```

> Call sequence diagram shows 6 of 6 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 4 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 2; effect analysis evaluated: 2, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. traverse_typed_graph"]
    s2["2. _native_tool_call"]
    s3["3. callback"]
    s4["4. str"]
    s5["5. CallToolResult"]
    s6["6. TextContent"]
    s7["7. json.dumps"]
    s1 -->|"_native_tool_call(…)"| s2
    s2 -. "callback(..., **=kwargs)" .-> s3
    s2 -. "str(exc)" .-> s4
    s2 -. "CallToolResult(isError=True, content=[...], structuredContent=failure)" .-> s5
    s2 -. "TextContent(type='text', text=json.dumps(...))" .-> s6
    s2 -. "json.dumps(failure, sort_keys=True)" .-> s7
    click s1 "../modules/mcp_server.md"
    click s2 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `traverse_typed_graph` | `locator_or_exact_route: str`, `direction: str`, `kinds: list[str] \| None`, `origins: list[str] \| None`, `resolutions: list[str] \| None`, `include_evidence: bool`, `limit: int` | - | - | `_native_tool_call(...)` |
| `_native_tool_call` | `callback: Callable[..., Any]`, `args`, `kwargs` | `McpWikiError` | - | `callback(...)`, `CallToolResult(...)` |
| `callback` | - | - | - | - |
| `str` | - | - | - | - |
| `CallToolResult` | - | - | - | - |
| `TextContent` | - | - | - | - |
| `json.dumps` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| traverse_typed_graph | _native_tool_call | 1448 | `_native_tool_call(service.traverse_typed_graph, locator_or_exact_route, direction=direction, kinds=kinds, origins=origins, resolutions=resolutions, include_evidence=include_evidence, limit=limit)` |
| _native_tool_call | callback | 1348 | `callback(..., **=kwargs)` |
| _native_tool_call | str | 1356 | `str(exc)` |
| _native_tool_call | CallToolResult | 1360 | `CallToolResult(isError=True, content=[...], structuredContent=failure)` |
| _native_tool_call | TextContent | 1362 | `TextContent(type='text', text=json.dumps(...))` |
| _native_tool_call | json.dumps | 1362 | `json.dumps(failure, sort_keys=True)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_native_tool_call` | `callback` | 1348 |
| external_call | `_native_tool_call` | `CallToolResult` | 1360 |
| external_call | `_native_tool_call` | `TextContent` | 1362 |
| external_call | `_native_tool_call` | `json.dumps` | 1362 |

## Behavior

This flow starts at `traverse_typed_graph` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
