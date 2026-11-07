# prepare

**Entry point:** `publication_candidate._prepare`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_candidate](../modules/publication_candidate.md), [publication_config](../modules/publication_config.md), [publication_impact](../modules/publication_impact.md), [publication_links](../modules/publication_links.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `publication_config.load_publication_config`
3. `publication_config.publication_path`
4. `publication_config.publication_path`
5. `publication_impact.capture_publication_basis`
6. `knowledge_storage_io.StorageReadSession`
7. `knowledge_evidence.sha256_bytes`
8. `publication_links.prepare_wiki_markdown`
9. `knowledge_evidence.sha256_bytes`
10. `knowledge_evidence.sha256_bytes`
11. `knowledge_evidence.sha256_bytes`
12. `publication_links.check_github_wiki`
13. `publication_impact.project_publication_targets`
14. `publication_impact.compare_publication_impact`
15. `publication_impact.capture_publication_basis`
16. `publication_config.load_publication_config`
17. `knowledge_evidence.hash_json`
18. `knowledge_evidence.hash_json`
19. `knowledge_evidence.hash_json`
20. `knowledge_evidence.hash_json`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_config](../modules/publication_config.md)
- [publication_impact](../modules/publication_impact.md)
- [publication_links](../modules/publication_links.md)

## Behavior

This workflow starts at `publication_candidate._prepare`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
