# list_concept_sections

**Entry point:** `list_concept_sections` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as list_concept_sections
    participant p1 as _native_tool_call
    participant p2 as callback
    participant p3 as str
    participant p4 as CallToolResult
    participant p5 as TextContent
    participant p6 as json.dumps
    p0->>p1: _native_tool_call
    p1-->>p2: callback
    p1-->>p3: str
    p1-->>p4: CallToolResult
    p1-->>p5: TextContent
    p1-->>p6: json.dumps
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. list_concept_sections"]
    s2["2. _native_tool_call"]
    s3["3. callback"]
    s4["4. str"]
    s5["5. CallToolResult"]
    s6["6. TextContent"]
    s7["7. json.dumps"]
    s1 -->|"_native_tool_call(service.list_concept_sections, locator_or_exact_route, ownership=ownership, limit=limit)"| s2
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
| `list_concept_sections` | `locator_or_exact_route: str`, `ownership: str \| None`, `limit: int` | - | - | `_native_tool_call(...)` |
| `_native_tool_call` | `callback: Callable[..., Any]`, `args`, `kwargs` | `McpWikiError` | - | `callback(...)`, `CallToolResult(...)` |
| `callback` | - | - | - | - |
| `str` | - | - | - | - |
| `CallToolResult` | - | - | - | - |
| `TextContent` | - | - | - | - |
| `json.dumps` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| list_concept_sections | _native_tool_call | 1358 | `_native_tool_call(service.list_concept_sections, locator_or_exact_route, ownership=ownership, limit=limit)` |
| _native_tool_call | callback | 1275 | `callback(..., **=kwargs)` |
| _native_tool_call | str | 1283 | `str(exc)` |
| _native_tool_call | CallToolResult | 1287 | `CallToolResult(isError=True, content=[...], structuredContent=failure)` |
| _native_tool_call | TextContent | 1289 | `TextContent(type='text', text=json.dumps(...))` |
| _native_tool_call | json.dumps | 1289 | `json.dumps(failure, sort_keys=True)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_native_tool_call` | `callback` | 1275 |
| external_call | `_native_tool_call` | `CallToolResult` | 1287 |
| external_call | `_native_tool_call` | `TextContent` | 1289 |
| external_call | `_native_tool_call` | `json.dumps` | 1289 |

## Behavior

This flow starts at `list_concept_sections` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
