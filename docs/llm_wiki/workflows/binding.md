# binding

**Entry point:** `publication._binding`
**Modules involved:** [documentation_run_contracts](../modules/documentation_run_contracts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [publication](../modules/publication.md), [workspace](../modules/workspace.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `workspace._read_json`
2. `workspace._workspace_path`
3. `knowledge_evidence.hash_json`
4. `documentation_run_contracts.DocumentationIntegrityError`

## Touches

- [documentation_run_contracts](../modules/documentation_run_contracts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [publication](../modules/publication.md)
- [workspace](../modules/workspace.md)

## Behavior

This workflow starts at `publication._binding`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
