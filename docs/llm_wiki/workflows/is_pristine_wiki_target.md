# is_pristine_wiki_target

**Entry point:** `wiki_lifecycle.is_pristine_wiki_target`
**Modules involved:** [current_contracts](../modules/current_contracts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [wiki_lifecycle](../modules/wiki_lifecycle.md), [wiki_surface](../modules/wiki_surface.md)

> Return whether a target is absent, empty, or the exact init scaffold.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface.iter_page_kinds`
2. `current_contracts.current_contract_defaults`
3. `knowledge_evidence.formatted_json_bytes`
4. `knowledge_evidence.formatted_json_bytes`

## Touches

- [current_contracts](../modules/current_contracts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `wiki_lifecycle.is_pristine_wiki_target`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
