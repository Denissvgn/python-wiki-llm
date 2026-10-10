# ci_report

**Entry point:** `main` (`process`)
**Source:** [ci_report](../modules/ci_report.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [ci_report](../modules/ci_report.md), [health_contract](../modules/health_contract.md), [health_summary](../modules/health_summary.md), and 1 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [ci_report](../modules/ci_report.md)
- [health_contract](../modules/health_contract.md)
- [health_summary](../modules/health_summary.md)
- [knowledge_observability](../modules/knowledge_observability.md)

**Related modules:** [doctor_service](../modules/doctor_service.md), [health_contract](../modules/health_contract.md), [health_summary](../modules/health_summary.md), and 3 more

**Complete related modules:**

- [doctor_service](../modules/doctor_service.md)
- [health_contract](../modules/health_contract.md)
- [health_summary](../modules/health_summary.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [lint_service](../modules/lint_service.md)
- [services_contracts](../modules/services_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as main
    participant p1 as _arguments
    participant p2 as load_ci_check_payload
    participant p3 as CiCheckReportError
    participant p4 as Path (src/llm_wiki_cli/services/ci_report.py:main)
    participant p5 as status_path.is_symlink
    participant p6 as status_path.is_file
    participant p7 as status_path.read_bytes().splitlines
    participant p8 as status_path.read_bytes
    participant p9 as render_ci_summary
    participant p10 as output.is_symlink
    participant p11 as output.parent.is_dir
    participant p12 as output.write_bytes
    participant p13 as SystemExit
    participant p14 as argparse.ArgumentParser
    participant p15 as Path (src/llm_wiki_cli/services….py:load_ci_check_payload)
    participant p16 as parser.add_subparsers
    participant p17 as report_path.is_symlink
    participant p18 as isinstance (src/llm_wiki_cli/services…port.py:render_ci_summary)
    participant p19 as commands.add_parser
    participant p20 as report_path.is_file
    participant p21 as validate.add_argument
    p0->>p1: _arguments
    p0->>p2: load_ci_check_payload
    p0->>p3: CiCheckReportError
    p0->>p2: load_ci_check_payload
    p0-->>p4: Path (src/llm_wiki_cli/services/ci_report.py:main)(args.status_path)
    p0-->>p5: status_path.is_symlink
    p0-->>p6: status_path.is_file
    p0->>p3: CiCheckReportError
    p0-->>p7: status_path.read_bytes().splitlines
    p0-->>p8: status_path.read_bytes
    p0->>p9: render_ci_summary
    p0-->>p4: Path (src/llm_wiki_cli/services/ci_report.py:main)(args.report)
    p0-->>p4: Path (src/llm_wiki_cli/services/ci_report.py:main)(args.output)
    p0-->>p10: output.is_symlink
    p0-->>p11: output.parent.is_dir
    p0->>p3: CiCheckReportError
    p0-->>p12: output.write_bytes(payload)
    p0-->>p13: SystemExit(...)
    p1-->>p14: argparse.ArgumentParser
    p2-->>p15: Path (src/llm_wiki_cli/services….py:load_ci_check_payload)(path)
    p9->>p3: CiCheckReportError
    p1-->>p16: parser.add_subparsers(dest='action', required=True)
    p2-->>p17: report_path.is_symlink
    p9-->>p18: isinstance (src/llm_wiki_cli/services…port.py:render_ci_summary)(value, bool)
    p1-->>p19: commands.add_parser('validate')
    p2-->>p20: report_path.is_file
    p9-->>p18: isinstance (src/llm_wiki_cli/services…port.py:render_ci_summary)(value, int)
    p1-->>p21: validate.add_argument('--report', required=True)
    p2->>p3: CiCheckReportError
    p9->>p3: CiCheckReportError
```

> Call sequence diagram shows 30 of 559 interactions; 529 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 128 (120 omitted); unresolved 12 of 107 (95 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/ci_report.py:_arguments` | 2 | - | unresolved | 17 |
| `src/llm_wiki_cli/services/ci_report.py:load_ci_check_payload` | 24 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/ci_report.py:load_ci_check_payload` | 24 | - | external | 1 |
| `src/llm_wiki_cli/services/ci_report.py:load_ci_check_payload` | 24 | [src/llm_wiki_cli/services/ci_report.py](../modules/ci_report.md) | internal | 2 |
| `src/llm_wiki_cli/services/ci_report.py:validate_ci_check_payload` | 32 | - | external | 9 |
| `src/llm_wiki_cli/services/ci_report.py:validate_ci_check_payload` | 32 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/ci_report.py:validate_ci_check_payload` | 32 | [src/llm_wiki_cli/services/ci_report.py](../modules/ci_report.md) | internal | 31 |
| `src/llm_wiki_cli/services/ci_report.py:_validate_ci_v3` | 35 | [src/llm_wiki_cli/services/ci_report.py](../modules/ci_report.md) | internal | 4 |
> Omission summary shows 8 of 72 groups; 64 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

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
    s2 -. "summary.add_argument('--evidence-artifact')" .-> s11
    s2 -. "summary.add_argument('--cli-exit', required=True, type=int)" .-> s12
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
| main | _arguments | 1569 | `_arguments(argv)` |
| _arguments | argparse.ArgumentParser | 1542 | `argparse.ArgumentParser(data not statically known)` |
| _arguments | parser.add_subparsers | 1543 | `parser.add_subparsers(dest='action', required=True)` |
| _arguments | commands.add_parser | 1544 | `commands.add_parser('validate')` |
| _arguments | validate.add_argument | 1545 | `validate.add_argument('--report', required=True)` |
| _arguments | validate.add_argument | 1546 | `validate.add_argument('--cli-exit', required=True, type=int)` |
| _arguments | validate.add_argument | 1547 | `validate.add_argument('--schema', choices=(...))` |
| _arguments | commands.add_parser | 1549 | `commands.add_parser('render-summary')` |
| _arguments | summary.add_argument | 1550 | `summary.add_argument('--report')` |
| _arguments | summary.add_argument | 1551 | `summary.add_argument('--evidence-artifact')` |
| _arguments | summary.add_argument | 1552 | `summary.add_argument('--cli-exit', required=True, type=int)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `output.write_bytes` | `main` | 1609 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_arguments` | `argparse.ArgumentParser` | 1542 |
| unresolved_call | `_arguments` | `parser.add_subparsers` | 1543 |
| unresolved_call | `_arguments` | `commands.add_parser` | 1544 |
| unresolved_call | `_arguments` | `validate.add_argument` | 1545 |
| unresolved_call | `_arguments` | `validate.add_argument` | 1546 |
| unresolved_call | `_arguments` | `validate.add_argument` | 1547 |
| unresolved_call | `_arguments` | `commands.add_parser` | 1549 |
| unresolved_call | `_arguments` | `summary.add_argument` | 1550 |
| unresolved_call | `_arguments` | `summary.add_argument` | 1551 |
| unresolved_call | `_arguments` | `summary.add_argument` | 1552 |
| step_limit | `main` | `first 12 steps` | 0 |
| truncated_flow | `main` | `depth limit` | 0 |

## Behavior

This flow starts at `main` and is classified as `process`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
