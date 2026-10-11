# save_documentation_run

**Entry point:** `save_documentation_run` (`api`)
**Source:** [workspace](../modules/workspace.md)
**Modules touched:** [workspace](../modules/workspace.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as save_documentation_run
    participant p1 as _write_json
    participant p2 as documentation_run_path
    participant p3 as _resolve_workspace_root_argument
    participant p4 as _write_workspace_text
    participant p5 as _assert_existing_workspace_layout_safe
    participant p6 as _write_descriptor_bound_workspace_text
    participant p7 as _control_workspace_root
    participant p8 as _assert_safe_workspace_directory
    participant p9 as _supports_descriptor_bound_workspace_writes
    participant p10 as _uses_windows_guarded_path_writes
    participant p11 as _directory_identity
    participant p12 as _assert_workspace_control_tree_safe
    participant p13 as _assert_workspace_output_tree_safe
    participant p14 as _assert_open_parent_within_workspace
    participant p15 as _assert_relative_write_target_regular
    participant p16 as _fsync_directory_after_replace
    participant p17 as _utc_now
    participant p18 as _validate_run_payload
    participant p19 as run.to_dict
    participant p20 as json.dumps
    participant p21 as Path (src/llm_wiki_cli/services…y:_control_workspace_root)
    participant p22 as Path (src/llm_wiki_cli/services….py:_write_workspace_text)
    participant p23 as Path (src/llm_wiki_cli/services…e_workspace_root_argument)
    participant p24 as os.path.abspath (src/llm_wiki_cli/services…y:_control_workspace_root)
    participant p25 as os.path.abspath (src/llm_wiki_cli/services….py:_write_workspace_text)
    participant p26 as os.path.abspath (src/llm_wiki_cli/services…e_workspace_root_argument)
    participant p27 as os.fspath (src/llm_wiki_cli/services…y:_control_workspace_root)
    participant p28 as os.fspath (src/llm_wiki_cli/services….py:_write_workspace_text)
    participant p29 as os.fspath (src/llm_wiki_cli/services…e_workspace_root_argument)
    p0->>p1: _write_json
    p0->>p2: documentation_run_path
    p2->>p3: _resolve_workspace_root_argument
    p1->>p4: _write_workspace_text
    p4->>p5: _assert_existing_workspace_layout_safe
    p4->>p6: _write_descriptor_bound_workspace_text
    p1->>p7: _control_workspace_root
    p4->>p8: _assert_safe_workspace_directory
    p4->>p9: _supports_descriptor_bound_workspace_writes
    p4->>p10: _uses_windows_guarded_path_writes
    p4->>p11: _directory_identity
    p5->>p12: _assert_workspace_control_tree_safe
    p5->>p13: _assert_workspace_output_tree_safe
    p6->>p14: _assert_open_parent_within_workspace
    p6->>p15: _assert_relative_write_target_regular
    p6->>p16: _fsync_directory_after_replace
    p0-->>p17: _utc_now
    p0-->>p18: _validate_run_payload(run.to_dict(...))
    p0-->>p19: run.to_dict
    p0-->>p19: run.to_dict
    p1-->>p20: json.dumps(payload, indent=2, sort_keys=True)
    p7-->>p21: Path (src/llm_wiki_cli/services…y:_control_workspace_root)(os.path.abspath(...))
    p4-->>p22: Path (src/llm_wiki_cli/services….py:_write_workspace_text)(os.path.abspath(...))
    p3-->>p23: Path (src/llm_wiki_cli/services…e_workspace_root_argument)(os.path.abspath(...))
    p7-->>p24: os.path.abspath (src/llm_wiki_cli/services…y:_control_workspace_root)(os.fspath(...))
    p4-->>p25: os.path.abspath (src/llm_wiki_cli/services….py:_write_workspace_text)(os.fspath(...))
    p3-->>p26: os.path.abspath (src/llm_wiki_cli/services…e_workspace_root_argument)(os.fspath(...))
    p7-->>p27: os.fspath (src/llm_wiki_cli/services…y:_control_workspace_root)(path)
    p4-->>p28: os.fspath (src/llm_wiki_cli/services….py:_write_workspace_text)(workspace_root)
    p3-->>p29: os.fspath (src/llm_wiki_cli/services…e_workspace_root_argument)(...)
```

> Call sequence diagram shows 30 of 193 interactions; 163 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 14 of 168 (154 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_control_workspace_root` | 6 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_write_workspace_text` | 13 | - | unresolved | 26 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_existing_workspace_layout_safe` | 22 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_existing_workspace_layout_safe` | 22 | [src/llm_wiki_cli/services/documentation_run/workspace.py](../modules/workspace.md) | internal | 2 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_safe_workspace_directory` | 24 | - | unresolved | 14 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_workspace_control_tree_safe` | 41 | - | unresolved | 21 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_assert_workspace_output_tree_safe` | 63 | - | unresolved | 21 |
| `src/llm_wiki_cli/services/documentation_run/workspace.py:_supports_descriptor_bound_workspace_writes` | 101 | - | unresolved | 2 |
> Omission summary shows 8 of 17 groups; 9 further groups are not expanded here. Counts above include all omitted interactions.
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
