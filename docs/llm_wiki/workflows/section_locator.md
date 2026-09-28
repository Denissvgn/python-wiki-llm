# section_locator

**Entry point:** `knowledge_governance._section_locator`
**Modules involved:** [concept_identity](../modules/concept_identity.md), [knowledge_governance](../modules/knowledge_governance.md), [validation](../modules/validation.md), [wiki_media](../modules/wiki_media.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `concept_identity.validate_locator`
2. `validation.require_no_control_characters`
3. `wiki_media.contains_uri_authority_userinfo`

## Touches

- [concept_identity](../modules/concept_identity.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)

## Behavior

This workflow starts at `knowledge_governance._section_locator`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
