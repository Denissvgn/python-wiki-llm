# verify_documentation_run

**Entry point:** `verify_documentation_run` (`api`)
**Source:** [verify](../modules/verify.md)
**Modules touched:** [verify](../modules/verify.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as verify_documentation_run
    participant p1 as _resolve_workspace_root_argument
    participant p2 as load_documentation_run
    participant p3 as list
    participant p4 as checks.extend
    participant p5 as _verify_read_only_inputs
    participant p6 as checks.append
    participant p7 as str
    participant p8 as run.evidence.get
    participant p9 as _read_json
    participant p10 as _workspace_path
    participant p11 as compare_generated_ownership
    participant p12 as generated_payload.get
    participant p13 as any
    participant p14 as generated_diff.values
    participant p15 as bool
    participant p16 as readiness.get
    participant p17 as evidence_payload.get
    p0-->>p1: _resolve_workspace_root_argument
    p0-->>p2: load_documentation_run
    p0-->>p3: list
    p0-->>p4: checks.extend
    p0-->>p5: _verify_read_only_inputs
    p0-->>p6: checks.append
    p0-->>p7: str
    p0-->>p8: run.evidence.get
    p0-->>p9: _read_json
    p0-->>p10: _workspace_path
    p0-->>p11: compare_generated_ownership
    p0-->>p12: generated_payload.get
    p0-->>p6: checks.append
    p0-->>p13: any
    p0-->>p14: generated_diff.values
    p0-->>p9: _read_json
    p0-->>p10: _workspace_path
    p0-->>p6: checks.append
    p0-->>p15: bool
    p0-->>p16: readiness.get
    p0-->>p16: readiness.get
    p0-->>p16: readiness.get
    p0-->>p8: run.evidence.get
    p0-->>p6: checks.append
    p0-->>p9: _read_json
    p0-->>p10: _workspace_path
    p0-->>p6: checks.append
    p0-->>p15: bool
    p0-->>p17: evidence_payload.get
    p0-->>p17: evidence_payload.get
```

> Call sequence diagram shows 30 of 79 interactions; 49 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. verify_documentation_run"]
    s2["2. _resolve_workspace_root_argument"]
    s3["3. load_documentation_run"]
    s4["4. list"]
    s5["5. checks.extend"]
    s6["6. _verify_read_only_inputs"]
    s7["7. checks.append"]
    s8["8. str"]
    s9["9. run.evidence.get"]
    s10["10. _read_json"]
    s11["11. _workspace_path"]
    s12["12. compare_generated_ownership"]
    s1 -. "_resolve_workspace_root_argument(workspace)" .-> s2
    s1 -. "load_documentation_run(workspace_root)" .-> s3
    s1 -. "list(run.verdict_limitations)" .-> s4
    s1 -. "checks.extend(_verify_read_only_inputs(...))" .-> s5
    s1 -. "_verify_read_only_inputs(workspace_root, run)" .-> s6
    s1 -. "checks.append({...})" .-> s7
    s1 -. "str(exc)" .-> s8
    s1 -. "run.evidence.get('generated_ownership')" .-> s9
    s1 -. "_read_json(_workspace_path(...))" .-> s10
    s1 -. "_workspace_path(workspace_root, generated_path)" .-> s11
    s1 -. "compare_generated_ownership(generated_payload.get(...), ...)" .-> s12
    b0["mutation checks.extend"]
    s1 -. "mutation checks.extend" .-> b0
    b1["mutation checks.append"]
    s1 -. "mutation checks.append" .-> b1
    b2["mutation checks.append"]
    s1 -. "mutation checks.append" .-> b2
    b3["mutation checks.append"]
    s1 -. "mutation checks.append" .-> b3
    b4["mutation checks.append"]
    s1 -. "mutation checks.append" .-> b4
    b5["mutation checks.append"]
    s1 -. "mutation checks.append" .-> b5
    b6["mutation checks.append"]
    s1 -. "mutation checks.append" .-> b6
    b7["mutation checks.append"]
    s1 -. "mutation checks.append" .-> b7
    click s1 "../modules/verify.md"
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
| `verify_documentation_run` | `workspace: str \| Path`, `advance: bool` | - | `run.evidence[...]`, `run.validation_results` | `report` |
| `_resolve_workspace_root_argument` | - | - | - | - |
| `load_documentation_run` | - | - | - | - |
| `list` | - | - | - | - |
| `checks.extend` | - | - | - | - |
| `_verify_read_only_inputs` | - | - | - | - |
| `checks.append` | - | - | - | - |
| `str` | - | - | - | - |
| `run.evidence.get` | - | - | - | - |
| `_read_json` | - | - | - | - |
| `_workspace_path` | - | - | - | - |
| `compare_generated_ownership` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| verify_documentation_run | _resolve_workspace_root_argument | 20 | `_resolve_workspace_root_argument(workspace)` |
| verify_documentation_run | load_documentation_run | 21 | `load_documentation_run(workspace_root)` |
| verify_documentation_run | list | 23 | `list(run.verdict_limitations)` |
| verify_documentation_run | checks.extend | 25 | `checks.extend(_verify_read_only_inputs(...))` |
| verify_documentation_run | _verify_read_only_inputs | 25 | `_verify_read_only_inputs(workspace_root, run)` |
| verify_documentation_run | checks.append | 27 | `checks.append({...})` |
| verify_documentation_run | str | 27 | `str(exc)` |
| verify_documentation_run | run.evidence.get | 29 | `run.evidence.get('generated_ownership')` |
| verify_documentation_run | _read_json | 31 | `_read_json(_workspace_path(...))` |
| verify_documentation_run | _workspace_path | 31 | `_workspace_path(workspace_root, generated_path)` |
| verify_documentation_run | compare_generated_ownership | 32 | `compare_generated_ownership(generated_payload.get(...), ...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `checks.extend` | `verify_documentation_run` | 25 |
| mutation | `checks.append` | `verify_documentation_run` | 27 |
| mutation | `checks.append` | `verify_documentation_run` | 36 |
| mutation | `checks.append` | `verify_documentation_run` | 47 |
| mutation | `checks.append` | `verify_documentation_run` | 58 |
| mutation | `checks.append` | `verify_documentation_run` | 67 |
| mutation | `checks.append` | `verify_documentation_run` | 80 |
| mutation | `checks.append` | `verify_documentation_run` | 82 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `verify_documentation_run` | `_resolve_workspace_root_argument` | 20 |
| unresolved_call | `verify_documentation_run` | `load_documentation_run` | 21 |
| unresolved_call | `verify_documentation_run` | `run.evidence.get` | 29 |
| unresolved_call | `verify_documentation_run` | `_read_json` | 31 |
| unresolved_call | `verify_documentation_run` | `_workspace_path` | 31 |
| unresolved_call | `verify_documentation_run` | `compare_generated_ownership` | 32 |
| step_limit | `verify_documentation_run` | `first 12 steps` | 0 |

## Behavior

This flow starts at `verify_documentation_run` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
