# guard_destination

**Entry point:** `publication_candidate_cmd._guard_destination`
**Modules involved:** [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_candidate_cmd](../modules/publication_candidate_cmd.md), [publication_cmd](../modules/publication_cmd.md), [publication_config](../modules/publication_config.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot._is_package_marker`
2. `knowledge_storage_io._absolute_path`
3. `publication_config.load_publication_config`
4. `publication_cmd._inside_input_tree`
5. `publication_cmd._same_file`
6. `publication_cmd._declared_files`
7. `publication_cmd._inside_input_tree`

## Touches

- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_candidate_cmd](../modules/publication_candidate_cmd.md)
- [publication_cmd](../modules/publication_cmd.md)
- [publication_config](../modules/publication_config.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `publication_candidate_cmd._guard_destination`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
