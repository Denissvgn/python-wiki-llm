# wiki_input_hashes

**Entry point:** `knowledge_reuse.wiki_input_hashes`
**Modules involved:** [io](../modules/io.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_reuse](../modules/knowledge_reuse.md), [validation](../modules/validation.md), [wiki_media](../modules/wiki_media.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `io.read_md`
2. `wiki_surface.collect_wiki_pages`
3. `wiki_media.build_asset_index`
4. `validation.resolve_portable_workspace_path`
5. `knowledge_envelope.hash_markdown_snapshot`
6. `knowledge_evidence.hash_json`

## Touches

- [io](../modules/io.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `knowledge_reuse.wiki_input_hashes`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
