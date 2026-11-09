# publication_candidate_cmd_flow

**Entry point:** `publication_candidate_cmd.run`
**Modules involved:** [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_candidate](../modules/publication_candidate.md), [publication_candidate_cmd](../modules/publication_candidate_cmd.md), [publication_cmd](../modules/publication_cmd.md), [publication_config](../modules/publication_config.md), [publication_contracts](../modules/publication_contracts.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_cmd._normalize_consumer_paths`
2. `publication_config.publication_control_overlap`
3. `publication_candidate.validate_publication_receipt`
4. `publication_candidate.validate_candidate_tree`
5. `publication_candidate.validate_candidate_target`
6. `publication_candidate.review_publication_candidate`
7. `publication_cmd._document_bytes`
8. `publication_contracts.validate_publication_basis`
9. `publication_candidate.validate_publication_receipt`
10. `knowledge_storage_io._absolute_path`
11. `publication_config.publication_control_overlap`
12. `publication_cmd._document_bytes`
13. `publication_candidate.export_publication_candidate`
14. `publication_candidate.check_publication_candidate`
15. `publication_cmd._document_bytes`

## Touches

- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_candidate_cmd](../modules/publication_candidate_cmd.md)
- [publication_cmd](../modules/publication_cmd.md)
- [publication_config](../modules/publication_config.md)
- [publication_contracts](../modules/publication_contracts.md)

## Behavior

This workflow starts at `publication_candidate_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
