# attach_fastapi_declarations

**Entry point:** `attach_fastapi_declarations` (`api`)
**Source:** [fastapi_contracts](../modules/fastapi_contracts.md)
**Modules touched:** [fastapi_contracts](../modules/fastapi_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as attach_fastapi_declarations
    participant p1 as extract_fastapi_declarations
    participant p2 as parse
    participant p3 as _FastAPIScanner
    participant p4 as visit
    participant p5 as result
    participant p6 as setdefault
    p0->>p1: extract_fastapi_declarations
    p1-->>p2: parse
    p1->>p3: _FastAPIScanner
    p1-->>p4: visit
    p1-->>p5: result
    p0-->>p6: setdefault
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. attach_fastapi_declarations"]
    s2["2. extract_fastapi_declarations"]
    s3["3. parse"]
    s4["4. _FastAPIScanner"]
    s5["5. visit"]
    s6["6. result"]
    s7["7. setdefault"]
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
| `parse` | - | - | - | - |
| `_FastAPIScanner` | - | - | - | - |
| `visit` | - | - | - | - |
| `result` | - | - | - | - |
| `setdefault` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| attach_fastapi_declarations | extract_fastapi_declarations | 489 | `extract_fastapi_declarations(source, filepath=filepath)` |
| extract_fastapi_declarations | parse | 474 | `ast.parse(source, filename=...)` |
| extract_fastapi_declarations | _FastAPIScanner | 477 | `_FastAPIScanner(tree, filepath)` |
| extract_fastapi_declarations | visit | 478 | `scanner.visit(tree)` |
| extract_fastapi_declarations | result | 479 | `scanner.result(data not statically known)` |
| attach_fastapi_declarations | setdefault | 491 | `file_entry.setdefault('frameworks', {...})` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `extract_fastapi_declarations` | `ast.parse` | 474 |
| unresolved_call | `extract_fastapi_declarations` | `scanner.visit` | 478 |
| unresolved_call | `extract_fastapi_declarations` | `scanner.result` | 479 |
| unresolved_call | `attach_fastapi_declarations` | `file_entry.setdefault` | 491 |

## Behavior

This flow starts at `attach_fastapi_declarations` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
