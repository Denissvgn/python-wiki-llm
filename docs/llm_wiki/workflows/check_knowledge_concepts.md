# check_knowledge_concepts

**Entry point:** `lint_service._check_knowledge_concepts`
**Modules involved:** [evidence_diagnostics](../modules/evidence_diagnostics.md), [knowledge_observability](../modules/knowledge_observability.md), [lint_service](../modules/lint_service.md), [source_retirement](../modules/source_retirement.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_retirement.source_retirement_projection`
2. `evidence_diagnostics.captured_evidence_diagnostic`
3. `knowledge_observability.knowledge_freshness_hint`
4. `knowledge_observability.freshness_analysis_diagnostic`
5. `evidence_diagnostics.captured_evidence_diagnostic`

## Touches

- [evidence_diagnostics](../modules/evidence_diagnostics.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [lint_service](../modules/lint_service.md)
- [source_retirement](../modules/source_retirement.md)

## Behavior

This workflow starts at `lint_service._check_knowledge_concepts`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
