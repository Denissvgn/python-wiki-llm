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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as load_request
    participant p2 as query_documentation
    participant p3 as write_text_output
    participant p4 as write_utf8_stdout
    participant p5 as _validate_documentation_query_request
    participant p6 as _impact_query
    participant p7 as _write_utf8_text
    participant p8 as normalize_concept_coordinate
    participant p9 as _require_full_inventory_opt_in
    participant p10 as build_documentation_query_service
    participant p11 as _snapshot_query_service
    participant p12 as _combined_query_payload
    participant p13 as normalize_documentation_query_text
    participant p14 as normalize_supplied_paths
    participant p15 as validate_exact_page_coordinate
    participant p16 as write_bytes_atomic
    participant p17 as supplied_paths_from_unified_diff
    participant p18 as validate_source_root
    participant p19 as _validate_wiki_dir
    participant p20 as _normalize_query_limit
    participant p21 as resolve_source_selection
    participant p22 as _normalize_query_choice
    participant p23 as _existing_supplied_source_paths
    participant p24 as build_live_documentation_query_service
    participant p25 as _normalize_query_values
    participant p26 as build_snapshot_documentation_query_service
    participant p27 as _with_query_envelope
    participant p28 as _normalize_query_input
    participant p29 as json.dumps (src/llm_wiki_cli/commands/query_cmd.py:run)
    participant p30 as Path(…).expanduser (src/llm_wiki_cli/services/io.py:write_text_output)
    p0->>p1: load_request
    p0->>p2: query_documentation
    p0->>p3: write_text_output
    p0->>p4: write_utf8_stdout
    p2->>p5: _validate_documentation_query_request
    p2->>p6: _impact_query
    p3->>p7: _write_utf8_text
    p2->>p8: normalize_concept_coordinate
    p2->>p9: _require_full_inventory_opt_in
    p2->>p10: build_documentation_query_service
    p2->>p11: _snapshot_query_service
    p2->>p12: _combined_query_payload
    p8->>p13: normalize_documentation_query_text
    p6->>p14: normalize_supplied_paths
    p8->>p15: validate_exact_page_coordinate
    p7->>p16: write_bytes_atomic
    p6->>p17: supplied_paths_from_unified_diff
    p6->>p18: validate_source_root
    p6->>p19: _validate_wiki_dir
    p5->>p20: _normalize_query_limit
    p6->>p21: resolve_source_selection
    p5->>p22: _normalize_query_choice
    p6->>p23: _existing_supplied_source_paths
    p6->>p24: build_live_documentation_query_service
    p5->>p25: _normalize_query_values
    p6->>p26: build_snapshot_documentation_query_service
    p6->>p27: _with_query_envelope
    p20->>p28: _normalize_query_input
    p0-->>p29: json.dumps (src/llm_wiki_cli/commands/query_cmd.py:run)(result, ensure_ascii=False, sort_keys=True, separators=(...), allow_nan=False)
    p3-->>p30: Path(…).expanduser (src/llm_wiki_cli/services/io.py:write_text_output)
```

> Call sequence diagram shows 30 of 1460 interactions; 1430 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 581 (580 omitted); unresolved 1 of 359 (358 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/request_json.py:load_request` | 2 | - | external | 2 |
| `src/llm_wiki_cli/services/request_json.py:load_request` | 2 | [src/llm_wiki_cli/services/request_json.py](../modules/request_json.md) | internal | 2 |
| `src/llm_wiki_cli/services/request_json.py:parse_request` | 4 | - | external | 8 |
| `src/llm_wiki_cli/services/request_json.py:parse_request` | 4 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/request_json.py:load_request` | 2 | - | unresolved | 3 |
| `src/llm_wiki_cli/api.py:_validate_documentation_query_request` | 21 | - | external | 11 |
| `src/llm_wiki_cli/api.py:_validate_documentation_query_request` | 21 | [src/llm_wiki_cli/api.py](../modules/api.md) | internal | 10 |
| `src/llm_wiki_cli/api.py:_validate_documentation_query_request` | 21 | - | unresolved | 11 |
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
