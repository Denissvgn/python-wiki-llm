# stage_publication_documents

**Entry point:** `publication._stage_publication_documents`
**Modules involved:** [documentation_run_contracts](../modules/documentation_run_contracts.md), [filesystem_guard](../modules/filesystem_guard.md), [publication](../modules/publication.md), [publication_candidate](../modules/publication_candidate.md), [workspace](../modules/workspace.md)

> Validate, copy and re-read each declared Markdown file before committing the binding.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `workspace._workspace_path`
2. `documentation_run_contracts.DocumentationIntegrityError`
3. `filesystem_guard.ensure_guarded_directory`
4. `filesystem_guard.atomic_write_private_bytes`
5. `publication_candidate._read_tree`
6. `documentation_run_contracts.DocumentationIntegrityError`

## Touches

- [documentation_run_contracts](../modules/documentation_run_contracts.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [publication](../modules/publication.md)
- [publication_candidate](../modules/publication_candidate.md)
- [workspace](../modules/workspace.md)

## Behavior

This workflow starts at `publication._stage_publication_documents`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
