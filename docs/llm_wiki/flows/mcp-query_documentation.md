# query_documentation

**Entry point:** `query_documentation` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as query_documentation
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

Collector observations for 2 source steps with known totals: observed: 8, emitted: 8, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. query_documentation"]
    s2["2. _native_tool_call"]
    s3["3. callback"]
    s4["4. str"]
    s5["5. CallToolResult"]
    s6["6. TextContent"]
    s7["7. json.dumps"]
    s1 -->|"_native_tool_call(service.query_documentation, request)"| s2
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
| `query_documentation` | `request: dict` | - | - | `_native_tool_call(...)` |
| `_native_tool_call` | `callback: Callable[..., Any]`, `args`, `kwargs` | `McpWikiError` | - | `callback(...)`, `CallToolResult(...)` |
| `callback` | - | - | - | - |
| `str` | - | - | - | - |
| `CallToolResult` | - | - | - | - |
| `TextContent` | - | - | - | - |
| `json.dumps` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| query_documentation | _native_tool_call | 1399 | `_native_tool_call(service.query_documentation, request)` |
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

This flow starts at `query_documentation` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.

The shared dispatcher also supports bounded evidence explanation. Snapshot
requests do not extract source; live requests explicitly authorize the full
inventory cost. Existing dedicated explain_evidence behavior stays compatible.
Receipt inspection reads existing helper state and runtime versions without setup;
missing, mismatched and truncated data remain limitations, not passing evidence.
