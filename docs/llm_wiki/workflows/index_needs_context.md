# index_needs_context

**Entry point:** `documentation_worklist._index_needs_context`
**Modules involved:** [documentation_worklist](../modules/documentation_worklist.md), [markdown_sections](../modules/markdown_sections.md), [wiki_media](../modules/wiki_media.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `markdown_sections.parse_markdown_sections`
2. `wiki_media.mask_markdown_code`
3. `wiki_media.iter_markdown_link_targets`
4. `wiki_media.mask_markdown_code`
5. `wiki_media.local_link_path`
6. `wiki_surface.is_safe_page_id`

## Touches

- [documentation_worklist](../modules/documentation_worklist.md)
- [markdown_sections](../modules/markdown_sections.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `documentation_worklist._index_needs_context`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
