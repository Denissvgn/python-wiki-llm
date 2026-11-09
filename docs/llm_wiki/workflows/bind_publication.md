# bind_publication

**Entry point:** `publication._bind_publication`
**Modules involved:** [documentation_policy](../modules/documentation_policy.md), [documentation_run_contracts](../modules/documentation_run_contracts.md), [filesystem_guard](../modules/filesystem_guard.md), [integrity](../modules/integrity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [publication](../modules/publication.md), [publication_candidate](../modules/publication_candidate.md), [workspace](../modules/workspace.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `workspace.documentation_run_path`
2. `workspace.load_documentation_run`
3. `integrity._verify_read_only_inputs`
4. `documentation_run_contracts.DocumentationTransitionError`
5. `knowledge_evidence.hash_json`
6. `documentation_run_contracts.DocumentationIntegrityError`
7. `documentation_run_contracts.DocumentationIntegrityError`
8. `documentation_policy.capture_tree_baseline`
9. `documentation_run_contracts.DocumentationTransitionError`
10. `workspace._read_json`
11. `workspace._workspace_path`
12. `documentation_policy.capture_tree_baseline`
13. `documentation_run_contracts.DocumentationIntegrityError`
14. `workspace._workspace_path`
15. `workspace._workspace_path`
16. `documentation_run_contracts.DocumentationIntegrityError`
17. `documentation_run_contracts._utc_now`
18. `documentation_run_contracts.DocumentationRun.from_dict`
19. `filesystem_guard.atomic_write_private_bytes`
20. `publication_candidate._read_tree`
21. `documentation_run_contracts.DocumentationIntegrityError`
22. `filesystem_guard.atomic_write_private_bytes`
23. `publication_candidate._read_tree`
24. `filesystem_guard.unlink_guarded_bytes`

## Touches

- [documentation_policy](../modules/documentation_policy.md)
- [documentation_run_contracts](../modules/documentation_run_contracts.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [integrity](../modules/integrity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [publication](../modules/publication.md)
- [publication_candidate](../modules/publication_candidate.md)
- [workspace](../modules/workspace.md)

## Behavior

This workflow starts at `publication._bind_publication`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
