# accepted_reviews

**Entry point:** `publish.accepted_reviews`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [publication_candidate](../modules/publication_candidate.md), [publication_impact](../modules/publication_impact.md), [publish](../modules/publish.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_candidate.validate_publication_receipt`
2. `knowledge_evidence.hash_json`
3. `publication_impact.compare_publication_impact`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_impact](../modules/publication_impact.md)
- [publish](../modules/publish.md)

## Behavior

This workflow starts at `publish.accepted_reviews`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
