# extract

**Entry point:** `run` (`cli`)
**Source:** [extraction_service](../modules/extraction_service.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [common](../modules/common.md), [config](../modules/config.md), [data_flow](../modules/data_flow.md), and 15 more

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
    participant p1 as getattr
    participant p2 as print
    participant p3 as exit
    participant p4 as len
    participant p5 as build_extract_payload
    participant p6 as validate_source_root
    participant p7 as validate_path
    participant p8 as PathValidationError
    participant p9 as resolve
    participant p10 as cwd
    participant p11 as relative_to
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p2: print
    p0-->>p3: exit
    p0-->>p2: print
    p0-->>p2: print
    p0-->>p4: len
    p0-->>p2: print
    p0->>p5: build_extract_payload
    p5->>p6: validate_source_root
    p6->>p7: validate_path
    p7->>p8: PathValidationError
    p7-->>p9: resolve
    p7-->>p10: cwd
    p7-->>p9: resolve
    p7-->>p10: cwd
    p7-->>p11: relative_to
    p7->>p8: PathValidationError
```

> Call sequence diagram shows 30 of 2557 interactions; 2527 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. getattr"]
    s4["4. getattr"]
    s5["5. getattr"]
    s6["6. getattr"]
    s7["7. getattr"]
    s8["8. getattr"]
    s9["9. getattr"]
    s10["10. getattr"]
    s11["11. getattr"]
    s12["12. getattr"]
    s1 -. "getattr(args, 'src_dir', '.')" .-> s2
    s1 -. "getattr(args, 'changed', False)" .-> s3
    s1 -. "getattr(args, 'summary', False)" .-> s4
    s1 -. "getattr(args, 'deep', False)" .-> s5
    s1 -. "getattr(args, 'paths', None)" .-> s6
    s1 -. "getattr(args, 'package', None)" .-> s7
    s1 -. "getattr(args, 'include_empty', False)" .-> s8
    s1 -. "getattr(args, 'output', None)" .-> s9
    s1 -. "getattr(args, 'read_only', False)" .-> s10
    s1 -. "getattr(args, 'allow_external_src', False)" .-> s11
    s1 -. "getattr(args, 'helper_cache_dir', None)" .-> s12
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
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 2186 | `getattr(args, 'src_dir', '.')` |
| run | getattr | 2187 | `getattr(args, 'changed', False)` |
| run | getattr | 2188 | `getattr(args, 'summary', False)` |
| run | getattr | 2189 | `getattr(args, 'deep', False)` |
| run | getattr | 2190 | `getattr(args, 'paths', None)` |
| run | getattr | 2191 | `getattr(args, 'package', None)` |
| run | getattr | 2192 | `getattr(args, 'include_empty', False)` |
| run | getattr | 2193 | `getattr(args, 'output', None)` |
| run | getattr | 2194 | `getattr(args, 'read_only', False)` |
| run | getattr | 2195 | `getattr(args, 'allow_external_src', False)` |
| run | getattr | 2196 | `getattr(args, 'helper_cache_dir', None)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 2202 |
| output | `print` | `run` | 2206 |
| output | `print` | `run` | 2208 |
| output | `print` | `run` | 2210 |
| output | `print` | `run` | 2236 |
| output | `print` | `run` | 2238 |
| output | `print` | `run` | 2243 |
| output | `print` | `run` | 2247 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 2186 |
| unresolved_call | `run` | `getattr` | 2187 |
| unresolved_call | `run` | `getattr` | 2188 |
| unresolved_call | `run` | `getattr` | 2189 |
| unresolved_call | `run` | `getattr` | 2190 |
| unresolved_call | `run` | `getattr` | 2191 |
| unresolved_call | `run` | `getattr` | 2192 |
| unresolved_call | `run` | `getattr` | 2193 |
| unresolved_call | `run` | `getattr` | 2194 |
| unresolved_call | `run` | `getattr` | 2195 |
| unresolved_call | `run` | `getattr` | 2196 |
| step_limit | `run` | `first 12 steps` | 0 |

## Behavior

Builds the stable extraction payload for the requested source boundary and
writes JSON to stdout or an explicitly selected output. Changed, path, package,
summary, and deep modes narrow or enrich that payload without importing the
target application. Extractor failures are reported on stderr and return a
nonzero status; successful output retains the source-relative inventory
contract.
