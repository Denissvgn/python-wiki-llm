# attach_fastapi_declarations

**Entry point:** `attach_fastapi_declarations` (`api`)
**Source:** [fastapi_contracts](../modules/fastapi_contracts.md)
**Modules touched:** [fastapi_contracts](../modules/fastapi_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as attach_fastapi_declarations
    participant p1 as extract_fastapi_declarations
    participant p2 as file_entry.setdefault
    participant p3 as ast.parse
    participant p4 as _FastAPIScanner
    participant p5 as scanner.visit
    participant p6 as scanner.result
    p0->>p1: extract_fastapi_declarations
    p0-->>p2: file_entry.setdefault('frameworks', {...})
    p1-->>p3: ast.parse(source, filename=...)
    p1->>p4: _FastAPIScanner
    p1-->>p5: scanner.visit(tree)
    p1-->>p6: scanner.result
```

> Call sequence diagram shows 6 of 6 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1 (0 omitted); unresolved 3 of 3 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 3; effect analysis evaluated: 2, partial: 0, unavailable: 1. Counts include steps omitted from the displayed trace.

Collector observations for 2 source steps with known totals: observed: 8, emitted: 8, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `attach_fastapi_declarations` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `extract_fastapi_declarations` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `ast.parse` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_FastAPIScanner` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `scanner.visit` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `scanner.result` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `file_entry.setdefault` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. attach_fastapi_declarations"]
    s2["2. extract_fastapi_declarations"]
    s3["3. ast.parse"]
    s4["4. _FastAPIScanner"]
    s5["5. scanner.visit"]
    s6["6. scanner.result"]
    s7["7. file_entry.setdefault"]
    s1 -->|"extract_fastapi_declarations(source, filepath=filepath)"| s2
    s2 -. "ast.parse(source, filename=...)" .-> s3
    s2 -->|"_FastAPIScanner(tree, filepath)"| s4
    s2 -. "scanner.visit(tree)" .-> s5
    s2 -. "scanner.result(data not statically known)" .-> s6
    s1 -. "file_entry.setdefault('frameworks', {...})" .-> s7
    click s1 "../modules/fastapi_contracts.md"
    click s2 "../modules/fastapi_contracts.md"
    click s4 "../modules/fastapi_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `attach_fastapi_declarations` | `file_entry: dict[str, Any]`, `source: str`, `filepath: str` | - | - | `file_entry` |
| `extract_fastapi_declarations` | `source: str`, `filepath: str` | - | - | `{...}`, `scanner.result(...)` |
| `ast.parse` | - | - | - | - |
| `_FastAPIScanner` | - | - | - | - |
| `scanner.visit` | - | - | - | - |
| `scanner.result` | - | - | - | - |
| `file_entry.setdefault` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| attach_fastapi_declarations | extract_fastapi_declarations | 489 | `extract_fastapi_declarations(source, filepath=filepath)` |
| extract_fastapi_declarations | ast.parse | 474 | `ast.parse(source, filename=...)` |
| extract_fastapi_declarations | _FastAPIScanner | 477 | `_FastAPIScanner(tree, filepath)` |
| extract_fastapi_declarations | scanner.visit | 478 | `scanner.visit(tree)` |
| extract_fastapi_declarations | scanner.result | 479 | `scanner.result(data not statically known)` |
| attach_fastapi_declarations | file_entry.setdefault | 491 | `file_entry.setdefault('frameworks', {...})` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `extract_fastapi_declarations` | `ast.parse` | 474 |
| unresolved_call | `extract_fastapi_declarations` | `scanner.visit` | 478 |
| unresolved_call | `extract_fastapi_declarations` | `scanner.result` | 479 |
| unresolved_call | `attach_fastapi_declarations` | `file_entry.setdefault` | 491 |

## Behavior

This flow starts at `attach_fastapi_declarations` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
