# fields

**Entry point:** `search_lexical._fields`
**Modules involved:** [markdown_sections](../modules/markdown_sections.md), [search_lexical](../modules/search_lexical.md), [search_rank](../modules/search_rank.md), [wiki_media](../modules/wiki_media.md)

> Disjoint captured spans; child sections do not multiply parent evidence.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `markdown_sections.parse_markdown_document`
2. `search_rank._tokens`
3. `search_rank._tokens`
4. `wiki_media.mask_fenced_code_blocks`
5. `markdown_sections.split_table_row`
6. `markdown_sections.semantic_table_key`
7. `search_rank._tokens`
8. `search_rank._tokens`

## Touches

- [markdown_sections](../modules/markdown_sections.md)
- [search_lexical](../modules/search_lexical.md)
- [search_rank](../modules/search_rank.md)
- [wiki_media](../modules/wiki_media.md)

## Behavior

This workflow starts at `search_lexical._fields`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
