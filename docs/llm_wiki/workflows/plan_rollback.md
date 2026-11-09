# plan_rollback

**Entry point:** `publication_delivery.plan_rollback`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [publication_candidate](../modules/publication_candidate.md), [publication_delivery](../modules/publication_delivery.md), [publication_links](../modules/publication_links.md)

> Propose a new target commit restoring earlier ownership and preserving manual changes.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_links.check_github_wiki`
2. `knowledge_evidence.hash_json`
3. `knowledge_evidence.hash_json`
4. `publication_candidate._hashes`
5. `knowledge_evidence.hash_json`
6. `knowledge_evidence.hash_json`
7. `knowledge_evidence.hash_json`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_delivery](../modules/publication_delivery.md)
- [publication_links](../modules/publication_links.md)

## Behavior

This workflow starts at `publication_delivery.plan_rollback`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
