# docs

**Entry point:** `run` (`cli`)
**Source:** [docs_cmd](../modules/docs_cmd.md)
**Modules touched:** [docs_cmd](../modules/docs_cmd.md), [documentation_run_contracts](../modules/documentation_run_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as isinstance
    participant p3 as get
    participant p4 as DocumentationRunError
    participant p5 as handler
    participant p6 as print
    participant p7 as SystemExit
    p0-->>p1: getattr
    p0-->>p2: isinstance
    p0-->>p3: get
    p0->>p4: DocumentationRunError
    p0-->>p5: handler
    p0-->>p6: print
    p0-->>p7: SystemExit
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. isinstance"]
    s4["4. get"]
    s5["5. DocumentationRunError"]
    s6["6. handler"]
    s7["7. print"]
    s8["8. SystemExit"]
    s1 -. "getattr(args, 'docs_action', None)" .-> s2
    s1 -. "isinstance(action, str)" .-> s3
    s1 -. "handlers.get(action)" .-> s4
    s1 -->|"DocumentationRunError('Missing documentation action.')"| s5
    s1 -. "handler(args)" .-> s6
    s1 -. "print(..., file=sys.stderr)" .-> s7
    s1 -. "SystemExit(1)" .-> s8
    b0["output print"]
    s1 -. "output print" .-> b0
    click s1 "../modules/docs_cmd.md"
    click s5 "../modules/documentation_run_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `_prepare`, `_status`, `_packet`, `_record_result`, `_verify`, `_export`, `_calibration`, `PathValidationError` | - | - |
| `getattr` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `get` | - | - | - | - |
| `DocumentationRunError` | - | - | - | - |
| `handler` | - | - | - | - |
| `print` | - | - | - | - |
| `SystemExit` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 654 | `getattr(args, 'docs_action', None)` |
| run | isinstance | 664 | `isinstance(action, str)` |
| run | get | 664 | `handlers.get(action)` |
| run | DocumentationRunError | 666 | `DocumentationRunError('Missing documentation action.')` |
| run | handler | 668 | `handler(args)` |
| run | print | 672 | `print(..., file=sys.stderr)` |
| run | SystemExit | 673 | `SystemExit(1)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 672 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 654 |
| unresolved_call | `run` | `isinstance` | 664 |
| unresolved_call | `run` | `handlers.get` | 664 |
| unresolved_call | `run` | `handler` | 668 |
| unresolved_call | `run` | `SystemExit` | 673 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
