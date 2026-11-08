# validate_candidate_tree

**Entry point:** `publication_candidate.validate_candidate_tree`
**Modules involved:** [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_candidate](../modules/publication_candidate.md), [publication_impact](../modules/publication_impact.md), [publication_links](../modules/publication_links.md)

> Verify the full artifact inventory before preparing a local review.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `publication_links.check_github_wiki`
3. `publication_impact.publication_target_observation`
4. `publication_impact.publication_target_observation`

## Touches

- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_impact](../modules/publication_impact.md)
- [publication_links](../modules/publication_links.md)

## Behavior

This workflow starts at `publication_candidate.validate_candidate_tree`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
