# current_markdown

**Entry point:** `knowledge_loader._current_markdown`
**Modules involved:** [io](../modules/io.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_loader](../modules/knowledge_loader.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_envelope.hash_markdown_snapshot`
2. `io.read_md`
3. `wiki_surface.collect_wiki_pages`

## Touches

- [io](../modules/io.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `knowledge_loader._current_markdown`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
