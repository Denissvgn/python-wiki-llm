# extract

**Entry point:** `run` (`cli`)
**Source:** [extraction_service](../modules/extraction_service.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [api_contracts](../modules/api_contracts.md), [common](../modules/common.md), and 28 more

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

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    participant p2 as print (src/llm_wiki_cli/services/extraction_service.py:run)
    participant p3 as sys.exit
    participant p4 as len (src/llm_wiki_cli/services/extraction_service.py:run)
    participant p5 as build_extract_payload
    participant p6 as print_inventory_failures
    participant p7 as str (src/llm_wiki_cli/services/extraction_service.py:run)
    participant p8 as message.startswith
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'src_dir', '.')
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'changed', False)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'summary', False)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'deep', False)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'paths', None)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'package', None)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'include_empty', False)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'output', None)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'read_only', False)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'allow_external_src', False)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'helper_cache_dir', None)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'include_tests', None)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'openapi_file', None)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)(args, 'source_selection', None)
    p0-->>p2: print (src/llm_wiki_cli/services/extraction_service.py:run)('Error: --changed and --paths are mutually exclusive.', file=sys.stderr)
    p0-->>p3: sys.exit(2)
    p0-->>p2: print (src/llm_wiki_cli/services/extraction_service.py:run)('Extracting changed file(s)...', file=sys.stderr)
    p0-->>p2: print (src/llm_wiki_cli/services/extraction_service.py:run)(..., file=sys.stderr)
    p0-->>p4: len (src/llm_wiki_cli/services/extraction_service.py:run)(paths)
    p0-->>p2: print (src/llm_wiki_cli/services/extraction_service.py:run)(..., file=sys.stderr)
    p0->>p5: build_extract_payload
    p0->>p6: print_inventory_failures
    p0-->>p3: sys.exit(1)
    p0-->>p7: str (src/llm_wiki_cli/services/extraction_service.py:run)(exc)
    p0-->>p8: message.startswith('No files found for package')
    p0-->>p2: print (src/llm_wiki_cli/services/extraction_service.py:run)(message, file=sys.stderr)
    p0-->>p3: sys.exit(1)
    p0-->>p2: print (src/llm_wiki_cli/services/extraction_service.py:run)(..., file=sys.stderr)
    p0-->>p3: sys.exit(2)
    p0-->>p2: print (src/llm_wiki_cli/services/extraction_service.py:run)('No files changed in the last commit.', file=sys.stderr)
```

> Call sequence diagram shows 30 of 3111 interactions; 3081 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 27 of 1030 (1003 omitted); unresolved 1 of 1315 (1314 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/extraction_service.py:build_extract_payload` | 22 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 23 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 7 |
| `src/llm_wiki_cli/config.py:validate_path` | 24 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 24 | - | unresolved | 3 |
| `src/llm_wiki_cli/config.py:validate_path` | 24 | - | external | 2 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 23 | - | unresolved | 5 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 23 | - | external | 11 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 23 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 1 |
> Omission summary shows 8 of 705 groups; 697 further groups are not expanded here. Counts above include all omitted interactions.
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
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2388 | `getattr(args, 'src_dir', '.')` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2389 | `getattr(args, 'changed', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2390 | `getattr(args, 'summary', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2391 | `getattr(args, 'deep', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2392 | `getattr(args, 'paths', None)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2393 | `getattr(args, 'package', None)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2394 | `getattr(args, 'include_empty', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2395 | `getattr(args, 'output', None)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2396 | `getattr(args, 'read_only', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2397 | `getattr(args, 'allow_external_src', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2398 | `getattr(args, 'helper_cache_dir', None)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 2404 |
| output | `print` | `run` | 2408 |
| output | `print` | `run` | 2410 |
| output | `print` | `run` | 2412 |
| output | `print` | `run` | 2438 |
| output | `print` | `run` | 2440 |
| output | `print` | `run` | 2445 |
| output | `print` | `run` | 2449 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 2388 |
| external_call | `run` | `getattr` | 2389 |
| external_call | `run` | `getattr` | 2390 |
| external_call | `run` | `getattr` | 2391 |
| external_call | `run` | `getattr` | 2392 |
| external_call | `run` | `getattr` | 2393 |
| external_call | `run` | `getattr` | 2394 |
| external_call | `run` | `getattr` | 2395 |
| external_call | `run` | `getattr` | 2396 |
| external_call | `run` | `getattr` | 2397 |
| external_call | `run` | `getattr` | 2398 |
| step_limit | `run` | `first 12 steps` | 0 |

## Behavior

Builds the stable extraction payload for the requested source boundary and
writes JSON to stdout or an explicitly selected output. Changed, path, package,
summary, and deep modes narrow or enrich that payload without importing the
target application. Extractor failures are reported on stderr and return a
nonzero status; successful output retains the source-relative inventory
contract.
