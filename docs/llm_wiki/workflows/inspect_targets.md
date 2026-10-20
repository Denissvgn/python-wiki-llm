# inspect_targets

**Entry point:** `analysis_targets.inspect_targets`
**Modules involved:** [analysis_compatibility](../modules/analysis_compatibility.md), [analysis_targets](../modules/analysis_targets.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [sync_manifest](../modules/sync_manifest.md)

> Read committed producer headers, without source discovery or extraction.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io.StorageReadSession`
2. `knowledge_storage_io.StorageReadSession.read`
3. `knowledge_model._parse_bundle`
4. `knowledge_packs.parse_packed_root`
5. `knowledge_model._parse_bundle`
6. `knowledge_storage.parse_store_root`
7. `knowledge_model.parse_knowledge_index`
8. `knowledge_storage_io.StorageReadSession.read`
9. `sync_manifest.SyncManifest.load`
10. `knowledge_storage_io.StorageReadSession.read`
11. `analysis_compatibility.component_record`
12. `knowledge_storage_io.StorageReadSession.recheck`

## Touches

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [analysis_targets](../modules/analysis_targets.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `analysis_targets.inspect_targets`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.

Reads committed knowledge and surface roots and the manifest through guarded storage interfaces. Flat, indexed and packed headers use their existing parsers. Root/surface commitments and read rechecks bind the returned metadata; this is not a full object-store health audit or live source comparison. Missing/corrupt/unsupported metadata produces unknown prerequisites without source discovery, extraction, setup or mutation.

The pure comparator uses project declarations and registered runtime portability, preserving opaque recorded runtime commitments. Matching declared provenance is separate from actual target runtime identity. Unknown helper/profile/patch declarations remain explicit; known differences request the authorized complete target-host capture and review followed by fresh native proof. Component/row/byte bounds do not hide aggregate mismatch counts.
