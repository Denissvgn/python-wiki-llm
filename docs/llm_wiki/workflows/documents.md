# documents

**Entry point:** `publication._documents`
**Modules involved:** [documentation_run_contracts](../modules/documentation_run_contracts.md), [publication](../modules/publication.md), [publication_candidate](../modules/publication_candidate.md), [workspace](../modules/workspace.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_candidate._read_tree`
2. `workspace._workspace_path`
3. `documentation_run_contracts.DocumentationIntegrityError`
4. `documentation_run_contracts.DocumentationIntegrityError`

## Touches

- [documentation_run_contracts](../modules/documentation_run_contracts.md)
- [publication](../modules/publication.md)
- [publication_candidate](../modules/publication_candidate.md)
- [workspace](../modules/workspace.md)

## Behavior

This workflow starts at `publication._documents`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
