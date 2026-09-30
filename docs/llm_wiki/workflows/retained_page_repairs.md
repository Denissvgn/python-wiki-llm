# retained_page_repairs

**Entry point:** `sync_transitions._retained_page_repairs`
**Modules involved:** [knowledge_storage_io](../modules/knowledge_storage_io.md), [markdown_sections](../modules/markdown_sections.md), [sync_retained_links](../modules/sync_retained_links.md), [sync_transitions](../modules/sync_transitions.md), [validation](../modules/validation.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `validation.portable_path_key`
2. `validation.portable_path_key`
3. `validation.portable_path_key`
4. `knowledge_storage_io.StorageReadSession`
5. `markdown_sections.normalize_markdown`
6. `sync_retained_links.repair_retained_page_links`

## Touches

- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [markdown_sections](../modules/markdown_sections.md)
- [sync_retained_links](../modules/sync_retained_links.md)
- [sync_transitions](../modules/sync_transitions.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `sync_transitions._retained_page_repairs`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
