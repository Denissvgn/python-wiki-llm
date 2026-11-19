# checked_preview

**Entry point:** `publication_maintenance._checked_preview`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [publication_candidate](../modules/publication_candidate.md), [publication_maintenance](../modules/publication_maintenance.md), [publication_targets](../modules/publication_targets.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_candidate._read_tree`
2. `publication_candidate._hashes`
3. `publication_targets.publication_target`
4. `knowledge_evidence.hash_json`
5. `publication_candidate._hashes`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_maintenance](../modules/publication_maintenance.md)
- [publication_targets](../modules/publication_targets.md)

## Behavior

This workflow starts at `publication_maintenance._checked_preview`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
