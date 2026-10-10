# export_documentation_run

**Entry point:** `export_documentation_run` (`api`)
**Source:** [export](../modules/export.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [export](../modules/export.md), [filesystem_guard](../modules/filesystem_guard.md), [io](../modules/io.md), and 7 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [export](../modules/export.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_projection](../modules/knowledge_projection.md)
- [site_export](../modules/site_export.md)
- [site_html_check](../modules/site_html_check.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as export_documentation_run
    participant p1 as _resolve_workspace_root_argument
    participant p2 as load_documentation_run
    participant p3 as _verify_read_only_inputs
    participant p4 as run.evidence.get
    participant p5 as DocumentationIntegrityError (src/llm_wiki_cli/services…:export_documentation_run)
    participant p6 as _read_json
    participant p7 as _workspace_path
    participant p8 as compare_generated_ownership
    participant p9 as generated_payload.get
    participant p10 as any (src/llm_wiki_cli/services…:export_documentation_run)
    participant p11 as generated_diff.values
    participant p12 as DocumentationTransitionError
    participant p13 as _assert_documentation_export_projection_policy
    participant p14 as str (src/llm_wiki_cli/services…:export_documentation_run)
    participant p15 as _load_documentation_knowledge_projection
    participant p16 as export_site_mirror
    participant p17 as _block_run_for_integrity
    participant p18 as _documentation_projection_evidence
    participant p19 as export_report.to_dict
    participant p20 as _write_json
    participant p21 as export_path.relative_to(…).as_posix
    participant p22 as export_path.relative_to
    participant p23 as _run_authorized_builder
    participant p24 as builder_path.relative_to(…).as_posix
    participant p25 as builder_path.relative_to
    p0-->>p1: _resolve_workspace_root_argument(workspace)
    p0-->>p2: load_documentation_run(workspace_root)
    p0-->>p3: _verify_read_only_inputs(workspace_root, run)
    p0-->>p4: run.evidence.get('generated_ownership')
    p0-->>p5: DocumentationIntegrityError (src/llm_wiki_cli/services…:export_documentation_run)('Workspace export requires generated-ownership evidence.')
    p0-->>p6: _read_json(_workspace_path(...))
    p0-->>p7: _workspace_path(workspace_root, generated_path)
    p0-->>p8: compare_generated_ownership(generated_payload.get(...), ...)
    p0-->>p9: generated_payload.get('fingerprints', {...})
    p0-->>p10: any (src/llm_wiki_cli/services…:export_documentation_run)(generated_diff.values(...))
    p0-->>p11: generated_diff.values
    p0-->>p5: DocumentationIntegrityError (src/llm_wiki_cli/services…:export_documentation_run)(...)
    p0-->>p12: DocumentationTransitionError('Workspace export requires a completed user-docs stage and review state.')
    p0-->>p13: _assert_documentation_export_projection_policy(run, knowledge_mode=knowledge_mode, knowledge_public_repository_identity=knowledge_public_repository_identity)
    p0-->>p14: str (src/llm_wiki_cli/services…:export_documentation_run)(run.publication[...])
    p0-->>p14: str (src/llm_wiki_cli/services…:export_documentation_run)(run.publication[...])
    p0-->>p15: _load_documentation_knowledge_projection(…)
    p0->>p16: export_site_mirror
    p0-->>p14: str (src/llm_wiki_cli/services…:export_documentation_run)(run.publication[...])
    p0-->>p17: _block_run_for_integrity(workspace_root, run, message)
    p0-->>p5: DocumentationIntegrityError (src/llm_wiki_cli/services…:export_documentation_run)(message)
    p0-->>p18: _documentation_projection_evidence(…)
    p0-->>p19: export_report.to_dict
    p0-->>p20: _write_json(export_path, export_payload)
    p0-->>p21: export_path.relative_to(…).as_posix
    p0-->>p22: export_path.relative_to(workspace_root)
    p0->>p23: _run_authorized_builder
    p0-->>p20: _write_json(builder_path, builder_evidence)
    p0-->>p24: builder_path.relative_to(…).as_posix
    p0-->>p25: builder_path.relative_to(workspace_root)
```

> Call sequence diagram shows 30 of 1744 interactions; 1714 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 356 (356 omitted); unresolved 28 of 756 (728 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/site_export.py:export_site_mirror` | 19 | [src/llm_wiki_cli/services/site_export.py](../modules/site_export.md) | internal | 41 |
| `src/llm_wiki_cli/services/site_export.py:_validate_format` | 20 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/site_export.py:_validate_format` | 20 | - | external | 1 |
| `src/llm_wiki_cli/services/site_export.py:_validate_format` | 20 | [src/llm_wiki_cli/services/site_export.py](../modules/site_export.md) | internal | 1 |
| `src/llm_wiki_cli/services/site_export.py:_validate_file_friendly` | 24 | [src/llm_wiki_cli/services/site_export.py](../modules/site_export.md) | internal | 1 |
| `src/llm_wiki_cli/services/site_export.py:_validate_profile` | 26 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/site_export.py:_validate_profile` | 26 | - | external | 1 |
| `src/llm_wiki_cli/services/site_export.py:_validate_profile` | 26 | [src/llm_wiki_cli/services/site_export.py](../modules/site_export.md) | internal | 1 |
> Omission summary shows 8 of 362 groups; 354 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. export_documentation_run"]
    s2["2. _resolve_workspace_root_argument"]
    s3["3. load_documentation_run"]
    s4["4. _verify_read_only_inputs"]
    s5["5. run.evidence.get"]
    s6["6. DocumentationIntegrityError (src/llm_wiki_cli/services…:export_documentation_run)"]
    s7["7. _read_json"]
    s8["8. _workspace_path"]
    s9["9. compare_generated_ownership"]
    s10["10. generated_payload.get"]
    s11["11. any (src/llm_wiki_cli/services…:export_documentation_run)"]
    s12["12. generated_diff.values"]
    s1 -. "_resolve_workspace_root_argument(workspace)" .-> s2
    s1 -. "load_documentation_run(workspace_root)" .-> s3
    s1 -. "_verify_read_only_inputs(workspace_root, run)" .-> s4
    s1 -. "run.evidence.get('generated_ownership')" .-> s5
    s1 -. "DocumentationIntegrityError (src/llm_wiki_cli/services…:export_documentation_run)('Workspace export requires generated-ownership evidence.')" .-> s6
    s1 -. "_read_json(_workspace_path(...))" .-> s7
    s1 -. "_workspace_path(workspace_root, generated_path)" .-> s8
    s1 -. "compare_generated_ownership(generated_payload.get(...), ...)" .-> s9
    s1 -. "generated_payload.get('fingerprints', {...})" .-> s10
    s1 -. "any (src/llm_wiki_cli/services…:export_documentation_run)(generated_diff.values(...))" .-> s11
    s1 -. "generated_diff.values(data not statically known)" .-> s12
    b0["mutation run.verdict_limitations.append"]
    s1 -. "mutation run.verdict_limitations.append" .-> b0
    b1["mutation run.verdict_limitations.remove"]
    s1 -. "mutation run.verdict_limitations.remove" .-> b1
    click s1 "../modules/export.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `export_documentation_run` | `workspace: str \| Path`, `build: bool`, `builder_command: Iterable[str] \| None`, `knowledge_mode: str \| None`, `knowledge_public_repository_identity: str \| None` | - | `export_payload[...]`, `run.evidence[...]`, `run.evidence[...]`, `check_payload[...]`, `run.evidence[...]`, `run.evidence[...]` | `final_report` |
| `_resolve_workspace_root_argument` | - | - | - | - |
| `load_documentation_run` | - | - | - | - |
| `_verify_read_only_inputs` | - | - | - | - |
| `run.evidence.get` | - | - | - | - |
| `DocumentationIntegrityError (src/llm_wiki_cli/services…:export_documentation_run)` | - | - | - | - |
| `_read_json` | - | - | - | - |
| `_workspace_path` | - | - | - | - |
| `compare_generated_ownership` | - | - | - | - |
| `generated_payload.get` | - | - | - | - |
| `any (src/llm_wiki_cli/services…:export_documentation_run)` | - | - | - | - |
| `generated_diff.values` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| export_documentation_run | _resolve_workspace_root_argument | 477 | `_resolve_workspace_root_argument(workspace)` |
| export_documentation_run | load_documentation_run | 478 | `load_documentation_run(workspace_root)` |
| export_documentation_run | _verify_read_only_inputs | 479 | `_verify_read_only_inputs(workspace_root, run)` |
| export_documentation_run | run.evidence.get | 480 | `run.evidence.get('generated_ownership')` |
| export_documentation_run | DocumentationIntegrityError (src/llm_wiki_cli/services…:export_documentation_run) | 482 | `DocumentationIntegrityError('Workspace export requires generated-ownership evidence.')` |
| export_documentation_run | _read_json | 485 | `_read_json(_workspace_path(...))` |
| export_documentation_run | _workspace_path | 485 | `_workspace_path(workspace_root, generated_path)` |
| export_documentation_run | compare_generated_ownership | 486 | `compare_generated_ownership(generated_payload.get(...), ...)` |
| export_documentation_run | generated_payload.get | 487 | `generated_payload.get('fingerprints', {...})` |
| export_documentation_run | any (src/llm_wiki_cli/services…:export_documentation_run) | 490 | `any(generated_diff.values(...))` |
| export_documentation_run | generated_diff.values | 490 | `generated_diff.values(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `run.verdict_limitations.append` | `export_documentation_run` | 639 |
| mutation | `run.verdict_limitations.remove` | `export_documentation_run` | 641 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `export_documentation_run` | `_resolve_workspace_root_argument` | 477 |
| unresolved_call | `export_documentation_run` | `load_documentation_run` | 478 |
| unresolved_call | `export_documentation_run` | `_verify_read_only_inputs` | 479 |
| unresolved_call | `export_documentation_run` | `run.evidence.get` | 480 |
| unresolved_call | `export_documentation_run` | `DocumentationIntegrityError` | 482 |
| unresolved_call | `export_documentation_run` | `_read_json` | 485 |
| unresolved_call | `export_documentation_run` | `_workspace_path` | 485 |
| unresolved_call | `export_documentation_run` | `compare_generated_ownership` | 486 |
| unresolved_call | `export_documentation_run` | `generated_payload.get` | 487 |
| unresolved_call | `export_documentation_run` | `any` | 490 |
| unresolved_call | `export_documentation_run` | `generated_diff.values` | 490 |
| step_limit | `export_documentation_run` | `first 12 steps` | 0 |

## Behavior

This flow starts at `export_documentation_run` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
