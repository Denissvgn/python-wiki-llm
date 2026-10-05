# maintenance

**Entry point:** `run` (`cli`)
**Source:** [maintenance_cmd](../modules/maintenance_cmd.md)
**Modules touched:** [maintenance_cmd](../modules/maintenance_cmd.md), [request_json](../modules/request_json.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as api.adopt_maintenance
    participant p2 as _capture_options
    participant p3 as api.get_maintenance_status
    participant p4 as api.acknowledge_maintenance
    participant p5 as load_request
    participant p6 as api.recover_maintenance
    participant p7 as print
    participant p8 as json.dumps
    participant p9 as str
    participant p10 as SystemExit
    participant p11 as _render_status
    participant p12 as getattr
    participant p13 as result.get
    participant p14 as parse_request
    participant p15 as lines.append
    participant p16 as stream.read
    participant p17 as Path(…).open
    participant p18 as record.get
    participant p19 as Path
    p0-->>p1: api.adopt_maintenance(args.src_dir, args.wiki_dir, recovery_dir=args.recovery_dir, manifest_format=args.manifest_format, **=_capture_options(...))
    p0->>p2: _capture_options
    p0-->>p3: api.get_maintenance_status(args.src_dir, args.wiki_dir, live=..., record_id=args.record_id, limit=args.limit, **=_capture_options(...))
    p0->>p2: _capture_options
    p0-->>p4: api.acknowledge_maintenance(…)
    p0->>p5: load_request
    p0->>p2: _capture_options
    p0-->>p6: api.recover_maintenance(…)
    p0-->>p7: print(json.dumps(...))
    p0-->>p8: json.dumps({...}, ensure_ascii=False, sort_keys=True)
    p0-->>p9: str(exc)
    p0-->>p10: SystemExit(1)
    p0-->>p7: print(json.dumps(...))
    p0-->>p8: json.dumps({...}, ensure_ascii=False, sort_keys=True)
    p0-->>p9: str(exc)
    p0-->>p10: SystemExit(1)
    p0-->>p7: print(_render_status(...))
    p0->>p11: _render_status
    p0-->>p7: print(json.dumps(...))
    p0-->>p8: json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(...), allow_nan=False)
    p5-->>p12: getattr(sys.stdin, 'buffer', sys.stdin)
    p11-->>p13: result.get('requires_sync')
    p5->>p14: parse_request
    p11-->>p15: lines.append('Current prose requires sync before acknowledgment.')
    p5-->>p16: stream.read(...)
    p11-->>p13: result.get('records', [...])
    p5-->>p17: Path(…).open('rb')
    p11-->>p18: record.get('effective_status')
    p5-->>p19: Path(path)
    p11-->>p15: lines.append(...)
```

> Call sequence diagram shows 30 of 54 interactions; 24 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 13 of 21 (8 omitted); unresolved 11 of 26 (15 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/request_json.py:parse_request` | 9 | - | external | 8 |
| `src/llm_wiki_cli/services/request_json.py:parse_request` | 9 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/request_json.py:load_request` | 7 | [src/llm_wiki_cli/services/request_json.py](../modules/request_json.md) | internal | 1 |
| `src/llm_wiki_cli/services/request_json.py:load_request` | 7 | - | unresolved | 1 |
| `src/llm_wiki_cli/commands/maintenance_cmd.py:_render_status` | 36 | - | unresolved | 12 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. api.adopt_maintenance"]
    s3["3. _capture_options"]
    s4["4. api.get_maintenance_status"]
    s5["5. _capture_options"]
    s6["6. api.acknowledge_maintenance"]
    s7["7. load_request"]
    s8["8. getattr"]
    s9["9. parse_request"]
    s10["10. len"]
    s11["11. isinstance"]
    s12["12. raw.encode"]
    s1 -. "api.adopt_maintenance(args.src_dir, args.wiki_dir, recovery_dir=args.recovery_dir, manifest_format=args.manifest_format, **=_capture_options(...))" .-> s2
    s1 -->|"_capture_options(args)"| s3
    s1 -. "api.get_maintenance_status(args.src_dir, args.wiki_dir, live=..., record_id=args.record_id, limit=args.limit, **=_capture_options(...))" .-> s4
    s1 -->|"_capture_options(args)"| s5
    s1 -. "api.acknowledge_maintenance(…)" .-> s6
    s1 -->|"load_request(args.basis_file)"| s7
    s7 -. "getattr(sys.stdin, 'buffer', sys.stdin)" .-> s8
    s7 -->|"parse_request(stream.read(...))"| s9
    s9 -. "len(...)" .-> s10
    s9 -. "isinstance(raw, bytes)" .-> s11
    s9 -. "raw.encode('utf-8')" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    click s1 "../modules/maintenance_cmd.md"
    click s3 "../modules/maintenance_cmd.md"
    click s5 "../modules/maintenance_cmd.md"
    click s7 "../modules/request_json.md"
    click s9 "../modules/request_json.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | - | - | - |
| `api.adopt_maintenance` | - | - | - | - |
| `_capture_options` | `args` | - | - | `{...}` |
| `api.get_maintenance_status` | - | - | - | - |
| `_capture_options` | `args` | - | - | `{...}` |
| `api.acknowledge_maintenance` | - | - | - | - |
| `load_request` | `path: str` | `sys`, `MAX_REQUEST_BYTES`, `MAX_REQUEST_BYTES` | - | `parse_request(...)`, `parse_request(...)` |
| `getattr` | - | - | - | - |
| `parse_request` | `raw: bytes \| str` | `MAX_REQUEST_BYTES`, `_pairs`, `_constant`, `json` | - | `value` |
| `len` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `raw.encode` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | api.adopt_maintenance | 58 | `api.adopt_maintenance(args.src_dir, args.wiki_dir, recovery_dir=args.recovery_dir, manifest_format=args.manifest_format, **=_capture_options(...))` |
| run | _capture_options | 63 | `_capture_options(args)` |
| run | api.get_maintenance_status | 66 | `api.get_maintenance_status(args.src_dir, args.wiki_dir, live=..., record_id=args.record_id, limit=args.limit, **=_capture_options(...))` |
| run | _capture_options | 72 | `_capture_options(args)` |
| run | api.acknowledge_maintenance | 75 | `api.acknowledge_maintenance(args.src_dir, args.wiki_dir, record_id=args.record_id, expected_state_hash=args.expected_state_hash, expected_basis=load_request(...), actor_kind=args.actor_kind, actor_id=args.actor_id, recovery_dir=args.recovery_dir, **=_capture_options(...))` |
| run | load_request | 80 | `load_request(args.basis_file)` |
| load_request | getattr | 41 | `getattr(sys.stdin, 'buffer', sys.stdin)` |
| load_request | parse_request | 42 | `parse_request(stream.read(...))` |
| parse_request | len | 27 | `len(...)` |
| parse_request | isinstance | 27 | `isinstance(raw, bytes)` |
| parse_request | raw.encode | 27 | `raw.encode('utf-8')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 96 |
| output | `print` | `run` | 112 |
| output | `print` | `run` | 124 |
| output | `print` | `run` | 126 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `api.adopt_maintenance` | 58 |
| unresolved_call | `run` | `api.get_maintenance_status` | 66 |
| unresolved_call | `run` | `api.acknowledge_maintenance` | 75 |
| external_call | `load_request` | `getattr` | 41 |
| external_call | `parse_request` | `isinstance` | 27 |
| unresolved_call | `parse_request` | `raw.encode` | 27 |
| step_limit | `run` | `first 12 steps` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
