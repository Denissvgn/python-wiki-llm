# assert_bootstrap_output_excluded

**Entry point:** `publication_snapshot.assert_bootstrap_output_excluded`
**Modules involved:** [config](../modules/config.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_snapshot](../modules/publication_snapshot.md), [source_snapshot](../modules/source_snapshot.md)

> Reject future output files that would become bootstrap producer inputs.

Only prospective source, infrastructure, package or selection inputs need
an exclusion. Ordinary Markdown and public media remain usable beneath a
source root. This reads the consumer's current selection; it never edits
ignore rules or silently adds an exclusion.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io._absolute_path`
3. `config.is_agent_worktree_path`
4. `source_snapshot._language_for_path`
5. `source_snapshot._unsupported_language_for_path`
6. `source_snapshot._is_dockerfile_candidate`
7. `source_snapshot._is_compose_candidate`
8. `source_snapshot._is_package_marker`
9. `source_snapshot.build_source_snapshot`
10. `config.GitIgnoreMatcher`
11. `config.GitIgnoreMatcher.is_ignored`
12. `source_snapshot._is_rescuable_typescript_src_lib_file`

## Touches

- [config](../modules/config.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_snapshot](../modules/publication_snapshot.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `publication_snapshot.assert_bootstrap_output_excluded`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
