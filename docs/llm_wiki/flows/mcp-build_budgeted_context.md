# build_budgeted_context

**Entry point:** `build_budgeted_context` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_budgeted_context
    participant p1 as _native_tool_call
    participant p2 as isinstance
    participant p3 as CallToolResult (src/llm_wiki_cli/services….py:build_budgeted_context)
    participant p4 as TextContent (src/llm_wiki_cli/services….py:build_budgeted_context)
    participant p5 as callback
    participant p6 as str
    participant p7 as CallToolResult (src/llm_wiki_cli/services…erver.py:_native_tool_call)
    participant p8 as TextContent (src/llm_wiki_cli/services…erver.py:_native_tool_call)
    participant p9 as json.dumps
    p0->>p1: _native_tool_call
    p0-->>p2: isinstance(result, str)
    p0-->>p3: CallToolResult (src/llm_wiki_cli/services….py:build_budgeted_context)(content=[...])
    p0-->>p4: TextContent (src/llm_wiki_cli/services….py:build_budgeted_context)(type='text', text=result)
    p1-->>p5: callback(..., **=kwargs)
    p1-->>p6: str(exc)
    p1-->>p7: CallToolResult (src/llm_wiki_cli/services…erver.py:_native_tool_call)(isError=True, content=[...], structuredContent=failure)
    p1-->>p8: TextContent (src/llm_wiki_cli/services…erver.py:_native_tool_call)(type='text', text=json.dumps(...))
    p1-->>p9: json.dumps(failure, sort_keys=True)
```

> Call sequence diagram shows 9 of 9 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 7 of 7 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_budgeted_context"]
    s2["2. _native_tool_call"]
    s3["3. callback"]
    s4["4. str"]
    s5["5. CallToolResult (src/llm_wiki_cli/services…erver.py:_native_tool_call)"]
    s6["6. TextContent (src/llm_wiki_cli/services…erver.py:_native_tool_call)"]
    s7["7. json.dumps"]
    s8["8. isinstance"]
    s9["9. CallToolResult (src/llm_wiki_cli/services….py:build_budgeted_context)"]
    s10["10. TextContent (src/llm_wiki_cli/services….py:build_budgeted_context)"]
    s1 -->|"_native_tool_call(service.build_budgeted_context, request)"| s2
    s2 -. "callback(..., **=kwargs)" .-> s3
    s2 -. "str(exc)" .-> s4
    s2 -. "CallToolResult (src/llm_wiki_cli/services…erver.py:_native_tool_call)(isError=True, content=[...], structuredContent=failure)" .-> s5
    s2 -. "TextContent (src/llm_wiki_cli/services…erver.py:_native_tool_call)(type='text', text=json.dumps(...))" .-> s6
    s2 -. "json.dumps(failure, sort_keys=True)" .-> s7
    s1 -. "isinstance(result, str)" .-> s8
    s1 -. "CallToolResult (src/llm_wiki_cli/services….py:build_budgeted_context)(content=[...])" .-> s9
    s1 -. "TextContent (src/llm_wiki_cli/services….py:build_budgeted_context)(type='text', text=result)" .-> s10
    click s1 "../modules/mcp_server.md"
    click s2 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_budgeted_context` | `request: dict` | - | - | `CallToolResult(...)`, `result` |
| `_native_tool_call` | `callback: Callable[..., Any]`, `args`, `kwargs` | `McpWikiError` | - | `callback(...)`, `CallToolResult(...)` |
| `callback` | - | - | - | - |
| `str` | - | - | - | - |
| `CallToolResult (src/llm_wiki_cli/services…erver.py:_native_tool_call)` | - | - | - | - |
| `TextContent (src/llm_wiki_cli/services…erver.py:_native_tool_call)` | - | - | - | - |
| `json.dumps` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `CallToolResult (src/llm_wiki_cli/services….py:build_budgeted_context)` | - | - | - | - |
| `TextContent (src/llm_wiki_cli/services….py:build_budgeted_context)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_budgeted_context | _native_tool_call | 1572 | `_native_tool_call(service.build_budgeted_context, request)` |
| _native_tool_call | callback | 1354 | `callback(..., **=kwargs)` |
| _native_tool_call | str | 1362 | `str(exc)` |
| _native_tool_call | CallToolResult (src/llm_wiki_cli/services…erver.py:_native_tool_call) | 1366 | `CallToolResult(isError=True, content=[...], structuredContent=failure)` |
| _native_tool_call | TextContent (src/llm_wiki_cli/services…erver.py:_native_tool_call) | 1368 | `TextContent(type='text', text=json.dumps(...))` |
| _native_tool_call | json.dumps | 1368 | `json.dumps(failure, sort_keys=True)` |
| build_budgeted_context | isinstance | 1573 | `isinstance(result, str)` |
| build_budgeted_context | CallToolResult (src/llm_wiki_cli/services….py:build_budgeted_context) | 1574 | `CallToolResult(content=[...])` |
| build_budgeted_context | TextContent (src/llm_wiki_cli/services….py:build_budgeted_context) | 1574 | `TextContent(type='text', text=result)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_native_tool_call` | `callback` | 1354 |
| external_call | `_native_tool_call` | `CallToolResult` | 1366 |
| external_call | `_native_tool_call` | `TextContent` | 1368 |
| external_call | `_native_tool_call` | `json.dumps` | 1368 |
| external_call | `build_budgeted_context` | `isinstance` | 1573 |
| external_call | `build_budgeted_context` | `CallToolResult` | 1574 |
| external_call | `build_budgeted_context` | `TextContent` | 1574 |

## Behavior

Requires a versioned v3 request with explicit change selection. Trusted server configuration supplies any exact counter. One canonical text representation preserves the declared count; cannot-fit and capability errors never return a partial successful context. Transport and host framing remain outside that count.
