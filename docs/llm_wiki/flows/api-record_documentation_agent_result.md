# record_documentation_agent_result

**Entry point:** `record_documentation_agent_result` (`api`)
**Source:** [record](../modules/record.md)
**Modules touched:** [record](../modules/record.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as record_documentation_agent_result
    participant p1 as _merge_agent_findings
    participant p2 as _verify_user_docs_gate
    participant p3 as _preflight_documentation_native_evidence
    participant p4 as _validate_result_work_ids
    participant p5 as _reconcile_imported_page_edits
    participant p6 as _capture_native_evidence_transaction
    participant p7 as _reconcile_documentation_native_evidence
    participant p8 as _rollback_native_evidence_transaction
    participant p9 as _merge_unique
    participant p10 as _reconcile_semantic_readiness
    participant p11 as _record_review_ledger_iteration
    participant p12 as _has_unresolved_high_findings
    participant p13 as _review_adjustment_state
    participant p14 as _finding_text_values
    participant p15 as _canonical_evidence_targets
    participant p16 as _resolve_workspace_root_argument
    participant p17 as load_documentation_run
    participant p18 as DocumentationAgentResult.from_dict
    participant p19 as isinstance (src/llm_wiki_cli/services…ocumentation_agent_result)
    participant p20 as result.to_dict
    participant p21 as DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)
    participant p22 as run.stage_attempts.get
    participant p23 as result_path.exists
    participant p24 as _verify_stage_dispatch_integrity
    participant p25 as _block_run_for_integrity
    participant p26 as DocumentationIntegrityError (src/llm_wiki_cli/services…ocumentation_agent_result)
    participant p27 as _verify_read_only_inputs
    p0->>p1: _merge_agent_findings
    p0->>p2: _verify_user_docs_gate
    p0->>p3: _preflight_documentation_native_evidence
    p0->>p4: _validate_result_work_ids
    p0->>p5: _reconcile_imported_page_edits
    p0->>p6: _capture_native_evidence_transaction
    p0->>p7: _reconcile_documentation_native_evidence
    p0->>p8: _rollback_native_evidence_transaction
    p0->>p9: _merge_unique
    p0->>p10: _reconcile_semantic_readiness
    p0->>p11: _record_review_ledger_iteration
    p0->>p12: _has_unresolved_high_findings
    p0->>p13: _review_adjustment_state
    p1->>p14: _finding_text_values
    p2->>p15: _canonical_evidence_targets
    p0-->>p16: _resolve_workspace_root_argument(workspace)
    p0-->>p17: load_documentation_run(workspace_root)
    p0-->>p18: DocumentationAgentResult.from_dict(...)
    p0-->>p19: isinstance (src/llm_wiki_cli/services…ocumentation_agent_result)(result, DocumentationAgentResult)
    p0-->>p20: result.to_dict
    p0-->>p21: DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)('Agent result run_id does not match the workspace.')
    p0-->>p21: DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)(...)
    p0-->>p22: run.stage_attempts.get(normalized.stage, 0)
    p0-->>p21: DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)('Agent result requires a previously recorded stage packet attempt.')
    p0-->>p23: result_path.exists
    p0-->>p21: DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)(…)
    p0-->>p24: _verify_stage_dispatch_integrity(workspace_root, run, stage=normalized.stage, attempt=attempt)
    p0-->>p25: _block_run_for_integrity(workspace_root, run, 'Worker reported a forbidden source/input/generated mutation.')
    p0-->>p26: DocumentationIntegrityError (src/llm_wiki_cli/services…ocumentation_agent_result)(…)
    p0-->>p27: _verify_read_only_inputs(workspace_root, run)
```

> Call sequence diagram shows 30 of 458 interactions; 428 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 15 of 436 (421 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_run/record.py:record_documentation_agent_result` | 1 | - | unresolved | 67 |
| `src/llm_wiki_cli/services/documentation_run/record.py:_preflight_documentation_native_evidence` | 45 | - | unresolved | 22 |
| `src/llm_wiki_cli/services/documentation_run/record.py:_validate_result_work_ids` | 68 | - | unresolved | 38 |
| `src/llm_wiki_cli/services/documentation_run/record.py:_reconcile_imported_page_edits` | 108 | - | unresolved | 36 |
| `src/llm_wiki_cli/services/documentation_run/record.py:_capture_native_evidence_transaction` | 147 | - | unresolved | 8 |
| `src/llm_wiki_cli/services/documentation_run/record.py:_reconcile_documentation_native_evidence` | 161 | - | unresolved | 26 |
| `src/llm_wiki_cli/services/documentation_run/record.py:_rollback_native_evidence_transaction` | 190 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/documentation_run/record.py:_merge_unique` | 210 | - | unresolved | 1 |
> Omission summary shows 8 of 18 groups; 10 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. record_documentation_agent_result"]
    s2["2. _resolve_workspace_root_argument"]
    s3["3. load_documentation_run"]
    s4["4. DocumentationAgentResult.from_dict"]
    s5["5. isinstance (src/llm_wiki_cli/services…ocumentation_agent_result)"]
    s6["6. result.to_dict"]
    s7["7. DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)"]
    s8["8. DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)"]
    s9["9. run.stage_attempts.get"]
    s10["10. DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)"]
    s11["11. result_path.exists"]
    s12["12. DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)"]
    s1 -. "_resolve_workspace_root_argument(workspace)" .-> s2
    s1 -. "load_documentation_run(workspace_root)" .-> s3
    s1 -. "DocumentationAgentResult.from_dict(...)" .-> s4
    s1 -. "isinstance (src/llm_wiki_cli/services…ocumentation_agent_result)(result, DocumentationAgentResult)" .-> s5
    s1 -. "result.to_dict(data not statically known)" .-> s6
    s1 -. "DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)('Agent result run_id does not match the workspace.')" .-> s7
    s1 -. "DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)(...)" .-> s8
    s1 -. "run.stage_attempts.get(normalized.stage, 0)" .-> s9
    s1 -. "DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)('Agent result requires a previously recorded stage packet attempt.')" .-> s10
    s1 -. "result_path.exists(data not statically known)" .-> s11
    s1 -. "DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)(…)" .-> s12
    b0["filesystem_read result_path.read_bytes"]
    s1 -. "filesystem_read result_path.read_bytes" .-> b0
    b1["mutation run.validation_results.append"]
    s1 -. "mutation run.validation_results.append" .-> b1
    b2["mutation run.validation_results.append"]
    s1 -. "mutation run.validation_results.append" .-> b2
    click s1 "../modules/record.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `record_documentation_agent_result` | `workspace: str \| Path`, `result: DocumentationAgentResult \| Mapping[str, Any]` | - | - | `run`, `run`, `run`, `run`, `run`, `run`, `run` |
| `_resolve_workspace_root_argument` | - | - | - | - |
| `load_documentation_run` | - | - | - | - |
| `DocumentationAgentResult.from_dict` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ocumentation_agent_result)` | - | - | - | - |
| `result.to_dict` | - | - | - | - |
| `DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)` | - | - | - | - |
| `DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)` | - | - | - | - |
| `run.stage_attempts.get` | - | - | - | - |
| `DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)` | - | - | - | - |
| `result_path.exists` | - | - | - | - |
| `DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| record_documentation_agent_result | _resolve_workspace_root_argument | 781 | `_resolve_workspace_root_argument(workspace)` |
| record_documentation_agent_result | load_documentation_run | 782 | `load_documentation_run(workspace_root)` |
| record_documentation_agent_result | DocumentationAgentResult.from_dict | 783 | `DocumentationAgentResult.from_dict(...)` |
| record_documentation_agent_result | isinstance (src/llm_wiki_cli/services…ocumentation_agent_result) | 784 | `isinstance(result, DocumentationAgentResult)` |
| record_documentation_agent_result | result.to_dict | 784 | `result.to_dict(data not statically known)` |
| record_documentation_agent_result | DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result) | 787 | `DocumentationSchemaError('Agent result run_id does not match the workspace.')` |
| record_documentation_agent_result | DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result) | 791 | `DocumentationSchemaError(...)` |
| record_documentation_agent_result | run.stage_attempts.get | 795 | `run.stage_attempts.get(normalized.stage, 0)` |
| record_documentation_agent_result | DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result) | 797 | `DocumentationSchemaError('Agent result requires a previously recorded stage packet attempt.')` |
| record_documentation_agent_result | result_path.exists | 802 | `result_path.exists(data not statically known)` |
| record_documentation_agent_result | DocumentationSchemaError (src/llm_wiki_cli/services…ocumentation_agent_result) | 803 | `DocumentationSchemaError('This stage-packet attempt already has a result; build a new packet before recording another result.')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `result_path.read_bytes` | `record_documentation_agent_result` | 1018 |
| mutation | `run.validation_results.append` | `record_documentation_agent_result` | 1039 |
| mutation | `run.validation_results.append` | `record_documentation_agent_result` | 1100 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `record_documentation_agent_result` | `_resolve_workspace_root_argument` | 781 |
| unresolved_call | `record_documentation_agent_result` | `load_documentation_run` | 782 |
| unresolved_call | `record_documentation_agent_result` | `DocumentationAgentResult.from_dict` | 783 |
| unresolved_call | `record_documentation_agent_result` | `isinstance` | 784 |
| unresolved_call | `record_documentation_agent_result` | `result.to_dict` | 784 |
| unresolved_call | `record_documentation_agent_result` | `DocumentationSchemaError` | 787 |
| unresolved_call | `record_documentation_agent_result` | `DocumentationSchemaError` | 791 |
| unresolved_call | `record_documentation_agent_result` | `run.stage_attempts.get` | 795 |
| unresolved_call | `record_documentation_agent_result` | `DocumentationSchemaError` | 797 |
| unresolved_call | `record_documentation_agent_result` | `result_path.exists` | 802 |
| unresolved_call | `record_documentation_agent_result` | `DocumentationSchemaError` | 803 |
| step_limit | `record_documentation_agent_result` | `first 12 steps` | 0 |

## Behavior

This flow starts at `record_documentation_agent_result` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
