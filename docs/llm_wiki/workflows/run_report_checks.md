# run_report_checks

**Entry point:** `lint_service._run_report_checks`
**Modules involved:** [knowledge_observability](../modules/knowledge_observability.md), [knowledge_verification](../modules/knowledge_verification.md), [lint_service](../modules/lint_service.md), [plugins](../modules/plugins.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `plugins.runtime_project_plugins_enabled`
2. `knowledge_verification.attach_machine_verification_read_view`
3. `knowledge_observability.KnowledgePhaseDurations`

## Touches

- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [lint_service](../modules/lint_service.md)
- [plugins](../modules/plugins.md)

## Behavior

This workflow starts at `lint_service._run_report_checks`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
