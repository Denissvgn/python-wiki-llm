# audit_knowledge_stream

**Entry point:** `knowledge_stream_audit.audit_knowledge_stream`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_audit](../modules/knowledge_audit.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_graph](../modules/knowledge_graph.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_stream_audit](../modules/knowledge_stream_audit.md), [manifest_storage](../modules/manifest_storage.md), [storage_sort](../modules/storage_sort.md), [storage_spool](../modules/storage_spool.md)

> Validate all storage bytes, logical hash, record shapes and exact routing.

Expanded records are capped at 1 MiB by default (8 MiB maximum), merge runs
use 1 MiB batches/32 handles, each spill index is capped at 16 MiB encoded
key weight, and each private spill has a 2 GiB write quota. These are explicit
streaming limits; the existing full-model API keeps its original limits.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_packs.open_knowledge_store`
3. `storage_spool.DecodeCache`
4. `storage_spool.DecodeCache`
5. `storage_spool.DecodeCache`
6. `storage_spool.DecodeCache`
7. `manifest_storage.read_manifest_header`
8. `knowledge_model._parse_bundle`
9. `knowledge_storage.digest`
10. `knowledge_envelope.EvaluatedEnvelope`
11. `knowledge_storage.KnowledgeStorageError`
12. `storage_sort.SortedRuns`
13. `storage_spool.JsonSpool`
14. `storage_spool.JsonSpool`
15. `storage_spool.JsonSpool`
16. `knowledge_storage._validate_selected_record`
17. `knowledge_model._parse_concept`
18. `knowledge_model._validate_index_references`
19. `knowledge_storage.KnowledgeStorageError`
20. `knowledge_storage.canonical_bytes`
21. `knowledge_model._concept_to_payload`
22. `knowledge_storage.canonical_bytes`
23. `knowledge_storage.KnowledgeStorageError`
24. `knowledge_model._parse_relationship`
25. `knowledge_storage.KnowledgeStorageError`
26. `knowledge_storage.canonical_bytes`
27. `knowledge_model._relationship_to_payload`
28. `knowledge_storage.canonical_bytes`
29. `knowledge_storage.KnowledgeStorageError`
30. `knowledge_storage.canonical_bytes`
31. `knowledge_graph._normalise_edge`
32. `knowledge_storage.canonical_bytes`
33. `knowledge_storage.KnowledgeStorageError`
34. `knowledge_storage.KnowledgeStorageError`
35. `canonical_json.CanonicalArray`
36. `knowledge_storage.KnowledgeStorageError`
37. `canonical_json.CanonicalArray`
38. `canonical_json.CanonicalArray`
39. `knowledge_storage.KnowledgeStorageError`
40. `knowledge_storage.logical_digest`
41. `knowledge_storage.KnowledgeStorageError`
42. `knowledge_storage.digest`
43. `knowledge_storage.canonical_bytes`
44. `knowledge_storage.KnowledgeStorageError`
45. `knowledge_audit.audit_spilled_records`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_audit](../modules/knowledge_audit.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_stream_audit](../modules/knowledge_stream_audit.md)
- [manifest_storage](../modules/manifest_storage.md)
- [storage_sort](../modules/storage_sort.md)
- [storage_spool](../modules/storage_spool.md)

## Behavior

This workflow starts at `knowledge_stream_audit.audit_knowledge_stream`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
