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
    participant p2 as argparse.ArgumentParser
    participant p3 as parser.add_subparsers
    participant p4 as commands.add_parser
    participant p5 as validate.add_argument
    participant p6 as summary.add_argument
    participant p7 as parser.parse_args
    participant p8 as load_ci_check_payload
    participant p9 as Path (src/llm_wiki_cli/services….py:load_ci_check_payload)
    participant p10 as report_path.is_symlink
    participant p11 as report_path.is_file
    participant p12 as CiCheckReportError
    participant p13 as report_path.read_text
    participant p14 as json.loads
    participant p15 as validate_ci_check_payload
    p0->>p1: _arguments
    p1-->>p2: argparse.ArgumentParser
    p1-->>p3: parser.add_subparsers
    p1-->>p4: commands.add_parser
    p1-->>p5: validate.add_argument
    p1-->>p5: validate.add_argument
    p1-->>p5: validate.add_argument
    p1-->>p4: commands.add_parser
    p1-->>p6: summary.add_argument
    p1-->>p6: summary.add_argument
    p1-->>p6: summary.add_argument
    p1-->>p6: summary.add_argument
    p1-->>p6: summary.add_argument
    p1-->>p6: summary.add_argument
    p1-->>p6: summary.add_argument
    p1-->>p6: summary.add_argument
    p1-->>p6: summary.add_argument
    p1-->>p6: summary.add_argument
    p1-->>p6: summary.add_argument
    p1-->>p6: summary.add_argument
    p1-->>p7: parser.parse_args
    p0->>p8: load_ci_check_payload
    p8-->>p9: Path (src/llm_wiki_cli/services….py:load_ci_check_payload)
    p8-->>p10: report_path.is_symlink
    p8-->>p11: report_path.is_file
    p8->>p12: CiCheckReportError
    p8-->>p13: report_path.read_text
    p8-->>p14: json.loads
    p8->>p12: CiCheckReportError
    p8->>p15: validate_ci_check_payload
```

> Call sequence diagram shows 30 of 382 interactions; 352 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. main"]
    s2["2. _arguments"]
    s3["3. argparse.ArgumentParser"]
    s4["4. parser.add_subparsers"]
    s5["5. commands.add_parser"]
    s6["6. validate.add_argument"]
    s7["7. validate.add_argument"]
    s8["8. validate.add_argument"]
    s9["9. commands.add_parser"]
    s10["10. summary.add_argument"]
    s11["11. summary.add_argument"]
    s12["12. summary.add_argument"]
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
| `argparse.ArgumentParser` | - | - | - | - |
| `parser.add_subparsers` | - | - | - | - |
| `commands.add_parser` | - | - | - | - |
| `validate.add_argument` | - | - | - | - |
| `validate.add_argument` | - | - | - | - |
| `validate.add_argument` | - | - | - | - |
| `commands.add_parser` | - | - | - | - |
| `summary.add_argument` | - | - | - | - |
| `summary.add_argument` | - | - | - | - |
| `summary.add_argument` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| main | _arguments | 1450 | `_arguments(argv)` |
| _arguments | argparse.ArgumentParser | 1424 | `argparse.ArgumentParser(data not statically known)` |
| _arguments | parser.add_subparsers | 1425 | `parser.add_subparsers(dest='action', required=True)` |
| _arguments | commands.add_parser | 1426 | `commands.add_parser('validate')` |
| _arguments | validate.add_argument | 1427 | `validate.add_argument('--report', required=True)` |
| _arguments | validate.add_argument | 1428 | `validate.add_argument('--cli-exit', required=True, type=int)` |
| _arguments | validate.add_argument | 1429 | `validate.add_argument('--schema', choices=(...))` |
| _arguments | commands.add_parser | 1431 | `commands.add_parser('render-summary')` |
| _arguments | summary.add_argument | 1432 | `summary.add_argument('--report')` |
| _arguments | summary.add_argument | 1433 | `summary.add_argument('--cli-exit', required=True, type=int)` |
| _arguments | summary.add_argument | 1434 | `summary.add_argument('--result', choices=(...), required=True)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `output.write_bytes` | `main` | 1488 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_arguments` | `argparse.ArgumentParser` | 1424 |
| unresolved_call | `_arguments` | `parser.add_subparsers` | 1425 |
| unresolved_call | `_arguments` | `commands.add_parser` | 1426 |
| unresolved_call | `_arguments` | `validate.add_argument` | 1427 |
| unresolved_call | `_arguments` | `validate.add_argument` | 1428 |
| unresolved_call | `_arguments` | `validate.add_argument` | 1429 |
| unresolved_call | `_arguments` | `commands.add_parser` | 1431 |
| unresolved_call | `_arguments` | `summary.add_argument` | 1432 |
| unresolved_call | `_arguments` | `summary.add_argument` | 1433 |
| unresolved_call | `_arguments` | `summary.add_argument` | 1434 |
| step_limit | `main` | `first 12 steps` | 0 |

## Behavior

This flow starts at `main` and is classified as `process`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
