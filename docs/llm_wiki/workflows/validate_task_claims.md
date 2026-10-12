# validate_task_claims

**Entry point:** `task_context._validate_task_claims`
**Modules involved:** [analysis_capture](../modules/analysis_capture.md), [documentation_query_builder](../modules/documentation_query_builder.md), [knowledge_evidence](../modules/knowledge_evidence.md), [task_context](../modules/task_context.md)

> Check semantic bindings that a self-consistent content hash cannot prove.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_evidence.is_valid_sha256`
2. `documentation_query_builder.normalize_supplied_paths`
3. `documentation_query_builder.normalize_supplied_paths`
4. `analysis_capture.validate_analysis_diagnostics`

## Touches

- [analysis_capture](../modules/analysis_capture.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [task_context](../modules/task_context.md)

## Behavior

This workflow starts at `task_context._validate_task_claims`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
