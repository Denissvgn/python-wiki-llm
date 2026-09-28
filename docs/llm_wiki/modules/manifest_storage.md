# manifest_storage Module

**Path:** `src/llm_wiki_cli/services/manifest_storage.py`

## Description

Stores manifest v6 as a bounded commit root plus immutable catalogs under `.llm-wiki-manifest/objects/`. Artifact commitments and small generation policy remain in the root; oversized policy is referenced and charged to the caller. Full readers reconstruct and validate the complete logical v5 manifest. Selected readers receive a typed header containing only policy and artifact commitments.

## Imports

| Source | Symbols |
|--------|---------|
| `.canonical_json` | `canonical_chunks` |
| `.immutable` | `freeze` |
| `.knowledge_artifacts` | `_decode_json_object` |
| `.knowledge_storage` | `MAX_EXPANDED_BYTES`, `KnowledgeStorageError`, `canonical_bytes`, `decode_bytes`, `digest`, `logical_digest`, `_hash` |
| `.knowledge_storage_io` | `read_guarded` |
| `.sync_manifest` | `ManifestArtifactHashes`, `SyncManifest`, `validate_manifest_policy`, `MANIFEST_FILENAME` |
| `__future__` | `annotations` |
| `base64` | `base64` |
| `collections.abc` | `Callable`, `Mapping` |
| `dataclasses` | `dataclass` |
| `json` | `json` |
| `pathlib` | `Path` |
| `re` | `re` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/canonical_json.py"]
    n1["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n2["src/llm_wiki_cli/services/immutable.py"]
    n3["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n4["src/llm_wiki_cli/services/knowledge_storage.py"]
    n5["src/llm_wiki_cli/services/knowledge_storage_access.py"]
    n6["src/llm_wiki_cli/services/knowledge_storage_diagnostics.py"]
    n7["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n8["src/llm_wiki_cli/services/knowledge_storage_lifecycle.py"]
    n9["src/llm_wiki_cli/services/knowledge_stream_audit.py"]
    n10["src/llm_wiki_cli/services/manifest_storage.py"]
    n11["src/llm_wiki_cli/services/sync_manifest.py"]
    n1 --> n3
    n1 --> n10
    n1 --> n11
    n3 --> n2
    n3 --> n4
    n3 --> n7
    n3 --> n10
    n3 --> n11
    n4 --> n0
    n5 --> n3
    n5 --> n4
    n5 --> n7
    n5 --> n10
    n5 --> n11
    n6 --> n3
    n6 --> n4
    n6 --> n5
    n6 --> n7
    n6 --> n8
    n6 --> n10
    n6 --> n11
    n7 --> n4
    n8 --> n3
    n8 --> n4
    n8 --> n7
    n8 --> n10
    n8 --> n11
    n9 --> n0
    n9 --> n4
    n9 --> n7
    n9 --> n10
    n9 --> n11
    n10 --> n0
    n10 --> n2
    n10 --> n3
    n10 --> n4
    n10 --> n7
    n10 --> n11
    click n0 "../modules/canonical_json.md"
    click n1 "../modules/documentation_wiki_input.md"
    click n2 "../modules/immutable.md"
    click n3 "../modules/knowledge_artifacts.md"
    click n4 "../modules/knowledge_storage.md"
    click n5 "../modules/knowledge_storage_access.md"
    click n6 "../modules/knowledge_storage_diagnostics.md"
    click n7 "../modules/knowledge_storage_io.md"
    click n8 "../modules/knowledge_storage_lifecycle.md"
    click n9 "../modules/knowledge_stream_audit.md"
    click n10 "../modules/manifest_storage.md"
    click n11 "../modules/sync_manifest.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| Inbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Inbound | [knowledge_storage_access](../modules/knowledge_storage_access.md) |
| Inbound | [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md) |
| Inbound | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) |
| Inbound | [knowledge_stream_audit](../modules/knowledge_stream_audit.md) |
| Outbound | [canonical_json](../modules/canonical_json.md) |
| Outbound | [immutable](../modules/immutable.md) |
| Outbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [sync_manifest](../modules/sync_manifest.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [ManifestStore](../entities/ManifestStore.md) | 77 | — | — |
| [ManifestStoreReader](../entities/ManifestStoreReader.md) | 143 | — | — |
| [ValidatedManifestHeader](../entities/ValidatedManifestHeader.md) | 212 | — | Policy and artifact commitments only; never a complete sync manifest. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `object_path` | `(commitment: str) -> str` | — | — |
| `_descriptor` | `(value: object) -> dict[str, Any]` | — | — |
| `validate_catalog` | `(raw: bytes) -> dict[str, Any]` | — | — |
| `build_manifest_store` | `(payload: Mapping[str, Any]) -> ManifestStore` | — | — |
| `read_manifest_header` | `(raw: bytes, read: Reader) -> ValidatedManifestHeader` | — | — |
| `current_manifest_format` | `(wiki_dir: str \| Path) -> str` | — | — |