# inspect_branch_wiki_changes

**Entry point:** `wiki_git_delivery.inspect_branch_wiki_changes`
**Modules involved:** [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [team](../modules/team.md), [wiki_git_delivery](../modules/wiki_git_delivery.md), [wiki_git_policy](../modules/wiki_git_policy.md)

> Report generated wiki paths a branch changed since ``base``.

Under trunk ownership a non-writer branch must leave generated paths as
they are at its merge base. Only Git metadata is read: no snapshot is
validated and no source is scanned.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `team.wiki_ownership`
3. `team.load_team_config`
4. `knowledge_storage_io._absolute_path`
5. `wiki_git_policy.classify_wiki_git_policy`

## Touches

- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [team](../modules/team.md)
- [wiki_git_delivery](../modules/wiki_git_delivery.md)
- [wiki_git_policy](../modules/wiki_git_policy.md)

## Behavior

This workflow starts at `wiki_git_delivery.inspect_branch_wiki_changes`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
