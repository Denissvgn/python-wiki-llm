# ci_report

**Entry point:** `main` (`process`)
**Source:** [ci_report](../modules/ci_report.md)
**Modules touched:** [ci_report](../modules/ci_report.md), [knowledge_observability](../modules/knowledge_observability.md)

**Related modules:** [doctor_service](../modules/doctor_service.md), [knowledge_observability](../modules/knowledge_observability.md), [lint_service](../modules/lint_service.md), [services_contracts](../modules/services_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as main
    participant p1 as _arguments
    participant p2 as ArgumentParser
    participant p3 as add_subparsers
    participant p4 as add_parser
    participant p5 as add_argument
    participant p6 as parse_args
    participant p7 as load_ci_check_payload
    participant p8 as Path
    participant p9 as is_symlink
    participant p10 as is_file
    participant p11 as CiCheckReportError
    participant p12 as read_text
    participant p13 as loads
    participant p14 as validate_ci_check_payload
    p0->>p1: _arguments
    p1-->>p2: ArgumentParser
    p1-->>p3: add_subparsers
    p1-->>p4: add_parser
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p4: add_parser
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p5: add_argument
    p1-->>p6: parse_args
    p0->>p7: load_ci_check_payload
    p7-->>p8: Path
    p7-->>p9: is_symlink
    p7-->>p10: is_file
    p7->>p11: CiCheckReportError
    p7-->>p12: read_text
    p7-->>p13: loads
    p7->>p11: CiCheckReportError
    p7->>p14: validate_ci_check_payload
```

> Call sequence diagram shows 30 of 382 interactions; 352 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. main"]
    s2["2. _arguments"]
    s3["3. ArgumentParser"]
    s4["4. add_subparsers"]
    s5["5. add_parser"]
    s6["6. add_argument"]
    s7["7. add_argument"]
    s8["8. add_argument"]
    s9["9. add_parser"]
    s10["10. add_argument"]
    s11["11. add_argument"]
    s12["12. add_argument"]
    s1 -->|"_arguments(argv)"| s2
    s2 -. "argparse.ArgumentParser(data not statically known)" .-> s3
    s2 -. "parser.add_subparsers(dest='action', required=True)" .-> s4
    s2 -. "commands.add_parser('validate')" .-> s5
    s2 -. "validate.add_argument('--report', required=True)" .-> s6
    s2 -. "validate.add_argument('--cli-exit', required=True, type=int)" .-> s7
    s2 -. "validate.add_argument('--schema', choices=(...))" .-> s8
    s2 -. "commands.add_parser('render-summary')" .-> s9
    s2 -. "summary.add_argument('--report')" .-> s10
    s2 -. "summary.add_argument('--cli-exit', required=True, type=int)" .-> s11
    s2 -. "summary.add_argument('--result', choices=(...), required=True)" .-> s12
    b0["filesystem_write output.write_bytes"]
    s1 -. "filesystem_write output.write_bytes" .-> b0
    click s1 "../modules/ci_report.md"
    click s2 "../modules/ci_report.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `main` | `argv: Sequence[str] \| None` | `CiCheckReportError` | - | `0`, `0` |
| `_arguments` | `argv: Sequence[str] \| None` | - | - | `parser.parse_args(...)` |
| `ArgumentParser` | - | - | - | - |
| `add_subparsers` | - | - | - | - |
| `add_parser` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `add_parser` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `add_argument` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| main | _arguments | 1451 | `_arguments(argv)` |
| _arguments | ArgumentParser | 1425 | `argparse.ArgumentParser(data not statically known)` |
| _arguments | add_subparsers | 1426 | `parser.add_subparsers(dest='action', required=True)` |
| _arguments | add_parser | 1427 | `commands.add_parser('validate')` |
| _arguments | add_argument | 1428 | `validate.add_argument('--report', required=True)` |
| _arguments | add_argument | 1429 | `validate.add_argument('--cli-exit', required=True, type=int)` |
| _arguments | add_argument | 1430 | `validate.add_argument('--schema', choices=(...))` |
| _arguments | add_parser | 1432 | `commands.add_parser('render-summary')` |
| _arguments | add_argument | 1433 | `summary.add_argument('--report')` |
| _arguments | add_argument | 1434 | `summary.add_argument('--cli-exit', required=True, type=int)` |
| _arguments | add_argument | 1435 | `summary.add_argument('--result', choices=(...), required=True)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `output.write_bytes` | `main` | 1489 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_arguments` | `argparse.ArgumentParser` | 1425 |
| unresolved_call | `_arguments` | `parser.add_subparsers` | 1426 |
| unresolved_call | `_arguments` | `commands.add_parser` | 1427 |
| unresolved_call | `_arguments` | `validate.add_argument` | 1428 |
| unresolved_call | `_arguments` | `validate.add_argument` | 1429 |
| unresolved_call | `_arguments` | `validate.add_argument` | 1430 |
| unresolved_call | `_arguments` | `commands.add_parser` | 1432 |
| unresolved_call | `_arguments` | `summary.add_argument` | 1433 |
| unresolved_call | `_arguments` | `summary.add_argument` | 1434 |
| unresolved_call | `_arguments` | `summary.add_argument` | 1435 |
| step_limit | `main` | `first 12 steps` | 0 |

## Behavior

This flow starts at `main` and is classified as `process`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
