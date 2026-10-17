# extract

**Entry point:** `run` (`cli`)
**Source:** [extraction_service](../modules/extraction_service.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [api_contracts](../modules/api_contracts.md), [common](../modules/common.md), and 29 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [api_contracts](../modules/api_contracts.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [go_calls](../modules/go_calls.md)
- [imports](../modules/imports.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [packages](../modules/packages.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_bindings](../modules/python_bindings.md)
- [python_calls](../modules/python_calls.md)
- [python_contracts](../modules/python_contracts.md)
- [python_implementation](../modules/python_implementation.md)
- [python_imports](../modules/python_imports.md)
- [python_observations](../modules/python_observations.md)
- [resource_diagnostics](../modules/resource_diagnostics.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)
- [yaml_syntax](../modules/yaml_syntax.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as build_extract_payload
    participant p2 as write_text_output
    participant p3 as format_unsupported_source_summary
    participant p4 as print_inventory_failures
    participant p5 as validate_source_root
    participant p6 as _format_unsupported_language_count
    participant p7 as validate_source_paths
    participant p8 as _write_utf8_text
    participant p9 as _source_snapshot_for_inventory_request
    participant p10 as _git_changed_files
    participant p11 as _build_extract_source_snapshot
    participant p12 as _partition_snapshot_git_changes
    participant p13 as analyze_dependencies
    participant p14 as build_api_contracts
    participant p15 as _data_flow_details_contract
    participant p16 as get_inventory_result
    participant p17 as detect_entry_points
    participant p18 as read_console_scripts
    participant p19 as attach_routes_to_entry_points
    participant p20 as resolve_call_edges
    participant p21 as build_data_flow_context
    participant p22 as analyze_data_flow_detailed
    participant p23 as build_flow_detailed
    participant p24 as _summarize_inventory
    participant p25 as get_docker_inventory
    participant p26 as validate_path
    participant p27 as build_source_snapshot
    participant p28 as build_dependency_graph
    participant p29 as getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    participant p30 as message.startswith
    p0->>p1: build_extract_payload
    p0->>p2: write_text_output
    p0->>p3: format_unsupported_source_summary
    p0->>p4: print_inventory_failures
    p1->>p5: validate_source_root
    p3->>p6: _format_unsupported_language_count
    p1->>p7: validate_source_paths
    p2->>p8: _write_utf8_text
    p1->>p9: _source_snapshot_for_inventory_request
    p1->>p10: _git_changed_files
    p1->>p11: _build_extract_source_snapshot
    p1->>p12: _partition_snapshot_git_changes
    p1->>p13: analyze_dependencies
    p1->>p14: build_api_contracts
    p1->>p15: _data_flow_details_contract
    p1->>p16: get_inventory_result
    p1->>p17: detect_entry_points
    p1->>p18: read_console_scripts
    p1->>p19: attach_routes_to_entry_points
    p1->>p20: resolve_call_edges
    p1->>p21: build_data_flow_context
    p1->>p22: analyze_data_flow_detailed
    p1->>p23: build_flow_detailed
    p1->>p24: _summarize_inventory
    p1->>p25: get_docker_inventory
    p5->>p26: validate_path
    p9->>p27: build_source_snapshot
    p13->>p28: build_dependency_graph
    p0-->>p29: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'src_dir', '.')
    p0-->>p30: message.startswith('No files found for package')
```

> Call sequence diagram shows 30 of 3128 interactions; 3098 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1055 (1054 omitted); unresolved 1 of 1298 (1297 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/extraction_service.py:run` | 1 | - | external | 36 |
| `src/llm_wiki_cli/config.py:validate_path` | 24 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 24 | - | unresolved | 3 |
| `src/llm_wiki_cli/config.py:validate_path` | 24 | - | external | 2 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 23 | - | unresolved | 5 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 23 | - | external | 11 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 23 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 6 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 23 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 1 |
> Omission summary shows 8 of 702 groups; 694 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/services/extraction_service.py:run)"]
    s3["3. getattr (src/llm_wiki_cli/services/extraction_service.py:run)"]
    s4["4. getattr (src/llm_wiki_cli/services/extraction_service.py:run)"]
    s5["5. getattr (src/llm_wiki_cli/services/extraction_service.py:run)"]
    s6["6. getattr (src/llm_wiki_cli/services/extraction_service.py:run)"]
    s7["7. getattr (src/llm_wiki_cli/services/extraction_service.py:run)"]
    s8["8. getattr (src/llm_wiki_cli/services/extraction_service.py:run)"]
    s9["9. getattr (src/llm_wiki_cli/services/extraction_service.py:run)"]
    s10["10. getattr (src/llm_wiki_cli/services/extraction_service.py:run)"]
    s11["11. getattr (src/llm_wiki_cli/services/extraction_service.py:run)"]
    s12["12. getattr (src/llm_wiki_cli/services/extraction_service.py:run)"]
    s1 -. "getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'src_dir', '.')" .-> s2
    s1 -. "getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'changed', False)" .-> s3
    s1 -. "getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'summary', False)" .-> s4
    s1 -. "getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'deep', False)" .-> s5
    s1 -. "getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'paths', None)" .-> s6
    s1 -. "getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'package', None)" .-> s7
    s1 -. "getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'include_empty', False)" .-> s8
    s1 -. "getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'output', None)" .-> s9
    s1 -. "getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'read_only', False)" .-> s10
    s1 -. "getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'allow_external_src', False)" .-> s11
    s1 -. "getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'helper_cache_dir', None)" .-> s12
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
    click s1 "../modules/extraction_service.md"
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
| `run` | `args` | `sys`, `sys`, `sys`, `sys`, `ExtractorFailureError`, `PathValidationError`, `sys`, `sys` | - | `none` |
| `getattr (src/llm_wiki_cli/services/extraction_service.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/services/extraction_service.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/services/extraction_service.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/services/extraction_service.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/services/extraction_service.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/services/extraction_service.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/services/extraction_service.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/services/extraction_service.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/services/extraction_service.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/services/extraction_service.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/services/extraction_service.py:run)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2416 | `getattr(args, 'src_dir', '.')` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2417 | `getattr(args, 'changed', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2418 | `getattr(args, 'summary', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2419 | `getattr(args, 'deep', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2420 | `getattr(args, 'paths', None)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2421 | `getattr(args, 'package', None)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2422 | `getattr(args, 'include_empty', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2423 | `getattr(args, 'output', None)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2424 | `getattr(args, 'read_only', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2425 | `getattr(args, 'allow_external_src', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2426 | `getattr(args, 'helper_cache_dir', None)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 2432 |
| output | `print` | `run` | 2436 |
| output | `print` | `run` | 2438 |
| output | `print` | `run` | 2440 |
| output | `print` | `run` | 2466 |
| output | `print` | `run` | 2468 |
| output | `print` | `run` | 2473 |
| output | `print` | `run` | 2477 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 2416 |
| external_call | `run` | `getattr` | 2417 |
| external_call | `run` | `getattr` | 2418 |
| external_call | `run` | `getattr` | 2419 |
| external_call | `run` | `getattr` | 2420 |
| external_call | `run` | `getattr` | 2421 |
| external_call | `run` | `getattr` | 2422 |
| external_call | `run` | `getattr` | 2423 |
| external_call | `run` | `getattr` | 2424 |
| external_call | `run` | `getattr` | 2425 |
| external_call | `run` | `getattr` | 2426 |
| step_limit | `run` | `first 12 steps` | 0 |

## Behavior

Builds the stable extraction payload for the requested source boundary and
writes JSON to stdout or an explicitly selected output. Changed, path, package,
summary, and deep modes narrow or enrich that payload without importing the
target application. Extractor failures are reported on stderr and return a
nonzero status; successful output retains the source-relative inventory
contract.
