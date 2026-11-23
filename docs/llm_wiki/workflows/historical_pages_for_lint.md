# historical_pages_for_lint

**Entry point:** `lint_service._historical_pages_for_lint`
**Modules involved:** [historical_retirement](../modules/historical_retirement.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [lint_service](../modules/lint_service.md), [source_retirement](../modules/source_retirement.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_retirement.SourceRetirementError`
2. `knowledge_artifacts.require_validated_artifacts`
3. `knowledge_storage_io.StorageReadSession`
4. `historical_retirement.confirm_absence`

## Touches

- [historical_retirement](../modules/historical_retirement.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [lint_service](../modules/lint_service.md)
- [source_retirement](../modules/source_retirement.md)

## Behavior

This workflow starts at `lint_service._historical_pages_for_lint`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
