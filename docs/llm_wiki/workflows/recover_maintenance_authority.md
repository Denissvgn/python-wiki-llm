# recover_maintenance_authority

**Entry point:** `maintenance_service.recover_maintenance_authority`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_service](../modules/maintenance_service.md), [maintenance_state](../modules/maintenance_state.md), [source_snapshot](../modules/source_snapshot.md), [sync_manifest](../modules/sync_manifest.md), [validation](../modules/validation.md)

> Restore one validated complete snapshot; never reconstruct review history.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io._absolute_path`
3. `maintenance_protocol.MaintenanceProtocolError`
4. `maintenance_protocol.MaintenanceProtocolError`
5. `maintenance_protocol.governance_writer_lock`
6. `maintenance_protocol.storage_writer_lock`
7. `maintenance_protocol.load_adoption_marker`
8. `maintenance_protocol.MaintenanceProtocolError`
9. `sync_manifest.SyncManifest.load`
10. `maintenance_state.maintenance_state_hash`
11. `maintenance_state.maintenance_state_hash`
12. `maintenance_protocol.MaintenanceProtocolError`
13. `maintenance_protocol.MaintenanceProtocolError`
14. `knowledge_storage_io.read_guarded`
15. `maintenance_protocol.MaintenanceProtocolError`
16. `maintenance_protocol.MaintenanceProtocolError`
17. `source_snapshot.build_source_snapshot`
18. `knowledge_storage_io._absolute_path`
19. `knowledge_envelope.ConsumedInput`
20. `knowledge_envelope.hash_source_snapshot`
21. `knowledge_envelope.hash_source_snapshot`
22. `maintenance_protocol.MaintenanceProtocolError`
23. `maintenance_protocol.snapshot_wiki`
24. `knowledge_storage.digest`
25. `knowledge_storage_io.read_guarded`
26. `maintenance_protocol.MaintenanceProtocolError`
27. `knowledge_storage_io.read_guarded`
28. `maintenance_protocol.MaintenanceProtocolError`
29. `knowledge_storage.digest`
30. `knowledge_storage_io.read_guarded`
31. `maintenance_protocol.MaintenanceProtocolError`
32. `validation.is_portable_relative_path`
33. `knowledge_evidence.is_valid_sha256`
34. `maintenance_protocol.MaintenanceProtocolError`
35. `knowledge_storage.digest`
36. `maintenance_protocol.MaintenanceProtocolError`
37. `filesystem_guard.atomic_write_guarded_bytes`
38. `filesystem_guard.unlink_guarded_bytes`
39. `filesystem_guard.ensure_guarded_directory`
40. `filesystem_guard.atomic_write_guarded_bytes`
41. `filesystem_guard.atomic_write_guarded_bytes`
42. `maintenance_protocol.guard_maintenance_owner`
43. `knowledge_storage.digest`
44. `knowledge_storage.canonical_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_state](../modules/maintenance_state.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)

## Behavior

Loads and validates one complete retained snapshot before writing. It verifies the requested existing adoption identity, any surviving marker and current owner, and refuses a known newer committed state. For committed snapshots only, a surviving matching marker or owner permits absence of validated knowledge/surface roots and their exact referenced native objects. Filename prefixes and backup inventory entries do not establish ownership; missing authored or unreferenced files and changed current bytes retain their conflict checks.

After every input passes, existing guarded writes restore exact retained bytes and publish the manifest last. Concurrent appearance or substitution cannot authorize an overwrite. Prepared adoption and captured preimages retain their separate explicit modes and source/prose obligations. The operation never fabricates a new identity or history and does not establish backup recency beyond surviving evidence, live source freshness or prose approval.
