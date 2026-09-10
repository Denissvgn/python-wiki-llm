# extract

**Entry point:** `run` (`cli`)
**Source:** [extraction_service](../modules/extraction_service.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [common](../modules/common.md), [config](../modules/config.md), [data_flow](../modules/data_flow.md), and 20 more

**Complete modules touched:**

- [api_contracts](../modules/api_contracts.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [imports](../modules/imports.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_calls](../modules/python_calls.md)
- [python_contracts](../modules/python_contracts.md)
- [python_imports](../modules/python_imports.md)
- [python_observations](../modules/python_observations.md)
- [resource_diagnostics](../modules/resource_diagnostics.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    participant p2 as print (src/llm_wiki_cli/services/extraction_service.py:run)
    participant p3 as sys.exit
    participant p4 as len (src/llm_wiki_cli/services/extraction_service.py:run)
    participant p5 as build_extract_payload
    participant p6 as validate_source_root
    participant p7 as validate_path
    participant p8 as PathValidationError
    participant p9 as (…).resolve
    participant p10 as Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    participant p11 as Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)
    participant p12 as resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p1: getattr (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p2: print (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p3: sys.exit
    p0-->>p2: print (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p2: print (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p4: len (src/llm_wiki_cli/services/extraction_service.py:run)
    p0-->>p2: print (src/llm_wiki_cli/services/extraction_service.py:run)
    p0->>p5: build_extract_payload
    p5->>p6: validate_source_root
    p6->>p7: validate_path
    p7->>p8: PathValidationError
    p7-->>p9: (…).resolve
    p7-->>p10: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p7-->>p11: Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)
    p7-->>p10: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p7-->>p12: resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    p7->>p8: PathValidationError
```

> Call sequence diagram shows 30 of 2650 interactions; 2620 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

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
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2265 | `getattr(args, 'src_dir', '.')` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2266 | `getattr(args, 'changed', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2267 | `getattr(args, 'summary', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2268 | `getattr(args, 'deep', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2269 | `getattr(args, 'paths', None)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2270 | `getattr(args, 'package', None)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2271 | `getattr(args, 'include_empty', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2272 | `getattr(args, 'output', None)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2273 | `getattr(args, 'read_only', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2274 | `getattr(args, 'allow_external_src', False)` |
| run | getattr (src/llm_wiki_cli/services/extraction_service.py:run) | 2275 | `getattr(args, 'helper_cache_dir', None)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 2281 |
| output | `print` | `run` | 2285 |
| output | `print` | `run` | 2287 |
| output | `print` | `run` | 2289 |
| output | `print` | `run` | 2315 |
| output | `print` | `run` | 2317 |
| output | `print` | `run` | 2322 |
| output | `print` | `run` | 2326 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 2265 |
| external_call | `run` | `getattr` | 2266 |
| external_call | `run` | `getattr` | 2267 |
| external_call | `run` | `getattr` | 2268 |
| external_call | `run` | `getattr` | 2269 |
| external_call | `run` | `getattr` | 2270 |
| external_call | `run` | `getattr` | 2271 |
| external_call | `run` | `getattr` | 2272 |
| external_call | `run` | `getattr` | 2273 |
| external_call | `run` | `getattr` | 2274 |
| external_call | `run` | `getattr` | 2275 |
| step_limit | `run` | `first 12 steps` | 0 |

## Behavior

Builds the stable extraction payload for the requested source boundary and
writes JSON to stdout or an explicitly selected output. Changed, path, package,
summary, and deep modes narrow or enrich that payload without importing the
target application. Extractor failures are reported on stderr and return a
nonzero status; successful output retains the source-relative inventory
contract.
