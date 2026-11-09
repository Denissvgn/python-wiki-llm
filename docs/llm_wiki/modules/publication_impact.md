# publication_impact Module

**Path:** `src/llm_wiki_cli/services/publication_impact.py`

## Description

Portable, deterministic architecture-to-public-topic impact and review.

## Imports

| Source | Symbols |
|--------|---------|
| `.knowledge_evidence` | `hash_json`, `sha256_bytes` |
| `.knowledge_storage_io` | `StorageReadSession` |
| `.publication_config` | `load_publication_config`, `publication_path` |
| `.publication_contracts` | `PublicationProtocolError`, `validate_publication_basis`, `validate_publication_report`, `validate_publication_reviews` |
| `.publication_links` | `public_atx_section` |
| `.publication_references` | `capture_reference_inputs`, `recheck_reference_inputs`, `reference_dependency_basis` |
| `.publication_snapshot` | `build_publication_snapshot`, `build_bootstrap_publication_snapshot` |
| `.validation` | `portable_path_key`, `require_repository_relative_path` |
| `__future__` | `annotations` |
| `collections` | `Counter` |
| `copy` | `deepcopy` |
| `fnmatch` | `fnmatchcase` |
| `functools` | `partial` |
| `json` | `json` |
| `pathlib` | `Path` |
| `typing` | `Any`, `Mapping` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["integrations"]
    n1["src"]
    n2["src/llm_wiki_cli/services/publication_impact.py"]
    n0 --> n2
    n1 --> n2
    n2 --> n1
    click n2 "../modules/publication_impact.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `integrations` (3) |
| Inbound | `src` (4) |
| Outbound | `src` (8) |

> All 15 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `read_publication_document` | `(path: str \| Path) -> dict[str, Any]` | — | Read bounded JSON with unique keys and finite values. |
| `_unique_object` | `(pairs)` | — | — |
| `_invalid_constant` | `(value)` | — | — |
| `_seal` | `(value: dict[str, Any], key: str) -> dict[str, Any]` | — | — |
| `_file_hash` | `(session: StorageReadSession, root: Path, relative: str) -> str \| None` | — | — |
| `_topic_versions` | `(config, baseline)` | — | — |
| `publication_target_observation` | `(topic: Mapping[str, Any], raw: bytes \| None) -> dict[str, Any]` | — | Commit supplied public bytes without filesystem or remote access. |
| `_target_hash` | `(session: StorageReadSession, topic: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_projected_file_path` | `(value: object) -> str` | — | — |
| `project_publication_targets` | `(basis: Mapping[str, Any], files: Mapping[str, bytes], baseline: Mapping[str, Any] \| None = None) -> dict[str, Any]` | — | Rebind a captured input basis to checked candidate bytes, without I/O. |
| `capture_publication_basis` | `(consumer_root: str \| Path = '.', *, config_path: str \| Path = '.llm-wiki/publication.json', target_dir: str \| Path \| None = None, baseline: Mapping[str, Any] \| None = None) -> dict[str, Any]` | — | Capture a portable input basis without extraction or remote access. |
| `_dependency_basis` | `(dep: Mapping[str, Any], basis: Mapping[str, Any], providers = None) -> Any` | — | — |
| `_topic_inputs` | `(topic: Mapping[str, Any], basis: Mapping[str, Any], providers = None) -> dict[str, Any]` | — | — |
| `_finding` | `(kind: str, subject: str, details: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_topic_findings` | `(before, after) -> list[dict[str, Any]]` | — | — |
| `compare_publication_impact` | `(candidate: Mapping[str, Any], baseline: Mapping[str, Any] \| None = None, *, reviews: Mapping[str, Any] \| None = None) -> dict[str, Any]` | — | Compare complete bases through the union of previous/current bindings. |
| `resolve_publication_finding` | `(report: Mapping[str, Any], candidate: Mapping[str, Any], *, finding_id: str, reviewer: str, reason: str, reviews: Mapping[str, Any] \| None = None, decision: str = 'still-current') -> dict[str, Any]` | — | Prepare an exact-basis no-edit decision for normal repository review. |
| `_reviewable_target` | `(target, *, retired)` | — | — |
| `_reason_label` | `(reason)` | — | — |
| `render_publication_impact` | `(report: Mapping[str, Any]) -> str` | — | Render inert Markdown for CI summaries, including unresolved coverage. |
