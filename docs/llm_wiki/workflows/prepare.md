# prepare

**Entry point:** `publication_candidate._prepare`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_candidate](../modules/publication_candidate.md), [publication_config](../modules/publication_config.md), [publication_impact](../modules/publication_impact.md), [publication_links](../modules/publication_links.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `publication_config.load_publication_config`
3. `publication_config.publication_control_overlap`
4. `publication_config.publication_input_controls`
5. `publication_config.publication_path`
6. `publication_impact.capture_publication_basis`
7. `knowledge_storage_io.StorageReadSession`
8. `knowledge_evidence.sha256_bytes`
9. `publication_links.prepare_wiki_markdown`
10. `knowledge_evidence.sha256_bytes`
11. `knowledge_evidence.sha256_bytes`
12. `knowledge_evidence.sha256_bytes`
13. `publication_links.check_github_wiki`
14. `publication_impact.project_publication_targets`
15. `publication_impact.compare_publication_impact`
16. `publication_impact.capture_publication_basis`
17. `publication_config.load_publication_config`
18. `knowledge_evidence.hash_json`
19. `knowledge_evidence.hash_json`
20. `knowledge_evidence.hash_json`
21. `knowledge_evidence.hash_json`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_config](../modules/publication_config.md)
- [publication_impact](../modules/publication_impact.md)
- [publication_links](../modules/publication_links.md)

## Behavior

This workflow starts at `publication_candidate._prepare`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
