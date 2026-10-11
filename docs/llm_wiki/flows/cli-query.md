# query

**Entry point:** `run` (`cli`)
**Source:** [query_cmd](../modules/query_cmd.md)
**Modules touched:** [api](../modules/api.md), [common](../modules/common.md), [config](../modules/config.md), [context_packet](../modules/context_packet.md), and 27 more

**Complete modules touched:**

- [api](../modules/api.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [io](../modules/io.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [python_implementation](../modules/python_implementation.md)
- [query_cmd](../modules/query_cmd.md)
- [request_json](../modules/request_json.md)
- [source_path_diagnostics](../modules/source_path_diagnostics.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as load_request
    participant p2 as query_documentation
    participant p3 as json.dumps (src/llm_wiki_cli/commands/query_cmd.py:run)
    participant p4 as write_text_output
    participant p5 as write_utf8_stdout
    participant p6 as isinstance (src/llm_wiki_cli/commands/query_cmd.py:run)
    participant p7 as print
    participant p8 as getattr (src/llm_wiki_cli/commands/query_cmd.py:run)
    participant p9 as SystemExit
    participant p10 as getattr (src/llm_wiki_cli/services…uest_json.py:load_request)
    participant p11 as _validate_documentation_query_request
    participant p12 as Path(…).expanduser (src/llm_wiki_cli/services/io.py:write_text_output)
    participant p13 as text.encode
    participant p14 as parse_request
    participant p15 as _impact_query
    participant p16 as Path (src/llm_wiki_cli/services/io.py:write_text_output)
    participant p17 as getattr (src/llm_wiki_cli/services/io.py:write_utf8_stdout)
    participant p18 as stream.read
    participant p19 as _normalize_query_input
    participant p20 as _write_utf8_text
    participant p21 as stream.write
    participant p22 as Path(…).open
    participant p23 as normalize_concept_coordinate
    participant p24 as stream.flush
    participant p25 as Path (src/llm_wiki_cli/services…uest_json.py:load_request)
    participant p26 as request.get (src/llm_wiki_cli/api.py:query_documentation)
    participant p27 as buffer.write
    p0->>p1: load_request
    p0->>p2: query_documentation
    p0-->>p3: json.dumps (src/llm_wiki_cli/commands/query_cmd.py:run)(result, ensure_ascii=False, sort_keys=True, separators=(...), allow_nan=False)
    p0->>p4: write_text_output
    p0->>p5: write_utf8_stdout
    p0-->>p6: isinstance (src/llm_wiki_cli/commands/query_cmd.py:run)(exc, (...))
    p0-->>p7: print(json.dumps(...), file=sys.stderr)
    p0-->>p3: json.dumps (src/llm_wiki_cli/commands/query_cmd.py:run)({...}, sort_keys=True)
    p0-->>p8: getattr (src/llm_wiki_cli/commands/query_cmd.py:run)(exc, 'code', None)
    p0-->>p8: getattr (src/llm_wiki_cli/commands/query_cmd.py:run)(exc, 'details', None)
    p0-->>p9: SystemExit(...)
    p1-->>p10: getattr (src/llm_wiki_cli/services…uest_json.py:load_request)(sys.stdin, 'buffer', sys.stdin)
    p2->>p11: _validate_documentation_query_request
    p4-->>p12: Path(…).expanduser (src/llm_wiki_cli/services/io.py:write_text_output)
    p5-->>p13: text.encode('utf-8')
    p1->>p14: parse_request
    p2->>p15: _impact_query
    p4-->>p16: Path (src/llm_wiki_cli/services/io.py:write_text_output)(path)
    p5-->>p17: getattr (src/llm_wiki_cli/services/io.py:write_utf8_stdout)(stream, 'buffer', None)
    p1-->>p18: stream.read(...)
    p2->>p19: _normalize_query_input
    p4->>p20: _write_utf8_text
    p5-->>p21: stream.write(text)
    p1-->>p22: Path(…).open('rb')
    p2->>p23: normalize_concept_coordinate
    p5-->>p24: stream.flush
    p1-->>p25: Path (src/llm_wiki_cli/services…uest_json.py:load_request)(path)
    p2-->>p26: request.get (src/llm_wiki_cli/api.py:query_documentation)('value')
    p5-->>p27: buffer.write(encoded)
    p1->>p14: parse_request
```

> Call sequence diagram shows 30 of 1449 interactions; 1419 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 11 of 576 (565 omitted); unresolved 8 of 353 (345 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/request_json.py:parse_request` | 4 | - | external | 8 |
| `src/llm_wiki_cli/services/request_json.py:parse_request` | 4 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/request_json.py:load_request` | 2 | - | unresolved | 1 |
| `src/llm_wiki_cli/api.py:_validate_documentation_query_request` | 21 | - | external | 11 |
| `src/llm_wiki_cli/api.py:_validate_documentation_query_request` | 21 | [src/llm_wiki_cli/api.py](../modules/api.md) | internal | 13 |
| `src/llm_wiki_cli/api.py:_validate_documentation_query_request` | 21 | - | unresolved | 11 |
| `src/llm_wiki_cli/api.py:_normalize_query_limit` | 35 | [src/llm_wiki_cli/api.py](../modules/api.md) | internal | 1 |
| `src/llm_wiki_cli/api.py:_normalize_query_input` | 36 | - | unresolved | 1 |
> Omission summary shows 8 of 334 groups; 326 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. load_request"]
    s3["3. getattr (src/llm_wiki_cli/services…uest_json.py:load_request)"]
    s4["4. parse_request"]
    s5["5. len (src/llm_wiki_cli/services…est_json.py:parse_request)"]
    s6["6. isinstance (src/llm_wiki_cli/services…est_json.py:parse_request)"]
    s7["7. raw.encode (src/llm_wiki_cli/services…est_json.py:parse_request)"]
    s8["8. ValueError (src/llm_wiki_cli/services…est_json.py:parse_request)"]
    s9["9. isinstance (src/llm_wiki_cli/services…est_json.py:parse_request)"]
    s10["10. raw.decode"]
    s11["11. json.loads (src/llm_wiki_cli/services…est_json.py:parse_request)"]
    s12["12. ValueError (src/llm_wiki_cli/services…est_json.py:parse_request)"]
    s1 -->|"load_request(args.request)"| s2
    s2 -. "getattr (src/llm_wiki_cli/services…uest_json.py:load_request)(sys.stdin, 'buffer', sys.stdin)" .-> s3
    s2 -->|"parse_request(stream.read(...))"| s4
    s4 -. "len (src/llm_wiki_cli/services…est_json.py:parse_request)(...)" .-> s5
    s4 -. "isinstance (src/llm_wiki_cli/services…est_json.py:parse_request)(raw, bytes)" .-> s6
    s4 -. "raw.encode (src/llm_wiki_cli/services…est_json.py:parse_request)('utf-8')" .-> s7
    s4 -. "ValueError (src/llm_wiki_cli/services…est_json.py:parse_request)('Request exceeds 1 MiB')" .-> s8
    s4 -. "isinstance (src/llm_wiki_cli/services…est_json.py:parse_request)(raw, bytes)" .-> s9
    s4 -. "raw.decode('utf-8')" .-> s10
    s4 -. "json.loads (src/llm_wiki_cli/services…est_json.py:parse_request)(text, object_pairs_hook=_pairs, parse_constant=_constant)" .-> s11
    s4 -. "ValueError (src/llm_wiki_cli/services…est_json.py:parse_request)('Request must be a UTF-8 JSON object')" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    click s1 "../modules/query_cmd.md"
    click s2 "../modules/request_json.md"
    click s4 "../modules/request_json.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `sys` | - | - |
| `load_request` | `path: str` | `sys`, `MAX_REQUEST_BYTES`, `MAX_REQUEST_BYTES` | - | `parse_request(...)`, `parse_request(...)` |
| `getattr (src/llm_wiki_cli/services…uest_json.py:load_request)` | - | - | - | - |
| `parse_request` | `raw: bytes \| str` | `MAX_REQUEST_BYTES`, `_pairs`, `_constant`, `json` | - | `value` |
| `len (src/llm_wiki_cli/services…est_json.py:parse_request)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…est_json.py:parse_request)` | - | - | - | - |
| `raw.encode (src/llm_wiki_cli/services…est_json.py:parse_request)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…est_json.py:parse_request)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…est_json.py:parse_request)` | - | - | - | - |
| `raw.decode` | - | - | - | - |
| `json.loads (src/llm_wiki_cli/services…est_json.py:parse_request)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…est_json.py:parse_request)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | load_request | 16 | `load_request(args.request)` |
| load_request | getattr (src/llm_wiki_cli/services…uest_json.py:load_request) | 41 | `getattr(sys.stdin, 'buffer', sys.stdin)` |
| load_request | parse_request | 42 | `parse_request(stream.read(...))` |
| parse_request | len (src/llm_wiki_cli/services…est_json.py:parse_request) | 27 | `len(...)` |
| parse_request | isinstance (src/llm_wiki_cli/services…est_json.py:parse_request) | 27 | `isinstance(raw, bytes)` |
| parse_request | raw.encode (src/llm_wiki_cli/services…est_json.py:parse_request) | 27 | `raw.encode('utf-8')` |
| parse_request | ValueError (src/llm_wiki_cli/services…est_json.py:parse_request) | 28 | `ValueError('Request exceeds 1 MiB')` |
| parse_request | isinstance (src/llm_wiki_cli/services…est_json.py:parse_request) | 30 | `isinstance(raw, bytes)` |
| parse_request | raw.decode | 30 | `raw.decode('utf-8')` |
| parse_request | json.loads (src/llm_wiki_cli/services…est_json.py:parse_request) | 31 | `json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)` |
| parse_request | ValueError (src/llm_wiki_cli/services…est_json.py:parse_request) | 33 | `ValueError('Request must be a UTF-8 JSON object')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 28 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `load_request` | `getattr` | 41 |
| external_call | `parse_request` | `isinstance` | 27 |
| unresolved_call | `parse_request` | `raw.encode` | 27 |
| external_call | `parse_request` | `ValueError` | 28 |
| external_call | `parse_request` | `isinstance` | 30 |
| unresolved_call | `parse_request` | `raw.decode` | 30 |
| external_call | `parse_request` | `json.loads` | 31 |
| external_call | `parse_request` | `ValueError` | 33 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

Loads a bounded explicit JSON query from a file or stdin, delegates to the public exact-query API, and writes its canonical response to stdout or an explicitly chosen output file. Invalid request data is rejected before query state is loaded.
