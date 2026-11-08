# bind_publication_workspace

**Entry point:** `publication.bind_publication_workspace`
**Modules involved:** [documentation_run_contracts](../modules/documentation_run_contracts.md), [knowledge_governance](../modules/knowledge_governance.md), [publication](../modules/publication.md), [workspace](../modules/workspace.md)

> Seed an undispatched external workspace with the explicitly mapped originals.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `workspace._resolve_workspace_root_argument`
2. `workspace.documentation_run_path`
3. `documentation_run_contracts.DocumentationTransitionError`
4. `knowledge_governance.governance_lock`
5. `workspace._workspace_path`

## Touches

- [documentation_run_contracts](../modules/documentation_run_contracts.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [publication](../modules/publication.md)
- [workspace](../modules/workspace.md)

## Behavior

This workflow starts at `publication.bind_publication_workspace`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
