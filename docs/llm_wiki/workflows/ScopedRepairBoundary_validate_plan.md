# ScopedRepairBoundary_validate_plan

**Entry point:** `scoped_sync_repair.ScopedRepairBoundary.validate_plan`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_storage](../modules/knowledge_storage.md), [scoped_sync_repair](../modules/scoped_sync_repair.md)

> Verify the full candidate, including globals, before root publication.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_artifacts.validate_knowledge_artifacts`
2. `knowledge_model.knowledge_index_to_payload`
3. `knowledge_storage.canonical_bytes`
4. `knowledge_storage.canonical_bytes`
5. `knowledge_storage.canonical_bytes`
6. `knowledge_storage.canonical_bytes`
7. `knowledge_storage.canonical_bytes`
8. `knowledge_storage.canonical_bytes`
9. `knowledge_storage.canonical_bytes`
10. `knowledge_storage.canonical_bytes`
11. `knowledge_storage.canonical_bytes`
12. `knowledge_storage.canonical_bytes`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [scoped_sync_repair](../modules/scoped_sync_repair.md)

## Behavior

Before publication, this check revalidates source, provider and Markdown inputs
and validates the complete candidate's native artifacts. It compares producer,
global bundle, protected concepts, relationships and extensions against the
committed state while excluding only declared transaction metadata and selected
pages. Canonical JSON comparisons preserve boolean/number distinctions and
missing versus explicit null extension keys.

Selected review histories cannot change or acquire an acknowledgment. After
removing only the permitted selected observations and transaction fields, the
remaining manifest must also match. A mismatch refuses the scoped update before
active publication; success establishes these application boundaries, not global
evidence completeness or human review. The caller retains the ordinary guarded,
recoverable publication workflow.
