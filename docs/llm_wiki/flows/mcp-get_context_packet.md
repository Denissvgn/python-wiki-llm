# get_context_packet

**Entry point:** `get_context_packet` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_context_packet
    participant p1 as service.get_context_packet
    participant p2 as str
    participant p3 as CallToolResult
    participant p4 as TextContent
    participant p5 as json.dumps
    p0-->>p1: service.get_context_packet
    p0-->>p2: str
    p0-->>p3: CallToolResult
    p0-->>p4: TextContent
    p0-->>p5: json.dumps
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. get_context_packet"]
    s2["2. service.get_context_packet"]
    s3["3. str"]
    s4["4. CallToolResult"]
    s5["5. TextContent"]
    s6["6. json.dumps"]
    s1 -. "service.get_context_packet(**=options)" .-> s2
    s1 -. "str(exc)" .-> s3
    s1 -. "CallToolResult(isError=True, content=[...], structuredContent=failure)" .-> s4
    s1 -. "TextContent(type='text', text=json.dumps(...))" .-> s5
    s1 -. "json.dumps(failure, sort_keys=True)" .-> s6
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_context_packet` | `budget_tokens: int`, `focus: list[str] \| None`, `format: str`, `filters: dict \| None`, `prefer_fresh: bool`, `if_packet_id: str \| None`, `knowledge_mode: KnowledgeMode \| None` | `McpWikiError` | `options[...]` | `service.get_context_packet(...)`, `CallToolResult(...)` |
| `service.get_context_packet` | - | - | - | - |
| `str` | - | - | - | - |
| `CallToolResult` | - | - | - | - |
| `TextContent` | - | - | - | - |
| `json.dumps` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_context_packet | service.get_context_packet | 1288 | `service.get_context_packet(**=options)` |
| get_context_packet | str | 1298 | `str(exc)` |
| get_context_packet | CallToolResult | 1302 | `CallToolResult(isError=True, content=[...], structuredContent=failure)` |
| get_context_packet | TextContent | 1304 | `TextContent(type='text', text=json.dumps(...))` |
| get_context_packet | json.dumps | 1304 | `json.dumps(failure, sort_keys=True)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `get_context_packet` | `service.get_context_packet` | 1288 |
| external_call | `get_context_packet` | `CallToolResult` | 1302 |
| external_call | `get_context_packet` | `TextContent` | 1304 |
| external_call | `get_context_packet` | `json.dumps` | 1304 |

## Behavior

This flow starts at `get_context_packet` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
