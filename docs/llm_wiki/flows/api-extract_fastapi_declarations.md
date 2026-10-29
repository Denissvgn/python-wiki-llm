# extract_fastapi_declarations

**Entry point:** `extract_fastapi_declarations` (`api`)
**Source:** [fastapi_contracts](../modules/fastapi_contracts.md)
**Modules touched:** [fastapi_contracts](../modules/fastapi_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as extract_fastapi_declarations
    participant p1 as ast.parse
    participant p2 as _FastAPIScanner
    participant p3 as scanner.visit
    participant p4 as scanner.result
    p0-->>p1: ast.parse(source, filename=...)
    p0->>p2: _FastAPIScanner
    p0-->>p3: scanner.visit(tree)
    p0-->>p4: scanner.result
```

> Call sequence diagram shows 4 of 4 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1 (0 omitted); unresolved 2 of 2 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 2; effect analysis evaluated: 1, partial: 0, unavailable: 1. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 4, emitted: 4, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `extract_fastapi_declarations` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `ast.parse` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_FastAPIScanner` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `scanner.visit` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `scanner.result` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. extract_fastapi_declarations"]
    s2["2. ast.parse"]
    s3["3. _FastAPIScanner"]
    s4["4. scanner.visit"]
    s5["5. scanner.result"]
    s1 -. "ast.parse(source, filename=...)" .-> s2
    s1 -->|"_FastAPIScanner(tree, filepath)"| s3
    s1 -. "scanner.visit(tree)" .-> s4
    s1 -. "scanner.result(data not statically known)" .-> s5
    click s1 "../modules/fastapi_contracts.md"
    click s3 "../modules/fastapi_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `extract_fastapi_declarations` | `source: str`, `filepath: str` | - | - | `{...}`, `scanner.result(...)` |
| `ast.parse` | - | - | - | - |
| `_FastAPIScanner` | - | - | - | - |
| `scanner.visit` | - | - | - | - |
| `scanner.result` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| extract_fastapi_declarations | ast.parse | 474 | `ast.parse(source, filename=...)` |
| extract_fastapi_declarations | _FastAPIScanner | 477 | `_FastAPIScanner(tree, filepath)` |
| extract_fastapi_declarations | scanner.visit | 478 | `scanner.visit(tree)` |
| extract_fastapi_declarations | scanner.result | 479 | `scanner.result(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `extract_fastapi_declarations` | `ast.parse` | 474 |
| unresolved_call | `extract_fastapi_declarations` | `scanner.visit` | 478 |
| unresolved_call | `extract_fastapi_declarations` | `scanner.result` | 479 |

## Behavior

This flow starts at `extract_fastapi_declarations` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
