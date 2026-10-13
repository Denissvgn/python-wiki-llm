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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as main
    participant p1 as load_ci_check_payload
    participant p2 as render_ci_summary
    participant p3 as _arguments
    participant p4 as CiCheckReportError
    participant p5 as validate_ci_check_payload
    participant p6 as _health_detail_lines
    participant p7 as _bounded_summary
    participant p8 as _validate_ci_v3
    participant p9 as _validate_lint_findings
    participant p10 as _validate_execution
    participant p11 as _validate_knowledge_summary
    participant p12 as detailed_health_rows
    participant p13 as validate_doctor_payload
    participant p14 as _array
    participant p15 as _positive_integer
    participant p16 as _validate_ci_v2
    participant p17 as _count_mapping
    participant p18 as _canonical_plan_ids
    participant p19 as _exact_object
    participant p20 as validate_health_details
    participant p21 as _contract_object
    participant p22 as _string
    participant p23 as _validate_doctor
    participant p24 as _nullable_string
    participant p25 as summary_cell
    participant p26 as _object (src/llm_wiki_cli/services/ci_report.py)
    participant p27 as _finding_reasons
    participant p28 as _boolean
    participant p29 as Path (src/llm_wiki_cli/services/ci_report.py:main)
    participant p30 as status_path.is_symlink
    p0->>p1: load_ci_check_payload
    p0->>p2: render_ci_summary
    p0->>p3: _arguments
    p0->>p4: CiCheckReportError
    p1->>p5: validate_ci_check_payload
    p2->>p6: _health_detail_lines
    p2->>p7: _bounded_summary
    p5->>p8: _validate_ci_v3
    p5->>p9: _validate_lint_findings
    p5->>p10: _validate_execution
    p5->>p11: _validate_knowledge_summary
    p6->>p12: detailed_health_rows
    p8->>p13: validate_doctor_payload
    p9->>p14: _array
    p10->>p15: _positive_integer
    p8->>p16: _validate_ci_v2
    p11->>p17: _count_mapping
    p10->>p18: _canonical_plan_ids
    p13->>p19: _exact_object
    p13->>p20: validate_health_details
    p13->>p21: _contract_object
    p13->>p22: _string
    p13->>p23: _validate_doctor
    p16->>p24: _nullable_string
    p2->>p25: summary_cell
    p2->>p26: _object (src/llm_wiki_cli/services/ci_report.py)
    p6->>p27: _finding_reasons
    p5->>p28: _boolean
    p0-->>p29: Path (src/llm_wiki_cli/services/ci_report.py:main)(args.status_path)
    p0-->>p30: status_path.is_symlink
```

> Call sequence diagram shows 30 of 559 interactions; 529 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 128 (127 omitted); unresolved 1 of 107 (106 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/ci_report.py:_arguments` | 2 | - | external | 1 |
| `src/llm_wiki_cli/services/ci_report.py:_arguments` | 2 | - | unresolved | 20 |
| `src/llm_wiki_cli/services/ci_report.py:load_ci_check_payload` | 24 | - | external | 2 |
| `src/llm_wiki_cli/services/ci_report.py:load_ci_check_payload` | 24 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/ci_report.py:load_ci_check_payload` | 24 | [src/llm_wiki_cli/services/ci_report.py](../modules/ci_report.md) | internal | 2 |
| `src/llm_wiki_cli/services/ci_report.py:validate_ci_check_payload` | 32 | - | external | 9 |
| `src/llm_wiki_cli/services/ci_report.py:validate_ci_check_payload` | 32 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/ci_report.py:validate_doctor_payload` | 36 | - | external | 2 |
> Omission summary shows 8 of 74 groups; 66 further groups are not expanded here. Counts above include all omitted interactions.
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
