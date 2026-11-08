# checked_preview

**Entry point:** `publication_maintenance._checked_preview`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [publication_candidate](../modules/publication_candidate.md), [publication_links](../modules/publication_links.md), [publication_maintenance](../modules/publication_maintenance.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_candidate._read_tree`
2. `publication_candidate._hashes`
3. `publication_links.prepare_wiki_markdown`
4. `publication_links.check_github_wiki`
5. `knowledge_evidence.hash_json`
6. `publication_candidate._hashes`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_links](../modules/publication_links.md)
- [publication_maintenance](../modules/publication_maintenance.md)

## Behavior

This workflow starts at `publication_maintenance._checked_preview`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
