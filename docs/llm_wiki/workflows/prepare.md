# prepare

**Entry point:** `publication_candidate._prepare`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_candidate](../modules/publication_candidate.md), [publication_config](../modules/publication_config.md), [publication_impact](../modules/publication_impact.md), [publication_targets](../modules/publication_targets.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `publication_config.load_publication_config`
3. `publication_config.publication_control_overlap`
4. `publication_config.publication_input_controls`
5. `publication_config.publication_path`
6. `publication_targets.publication_target`
7. `publication_impact.capture_publication_basis`
8. `knowledge_storage_io.StorageReadSession`
9. `canonical_json.sha256_digest`
10. `canonical_json.sha256_digest`
11. `canonical_json.sha256_digest`
12. `canonical_json.sha256_digest`
13. `publication_impact.project_publication_targets`
14. `publication_impact.compare_publication_impact`
15. `publication_impact.capture_publication_basis`
16. `publication_config.load_publication_config`
17. `knowledge_evidence.hash_json`
18. `knowledge_evidence.hash_json`
19. `knowledge_evidence.hash_json`
20. `knowledge_evidence.hash_json`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_config](../modules/publication_config.md)
- [publication_impact](../modules/publication_impact.md)
- [publication_targets](../modules/publication_targets.md)

## Behavior

This workflow starts at `publication_candidate._prepare`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
