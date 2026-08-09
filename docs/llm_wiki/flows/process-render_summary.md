# render_summary

**Entry point:** `main` (`process`)
**Source:** [render_summary](../modules/render_summary.md)
**Modules touched:** [render_summary](../modules/render_summary.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as main
    participant p1 as _arguments
    participant p2 as ArgumentParser
    participant p3 as add_argument
    participant p4 as sorted
    participant p5 as range
    participant p6 as parse_args
    participant p7 as load_report
    participant p8 as loads
    participant p9 as read_text
    participant p10 as Path
    participant p11 as ValueError
    participant p12 as _required_object
    participant p13 as _object
    participant p14 as isinstance
    participant p15 as set
    participant p16 as get
    participant p17 as _enum
    participant p18 as _string
    participant p19 as strip
    p0->>p1: _arguments
    p1-->>p2: ArgumentParser
    p1-->>p3: add_argument
    p1-->>p3: add_argument
    p1-->>p4: sorted
    p1-->>p3: add_argument
    p1-->>p5: range
    p1-->>p6: parse_args
    p0->>p7: load_report
    p7-->>p8: loads
    p7-->>p9: read_text
    p7-->>p10: Path
    p7-->>p11: ValueError
    p7->>p12: _required_object
    p12->>p13: _object
    p13-->>p14: isinstance
    p13-->>p11: ValueError
    p12-->>p4: sorted
    p12-->>p15: set
    p12-->>p11: ValueError
    p7-->>p16: get
    p7-->>p11: ValueError
    p7->>p17: _enum
    p17->>p18: _string
    p18-->>p14: isinstance
    p18-->>p19: strip
    p18-->>p11: ValueError
    p17-->>p11: ValueError
    p7-->>p16: get
    p7-->>p14: isinstance
```

> Call sequence diagram shows 30 of 134 interactions; 104 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. main"]
    s2["2. _arguments"]
    s3["3. ArgumentParser"]
    s4["4. add_argument"]
    s5["5. add_argument"]
    s6["6. sorted"]
    s7["7. add_argument"]
    s8["8. range"]
    s9["9. parse_args"]
    s10["10. load_report"]
    s11["11. loads"]
    s12["12. read_text"]
    s1 -->|"_arguments(data not statically known)"| s2
    s2 -. "argparse.ArgumentParser(data not statically known)" .-> s3
    s2 -. "parser.add_argument('--report', required=True)" .-> s4
    s2 -. "parser.add_argument('--fail-on', choices=sorted(...), required=True)" .-> s5
    s2 -. "sorted(FAIL_THRESHOLDS)" .-> s6
    s2 -. "parser.add_argument('--doctor-exit-code', choices=range(...), required=True, type=int)" .-> s7
    s2 -. "range(4)" .-> s8
    s2 -. "parser.parse_args(data not statically known)" .-> s9
    s1 -->|"load_report(args.report, doctor_exit_code=args.doctor_exit_code)"| s10
    s10 -. "json.loads(..., object_pairs_hook=_strict_json_object, parse_constant=_reject_nonfinite)" .-> s11
    s10 -. "Path(path).read_text(encoding='utf-8')" .-> s12
    b0["environment_read os.environ.get"]
    s1 -. "environment_read os.environ.get" .-> b0
    b1["environment_read os.environ.get"]
    s1 -. "environment_read os.environ.get" .-> b1
    click s1 "../modules/render_summary.md"
    click s2 "../modules/render_summary.md"
    click s10 "../modules/render_summary.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `main` | - | `FAIL_THRESHOLDS`, `STATUS_SEVERITY` | - | `int(...)` |
| `_arguments` | - | `FAIL_THRESHOLDS` | - | `parser.parse_args(...)` |
| `ArgumentParser` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `sorted` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `range` | - | - | - | - |
| `parse_args` | - | - | - | - |
| `load_report` | `path: str \| Path`, `doctor_exit_code: int` | `_strict_json_object`, `_reject_nonfinite`, `json`, `REPORT_FIELDS`, `SCHEMA_VERSION`, `SCHEMA_VERSION`, `STATUS_SEVERITY`, `STATUS_SEVERITY` | - | `report` |
| `loads` | - | - | - | - |
| `read_text` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| main | _arguments | 437 | `_arguments(data not statically known)` |
| _arguments | ArgumentParser | 107 | `argparse.ArgumentParser(data not statically known)` |
| _arguments | add_argument | 108 | `parser.add_argument('--report', required=True)` |
| _arguments | add_argument | 109 | `parser.add_argument('--fail-on', choices=sorted(...), required=True)` |
| _arguments | sorted | 109 | `sorted(FAIL_THRESHOLDS)` |
| _arguments | add_argument | 110 | `parser.add_argument('--doctor-exit-code', choices=range(...), required=True, type=int)` |
| _arguments | range | 112 | `range(4)` |
| _arguments | parse_args | 116 | `parser.parse_args(data not statically known)` |
| main | load_report | 439 | `load_report(args.report, doctor_exit_code=args.doctor_exit_code)` |
| load_report | loads | 344 | `json.loads(..., object_pairs_hook=_strict_json_object, parse_constant=_reject_nonfinite)` |
| load_report | read_text | 345 | `Path(path).read_text(encoding='utf-8')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| environment_read | `os.environ.get` | `main` | 447 |
| environment_read | `os.environ.get` | `main` | 449 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_arguments` | `argparse.ArgumentParser` | 107 |
| unresolved_call | `_arguments` | `parser.add_argument` | 108 |
| unresolved_call | `_arguments` | `parser.add_argument` | 109 |
| unresolved_call | `_arguments` | `sorted` | 109 |
| unresolved_call | `_arguments` | `parser.add_argument` | 110 |
| unresolved_call | `_arguments` | `range` | 112 |
| unresolved_call | `_arguments` | `parser.parse_args` | 116 |
| external_call | `load_report` | `json.loads` | 344 |
| unresolved_call | `load_report` | `Path(path).read_text` | 345 |
| step_limit | `main` | `first 12 steps` | 0 |

## Behavior

Reads the GitHub Action's doctor JSON, validates the exact contract and captured
doctor exit code, and renders a compact health table. When GitHub output paths
are present it appends the summary and status output, then returns whether the
report severity meets the configured degraded or unhealthy threshold. Invalid
input stops with a contract error rather than publishing a partial summary.
