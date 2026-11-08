# checkout Module

**Path:** `integrations/wiki-candidate/checkout.py`

## Description

Bind a local candidate action to the consumer checkout and accepted inputs.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `json` | `json` |
| `llm_wiki_cli.services.knowledge_evidence` | `sha256_bytes` |
| `llm_wiki_cli.services.publication_config` | `publication_control_overlap`, `publication_path` |
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
    n2["src/llm_wiki_cli/services/publication_config.py"]
    n3["src/llm_wiki_cli/services/publication_impact.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n3 --> n1
    n3 --> n2
    click n0 "../modules/checkout.md"
    click n1 "../modules/knowledge_evidence.md"
    click n2 "../modules/publication_config.md"
    click n3 "../modules/publication_impact.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |
| Outbound | [publication_config](../modules/publication_config.md) |
| Outbound | [publication_impact](../modules/publication_impact.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_git` | `(directory: Path, *args: str) -> bytes` | — | — |
| `_revision` | `(value: str) -> str` | — | — |
| `_repository` | `(directory: Path) -> Path` | — | — |
| `_clean` | `(directory: Path, separate_target: Path \| None = None) -> None` | — | — |
| `verified_target` | `(consumer: Path, target_dir: str, target_revision: str) -> str \| None` | — | — |
| `verified_checkout` | `(consumer: Path, source_revision: str, target_dir: str, accepted: dict[str, str]) -> str` | — | — |
| `accepted_inputs` | `(consumer: Path, accepted: dict[str, str], revision: str, runtime: Path) -> tuple[dict[str, str], str \| None]` | — | Read explicitly accepted metadata from Git, independently of the source commit. |
