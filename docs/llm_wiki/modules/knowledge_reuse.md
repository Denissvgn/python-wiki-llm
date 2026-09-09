# knowledge_reuse Module

**Path:** `src/llm_wiki_cli/services/knowledge_reuse.py`

## Description

Versioned input commitments for conservative, validated sync no-ops.

## Imports

| Source | Symbols |
|--------|---------|
| `..` | `__version__` |
| `.contracts` | `KNOWLEDGE_REUSE_SCHEMA_VERSION` |
| `.extraction_service` | `EXTRACTOR_REGISTRY` |
| `.io` | `read_md` |
| `.knowledge_artifacts` | `ArtifactWriteState`, `KnowledgeCommitResult`, `PlannedArtifactWrite` |
| `.knowledge_envelope` | `hash_markdown_snapshot`, `INVENTORY_HASH_EXTENSION`, `build_repository_record`, `hash_inventory` |
| `.knowledge_evidence` | `hash_json`, `is_valid_sha256`, `sha256_bytes` |
| `.knowledge_governance` | `GOVERNANCE_FILENAME` |
| `.knowledge_orchestration` | `runtime_generation_options_hash`, `runtime_source_snapshot_hash` |
| `.validation` | `resolve_portable_workspace_path` |
| `.wiki_media` | `build_asset_index` |
| `.wiki_surface` | `collect_wiki_pages` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `dataclasses` | `asdict`, `replace` |
| `hashlib` | `hashlib` |
| `os` | `os` |
| `pathlib` | `Path` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/knowledge_reuse.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/knowledge_reuse.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (4) |
| Outbound | `src` (12) |

> All 15 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_file_hash` | `(path: Path) -> str` | — | — |
| `validate_reuse_commitment` | `(value: object) -> dict` | — | — |
| `manifest_lifecycle_hash` | `(manifest) -> str` | — | — |
| `repository_input_hash` | `(record) -> str` | — | — |
| `implementation_hash` | `() -> str \| None` | — | Fingerprint installed implementation inputs, without a process-global cache. |
| `wiki_input_hashes` | `(wiki_dir: str \| Path) -> tuple[str, str]` | — | — |
| `bind_reuse_commitment` | `(basis: Mapping[str, object], manifest) -> dict` | — | — |
| `validate_reuse_artifact_parity` | `(knowledge, manifest) -> None` | — | A manifest hint alone never authorizes reuse of a projection. |
| `build_reuse_input_basis` | `(wiki_dir, inventory_result, source_snapshot, generation_inputs, generation_options, repository_evidence, *, include_plugins = True, manifest = None, inventory_complete = True, observation_inputs_hash = None) -> dict[str, object] \| None` | — | Capture the inputs of the deterministic built-in sync pipeline. |
| `unchanged_commit_result` | `(state, manifest, *, dry_run: bool = False)` | — | Return the ordinary result shape using already captured, validated bytes. |
