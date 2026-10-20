# ScopedRepairBoundary_validate_plan

**Entry point:** `scoped_sync_repair.ScopedRepairBoundary.validate_plan`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_storage](../modules/knowledge_storage.md), [scoped_sync_repair](../modules/scoped_sync_repair.md)

> Verify the full candidate, including globals, before root publication.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_artifacts.validate_knowledge_artifacts`
2. `knowledge_storage.canonical_bytes`
3. `knowledge_storage.canonical_bytes`
4. `knowledge_model.knowledge_index_to_payload`
5. `knowledge_storage.canonical_bytes`
6. `knowledge_storage.canonical_bytes`
7. `knowledge_storage.canonical_bytes`
8. `knowledge_storage.canonical_bytes`
9. `knowledge_storage.canonical_bytes`
10. `knowledge_storage.canonical_bytes`
11. `knowledge_storage.canonical_bytes`
12. `knowledge_storage.canonical_bytes`
13. `knowledge_storage.canonical_bytes`
14. `knowledge_storage.canonical_bytes`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [scoped_sync_repair](../modules/scoped_sync_repair.md)

## Behavior

Before publication, this check revalidates source, provider and Markdown inputs and validates the complete native candidate. Its producer must match the checked current analysis through canonical JSON, preserving boolean/number and missing/null distinctions. Global source, policy, repository and graph facts remain protected alongside unselected structural baselines, page bytes and relationships.

Closed executable issuer fields can re-anchor only when the actual current capture supplies that issuer and all source, syntax, prose and availability facts match. An issuer change can reopen ordinary review, preserving its histories and mapping; it cannot manufacture an acknowledgement. All remaining manifest facts must match after the declared selected and transaction fields are removed.

A mismatch refuses the scoped update through the existing guarded publication and recovery workflow. Success establishes these application boundaries, not whole-wiki evidence completeness, runtime behavior or human review.
