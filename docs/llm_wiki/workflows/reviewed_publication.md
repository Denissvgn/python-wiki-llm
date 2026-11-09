# reviewed_publication

**Entry point:** `publication.reviewed_publication`
**Modules involved:** [documentation_policy](../modules/documentation_policy.md), [documentation_review](../modules/documentation_review.md), [documentation_run_contracts](../modules/documentation_run_contracts.md), [integrity](../modules/integrity.md), [publication](../modules/publication.md), [workspace](../modules/workspace.md)

> Read the same accepted bytes and independent packet/result hashes that were reconciled.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `documentation_run_contracts.DocumentationTransitionError`
2. `integrity._verify_read_only_inputs`
3. `documentation_policy.capture_tree_baseline`
4. `documentation_review.DocumentationReviewLedger.from_dict`
5. `workspace._read_json`
6. `workspace._workspace_path`
7. `documentation_run_contracts.DocumentationTransitionError`
8. `workspace._read_json`
9. `workspace._workspace_path`
10. `documentation_run_contracts.DocumentationIntegrityError`
11. `workspace._read_json`
12. `workspace._workspace_path`
13. `documentation_run_contracts.DocumentationIntegrityError`
14. `workspace._workspace_path`
15. `workspace._read_json`
16. `documentation_policy.hash_bytes`
17. `documentation_policy.hash_bytes`
18. `workspace._workspace_path`
19. `documentation_run_contracts.DocumentationIntegrityError`
20. `documentation_run_contracts.DocumentationIntegrityError`

## Touches

- [documentation_policy](../modules/documentation_policy.md)
- [documentation_review](../modules/documentation_review.md)
- [documentation_run_contracts](../modules/documentation_run_contracts.md)
- [integrity](../modules/integrity.md)
- [publication](../modules/publication.md)
- [workspace](../modules/workspace.md)

## Behavior

This workflow starts at `publication.reviewed_publication`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
