# sync_recovery Module

**Path:** `src/llm_wiki_cli/services/sync_recovery.py`

## Description

Explicit recovery of unchanged new Markdown pages from a rejected sync.

The owning sync observes Markdown writes that had neither a physical preimage
nor a committed outgoing owner. Before each new write it retains the intended
bytes outside the wiki; completion binds the actual file identity to those
bytes. A rejected operation emits its unique journal directory and exact hash.
Existing source/publication and ownership checks remain mandatory.

`maintenance recover-new-pages` previews or explicitly removes only matching
operation-created pages. It verifies the original wiki identity, committed root
hashes, source-selection commitments, current manifest ownership, page identities
and retained bytes before deletion. Edited or replaced pages and unsafe links
refuse recovery. Native absolute paths identify filesystem inputs; canonical
relative POSIX paths identify wiki pages.

Recovery preserves existing prose, source and committed authority. It does not
validate or restore the whole interrupted snapshot, adopt a wiki or reconstruct
review history. A subsequent owning sync is required. An I/O failure can stop
after partial deletion; all rejected-operation postimages remain available.
Adopted full-snapshot recovery keeps its separate authority contract. Successful
syncs discard only verified private scratch and retain unexpected contents.

## Imports

| Source | Symbols |
|--------|---------|
| `.filesystem_guard` | `atomic_write_guarded_bytes`, `ensure_guarded_directory`, `fresh_no_follow_stat`, `unlink_guarded_bytes` |
| `.io` | `first_unsafe_path_component` |
| `.knowledge_storage` | `canonical_bytes`, `digest` |
| `.knowledge_storage_io` | `_absolute_path`, `_identity`, `read_guarded` |
| `.maintenance_protocol` | `governance_writer_lock`, `storage_writer_lock` |
| `.request_json` | `_pairs`, `_constant` |
| `.source_snapshot` | `SourceSnapshot` |
| `.sync_manifest` | `SyncManifest` |
| `.wiki_write_basis` | `ACTIVE_SYNC_JOURNAL` |
| `__future__` | `annotations` |
| `contextlib` | `contextmanager` |
| `dataclasses` | `dataclass`, `field` |
| `json` | `json` |
| `pathlib` | `Path`, `PurePosixPath` |
| `re` | `re` |
| `sys` | `sys` |
| `tempfile` | `tempfile` |
| `typing` | `Any` |
| `uuid` | `UUID`, `uuid4` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/maintenance_cmd.py"]
    n1["src/llm_wiki_cli/commands/sync_cmd.py"]
    n2["src/llm_wiki_cli/services/filesystem_guard.py"]
    n3["src/llm_wiki_cli/services/io.py"]
    n4["src/llm_wiki_cli/services/knowledge_storage.py"]
    n5["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n6["src/llm_wiki_cli/services/maintenance_protocol.py"]
    n7["src/llm_wiki_cli/services/request_json.py"]
    n8["src/llm_wiki_cli/services/source_snapshot.py"]
    n9["src/llm_wiki_cli/services/sync_manifest.py"]
    n10["src/llm_wiki_cli/services/sync_recovery.py"]
    n11["src/llm_wiki_cli/services/wiki_write_basis.py"]
    n0 --> n7
    n0 --> n10
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n6
    n1 --> n8
    n1 --> n9
    n1 --> n10
    n2 --> n11
    n3 --> n11
    n5 --> n2
    n5 --> n3
    n5 --> n4
    n6 --> n2
    n6 --> n3
    n6 --> n4
    n6 --> n5
    n6 --> n7
    n6 --> n8
    n6 --> n9
    n6 --> n11
    n8 --> n2
    n9 --> n3
    n9 --> n8
    n10 --> n2
    n10 --> n3
    n10 --> n4
    n10 --> n5
    n10 --> n6
    n10 --> n7
    n10 --> n8
    n10 --> n9
    n10 --> n11
    n11 --> n8
    click n0 "../modules/maintenance_cmd.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/filesystem_guard.md"
    click n3 "../modules/io.md"
    click n4 "../modules/knowledge_storage.md"
    click n5 "../modules/knowledge_storage_io.md"
    click n6 "../modules/maintenance_protocol.md"
    click n7 "../modules/request_json.md"
    click n8 "../modules/source_snapshot.md"
    click n9 "../modules/sync_manifest.md"
    click n10 "../modules/sync_recovery.md"
    click n11 "../modules/wiki_write_basis.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [maintenance_cmd](../modules/maintenance_cmd.md) |
| Inbound | [sync_cmd](../modules/sync_cmd.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [maintenance_protocol](../modules/maintenance_protocol.md) |
| Outbound | [request_json](../modules/request_json.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |
| Outbound | [sync_manifest](../modules/sync_manifest.md) |
| Outbound | [wiki_write_basis](../modules/wiki_write_basis.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [SyncRecoveryError](../entities/SyncRecoveryError.md) | 42 | `ValueError` | A recovery proof or operation cannot be admitted safely. |
| [NewPageJournal](../entities/NewPageJournal.md) | 138 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_safe` | `(path: Path) -> None` | — | — |
| `_page` | `(name: str) -> str` | — | — |
| `_authority` | `(root: Path)` | — | — |
| `_anchors` | `(root: Path) -> dict[str, str \| None]` | — | — |
| `_root_identity` | `(root: Path) -> list[int]` | — | — |
| `_policy_inputs` | `(snapshot: SourceSnapshot) -> dict[str, str \| None]` | — | — |
| `_owned_pages` | `(manifest) -> set[str]` | — | Missing pages with committed outgoing owners are never new-page writes. |
| `capture_new_sync_pages` | `(wiki_dir, snapshot, manifest = None)` | `@contextmanager` | Retain rejected writes; never repair them implicitly. |
| `recover_new_sync_pages` | `(wiki_dir, *, recovery_dir, expected_journal_hash, dry_run = False)` | — | Remove only unchanged transaction-created pages, preserving postimages. |