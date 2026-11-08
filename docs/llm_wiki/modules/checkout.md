# checkout Module

**Path:** `integrations/wiki-candidate/checkout.py`

## Description

Bind a local candidate action to the consumer checkout and accepted inputs.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `llm_wiki_cli.services.knowledge_evidence` | `sha256_bytes` |
| `llm_wiki_cli.services.knowledge_storage_io` | `read_guarded` |
| `llm_wiki_cli.services.publication_candidate` | `MAX_FILE_BYTES`, `_read_tree` |
| `llm_wiki_cli.services.publication_config` | `DELIVERY_CHECKPOINT_PATH`, `_relative_path`, `publication_control_overlap`, `publication_path` |
| `llm_wiki_cli.services.publication_impact` | `MAX_JSON_BYTES` |
| `os` | `os` |
| `pathlib` | `Path` |
| `re` | `re` |
| `subprocess` | `subprocess` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["integrations/wiki-candidate/checkout.py"]
    n1["src/llm_wiki_cli/services/knowledge_evidence.py"]
    n2["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n3["src/llm_wiki_cli/services/publication_candidate.py"]
    n4["src/llm_wiki_cli/services/publication_config.py"]
    n5["src/llm_wiki_cli/services/publication_impact.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n4
    n0 --> n5
    n3 --> n1
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n5 --> n1
    n5 --> n2
    n5 --> n4
    click n0 "../modules/checkout.md"
    click n1 "../modules/knowledge_evidence.md"
    click n2 "../modules/knowledge_storage_io.md"
    click n3 "../modules/publication_candidate.md"
    click n4 "../modules/publication_config.md"
    click n5 "../modules/publication_impact.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [publication_candidate](../modules/publication_candidate.md) |
| Outbound | [publication_config](../modules/publication_config.md) |
| Outbound | [publication_impact](../modules/publication_impact.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_git` | `(directory: Path, *args: str) -> bytes` | — | — |
| `_revision` | `(value: str) -> str` | — | — |
| `_repository` | `(directory: Path) -> Path` | — | — |
| `_clean` | `(directory: Path, separate_target: Path \| None = None) -> None` | — | — |
| `_verify_target_blobs` | `(target: Path, pin: str, receipt_files: dict[str, str] \| None) -> None` | — | Bind the public bytes used by the exporter to the unfiltered Git tree. |
| `verified_target` | `(consumer: Path, target_dir: str, target_revision: str, *, receipt_files: dict[str, str] \| None = None) -> str \| None` | — | — |
| `committed_blob` | `(root: Path, pin: str, relative: str, maximum: int) -> tuple[str, bytes]` | — | Read one regular blob from a pinned commit, without checking out or filtering it. |
| `verified_checkout` | `(consumer: Path, source_revision: str, target_dir: str, accepted: dict[str, str]) -> str` | — | — |
| `accepted_inputs` | `(consumer: Path, accepted: dict[str, str], revision: str, runtime: Path) -> tuple[dict[str, str], str \| None]` | — | Read explicitly accepted metadata from Git, independently of the source commit. |
