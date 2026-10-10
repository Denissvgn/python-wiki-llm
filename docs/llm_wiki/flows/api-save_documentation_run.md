# save_documentation_run

**Entry point:** `save_documentation_run` (`api`)
**Source:** [workspace](../modules/workspace.md)
**Modules touched:** [workspace](../modules/workspace.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as save_documentation_run
    participant p1 as _utc_now
    participant p2 as _validate_run_payload
    participant p3 as run.to_dict
    participant p4 as _write_json
    participant p5 as documentation_run_path
    participant p6 as _control_workspace_root
    participant p7 as _resolve_workspace_root_argument
    participant p8 as _write_workspace_text
    participant p9 as json.dumps
    participant p10 as Path (src/llm_wiki_cli/services…y:_control_workspace_root)
    participant p11 as Path (src/llm_wiki_cli/services….py:_write_workspace_text)
    participant p12 as Path (src/llm_wiki_cli/services…e_workspace_root_argument)
    participant p13 as os.path.abspath (src/llm_wiki_cli/services…y:_control_workspace_root)
    participant p14 as os.path.abspath (src/llm_wiki_cli/services….py:_write_workspace_text)
    participant p15 as os.path.abspath (src/llm_wiki_cli/services…e_workspace_root_argument)
    participant p16 as os.fspath (src/llm_wiki_cli/services…y:_control_workspace_root)
    participant p17 as os.fspath (src/llm_wiki_cli/services….py:_write_workspace_text)
    participant p18 as os.fspath (src/llm_wiki_cli/services…e_workspace_root_argument)
    participant p19 as enumerate
    participant p20 as Path(…).expanduser
    participant p21 as DocumentationIntegrityError (src/llm_wiki_cli/services…y:_control_workspace_root)
    participant p22 as os.path.lexists (src/llm_wiki_cli/services…e_workspace_root_argument)
    participant p23 as target.relative_to
    participant p24 as requested.lstat
    p0-->>p1: _utc_now
    p0-->>p2: _validate_run_payload(run.to_dict(...))
    p0-->>p3: run.to_dict
    p0->>p4: _write_json
    p0->>p5: documentation_run_path
    p0-->>p3: run.to_dict
    p4->>p6: _control_workspace_root
    p5->>p7: _resolve_workspace_root_argument
    p4->>p8: _write_workspace_text
    p4-->>p9: json.dumps(payload, indent=2, sort_keys=True)
    p6-->>p10: Path (src/llm_wiki_cli/services…y:_control_workspace_root)(os.path.abspath(...))
    p8-->>p11: Path (src/llm_wiki_cli/services….py:_write_workspace_text)(os.path.abspath(...))
    p7-->>p12: Path (src/llm_wiki_cli/services…e_workspace_root_argument)(os.path.abspath(...))
    p6-->>p13: os.path.abspath (src/llm_wiki_cli/services…y:_control_workspace_root)(os.fspath(...))
    p8-->>p14: os.path.abspath (src/llm_wiki_cli/services….py:_write_workspace_text)(os.fspath(...))
    p7-->>p15: os.path.abspath (src/llm_wiki_cli/services…e_workspace_root_argument)(os.fspath(...))
    p6-->>p16: os.fspath (src/llm_wiki_cli/services…y:_control_workspace_root)(path)
    p8-->>p17: os.fspath (src/llm_wiki_cli/services….py:_write_workspace_text)(workspace_root)
    p7-->>p18: os.fspath (src/llm_wiki_cli/services…e_workspace_root_argument)(...)
    p6-->>p19: enumerate(absolute.parts)
    p8-->>p11: Path (src/llm_wiki_cli/services….py:_write_workspace_text)(os.path.abspath(...))
    p7-->>p20: Path(…).expanduser
    p6-->>p21: DocumentationIntegrityError (src/llm_wiki_cli/services…y:_control_workspace_root)(…)
    p8-->>p14: os.path.abspath (src/llm_wiki_cli/services….py:_write_workspace_text)(os.fspath(...))
    p7-->>p12: Path (src/llm_wiki_cli/services…e_workspace_root_argument)(workspace)
    p6-->>p10: Path (src/llm_wiki_cli/services…y:_control_workspace_root)(...)
    p8-->>p17: os.fspath (src/llm_wiki_cli/services….py:_write_workspace_text)(path)
    p7-->>p22: os.path.lexists (src/llm_wiki_cli/services…e_workspace_root_argument)(requested)
    p8-->>p23: target.relative_to(root)
    p7-->>p24: requested.lstat
```

> Call sequence diagram shows 30 of 193 interactions; 163 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 25 of 168 (143 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_write_workspace_text` | 13 | - | unresolved | 22 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_write_workspace_text` | 13 | [src/llm_wiki_cli/services/documentation_run/workspace.py](../modules/workspace.md) | internal | 8 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_existing_workspace_layout_safe` | 22 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_existing_workspace_layout_safe` | 22 | [src/llm_wiki_cli/services/documentation_run/workspace.py](../modules/workspace.md) | internal | 4 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_safe_workspace_directory` | 24 | - | unresolved | 14 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_workspace_control_tree_safe` | 41 | - | unresolved | 21 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_workspace_output_tree_safe` | 63 | - | unresolved | 21 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_supports_descriptor_bound_workspace_writes` | 101 | - | unresolved | 2 |
> Omission summary shows 8 of 16 groups; 8 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. save_documentation_run"]
    s2["2. _utc_now"]
    s3["3. _validate_run_payload"]
    s4["4. run.to_dict"]
    s5["5. _write_json"]
    s6["6. _control_workspace_root"]
    s7["7. Path (src/llm_wiki_cli/services…y:_control_workspace_root)"]
    s8["8. os.path.abspath (src/llm_wiki_cli/services…y:_control_workspace_root)"]
    s9["9. os.fspath (src/llm_wiki_cli/services…y:_control_workspace_root)"]
    s10["10. enumerate"]
    s11["11. DocumentationIntegrityError (src/llm_wiki_cli/services…y:_control_workspace_root)"]
    s12["12. Path (src/llm_wiki_cli/services…y:_control_workspace_root)"]
    s1 -. "_utc_now(data not statically known)" .-> s2
    s1 -. "_validate_run_payload(run.to_dict(...))" .-> s3
    s1 -. "run.to_dict(data not statically known)" .-> s4
    s1 -->|"_write_json(documentation_run_path(...), run.to_dict(...))"| s5
    s5 -->|"_control_workspace_root(path)"| s6
    s6 -. "Path (src/llm_wiki_cli/services…y:_control_workspace_root)(os.path.abspath(...))" .-> s7
    s6 -. "os.path.abspath (src/llm_wiki_cli/services…y:_control_workspace_root)(os.fspath(...))" .-> s8
    s6 -. "os.fspath (src/llm_wiki_cli/services…y:_control_workspace_root)(path)" .-> s9
    s6 -. "enumerate(absolute.parts)" .-> s10
    s6 -. "DocumentationIntegrityError (src/llm_wiki_cli/services…y:_control_workspace_root)(…)" .-> s11
    s6 -. "Path (src/llm_wiki_cli/services…y:_control_workspace_root)(...)" .-> s12
    click s1 "../modules/workspace.md"
    click s5 "../modules/workspace.md"
    click s6 "../modules/workspace.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `save_documentation_run` | `workspace: str \| Path`, `run: DocumentationRun` | - | `run.updated_at` | `run` |
| `_utc_now` | - | - | - | - |
| `_validate_run_payload` | - | - | - | - |
| `run.to_dict` | - | - | - | - |
| `_write_json` | `path: Path`, `payload: Mapping[str, Any]` | - | - | - |
| `_control_workspace_root` | `path: Path` | - | - | `Path(...)` |
| `Path (src/llm_wiki_cli/services…y:_control_workspace_root)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…y:_control_workspace_root)` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…y:_control_workspace_root)` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `DocumentationIntegrityError (src/llm_wiki_cli/services…y:_control_workspace_root)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…y:_control_workspace_root)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| save_documentation_run | _utc_now | 36 | `_utc_now(data not statically known)` |
| save_documentation_run | _validate_run_payload | 37 | `_validate_run_payload(run.to_dict(...))` |
| save_documentation_run | run.to_dict | 37 | `run.to_dict(data not statically known)` |
| save_documentation_run | _write_json | 38 | `_write_json(documentation_run_path(...), run.to_dict(...))` |
| _write_json | _control_workspace_root | 745 | `_control_workspace_root(path)` |
| _control_workspace_root | Path (src/llm_wiki_cli/services…y:_control_workspace_root) | 754 | `Path(os.path.abspath(...))` |
| _control_workspace_root | os.path.abspath (src/llm_wiki_cli/services…y:_control_workspace_root) | 754 | `os.path.abspath(os.fspath(...))` |
| _control_workspace_root | os.fspath (src/llm_wiki_cli/services…y:_control_workspace_root) | 754 | `os.fspath(path)` |
| _control_workspace_root | enumerate | 757 | `enumerate(absolute.parts)` |
| _control_workspace_root | DocumentationIntegrityError (src/llm_wiki_cli/services…y:_control_workspace_root) | 761 | `DocumentationIntegrityError('Lifecycle JSON writes must remain under the documentation control directory.')` |
| _control_workspace_root | Path (src/llm_wiki_cli/services…y:_control_workspace_root) | 764 | `Path(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `save_documentation_run` | `_utc_now` | 36 |
| unresolved_call | `save_documentation_run` | `_validate_run_payload` | 37 |
| unresolved_call | `save_documentation_run` | `run.to_dict` | 37 |
| unresolved_call | `_control_workspace_root` | `os.path.abspath` | 754 |
| unresolved_call | `_control_workspace_root` | `os.fspath` | 754 |
| unresolved_call | `_control_workspace_root` | `enumerate` | 757 |
| unresolved_call | `_control_workspace_root` | `DocumentationIntegrityError` | 761 |
| step_limit | `save_documentation_run` | `first 12 steps` | 0 |

## Behavior

This flow starts at `save_documentation_run` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
