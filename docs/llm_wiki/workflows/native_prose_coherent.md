# native_prose_coherent

**Entry point:** `maintenance_service._native_prose_coherent`
**Modules involved:** [io](../modules/io.md), [knowledge_envelope](../modules/knowledge_envelope.md), [maintenance_service](../modules/maintenance_service.md), [wiki_surface](../modules/wiki_surface.md)

> Check native normalized prose without treating ledger baselines as current.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `io.decode_markdown_bytes`
2. `wiki_surface.collect_wiki_pages`
3. `knowledge_envelope.hash_markdown_snapshot`

## Touches

- [io](../modules/io.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [maintenance_service](../modules/maintenance_service.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `maintenance_service._native_prose_coherent`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
